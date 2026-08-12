import contextlib
import json
import logging
import os
import re
import sqlite3
from datetime import datetime
from typing import Any, Optional

logger = logging.getLogger("db")

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "callers.db"))
SENSITIVE_KEY_PATTERNS = (
    "account",
    "bank",
    "card",
    "cvv",
    "otp",
    "pin",
    "upi",
    "aadhaar",
    "pan",
    "passport",
    "ifsc",
    "routing",
    "transaction",
    "balance",
    "phone",
    "mobile",
    "email",
    "number",
    "id",
)


def _is_sensitive_key(key: str) -> bool:
    normalized = key.strip().lower().replace(" ", "_")
    return any(pattern in normalized for pattern in SENSITIVE_KEY_PATTERNS)


def sanitize_text(text: str) -> str:
    """Redact sensitive information like emails, phone numbers, and potential IDs from free text."""
    if not text:
        return text
    
    # Redact email addresses
    text = re.sub(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', '[REDACTED EMAIL]', text)
    # Redact 10 to 16 digit numbers (Phone, Aadhaar, Account, Card)
    text = re.sub(r'\b\d{10,16}\b', '[REDACTED ID]', text)
    # Redact PAN format (5 letters, 4 digits, 1 letter)
    text = re.sub(r'\b[A-Za-z]{5}\d{4}[A-Za-z]\b', '[REDACTED PAN]', text)
    # Redact PIN/OTP context followed by numbers
    text = re.sub(r'\b(?:otp|pin|cvv)[\s:-]+\d{3,6}\b', '[REDACTED CREDENTIAL]', text, flags=re.IGNORECASE)
    
    return text


def sanitize_facts(facts: dict[str, Any]) -> dict[str, Any]:
    """Keep only safe context that is relevant to the service and not personally sensitive."""
    if not isinstance(facts, dict):
        return {}

    cleaned: dict[str, Any] = {}
    for key, value in facts.items():
        if not isinstance(key, str):
            continue

        if _is_sensitive_key(key):
            continue

        if any(token in key.lower() for token in ("otp", "pin", "cvv", "card", "aadhaar", "bank", "account", "number", "id")):
            continue

        cleaned[key] = value if isinstance(value, (str, int, float, bool)) else str(value)

    return cleaned


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS callers (
            user_id TEXT PRIMARY KEY,
            name TEXT,
            language_preference TEXT,
            facts TEXT,
            last_interaction TIMESTAMP,
            chat_history TEXT
        )
        """
    )

    # Simple migration: attempt to add the chat_history column if it doesn't exist
    with contextlib.suppress(sqlite3.OperationalError):
        cursor.execute("ALTER TABLE callers ADD COLUMN chat_history TEXT")

    # Day 7: Escalation requests table for human-help tickets
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS escalations (
            reference_id TEXT PRIMARY KEY,
            caller_id TEXT,
            caller_name TEXT,
            reason TEXT,
            summary TEXT,
            what_checked TEXT,
            urgency TEXT,
            language TEXT,
            preferred_followup TEXT,
            status TEXT DEFAULT 'open',
            created_at TIMESTAMP
        )
        """
    )

    conn.commit()
    conn.close()


def get_caller(identifier: str) -> Optional[dict[str, Any]]:
    """Look up a caller by their user_id or name."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT user_id, name, language_preference, facts, last_interaction, chat_history
        FROM callers
        WHERE user_id = ? OR name = ?
        """,
        (identifier, identifier),
    )

    row = cursor.fetchone()
    conn.close()

    if row:
        facts = json.loads(row[3]) if row[3] else {}
        history = json.loads(row[5]) if len(row) > 5 and row[5] else []
        return {
            "user_id": row[0],
            "name": row[1],
            "language_preference": row[2],
            "facts": sanitize_facts(facts),
            "last_interaction": row[4],
            "chat_history": history,
        }
    return None


def save_caller(user_id: str, name: str, language_preference: str, facts: dict[str, Any]):
    """Save or update a caller's information while filtering sensitive data."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    safe_facts = sanitize_facts(facts)
    now = datetime.now().isoformat()
    facts_json = json.dumps(safe_facts, ensure_ascii=False)

    cursor.execute(
        """
        INSERT INTO callers (user_id, name, language_preference, facts, last_interaction)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            name = excluded.name,
            language_preference = excluded.language_preference,
            facts = excluded.facts,
            last_interaction = excluded.last_interaction
        """,
        (user_id, name, language_preference, facts_json, now),
    )

    conn.commit()
    conn.close()
    logger.info("Saved info for caller: %s (ID: %s)", name, user_id)


def save_chat_history(user_id: str, chat_history: list[dict[str, Any]]):
    """Save the chat history for a specific caller."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    history_json = json.dumps(chat_history, ensure_ascii=False)

    # We use INSERT OR IGNORE and then UPDATE to handle cases where the user_id
    # doesn't exist yet (though it should by the time we save history).
    cursor.execute(
        """
        INSERT INTO callers (user_id, chat_history)
        VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            chat_history = excluded.chat_history
        """,
        (user_id, history_json),
    )
    conn.commit()
    conn.close()
    logger.debug("Saved chat history for caller (ID: %s)", user_id)


def create_escalation(
    caller_id: str,
    caller_name: str,
    reason: str,
    summary: str,
    what_checked: str,
    urgency: str,
    language: str,
    preferred_followup: str,
) -> str:
    """Create a human-help escalation request. Updates existing if open."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    safe_summary = sanitize_text(summary)
    safe_what_checked = sanitize_text(what_checked)
    safe_reason = sanitize_text(reason)
    now = datetime.now().isoformat()

    # Check for existing open escalation
    cursor.execute(
        "SELECT reference_id, summary FROM escalations WHERE caller_id = ? AND status = 'open' ORDER BY created_at DESC LIMIT 1",
        (caller_id,)
    )
    existing = cursor.fetchone()
    
    if existing:
        reference_id = existing[0]
        old_summary = existing[1]
        new_summary = f"{old_summary}\n[Update]: {safe_summary}"
        
        cursor.execute(
            """
            UPDATE escalations 
            SET summary = ?, what_checked = ?, urgency = ?, language = ?, preferred_followup = ?
            WHERE reference_id = ?
            """,
            (new_summary, safe_what_checked, urgency, language, preferred_followup, reference_id)
        )
        conn.commit()
        conn.close()
        logger.info("Updated escalation %s for caller %s", reference_id, caller_name)
        return reference_id

    today = datetime.now().strftime("%Y%m%d")

    # Count existing escalations for today to generate sequential suffix
    cursor.execute(
        "SELECT COUNT(*) FROM escalations WHERE reference_id LIKE ?",
        (f"MB-{today}-%",),
    )
    count = cursor.fetchone()[0]
    reference_id = f"MB-{today}-{count + 1:03d}"

    cursor.execute(
        """
        INSERT INTO escalations
            (reference_id, caller_id, caller_name, reason, summary,
             what_checked, urgency, language, preferred_followup, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'open', ?)
        """,
        (
            reference_id,
            caller_id,
            caller_name,
            safe_reason,
            safe_summary,
            safe_what_checked,
            urgency,
            language,
            preferred_followup,
            now,
        ),
    )

    conn.commit()
    conn.close()
    logger.info("Created escalation %s for caller %s", reference_id, caller_name)
    return reference_id


def get_open_escalations() -> list[dict[str, Any]]:
    """Return all escalation requests (most recent first)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT reference_id, caller_name, reason, summary, what_checked,
               urgency, language, preferred_followup, status, created_at
        FROM escalations
        ORDER BY created_at DESC
        """
    )

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "reference_id": r[0],
            "caller_name": r[1],
            "reason": r[2],
            "summary": r[3],
            "what_checked": r[4],
            "urgency": r[5],
            "language": r[6],
            "preferred_followup": r[7],
            "status": r[8],
            "created_at": r[9],
        }
        for r in rows
    ]


def get_escalation_status(reference_id: str) -> str:
    """Get the status of an escalation request."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM escalations WHERE reference_id = ?", (reference_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row[0]
    return "unknown"


init_db()

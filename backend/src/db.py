import contextlib
import json
import logging
import os
import re
import sqlite3
import threading
import urllib.request
from datetime import datetime
from typing import Any, Optional

from dotenv import load_dotenv

load_dotenv(".env.local")

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


def _send_discord_webhook(payload: dict):
    url = os.environ.get("DISCORD_HUMAN_SUPPORT_WEBHOOK_URL")
    if not url:
        logger.warning("DISCORD_HUMAN_SUPPORT_WEBHOOK_URL not set in environment.")
        return
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json', 'User-Agent': 'MoneyBuddy/1.0'}
        )
        urllib.request.urlopen(req, timeout=5)
    except Exception as e:
        logger.error("Failed to send Discord webhook: %s", e)


def notify_discord(reference_id, caller_name, reason, summary, what_checked, urgency, language, preferred_followup, callback_time):
    color = 16711680 if str(urgency).lower() in ["high", "emergency"] else 3447003
    payload = {
        "content": "🚨 **New Escalation Ticket Created** 🚨" if str(urgency).lower() in ["high", "emergency"] else "🎫 **New Escalation Ticket**",
        "embeds": [{
            "title": f"Ticket: {reference_id}",
            "color": color,
            "fields": [
                {"name": "Caller Name", "value": str(caller_name) or "Unknown", "inline": True},
                {"name": "Urgency", "value": str(urgency) or "Unknown", "inline": True},
                {"name": "Reason", "value": str(reason) or "Not provided"},
                {"name": "Summary", "value": str(summary) or "Not provided"},
                {"name": "What was checked", "value": str(what_checked) or "Not provided"},
                {"name": "Follow-up via", "value": f"{preferred_followup} ({language})"},
                {"name": "Callback Time", "value": str(callback_time) or "Not provided"}
            ]
        }]
    }
    threading.Thread(target=_send_discord_webhook, args=(payload,), daemon=True).start()


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




def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
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
            callback_time TEXT,
            status TEXT DEFAULT 'open',
            created_at TIMESTAMP
        )
        """
    )
    
    with contextlib.suppress(sqlite3.OperationalError):
        cursor.execute("ALTER TABLE escalations ADD COLUMN callback_time TEXT")

    conn.commit()
    conn.close()



def create_escalation(
    caller_id: str,
    caller_name: str,
    reason: str,
    summary: str,
    what_checked: str,
    urgency: str,
    language: str,
    preferred_followup: str,
    callback_time: str,
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
            SET summary = ?, what_checked = ?, urgency = ?, language = ?, preferred_followup = ?, callback_time = ?
            WHERE reference_id = ?
            """,
            (new_summary, safe_what_checked, urgency, language, preferred_followup, callback_time, reference_id)
        )
        conn.commit()
        conn.close()
        logger.info("Updated escalation %s for caller %s", reference_id, caller_name)
        notify_discord(reference_id, caller_name, "[UPDATE] " + safe_reason, new_summary, safe_what_checked, urgency, language, preferred_followup, callback_time)
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
             what_checked, urgency, language, preferred_followup, callback_time, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'open', ?)
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
            callback_time,
            now,
        ),
    )

    conn.commit()
    conn.close()
    logger.info("Created escalation %s for caller %s", reference_id, caller_name)
    notify_discord(reference_id, caller_name, safe_reason, safe_summary, safe_what_checked, urgency, language, preferred_followup, callback_time)
    return reference_id


def get_open_escalations() -> list[dict[str, Any]]:
    """Return all escalation requests (most recent first)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT reference_id, caller_name, reason, summary, what_checked,
               urgency, language, preferred_followup, callback_time, status, created_at
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
            "callback_time": r[8],
            "status": r[9],
            "created_at": r[10],
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

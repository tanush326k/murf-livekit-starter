import contextlib
import json
import logging
import os
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


init_db()

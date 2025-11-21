from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, Optional
import uuid
import re

from app.database import get_db, query_db as _query_db


def query_db(query: str, args: Iterable[Any] = (), one: bool = False):
    """
    Wrapper around app.database.query_db for compatibility.
    """
    return _query_db(query, args=args, one=one, commit=False)


def execute_db(query: str, args: Iterable[Any] = (), return_id: bool = False):
    """
    Execute INSERT/UPDATE/DELETE using the shared DB connection.
    Optionally return the last inserted id.
    """
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(query, args)
    conn.commit()
    lastrowid = cursor.lastrowid
    cursor.close()
    if return_id:
        return lastrowid
    return True


def create_notification(user_id: int, message: str, msg_type: str = "info"):
    """
    Convenience helper to create a notification for a user.
    """
    execute_db(
        """
        INSERT INTO notifications (user_id, message, type)
        VALUES (%s, %s, %s)
        """,
        (user_id, message, msg_type),
    )


def save_qr_session(client_id: int, expires_minutes: int = 5, proxy_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Create a short-lived QR session token that volunteers can validate.
    """
    session_id = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(minutes=expires_minutes)

    execute_db(
        """
        INSERT INTO qr_sessions (session_id, client_id, proxy_id, status, expires_at)
        VALUES (%s, %s, %s, 'pending', %s)
        """,
        (session_id, client_id, proxy_id, expires_at),
    )

    return {"session_id": session_id, "expires_at": expires_at}


def validate_qr_session(session_id: str):
    """
    Validate and update a QR session record.
    """
    session = query_db(
        "SELECT * FROM qr_sessions WHERE session_id=%s",
        (session_id,),
        one=True,
    )

    if not session:
        return None

    if session["status"] in ("completed", "expired", "cancelled"):
        return None

    if session["expires_at"] < datetime.utcnow():
        execute_db(
            "UPDATE qr_sessions SET status='expired' WHERE session_id=%s",
            (session_id,),
        )
        return None

    return session


SUSPICIOUS_TERMS = {"test", "fake", "asdf", "demo", "sample", "null", "none"}
ADDRESS_PATTERN = re.compile(r"\d+\s+[A-Za-z0-9#.\-\s]{5,}")
NO_SHOW_THRESHOLD = 3


def is_valid_address(address: str) -> bool:
    if not address:
        return False
    cleaned = address.strip()
    return bool(ADDRESS_PATTERN.match(cleaned))


def looks_suspicious_client_submission(full_name: str, address: str, email: str) -> bool:
    combo = f"{full_name} {address} {email}".lower()
    return any(term in combo for term in SUSPICIOUS_TERMS)


def flag_client_account(client_id: int, reason: str):
    execute_db(
        """
        UPDATE clients
        SET notes = CONCAT('[AUTO FLAG] ', %s, '\n', COALESCE(notes, ''))
        WHERE client_id=%s
        """,
        (reason, client_id),
    )


def log_no_show(client_id: int, logged_by: Optional[int] = None, reason: Optional[str] = None, schedule_id: Optional[int] = None):
    client = query_db(
        """
        SELECT c.client_id, c.client_number, c.no_show_count, u.user_id, u.full_name
        FROM clients c
        JOIN users u ON u.user_id = c.user_id
        WHERE c.client_id=%s
        """,
        (client_id,),
        one=True,
    )
    if not client:
        return False

    log_id = execute_db(
        """
        INSERT INTO no_show_logs (client_id, schedule_id, logged_by, reason)
        VALUES (%s, %s, %s, %s)
        """,
        (client_id, schedule_id, logged_by, reason or None),
        return_id=True,
    )

    execute_db(
        "UPDATE clients SET no_show_count = no_show_count + 1 WHERE client_id=%s",
        (client_id,),
    )

    new_count = client["no_show_count"] + 1

    create_notification(
        client["user_id"],
        "You missed your scheduled pickup. Please contact support to reschedule.",
        "warning",
    )

    admin_users = query_db("SELECT user_id FROM users WHERE role='admin'")
    for admin in admin_users:
        create_notification(
            admin["user_id"],
            f"{client['full_name']} ({client['client_number'] or 'unassigned'}) missed their pickup.",
            "danger" if new_count >= NO_SHOW_THRESHOLD else "warning",
        )

    if logged_by:
        create_notification(
            logged_by,
            f"No-show recorded for {client['client_number'] or client_id}.",
            "info",
        )

    if new_count >= NO_SHOW_THRESHOLD:
        execute_db(
            """
            UPDATE no_show_logs
            SET threshold_reached=1, action_taken='Flagged for outreach'
            WHERE log_id=%s
            """,
            (log_id,),
        )
        create_notification(
            client["user_id"],
            "Multiple no-shows detected. Your account is flagged for outreach. Please contact support to keep benefits active.",
            "danger",
        )

    return True

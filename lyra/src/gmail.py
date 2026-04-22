"""Gmail threaded reply sender via Google API (service account).

Spec §6 step 5: Approved body → Gmail threaded reply → customer receives booking link.
"""

from __future__ import annotations

import base64
import logging
import os
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)

_SENDER_ADDRESS = os.getenv("GMAIL_SENDER_ADDRESS", "leads@fornest.ca")
_SENDER_NAME = os.getenv("GMAIL_SENDER_NAME", "Fornest Automotive")


def _get_service() -> object:
    """Build Gmail API service from service account credentials."""
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        creds_path = os.getenv("GMAIL_SERVICE_ACCOUNT_JSON", "secrets/gmail-sa.json")
        scopes = ["https://www.googleapis.com/auth/gmail.send"]
        credentials = service_account.Credentials.from_service_account_file(
            creds_path, scopes=scopes
        ).with_subject(_SENDER_ADDRESS)
        return build("gmail", "v1", credentials=credentials, cache_discovery=False)
    except Exception as exc:
        logger.warning("Gmail service init failed: %s", exc)
        return None


def _encode_message(
    to: str,
    subject: str,
    body: str,
    thread_id: str | None,
    in_reply_to: str | None,
) -> dict:  # type: ignore[type-arg]
    """Build a base64-encoded RFC 2822 message dict for the Gmail API."""
    msg = MIMEText(body, "plain", "utf-8")
    msg["To"] = to
    msg["From"] = f"{_SENDER_NAME} <{_SENDER_ADDRESS}>"
    msg["Subject"] = subject
    if in_reply_to:
        msg["In-Reply-To"] = in_reply_to
        msg["References"] = in_reply_to

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    payload: dict = {"raw": raw}  # type: ignore[type-arg]
    if thread_id:
        payload["threadId"] = thread_id
    return payload


async def send_threaded_reply(
    to_email: str,
    subject: str,
    body: str,
    thread_id: str | None = None,
    message_id: str | None = None,
) -> bool:
    """Send an approved reply as a threaded Gmail message.

    Returns True on success, False on failure (never raises — caller logs the result).
    """
    service = _get_service()
    if service is None:
        logger.error("Gmail service unavailable — reply NOT sent to %s", to_email)
        return False

    try:
        payload = _encode_message(to_email, subject, body, thread_id, message_id)
        service.users().messages().send(userId="me", body=payload).execute()  # type: ignore[attr-defined]
        logger.info("Gmail reply sent to %s (thread=%s)", to_email, thread_id)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.error("Gmail send failed: %s", exc)
        return False

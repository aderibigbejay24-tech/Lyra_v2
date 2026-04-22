"""Telegram approval card fan-out and callback handler.

Spec §4: send_for_approval(draft) — post dual-channel approval card.
Uses the Bot API directly via httpx (no PTB dependency at runtime).
"""

from __future__ import annotations

import json
import logging
import os
from uuid import UUID

import httpx

from src.models import DraftRecord

logger = logging.getLogger(__name__)

_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
_APPROVAL_CHAT = os.getenv("TELEGRAM_APPROVAL_CHAT_ID", "")
_ALERT_CHAT = os.getenv("TELEGRAM_ALERT_CHAT_ID", "")
_BASE = f"https://api.telegram.org/bot{_BOT_TOKEN}"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _post(method: str, payload: dict) -> dict:  # type: ignore[type-arg]
    if not _BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN not set — skipping Telegram call")
        return {"ok": False, "description": "token not configured"}
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(f"{_BASE}/{method}", json=payload)
        data = resp.json()
        if not data.get("ok"):
            logger.error("Telegram %s error: %s", method, data.get("description"))
        return data  # type: ignore[return-value]


def _draft_card_text(draft: DraftRecord) -> str:
    lead = draft.lead
    out = draft.output
    vehicle_line = (
        f"{lead.vehicle_year} {lead.make} {lead.model}"
        if lead.vehicle_year and lead.make and lead.model
        else "Vehicle TBD"
    )
    return (
        f"🚗 *New lead — approval needed*\n\n"
        f"*From:* {lead.customer_name or lead.customer_email}\n"
        f"*Vehicle:* {vehicle_line}\n"
        f"*Rep:* {out.recommended_rep.value}\n"
        f"*Confidence:* {out.confidence:.0%}\n\n"
        f"*Subject:* {out.subject}\n\n"
        f"{out.body}\n\n"
        f"_Draft ID: `{draft.draft_id}`_"
    )


def _approval_keyboard(draft_id: UUID) -> dict:  # type: ignore[type-arg]
    return {
        "inline_keyboard": [
            [
                {"text": "✅ Approve", "callback_data": f"approve:{draft_id}"},
                {"text": "✏️ Edit", "callback_data": f"edit:{draft_id}"},
                {"text": "❌ Deny", "callback_data": f"deny:{draft_id}"},
            ]
        ]
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def send_approval_card(draft: DraftRecord) -> bool:
    """Send the draft as an inline-keyboard approval card to the approval chat."""
    result = await _post(
        "sendMessage",
        {
            "chat_id": _APPROVAL_CHAT,
            "text": _draft_card_text(draft),
            "parse_mode": "Markdown",
            "reply_markup": json.dumps(_approval_keyboard(draft.draft_id)),
        },
    )
    return result.get("ok", False)


async def send_escalation_alert(draft: DraftRecord) -> bool:
    """Post an escalation-only alert (no approve buttons) to the alert chat."""
    lead = draft.lead
    out = draft.output
    text = (
        f"🚨 *Escalation alert — human action required*\n\n"
        f"*From:* {lead.customer_name or lead.customer_email}\n"
        f"*Reason:* {out.escalation_reason or 'See lead details'}\n"
        f"*Lead ID:* `{lead.lead_id}`\n\n"
        f"*Message:*\n_{lead.message}_"
    )
    result = await _post(
        "sendMessage",
        {"chat_id": _ALERT_CHAT or _APPROVAL_CHAT, "text": text, "parse_mode": "Markdown"},
    )
    return result.get("ok", False)


async def send_booking_notification(
    rep_chat_id: str,
    customer_name: str,
    vehicle: str,
    start_time: str,
    stock: str | None,
) -> bool:
    """Notify a rep of a confirmed TidyCal booking."""
    text = (
        f"📅 *New booking confirmed*\n\n"
        f"*Customer:* {customer_name}\n"
        f"*Vehicle:* {vehicle}\n"
        f"*Time:* {start_time}\n"
        f"*Stock:* {stock or 'TBD'}"
    )
    result = await _post(
        "sendMessage",
        {"chat_id": rep_chat_id, "text": text, "parse_mode": "Markdown"},
    )
    return result.get("ok", False)


async def answer_callback(callback_query_id: str, text: str) -> bool:
    """Acknowledge a Telegram inline button tap."""
    result = await _post(
        "answerCallbackQuery",
        {"callback_query_id": callback_query_id, "text": text},
    )
    return result.get("ok", False)

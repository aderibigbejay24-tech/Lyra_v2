"""WhatsApp approval card fan-out via Evolution API.

Spec §4: send_for_approval(draft) — dual-channel with Telegram.
Evolution API is the self-hosted WhatsApp gateway used by Make.com.
"""

from __future__ import annotations

import logging
import os
from uuid import UUID

import httpx

from src.models import DraftRecord

logger = logging.getLogger(__name__)

_API_URL = os.getenv("EVOLUTION_API_URL", "").rstrip("/")
_API_KEY = os.getenv("EVOLUTION_API_KEY", "")
_INSTANCE = os.getenv("EVOLUTION_INSTANCE", "fornest")
_APPROVAL_JID = os.getenv("WHATSAPP_APPROVAL_JID", "")  # rep's WhatsApp number@s.whatsapp.net


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _headers() -> dict[str, str]:
    return {"apikey": _API_KEY, "Content-Type": "application/json"}


async def _post(endpoint: str, payload: dict) -> dict:  # type: ignore[type-arg]
    if not _API_URL or not _API_KEY:
        logger.warning("Evolution API not configured — skipping WhatsApp call")
        return {"status": "skipped"}
    url = f"{_API_URL}/{endpoint}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(url, json=payload, headers=_headers())
        try:
            return resp.json()  # type: ignore[return-value]
        except Exception:  # noqa: BLE001
            return {"status": resp.status_code}


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
        f"From: {lead.customer_name or lead.customer_email}\n"
        f"Vehicle: {vehicle_line}\n"
        f"Rep: {out.recommended_rep.value} | Confidence: {out.confidence:.0%}\n\n"
        f"Subject: {out.subject}\n\n"
        f"{out.body}\n\n"
        f"Draft ID: {draft.draft_id}\n\n"
        f"Reply: APPROVE / DENY / EDIT"
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def send_approval_card(draft: DraftRecord) -> bool:
    """Send draft approval card via Evolution API to the approval WhatsApp JID."""
    payload = {
        "number": _APPROVAL_JID,
        "options": {"delay": 200, "presence": "composing"},
        "textMessage": {"text": _draft_card_text(draft)},
    }
    result = await _post(f"message/sendText/{_INSTANCE}", payload)
    ok = "key" in result or result.get("status") in (200, "skipped")
    if not ok:
        logger.error("WhatsApp send_approval_card failed: %s", result)
    return ok


async def send_escalation_alert(draft: DraftRecord) -> bool:
    """Post escalation alert to WhatsApp (no reply options — human-only)."""
    lead = draft.lead
    out = draft.output
    text = (
        f"🚨 ESCALATION — human action required\n\n"
        f"From: {lead.customer_name or lead.customer_email}\n"
        f"Reason: {out.escalation_reason or 'See lead details'}\n"
        f"Lead ID: {lead.lead_id}\n\n"
        f"Message:\n{lead.message}"
    )
    payload = {
        "number": _APPROVAL_JID,
        "options": {"delay": 200},
        "textMessage": {"text": text},
    }
    result = await _post(f"message/sendText/{_INSTANCE}", payload)
    return "key" in result or result.get("status") in (200, "skipped")


async def send_booking_notification(
    jid: str,
    customer_name: str,
    vehicle: str,
    start_time: str,
    stock: str | None,
) -> bool:
    """Notify a rep of a confirmed TidyCal booking via WhatsApp."""
    text = (
        f"📅 New booking confirmed\n\n"
        f"Customer: {customer_name}\n"
        f"Vehicle: {vehicle}\n"
        f"Time: {start_time}\n"
        f"Stock: {stock or 'TBD'}"
    )
    payload = {
        "number": jid,
        "options": {"delay": 200},
        "textMessage": {"text": text},
    }
    result = await _post(f"message/sendText/{_INSTANCE}", payload)
    return "key" in result or result.get("status") in (200, "skipped")

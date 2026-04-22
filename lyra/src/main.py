"""FastAPI application — Lyra Lead Guardian v2.1.

Routes:
  POST /draft-reply          Ingest lead, parse, match inventory, call Claude, fan-out.
  POST /approve/{draft_id}   Record approval/edit/denial (first-approver-wins).
  POST /deny/{draft_id}      Convenience alias for denial.
  POST /telegram-webhook     Telegram inline-keyboard callback handler.
  POST /booking-webhook      TidyCal booking confirmation handler.
  GET  /health               Uptime probe (Make.com keep-warm + Fly.io).
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, Request, status
from fastapi.responses import JSONResponse

from src import approval, telegram, whatsapp
from src.claude_client import draft_reply as claude_draft_reply
from src.gmail import send_threaded_reply
from src.hillz_inventory import lookup_inventory
from src.lead_parser import is_escalation_trigger, parse_lead
from src.models import (
    ApprovalDecision,
    ApprovalRequest,
    ApprovalResponse,
    BookingWebhookPayload,
    DraftRecord,
    DraftReplyRequest,
    DraftReplyResponse,
    HealthResponse,
    LeadStatus,
)
from src.sheets import build_audit_row, log_event

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

_APP_SECRET = os.getenv("APP_SECRET", "")


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[type-arg]
    logger.info("Lyra Lead Guardian v2.1 starting up")
    yield
    logger.info("Lyra shutting down")


app = FastAPI(
    title="Lyra Lead Guardian",
    version="2.1.0",
    description="Inbound lead qualifier and appointment setter for Fornest Automotive.",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Auth helper
# ---------------------------------------------------------------------------


def _verify_secret(x_lyra_secret: str | None) -> None:
    """Reject requests without the shared secret when APP_SECRET is set."""
    if _APP_SECRET and x_lyra_secret != _APP_SECRET:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid secret")


# ---------------------------------------------------------------------------
# Background: fan-out approval cards
# ---------------------------------------------------------------------------


async def _fan_out_approval(draft: DraftRecord) -> None:
    """Send approval cards to Telegram and WhatsApp simultaneously."""
    await asyncio.gather(
        telegram.send_approval_card(draft),
        whatsapp.send_approval_card(draft),
        return_exceptions=True,
    )
    logger.info("Fan-out complete for draft %s", draft.draft_id)


async def _fan_out_escalation(draft: DraftRecord) -> None:
    """Send escalation alerts to both channels."""
    await asyncio.gather(
        telegram.send_escalation_alert(draft),
        whatsapp.send_escalation_alert(draft),
        return_exceptions=True,
    )


async def _send_and_log(
    draft: DraftRecord,
    start_time: float,
) -> None:
    """After approval: send the Gmail reply and write the audit row."""
    lead = draft.lead
    ok = await send_threaded_reply(
        to_email=lead.customer_email,
        subject=draft.output.subject,
        body=draft.final_body,
        thread_id=lead.gmail_thread_id,
        message_id=lead.gmail_message_id,
    )
    outcome = "sent" if ok else "send_failed"

    audit = build_audit_row(
        lead_id=str(lead.lead_id),
        source=lead.source.value,
        channel_used=draft.decided_by_channel or "unknown",
        approver=draft.decided_by_channel or "unknown",
        decision=draft.decision.value if draft.decision else "unknown",
        latency_s=time.time() - start_time,
        input_tokens=0,  # stored on ClaudeOutput in future
        output_tokens=0,
        outcome=outcome,
    )
    await log_event(audit)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/health", response_model=HealthResponse, tags=["ops"])
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post(
    "/draft-reply",
    response_model=DraftReplyResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["pipeline"],
)
async def draft_reply_endpoint(
    payload: DraftReplyRequest,
    background_tasks: BackgroundTasks,
    x_lyra_secret: str | None = Header(default=None),
) -> DraftReplyResponse:
    """Ingest a raw lead email, parse it, match inventory, call Claude, fan-out for approval."""
    _verify_secret(x_lyra_secret)
    start = time.time()

    # 1. Parse lead
    lead = parse_lead(
        raw_email_body=payload.raw_email_body,
        source=payload.source,
        received_at=payload.received_at,
        gmail_message_id=payload.gmail_message_id,
        gmail_thread_id=payload.gmail_thread_id,
    )

    # 2. Pre-escalation check (no Claude needed)
    should_escalate, pre_reason = is_escalation_trigger(lead)

    # 3. Inventory lookup
    vehicle = await lookup_inventory(
        vin=lead.vin,
        stock=lead.stock_number,
        hint=f"{lead.vehicle_year or ''} {lead.make or ''} {lead.model or ''}".strip() or None,
    )

    # 4. Claude draft
    try:
        claude_out = await claude_draft_reply(lead, vehicle)
    except Exception as exc:
        logger.error("Claude draft failed for lead %s: %s", lead.lead_id, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Draft generation failed: {exc}",
        ) from exc

    # 5. Honour pre-escalation override
    if should_escalate and not claude_out.escalate_to_human:
        claude_out.escalate_to_human = True
        claude_out.escalation_reason = pre_reason

    # 6. Build and register draft
    draft = DraftRecord(lead=lead, vehicle=vehicle, output=claude_out)
    approval.put(draft)

    # 7. Fan-out (background so we return fast)
    if claude_out.escalate_to_human:
        lead.status = LeadStatus.escalated
        background_tasks.add_task(_fan_out_escalation, draft)
        # Audit escalation immediately
        background_tasks.add_task(
            log_event,
            build_audit_row(
                lead_id=str(lead.lead_id),
                source=lead.source.value,
                channel_used="—",
                approver="—",
                decision="escalated",
                latency_s=time.time() - start,
                input_tokens=0,
                output_tokens=0,
                outcome="escalated",
            ),
        )
    else:
        lead.status = LeadStatus.drafted
        background_tasks.add_task(_fan_out_approval, draft)

    return DraftReplyResponse(
        draft_id=draft.draft_id,
        lead_id=lead.lead_id,
        escalated=claude_out.escalate_to_human,
        escalation_reason=claude_out.escalation_reason,
        recommended_rep=claude_out.recommended_rep.value if not claude_out.escalate_to_human else None,
        confidence=claude_out.confidence if not claude_out.escalate_to_human else None,
        subject=claude_out.subject if not claude_out.escalate_to_human else None,
    )


@app.post(
    "/approve/{draft_id}",
    response_model=ApprovalResponse,
    tags=["pipeline"],
)
async def approve_draft(
    draft_id: UUID,
    body: ApprovalRequest,
    background_tasks: BackgroundTasks,
    x_lyra_secret: str | None = Header(default=None),
) -> ApprovalResponse:
    """Record an approval decision. First call wins — idempotent on draft_id."""
    _verify_secret(x_lyra_secret)
    start = time.time()

    accepted, message = await approval.decide(
        draft_id=draft_id,
        decision=ApprovalDecision.approved,
        channel=body.channel,
        approver_name=body.approver_name,
        edited_body=body.edited_body,
    )

    if accepted:
        draft = approval.get(draft_id)
        if draft:
            draft.lead.status = LeadStatus.approved
            background_tasks.add_task(_send_and_log, draft, start)

    return ApprovalResponse(accepted=accepted, message=message)


@app.post(
    "/deny/{draft_id}",
    response_model=ApprovalResponse,
    tags=["pipeline"],
)
async def deny_draft(
    draft_id: UUID,
    body: ApprovalRequest,
    x_lyra_secret: str | None = Header(default=None),
) -> ApprovalResponse:
    """Record a denial. Logs to audit sheet; no email sent."""
    _verify_secret(x_lyra_secret)

    accepted, message = await approval.decide(
        draft_id=draft_id,
        decision=ApprovalDecision.denied,
        channel=body.channel,
        approver_name=body.approver_name,
    )

    if accepted:
        draft = approval.get(draft_id)
        if draft:
            draft.lead.status = LeadStatus.escalated
            audit = build_audit_row(
                lead_id=str(draft.lead.lead_id),
                source=draft.lead.source.value,
                channel_used=body.channel,
                approver=body.approver_name,
                decision="denied",
                latency_s=0,
                input_tokens=0,
                output_tokens=0,
                outcome="denied",
            )
            await log_event(audit)

    return ApprovalResponse(accepted=accepted, message=message)


@app.post("/telegram-webhook", tags=["webhooks"])
async def telegram_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
) -> JSONResponse:
    """Handle Telegram inline-keyboard callbacks (approve / edit / deny)."""
    data = await request.json()
    callback = data.get("callback_query")
    if not callback:
        return JSONResponse({"ok": True})

    callback_id = callback.get("id", "")
    callback_data = callback.get("data", "")
    from_user = callback.get("from", {}).get("first_name", "Rep")

    parts = callback_data.split(":", 1)
    if len(parts) != 2:
        return JSONResponse({"ok": True})

    action, draft_id_str = parts
    try:
        draft_id = UUID(draft_id_str)
    except ValueError:
        return JSONResponse({"ok": True})

    decision_map = {
        "approve": ApprovalDecision.approved,
        "deny": ApprovalDecision.denied,
        "edit": ApprovalDecision.edited,
    }
    decision = decision_map.get(action)
    if not decision:
        return JSONResponse({"ok": True})

    accepted, msg = await approval.decide(
        draft_id=draft_id,
        decision=decision,
        channel="telegram",
        approver_name=from_user,
    )

    if accepted and decision == ApprovalDecision.approved:
        draft = approval.get(draft_id)
        if draft:
            draft.lead.status = LeadStatus.approved
            background_tasks.add_task(_send_and_log, draft, time.time())

    await telegram.answer_callback(callback_id, msg)
    return JSONResponse({"ok": True})


@app.post("/booking-webhook", tags=["webhooks"])
async def booking_webhook(
    payload: BookingWebhookPayload,
    background_tasks: BackgroundTasks,
    x_lyra_secret: str | None = Header(default=None),
) -> JSONResponse:
    """Handle TidyCal booking confirmations — notify rep on both channels."""
    _verify_secret(x_lyra_secret)

    rep_lower = payload.rep.lower()
    start_str = payload.start_time.strftime("%A %b %d, %Y · %I:%M %p")
    vehicle = f"Stock {payload.stock_number}" if payload.stock_number else "TBD"

    background_tasks.add_task(
        telegram.send_booking_notification,
        rep_chat_id=os.getenv(f"TELEGRAM_{rep_lower.upper()}_CHAT_ID", ""),
        customer_name=payload.customer_name,
        vehicle=vehicle,
        start_time=start_str,
        stock=payload.stock_number,
    )
    background_tasks.add_task(
        whatsapp.send_booking_notification,
        jid=os.getenv(f"WHATSAPP_{rep_lower.upper()}_JID", ""),
        customer_name=payload.customer_name,
        vehicle=vehicle,
        start_time=start_str,
        stock=payload.stock_number,
    )

    logger.info(
        "Booking webhook: %s booked with rep %s at %s",
        payload.customer_name,
        payload.rep,
        start_str,
    )
    return JSONResponse({"status": "ok"})

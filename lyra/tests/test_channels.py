"""Tests for telegram.py, whatsapp.py, gmail.py, sheets.py with mocked HTTP."""

from __future__ import annotations

import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.models import (
    AuditRow,
    ClaudeOutput,
    DraftRecord,
    Lead,
    LeadSource,
    RepName,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_lead() -> Lead:
    return Lead(
        source=LeadSource.autotrader,
        received_at=datetime.utcnow(),
        customer_name="Priya Singh",
        customer_email="priya@example.com",
        customer_phone="403-555-0199",
        vehicle_year=2020,
        make="Honda",
        model="Accord",
        stock_number="FN-24-0112",
        message="Is this still available?",
    )


def _make_draft() -> DraftRecord:
    lead = _make_lead()
    body = (
        "Hi Priya, thanks for reaching out about the 2020 Honda Accord Sport 1.5T at "
        "Fornest Automotive. Great news it is still available and we would love to "
        "set up a test drive at your convenience this Saturday or any day that works. "
        "We offer flexible financing terms with newcomers considered, so come on in and "
        "we can walk through all the options together at no pressure whatsoever. Book "
        "your test drive slot using the link below and I will have the car ready and "
        "waiting for your arrival. Looking forward to meeting you very soon! "
        "Foster | Fornest Automotive"
    )
    output = ClaudeOutput(
        recommended_rep=RepName.foster,
        subject="Re: Your inquiry about the 2020 Honda Accord",
        body=body,
        booking_cta="https://tidycal.com/fornest/foster",
        financing_angle="newcomers_considered",
        confidence=0.87,
        escalate_to_human=False,
        escalation_reason=None,
    )
    return DraftRecord(lead=lead, output=output)


def _make_escalation_draft() -> DraftRecord:
    lead = _make_lead()
    lead.message = "My lawyer is aware. AMVIC complaint incoming."
    body = (
        "Thank you for reaching out to Fornest Automotive. We sincerely apologize "
        "for any delays in communication and want to resolve your concerns as quickly "
        "as possible. A senior team member will contact you within two business hours "
        "to discuss your situation personally and find the best resolution available "
        "for you today. We genuinely value every single customer and take all feedback "
        "very seriously at our dealership, and we are committed to making this right. "
        "Please do not hesitate to call us directly in the meantime if you prefer. "
        "Sam | Fornest Automotive"
    )
    output = ClaudeOutput(
        recommended_rep=RepName.sam,
        subject="Re: Your inquiry",
        body=body,
        booking_cta="https://tidycal.com/fornest/sam",
        financing_angle="none",
        confidence=0.10,
        escalate_to_human=True,
        escalation_reason="Legal threat: AMVIC + lawyer",
    )
    return DraftRecord(lead=lead, output=output)


# ---------------------------------------------------------------------------
# Telegram tests
# ---------------------------------------------------------------------------


class TestTelegram:
    async def test_send_approval_card_no_token(self):
        """Without token, returns False gracefully."""
        import src.telegram as tg
        draft = _make_draft()
        with patch.object(tg, "_BOT_TOKEN", ""), patch.object(tg, "_APPROVAL_CHAT", ""):
            result = await tg.send_approval_card(draft)
        assert result is False

    async def test_send_approval_card_with_token(self):
        import src.telegram as tg
        draft = _make_draft()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"ok": True, "result": {"message_id": 1}}
        with (
            patch.object(tg, "_BOT_TOKEN", "123:ABC"),
            patch.object(tg, "_APPROVAL_CHAT", "-100123"),
            patch("httpx.AsyncClient") as mock_client,
        ):
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_resp
            )
            result = await tg.send_approval_card(draft)
        assert result is True

    async def test_send_escalation_alert_no_token(self):
        import src.telegram as tg
        draft = _make_escalation_draft()
        with patch.object(tg, "_BOT_TOKEN", ""):
            result = await tg.send_escalation_alert(draft)
        assert result is False

    async def test_send_escalation_alert_with_token(self):
        import src.telegram as tg
        draft = _make_escalation_draft()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"ok": True}
        with (
            patch.object(tg, "_BOT_TOKEN", "123:ABC"),
            patch.object(tg, "_ALERT_CHAT", "-100456"),
            patch("httpx.AsyncClient") as mock_client,
        ):
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_resp
            )
            result = await tg.send_escalation_alert(draft)
        assert result is True

    async def test_send_booking_notification(self):
        import src.telegram as tg
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"ok": True}
        with (
            patch.object(tg, "_BOT_TOKEN", "123:ABC"),
            patch("httpx.AsyncClient") as mock_client,
        ):
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_resp
            )
            result = await tg.send_booking_notification(
                rep_chat_id="-100789",
                customer_name="Priya Singh",
                vehicle="2020 Honda Accord",
                start_time="Sat Apr 18, 1:00 PM",
                stock="FN-24-0112",
            )
        assert result is True

    async def test_answer_callback(self):
        import src.telegram as tg
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"ok": True}
        with (
            patch.object(tg, "_BOT_TOKEN", "123:ABC"),
            patch("httpx.AsyncClient") as mock_client,
        ):
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_resp
            )
            result = await tg.answer_callback("cb123", "Approved!")
        assert result is True

    def test_draft_card_text_contains_rep(self):
        import src.telegram as tg
        draft = _make_draft()
        text = tg._draft_card_text(draft)
        assert "Foster" in text

    def test_draft_card_text_contains_subject(self):
        import src.telegram as tg
        draft = _make_draft()
        text = tg._draft_card_text(draft)
        assert "Honda Accord" in text

    def test_approval_keyboard_structure(self):
        import uuid
        import src.telegram as tg
        did = uuid.uuid4()
        kb = tg._approval_keyboard(did)
        assert "inline_keyboard" in kb
        labels = [btn["text"] for btn in kb["inline_keyboard"][0]]
        assert "✅ Approve" in labels
        assert "❌ Deny" in labels


# ---------------------------------------------------------------------------
# WhatsApp tests
# ---------------------------------------------------------------------------


class TestWhatsApp:
    async def test_send_approval_card_no_config(self):
        import src.whatsapp as wa
        draft = _make_draft()
        with patch.object(wa, "_API_URL", ""), patch.object(wa, "_API_KEY", ""):
            result = await wa.send_approval_card(draft)
        assert result is True  # "skipped" counts as ok

    async def test_send_approval_card_with_config(self):
        import src.whatsapp as wa
        draft = _make_draft()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"key": {"id": "abc123"}}
        with (
            patch.object(wa, "_API_URL", "https://evo.example.com"),
            patch.object(wa, "_API_KEY", "test-key"),
            patch.object(wa, "_APPROVAL_JID", "15195550199@s.whatsapp.net"),
            patch("httpx.AsyncClient") as mock_client,
        ):
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_resp
            )
            result = await wa.send_approval_card(draft)
        assert result is True

    async def test_send_escalation_alert_no_config(self):
        import src.whatsapp as wa
        draft = _make_escalation_draft()
        with patch.object(wa, "_API_URL", ""), patch.object(wa, "_API_KEY", ""):
            result = await wa.send_escalation_alert(draft)
        assert result is True  # skipped

    async def test_send_escalation_alert_with_config(self):
        import src.whatsapp as wa
        draft = _make_escalation_draft()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"key": {"id": "xyz"}}
        with (
            patch.object(wa, "_API_URL", "https://evo.example.com"),
            patch.object(wa, "_API_KEY", "test-key"),
            patch.object(wa, "_APPROVAL_JID", "15195550199@s.whatsapp.net"),
            patch("httpx.AsyncClient") as mock_client,
        ):
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_resp
            )
            result = await wa.send_escalation_alert(draft)
        assert result is True

    async def test_send_booking_notification_no_config(self):
        import src.whatsapp as wa
        with patch.object(wa, "_API_URL", ""), patch.object(wa, "_API_KEY", ""):
            result = await wa.send_booking_notification(
                jid="1519@s.whatsapp.net",
                customer_name="Priya Singh",
                vehicle="2020 Honda Accord",
                start_time="Sat Apr 18, 1:00 PM",
                stock="FN-24-0112",
            )
        assert result is True

    def test_draft_card_text_contains_vehicle(self):
        import src.whatsapp as wa
        draft = _make_draft()
        text = wa._draft_card_text(draft)
        assert "Honda Accord" in text

    def test_draft_card_text_contains_rep(self):
        import src.whatsapp as wa
        draft = _make_draft()
        text = wa._draft_card_text(draft)
        assert "Foster" in text


# ---------------------------------------------------------------------------
# Gmail tests
# ---------------------------------------------------------------------------


class TestGmail:
    async def test_send_threaded_reply_no_service(self):
        import src.gmail as gm
        with patch.object(gm, "_get_service", return_value=None):
            result = await gm.send_threaded_reply(
                to_email="priya@example.com",
                subject="Re: Accord",
                body="Test body",
            )
        assert result is False

    async def test_send_threaded_reply_success(self):
        import src.gmail as gm
        mock_service = MagicMock()
        mock_service.users.return_value.messages.return_value.send.return_value.execute.return_value = {
            "id": "msg123"
        }
        with patch.object(gm, "_get_service", return_value=mock_service):
            result = await gm.send_threaded_reply(
                to_email="priya@example.com",
                subject="Re: Accord",
                body="Test body for the email that we are sending now.",
                thread_id="thread123",
                message_id="msg001",
            )
        assert result is True

    async def test_send_threaded_reply_exception_returns_false(self):
        import src.gmail as gm
        mock_service = MagicMock()
        mock_service.users.return_value.messages.return_value.send.return_value.execute.side_effect = (
            Exception("Gmail API error")
        )
        with patch.object(gm, "_get_service", return_value=mock_service):
            result = await gm.send_threaded_reply(
                to_email="priya@example.com",
                subject="Re: Accord",
                body="Test body",
            )
        assert result is False

    def test_encode_message_structure(self):
        import src.gmail as gm
        payload = gm._encode_message(
            to="priya@example.com",
            subject="Re: Accord inquiry",
            body="Hello this is a test body.",
            thread_id="t123",
            in_reply_to="msg001",
        )
        assert "raw" in payload
        assert payload["threadId"] == "t123"

    def test_encode_message_no_thread(self):
        import src.gmail as gm
        payload = gm._encode_message(
            to="priya@example.com",
            subject="Re: Accord",
            body="Hello body.",
            thread_id=None,
            in_reply_to=None,
        )
        assert "threadId" not in payload


# ---------------------------------------------------------------------------
# Sheets tests
# ---------------------------------------------------------------------------


class TestSheets:
    async def test_log_event_no_spreadsheet_id(self):
        import src.sheets as sh
        with patch.object(sh, "_SPREADSHEET_ID", ""):
            row = AuditRow(
                lead_id="LG-001", source="autotrader", channel_used="telegram",
                approver="Foster", decision="approved", latency_s=18.5,
                claude_cost_usd=0.0012, outcome="booked",
                timestamp=datetime.utcnow().isoformat(),
            )
            result = await sh.log_event(row)
        assert result is False

    async def test_log_event_sheet_unavailable(self):
        import src.sheets as sh
        with (
            patch.object(sh, "_SPREADSHEET_ID", "fake-id"),
            patch.object(sh, "_get_sheet", return_value=None),
        ):
            row = AuditRow(
                lead_id="LG-001", source="autotrader", channel_used="telegram",
                approver="Foster", decision="approved", latency_s=18.5,
                claude_cost_usd=0.0012, outcome="booked",
                timestamp=datetime.utcnow().isoformat(),
            )
            result = await sh.log_event(row)
        assert result is False

    async def test_log_event_success(self):
        import src.sheets as sh
        mock_ws = MagicMock()
        mock_ws.append_row.return_value = None
        with (
            patch.object(sh, "_SPREADSHEET_ID", "real-id"),
            patch.object(sh, "_get_sheet", return_value=mock_ws),
        ):
            row = AuditRow(
                lead_id="LG-001", source="autotrader", channel_used="telegram",
                approver="Foster", decision="approved", latency_s=18.5,
                claude_cost_usd=0.0012, outcome="booked",
                timestamp=datetime.utcnow().isoformat(),
            )
            result = await sh.log_event(row)
        assert result is True
        mock_ws.append_row.assert_called_once()

    async def test_log_event_exception_returns_false(self):
        import src.sheets as sh
        mock_ws = MagicMock()
        mock_ws.append_row.side_effect = Exception("Sheets API error")
        with (
            patch.object(sh, "_SPREADSHEET_ID", "real-id"),
            patch.object(sh, "_get_sheet", return_value=mock_ws),
        ):
            row = AuditRow(
                lead_id="LG-001", source="autotrader", channel_used="telegram",
                approver="Foster", decision="approved", latency_s=18.5,
                claude_cost_usd=0.0012, outcome="booked",
                timestamp=datetime.utcnow().isoformat(),
            )
            result = await sh.log_event(row)
        assert result is False

    def test_build_audit_row(self):
        from src.sheets import build_audit_row
        row = build_audit_row(
            lead_id="LG-001", source="autotrader", channel_used="telegram",
            approver="Foster", decision="approved", latency_s=18.5,
            input_tokens=500, output_tokens=200, outcome="booked",
        )
        assert row.lead_id == "LG-001"
        assert row.outcome == "booked"
        assert row.claude_cost_usd >= 0

    def test_estimate_cost(self):
        from src.claude_client import estimate_cost
        cost = estimate_cost(1_000_000, 0)
        assert cost == pytest.approx(0.80)
        cost2 = estimate_cost(0, 1_000_000)
        assert cost2 == pytest.approx(4.00)

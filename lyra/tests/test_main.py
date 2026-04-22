"""Integration tests for FastAPI routes in main.py.

Claude calls are mocked via respx so no real API key is needed.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src import approval
from src.models import (
    ApprovalDecision,
    ClaudeOutput,
    DraftRecord,
    Lead,
    LeadSource,
    RepName,
)
from tests.conftest import CLEAN_ADF, HOSTILE_ADF, VAGUE_PLAIN

MOCK_CLAUDE_OUTPUT = ClaudeOutput(
    recommended_rep=RepName.foster,
    subject="Re: Your inquiry about the 2020 Honda Accord Sport 1.5T",
    body=(
        "Hi Priya, thanks for reaching out about the 2020 Honda Accord Sport 1.5T at "
        "Fornest Automotive! Great news — it is still available. On pricing we do have "
        "some flexibility, especially when paired with our in-house financing. We offer "
        "flexible terms with newcomers considered, so whether you are looking to finance "
        "or pay cash we can work with you. Saturday works great for us — our lot is open "
        "nine to five. I would love to have the car pulled and ready for a test drive at "
        "a time that suits you. Book your slot directly at the link below and I will "
        "confirm same day. Looking forward to meeting you! "
        "Foster | Fornest Automotive"
    ),
    booking_cta="https://tidycal.com/fornest/foster",
    financing_angle="newcomers_considered",
    confidence=0.87,
    escalate_to_human=False,
    escalation_reason=None,
)

MOCK_ESCALATION_OUTPUT = ClaudeOutput(
    recommended_rep=RepName.sam,
    subject="Re: Your inquiry — Fornest Automotive",
    body=(
        "Thank you for your message. A senior member of our team will be in touch "
        "with you very shortly to address your concerns directly and personally. "
        "We take all customer feedback seriously and we genuinely want to resolve "
        "this situation as quickly as possible for you. Please expect a direct call "
        "or email from our general manager within the next two business hours. We "
        "appreciate your patience and look forward to making this right for you. "
        "In the meantime please do not hesitate to call the dealership directly. "
        "Sam | Fornest Automotive"
    ),
    booking_cta="https://tidycal.com/fornest/sam",
    financing_angle="none",
    confidence=0.10,
    escalate_to_human=True,
    escalation_reason="Legal threat detected (AMVIC, BBB, lawyer)",
)


def _patch_claude(output: ClaudeOutput):
    return patch("src.main.claude_draft_reply", new=AsyncMock(return_value=output))


def _patch_fanout():
    return patch("src.main._fan_out_approval", new=AsyncMock())


def _patch_escalation_fanout():
    return patch("src.main._fan_out_escalation", new=AsyncMock())


def _patch_log():
    return patch("src.main.log_event", new=AsyncMock())


class TestHealth:
    def test_health_ok(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_health_version(self, client):
        resp = client.get("/health")
        assert "version" in resp.json()


class TestDraftReply:
    def test_clean_adf_returns_202(self, client):
        with _patch_claude(MOCK_CLAUDE_OUTPUT), _patch_fanout(), _patch_log():
            resp = client.post(
                "/draft-reply",
                json={"source": "autotrader", "raw_email_body": CLEAN_ADF},
            )
        assert resp.status_code == 202

    def test_clean_adf_response_shape(self, client):
        with _patch_claude(MOCK_CLAUDE_OUTPUT), _patch_fanout(), _patch_log():
            resp = client.post(
                "/draft-reply",
                json={"source": "autotrader", "raw_email_body": CLEAN_ADF},
            )
        data = resp.json()
        assert "draft_id" in data
        assert "lead_id" in data
        assert data["escalated"] is False
        assert data["confidence"] == pytest.approx(0.87)

    def test_hostile_lead_escalated(self, client):
        with _patch_claude(MOCK_ESCALATION_OUTPUT), _patch_escalation_fanout(), _patch_log():
            resp = client.post(
                "/draft-reply",
                json={"source": "autotrader", "raw_email_body": HOSTILE_ADF},
            )
        assert resp.status_code == 202
        assert resp.json()["escalated"] is True

    def test_vague_lead_returns_draft(self, client):
        with _patch_claude(MOCK_CLAUDE_OUTPUT), _patch_fanout(), _patch_log():
            resp = client.post(
                "/draft-reply",
                json={"source": "autotrader", "raw_email_body": VAGUE_PLAIN},
            )
        assert resp.status_code == 202

    def test_pre_escalation_overrides_claude(self, client):
        # Claude says not escalate, but lead has AMVIC — pre-check should win
        non_escalating_claude = MOCK_CLAUDE_OUTPUT.model_copy(
            update={"escalate_to_human": False}
        )
        with _patch_claude(non_escalating_claude), _patch_escalation_fanout(), _patch_log():
            resp = client.post(
                "/draft-reply",
                json={"source": "autotrader", "raw_email_body": HOSTILE_ADF},
            )
        assert resp.json()["escalated"] is True

    def test_draft_stored_in_approval(self, client):
        with _patch_claude(MOCK_CLAUDE_OUTPUT), _patch_fanout(), _patch_log():
            resp = client.post(
                "/draft-reply",
                json={"source": "autotrader", "raw_email_body": CLEAN_ADF},
            )
        draft_id = uuid.UUID(resp.json()["draft_id"])
        assert approval.get(draft_id) is not None


class TestApprove:
    def _create_draft(self, client) -> str:
        with _patch_claude(MOCK_CLAUDE_OUTPUT), _patch_fanout(), _patch_log():
            resp = client.post(
                "/draft-reply",
                json={"source": "autotrader", "raw_email_body": CLEAN_ADF},
            )
        return resp.json()["draft_id"]

    def test_approve_accepts_first_call(self, client):
        draft_id = self._create_draft(client)
        with patch("src.main._send_and_log", new=AsyncMock()), _patch_log():
            resp = client.post(
                f"/approve/{draft_id}",
                json={"channel": "telegram", "approver_name": "Foster"},
            )
        assert resp.status_code == 200
        assert resp.json()["accepted"] is True

    def test_approve_rejects_second_call(self, client):
        draft_id = self._create_draft(client)
        with patch("src.main._send_and_log", new=AsyncMock()), _patch_log():
            client.post(
                f"/approve/{draft_id}",
                json={"channel": "telegram", "approver_name": "Foster"},
            )
            resp2 = client.post(
                f"/approve/{draft_id}",
                json={"channel": "whatsapp", "approver_name": "Foster"},
            )
        assert resp2.json()["accepted"] is False

    def test_approve_unknown_draft_rejects(self, client):
        resp = client.post(
            f"/approve/{uuid.uuid4()}",
            json={"channel": "telegram", "approver_name": "Foster"},
        )
        assert resp.json()["accepted"] is False


class TestDeny:
    def _create_draft(self, client) -> str:
        with _patch_claude(MOCK_CLAUDE_OUTPUT), _patch_fanout(), _patch_log():
            resp = client.post(
                "/draft-reply",
                json={"source": "autotrader", "raw_email_body": CLEAN_ADF},
            )
        return resp.json()["draft_id"]

    def test_deny_accepted(self, client):
        draft_id = self._create_draft(client)
        with _patch_log():
            resp = client.post(
                f"/deny/{draft_id}",
                json={"channel": "telegram", "approver_name": "Ben"},
            )
        assert resp.json()["accepted"] is True

    def test_deny_then_approve_rejected(self, client):
        draft_id = self._create_draft(client)
        with _patch_log(), patch("src.main._send_and_log", new=AsyncMock()):
            client.post(
                f"/deny/{draft_id}",
                json={"channel": "telegram", "approver_name": "Ben"},
            )
            resp2 = client.post(
                f"/approve/{draft_id}",
                json={"channel": "whatsapp", "approver_name": "Foster"},
            )
        assert resp2.json()["accepted"] is False


class TestTelegramWebhook:
    def _create_draft(self, client) -> uuid.UUID:
        with _patch_claude(MOCK_CLAUDE_OUTPUT), _patch_fanout(), _patch_log():
            resp = client.post(
                "/draft-reply",
                json={"source": "autotrader", "raw_email_body": CLEAN_ADF},
            )
        return uuid.UUID(resp.json()["draft_id"])

    def test_telegram_approve_callback(self, client):
        draft_id = self._create_draft(client)
        payload = {
            "callback_query": {
                "id": "abc123",
                "data": f"approve:{draft_id}",
                "from": {"first_name": "Foster"},
            }
        }
        with (
            patch("src.main.telegram.answer_callback", new=AsyncMock()),
            patch("src.main._send_and_log", new=AsyncMock()),
            _patch_log(),
        ):
            resp = client.post("/telegram-webhook", json=payload)
        assert resp.status_code == 200
        assert resp.json()["ok"] is True

    def test_telegram_webhook_no_callback(self, client):
        resp = client.post("/telegram-webhook", json={"update_id": 123})
        assert resp.status_code == 200

    def test_telegram_invalid_draft_id(self, client):
        payload = {
            "callback_query": {
                "id": "xyz",
                "data": "approve:not-a-uuid",
                "from": {"first_name": "Foster"},
            }
        }
        resp = client.post("/telegram-webhook", json=payload)
        assert resp.status_code == 200


class TestBookingWebhook:
    def test_booking_webhook_ok(self, client):
        payload = {
            "event": "booking.created",
            "booking_id": "BK-001",
            "rep": "ben",
            "customer_name": "Priya Singh",
            "customer_email": "priya@example.com",
            "start_time": "2024-04-18T13:00:00",
            "stock_number": "FN-24-0112",
        }
        with (
            patch("src.main.telegram.send_booking_notification", new=AsyncMock()),
            patch("src.main.whatsapp.send_booking_notification", new=AsyncMock()),
        ):
            resp = client.post("/booking-webhook", json=payload)
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

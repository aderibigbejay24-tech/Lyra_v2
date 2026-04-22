"""Tests for approval.py — first-approver-wins idempotency store."""

from __future__ import annotations

import uuid
from datetime import datetime

import pytest

from src import approval
from src.models import (
    ApprovalDecision,
    ClaudeOutput,
    DraftRecord,
    InventoryVehicle,
    Lead,
    LeadSource,
    RepName,
)


def _make_draft() -> DraftRecord:
    lead = Lead(
        source=LeadSource.autotrader,
        received_at=datetime.utcnow(),
        customer_email="test@example.com",
        message="Is this still available?",
    )
    output = ClaudeOutput(
        recommended_rep=RepName.foster,
        subject="Re: Your inquiry",
        body=(
            "Hi there, thanks for reaching out to Fornest Automotive about the vehicle "
            "you saw listed online. Great news — it is still available and we would love "
            "to set up a test drive at your convenience. We offer flexible financing "
            "terms with newcomers considered, so whether your credit is established or "
            "you are just getting started we can find a solution that works for you. "
            "Please book a time that works best for you using the TidyCal link below and "
            "I will have everything ready for your arrival. Looking forward to meeting "
            "you at the lot soon! Foster | Fornest Automotive"
        ),
        booking_cta="https://tidycal.com/fornest/foster",
        financing_angle="flexible_terms",
        confidence=0.85,
        escalate_to_human=False,
        escalation_reason=None,
    )
    return DraftRecord(lead=lead, output=output)


class TestApprovalStore:
    def test_put_and_get(self):
        draft = _make_draft()
        approval.put(draft)
        retrieved = approval.get(draft.draft_id)
        assert retrieved is not None
        assert retrieved.draft_id == draft.draft_id

    def test_get_unknown_returns_none(self):
        assert approval.get(uuid.uuid4()) is None

    async def test_first_approve_wins(self):
        draft = _make_draft()
        approval.put(draft)

        accepted1, _ = await approval.decide(
            draft.draft_id, ApprovalDecision.approved, "telegram", "Foster"
        )
        accepted2, _ = await approval.decide(
            draft.draft_id, ApprovalDecision.approved, "whatsapp", "Foster"
        )
        assert accepted1 is True
        assert accepted2 is False  # second call rejected

    async def test_channel_recorded(self):
        draft = _make_draft()
        approval.put(draft)
        await approval.decide(draft.draft_id, ApprovalDecision.approved, "telegram", "Foster")
        assert draft.decided_by_channel == "telegram"

    async def test_edited_body_stored(self):
        draft = _make_draft()
        approval.put(draft)
        await approval.decide(
            draft.draft_id,
            ApprovalDecision.edited,
            "whatsapp",
            "Sam",
            edited_body="Custom edited body here.",
        )
        assert draft.edited_body == "Custom edited body here."
        assert draft.final_body == "Custom edited body here."

    async def test_final_body_uses_original_when_not_edited(self):
        draft = _make_draft()
        approval.put(draft)
        await approval.decide(draft.draft_id, ApprovalDecision.approved, "telegram", "Foster")
        assert draft.final_body == draft.output.body

    async def test_denial_recorded(self):
        draft = _make_draft()
        approval.put(draft)
        accepted, _ = await approval.decide(
            draft.draft_id, ApprovalDecision.denied, "telegram", "Ben"
        )
        assert accepted is True
        assert draft.decision == ApprovalDecision.denied

    async def test_unknown_draft_id_rejected(self):
        accepted, msg = await approval.decide(
            uuid.uuid4(), ApprovalDecision.approved, "telegram", "Foster"
        )
        assert accepted is False
        assert "not found" in msg.lower()

    def test_clear_removes_all(self):
        draft = _make_draft()
        approval.put(draft)
        approval.clear()
        assert approval.get(draft.draft_id) is None

    def test_all_drafts(self):
        d1 = _make_draft()
        d2 = _make_draft()
        approval.put(d1)
        approval.put(d2)
        all_d = approval.all_drafts()
        assert len(all_d) >= 2

"""Tests for Pydantic v2 models — schema validation."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.models import ClaudeOutput, Lead, LeadSource, LeadStatus, RepName


class TestClaudeOutput:
    def _valid_output(self, **overrides):  # type: ignore[return]
        base = {
            "recommended_rep": "Foster",
            "subject": "Re: Your inquiry about the 2020 Honda Accord",
            "body": (
                "Hi Priya, thanks for reaching out about the 2020 Honda Accord Sport 1.5T "
                "at Fornest Automotive. Great news it is still available and we would love "
                "to set up a time for you to come take it for a spin. We offer flexible "
                "financing terms with newcomers considered, so whether you are financing "
                "or paying cash we can work something out that fits your budget and timeline. "
                "Saturday works great for us. Book your test drive at the link below and I "
                "will have the car pulled and ready for your arrival. Looking forward to "
                "meeting you! Foster | Fornest Automotive"
            ),
            "booking_cta": "https://tidycal.com/fornest/foster",
            "financing_angle": "flexible_terms",
            "confidence": 0.87,
            "escalate_to_human": False,
            "escalation_reason": None,
        }
        base.update(overrides)
        return ClaudeOutput.model_validate(base)

    def test_valid_output_parses(self):
        out = self._valid_output()
        assert out.recommended_rep == RepName.foster
        assert out.confidence == pytest.approx(0.87)

    def test_body_too_short_raises(self):
        with pytest.raises(ValidationError):
            self._valid_output(body="Too short")

    def test_confidence_out_of_range_raises(self):
        with pytest.raises(ValidationError):
            self._valid_output(confidence=1.5)

    def test_confidence_zero_valid(self):
        out = self._valid_output(confidence=0.0)
        assert out.confidence == 0.0

    def test_escalation_flag(self):
        out = self._valid_output(escalate_to_human=True, escalation_reason="Legal threat")
        assert out.escalate_to_human is True

    def test_all_reps_valid(self):
        for rep in ["Foster", "Ben", "Sam", "Justin"]:
            out = self._valid_output(recommended_rep=rep)
            assert out.recommended_rep.value == rep

    def test_invalid_rep_raises(self):
        with pytest.raises(ValidationError):
            self._valid_output(recommended_rep="NotARep")


class TestLead:
    def test_minimal_lead(self):
        lead = Lead(
            source=LeadSource.autotrader,
            received_at=__import__("datetime").datetime.utcnow(),
            customer_email="test@example.com",
        )
        assert lead.status == LeadStatus.new
        assert lead.parse_warnings == []

    def test_lead_id_auto_generated(self):
        lead = Lead(
            source=LeadSource.cargurus,
            received_at=__import__("datetime").datetime.utcnow(),
            customer_email="a@b.com",
        )
        assert lead.lead_id is not None

    def test_status_transitions(self):
        lead = Lead(
            source=LeadSource.autotrader,
            received_at=__import__("datetime").datetime.utcnow(),
            customer_email="x@x.com",
        )
        lead.status = LeadStatus.drafted
        assert lead.status == LeadStatus.drafted

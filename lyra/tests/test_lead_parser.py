"""Tests for lead_parser.py — ADF/XML parsing and regex fallback."""

from __future__ import annotations

import pytest

from src.lead_parser import is_escalation_trigger, parse_lead
from src.models import LeadSource
from tests.conftest import CLEAN_ADF, HOSTILE_ADF, VAGUE_PLAIN


class TestADFParser:
    def test_clean_adf_extracts_name(self):
        lead = parse_lead(CLEAN_ADF, LeadSource.autotrader)
        assert lead.customer_name == "Priya Singh"

    def test_clean_adf_extracts_email(self):
        lead = parse_lead(CLEAN_ADF, LeadSource.autotrader)
        assert lead.customer_email == "priya.singh@example.com"

    def test_clean_adf_extracts_phone(self):
        lead = parse_lead(CLEAN_ADF, LeadSource.autotrader)
        assert lead.customer_phone == "403-555-0199"

    def test_clean_adf_extracts_vehicle(self):
        lead = parse_lead(CLEAN_ADF, LeadSource.autotrader)
        assert lead.vehicle_year == 2020
        assert lead.make == "Honda"
        assert lead.model == "Accord"
        assert lead.trim == "Sport 1.5T"

    def test_clean_adf_extracts_vin(self):
        lead = parse_lead(CLEAN_ADF, LeadSource.autotrader)
        assert lead.vin == "1HGCV1F34LA012345"

    def test_clean_adf_extracts_stock(self):
        lead = parse_lead(CLEAN_ADF, LeadSource.autotrader)
        assert lead.stock_number == "FN-24-0112"

    def test_clean_adf_extracts_price(self):
        lead = parse_lead(CLEAN_ADF, LeadSource.autotrader)
        assert lead.listed_price_cad == 26995.0

    def test_clean_adf_no_warnings(self):
        lead = parse_lead(CLEAN_ADF, LeadSource.autotrader)
        assert lead.parse_warnings == []

    def test_hostile_adf_extracts_escalation_message(self):
        lead = parse_lead(HOSTILE_ADF, LeadSource.autotrader)
        assert "AMVIC" in lead.message or "lawyer" in lead.message.lower()

    def test_malformed_xml_falls_back_to_regex(self):
        malformed = "<adf><broken></adf>"
        lead = parse_lead(malformed, LeadSource.autotrader)
        # Should not raise; will have warnings
        assert isinstance(lead.parse_warnings, list)

    def test_source_preserved(self):
        lead = parse_lead(CLEAN_ADF, LeadSource.cargurus)
        assert lead.source == LeadSource.cargurus


class TestRegexFallback:
    def test_vague_extracts_email(self):
        lead = parse_lead(VAGUE_PLAIN, LeadSource.autotrader)
        assert lead.customer_email == "buyer99@example.com"

    def test_vague_has_degraded_warning(self):
        lead = parse_lead(VAGUE_PLAIN, LeadSource.autotrader)
        assert any("regex" in w.lower() or "fallback" in w.lower() for w in lead.parse_warnings)

    def test_vague_vehicle_fields_none(self):
        lead = parse_lead(VAGUE_PLAIN, LeadSource.autotrader)
        assert lead.vehicle_year is None
        assert lead.make is None
        assert lead.model is None

    def test_plain_text_with_phone(self):
        text = "Hi, interested in the Honda. Call me at 403-555-1234. sam@example.com"
        lead = parse_lead(text, LeadSource.autotrader)
        assert lead.customer_email == "sam@example.com"
        assert lead.customer_phone is not None
        assert "403" in lead.customer_phone

    def test_plain_text_with_vin(self):
        text = "VIN is 1HGCV1F34LA012345, test@example.com"
        lead = parse_lead(text, LeadSource.autotrader)
        assert lead.vin == "1HGCV1F34LA012345"

    def test_no_email_produces_fallback_address(self):
        lead = parse_lead("no contact info here", LeadSource.autotrader)
        assert "@" in lead.customer_email  # gets the sentinel address


class TestEscalationTriggers:
    def test_amvic_triggers_escalation(self):
        lead = parse_lead(HOSTILE_ADF, LeadSource.autotrader)
        escalate, reason = is_escalation_trigger(lead)
        assert escalate is True
        assert "AMVIC" in reason

    def test_lawyer_triggers_escalation(self):
        lead = parse_lead(HOSTILE_ADF, LeadSource.autotrader)
        escalate, _ = is_escalation_trigger(lead)
        assert escalate is True

    def test_bbb_triggers_escalation(self):
        from src.models import LeadSource
        lead = parse_lead(
            "<adf><prospect><customer><contact><email>x@x.com</email></contact>"
            "<comments>I'll report you to the BBB</comments></customer></prospect></adf>",
            LeadSource.autotrader,
        )
        escalate, _ = is_escalation_trigger(lead)
        assert escalate is True

    def test_clean_lead_no_escalation(self):
        lead = parse_lead(CLEAN_ADF, LeadSource.autotrader)
        escalate, _ = is_escalation_trigger(lead)
        assert escalate is False

    def test_price_match_triggers_escalation(self):
        lead = parse_lead(
            "<adf><prospect><customer><contact><email>x@x.com</email></contact>"
            "<comments>Can you price match the other dealer?</comments></customer></prospect></adf>",
            LeadSource.autotrader,
        )
        escalate, _ = is_escalation_trigger(lead)
        assert escalate is True

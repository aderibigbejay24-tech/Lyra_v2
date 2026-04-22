"""Tests for hillz_inventory cache helpers and claude_client helpers."""

from __future__ import annotations

import json
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.hillz_inventory import (
    _cache_valid,
    _get_cached,
    _set_cache,
    lookup_inventory,
    seed_inventory,
)
from src.models import InventoryVehicle
from tests.conftest import SAMPLE_VEHICLES


# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------


class TestInventoryCache:
    def test_cache_invalid_when_empty(self):
        import src.hillz_inventory as hi
        hi._CACHE.clear()
        assert _cache_valid() is False

    def test_cache_valid_after_set(self):
        _set_cache(SAMPLE_VEHICLES)
        assert _cache_valid() is True

    def test_cache_invalid_after_expiry(self):
        import src.hillz_inventory as hi
        hi._CACHE["vehicles"] = SAMPLE_VEHICLES
        hi._CACHE["fetched_at"] = time.time() - 9999
        assert _cache_valid() is False

    def test_get_cached_returns_list(self):
        _set_cache(SAMPLE_VEHICLES)
        result = _get_cached()
        assert isinstance(result, list)
        assert len(result) == len(SAMPLE_VEHICLES)

    def test_get_cached_empty_when_not_set(self):
        import src.hillz_inventory as hi
        hi._CACHE.clear()
        assert _get_cached() == []

    def test_set_cache_stores_vehicles(self):
        _set_cache(SAMPLE_VEHICLES)
        cached = _get_cached()
        assert cached[0].make == SAMPLE_VEHICLES[0].make

    async def test_lookup_uses_cache_when_valid(self):
        _set_cache(SAMPLE_VEHICLES)
        import src.hillz_inventory as hi
        hi._SEEDED = []  # clear seeded so cache path is used
        result = await lookup_inventory(vin="1HGCV1F34LA012345")
        assert result is not None
        assert result.make == "Honda"
        seed_inventory(SAMPLE_VEHICLES)  # restore

    async def test_lookup_falls_back_to_stale_cache(self):
        import src.hillz_inventory as hi
        hi._SEEDED = []
        _set_cache(SAMPLE_VEHICLES)
        hi._CACHE["fetched_at"] = time.time() - 9999  # expire the cache

        with patch("src.hillz_inventory._fetch_live", new=AsyncMock(return_value=[])):
            result = await lookup_inventory(stock="FN-24-0112")

        assert result is not None
        assert result.stock_number == "FN-24-0112"
        seed_inventory(SAMPLE_VEHICLES)  # restore

    async def test_lookup_no_vehicles_returns_none(self):
        import src.hillz_inventory as hi
        hi._SEEDED = []
        hi._CACHE.clear()
        with patch("src.hillz_inventory._fetch_live", new=AsyncMock(return_value=[])):
            result = await lookup_inventory(hint="2020 Honda Accord")
        assert result is None
        seed_inventory(SAMPLE_VEHICLES)  # restore


# ---------------------------------------------------------------------------
# HTML parser (mocked HTML)
# ---------------------------------------------------------------------------


class TestHillzHTMLParser:
    def test_parse_empty_html_returns_empty(self):
        from src.hillz_inventory import _parse_hillz_html
        result = _parse_hillz_html("<html><body></body></html>")
        assert result == []

    def test_parse_invalid_html_returns_empty(self):
        from src.hillz_inventory import _parse_hillz_html
        result = _parse_hillz_html("not html at all !!!")
        assert result == []


# ---------------------------------------------------------------------------
# Claude client helpers
# ---------------------------------------------------------------------------


class TestClaudeClientHelpers:
    def test_extract_json_clean(self):
        from src.claude_client import _extract_json
        data = {"key": "value", "num": 42}
        assert _extract_json(json.dumps(data)) == data

    def test_extract_json_with_preamble(self):
        from src.claude_client import _extract_json
        raw = 'Here is the JSON:\n{"recommended_rep": "Foster", "confidence": 0.9}'
        result = _extract_json(raw)
        assert result["recommended_rep"] == "Foster"

    def test_extract_json_raises_on_no_json(self):
        from src.claude_client import _extract_json
        with pytest.raises(ValueError, match="No valid JSON"):
            _extract_json("This has no JSON at all, just text.")

    def test_build_user_message_clean_lead(self):
        from datetime import datetime
        from src.claude_client import _build_user_message
        from src.models import Lead, LeadSource

        lead = Lead(
            source=LeadSource.autotrader,
            received_at=datetime.utcnow(),
            customer_name="Priya Singh",
            customer_email="priya@example.com",
            vehicle_year=2020,
            make="Honda",
            model="Accord",
            message="Is this still available?",
        )
        msg = _build_user_message(lead, None)
        assert "Priya Singh" in msg
        assert "Honda" in msg
        assert "2020" in msg

    def test_build_user_message_with_vehicle(self):
        from datetime import datetime
        from src.claude_client import _build_user_message
        from src.models import Lead, LeadSource

        lead = Lead(
            source=LeadSource.autotrader,
            received_at=datetime.utcnow(),
            customer_email="test@example.com",
            make="Honda",
            model="Accord",
            vehicle_year=2020,
            message="Hello",
        )
        vehicle = SAMPLE_VEHICLES[0]
        msg = _build_user_message(lead, vehicle)
        assert "FN-24-0112" in msg
        assert "Sonic Gray Pearl" in msg

    def test_build_user_message_no_vehicle(self):
        from datetime import datetime
        from src.claude_client import _build_user_message
        from src.models import Lead, LeadSource

        lead = Lead(
            source=LeadSource.autotrader,
            received_at=datetime.utcnow(),
            customer_email="test@example.com",
            message="Is this for sale?",
        )
        msg = _build_user_message(lead, None)
        assert "No inventory match" in msg

    def test_build_user_message_with_warnings(self):
        from datetime import datetime
        from src.claude_client import _build_user_message
        from src.models import Lead, LeadSource

        lead = Lead(
            source=LeadSource.autotrader,
            received_at=datetime.utcnow(),
            customer_email="test@example.com",
            message="vague",
            parse_warnings=["regex fallback used", "no phone found"],
        )
        msg = _build_user_message(lead, None)
        assert "Parse warnings" in msg
        assert "regex fallback used" in msg

    def test_estimate_cost_both_tokens(self):
        from src.claude_client import estimate_cost
        cost = estimate_cost(500_000, 100_000)
        assert cost == pytest.approx(0.80 * 0.5 + 4.00 * 0.1, rel=1e-4)

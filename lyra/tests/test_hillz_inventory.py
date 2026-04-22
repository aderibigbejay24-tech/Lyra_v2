"""Tests for hillz_inventory.py — lookup and matching logic."""

from __future__ import annotations

import pytest

from src.hillz_inventory import lookup_inventory
from src.models import InventoryVehicle


class TestInventoryLookup:
    async def test_exact_vin_match(self):
        result = await lookup_inventory(vin="1HGCV1F34LA012345")
        assert result is not None
        assert result.make == "Honda"
        assert result.model == "Accord"

    async def test_exact_stock_match(self):
        result = await lookup_inventory(stock="FN-24-0098")
        assert result is not None
        assert result.make == "Toyota"
        assert result.model == "Tundra"

    async def test_hint_match_make_model(self):
        result = await lookup_inventory(hint="2019 BMW 330i")
        assert result is not None
        assert result.make == "BMW"

    async def test_hint_match_year(self):
        result = await lookup_inventory(hint="2021 Tundra")
        assert result is not None
        assert result.year == 2021

    async def test_no_match_returns_none(self):
        result = await lookup_inventory(hint="1999 Pontiac Firebird")
        assert result is None

    async def test_vin_beats_hint_on_conflict(self):
        # VIN points to Honda, hint points to BMW — VIN should win
        result = await lookup_inventory(
            vin="1HGCV1F34LA012345", hint="2019 BMW 330i"
        )
        assert result is not None
        assert result.make == "Honda"

    async def test_stock_case_insensitive(self):
        result = await lookup_inventory(stock="fn-24-0112")
        assert result is not None
        assert result.stock_number == "FN-24-0112"

    async def test_empty_args_returns_none(self):
        result = await lookup_inventory()
        assert result is None

    async def test_returns_inventory_vehicle_type(self):
        result = await lookup_inventory(stock="FN-24-0155")
        assert isinstance(result, InventoryVehicle)

    async def test_price_populated(self):
        result = await lookup_inventory(vin="1HGCV1F34LA012345")
        assert result is not None
        assert result.price_cad == 26995.0

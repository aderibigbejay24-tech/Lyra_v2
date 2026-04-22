"""HillzDealer inventory lookup with 60-second TTL cache.

Spec §4: lookup_inventory(vin, stock, hint) — match vehicle to Fornest stock.
Strategy:
  1. Check seeded in-memory cache first (populated by seed_hillz.py / tests).
  2. Attempt live HTTP fetch from HillzDealer inventory page.
  3. Parse HTML with lxml; cache results for TTL seconds.
  4. Never raises — returns None if no match found.
"""

from __future__ import annotations

import logging
import os
import re
import time
from typing import Any

import httpx
from lxml import html

from src.models import InventoryVehicle

logger = logging.getLogger(__name__)

_CACHE: dict[str, Any] = {}  # {"vehicles": [...], "fetched_at": float}
_SEEDED: list[InventoryVehicle] = []  # injected by tests / seed script
_TTL = int(os.getenv("HILLZ_CACHE_TTL_SECONDS", "60"))
_BASE_URL = os.getenv("HILLZ_BASE_URL", "https://www.hillzdealer.com/inventory")

# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------


def seed_inventory(vehicles: list[InventoryVehicle]) -> None:
    """Inject inventory records directly (used by tests and seed_hillz.py)."""
    global _SEEDED
    _SEEDED = list(vehicles)


def _cache_valid() -> bool:
    fetched_at = _CACHE.get("fetched_at", 0.0)
    return (time.time() - fetched_at) < _TTL


def _get_cached() -> list[InventoryVehicle]:
    if _CACHE.get("vehicles"):
        return _CACHE["vehicles"]  # type: ignore[return-value]
    return []


def _set_cache(vehicles: list[InventoryVehicle]) -> None:
    _CACHE["vehicles"] = vehicles
    _CACHE["fetched_at"] = time.time()


# ---------------------------------------------------------------------------
# HillzDealer HTML scraper
# ---------------------------------------------------------------------------


def _parse_hillz_html(content: str) -> list[InventoryVehicle]:
    """Parse HillzDealer inventory HTML into vehicle records.

    Targets their standard inventory listing structure.
    Returns empty list on any parse error — never raises.
    """
    vehicles: list[InventoryVehicle] = []
    try:
        tree = html.fromstring(content)
        # HillzDealer uses .vehicle-card or .inventory-item containers
        cards = tree.cssselect(".vehicle-card, .inventory-item, [data-vehicle]")
        for card in cards:
            try:
                v = _parse_card(card)
                if v:
                    vehicles.append(v)
            except Exception as exc:  # noqa: BLE001
                logger.debug("Skipping card parse error: %s", exc)
    except Exception as exc:  # noqa: BLE001
        logger.warning("HillzDealer HTML parse error: %s", exc)
    return vehicles


def _parse_card(card: Any) -> InventoryVehicle | None:
    """Extract fields from a single vehicle card element."""

    def sel(css: str) -> str:
        nodes = card.cssselect(css)
        return nodes[0].text_content().strip() if nodes else ""

    def attr(css: str, attribute: str) -> str:
        nodes = card.cssselect(css)
        return nodes[0].get(attribute, "").strip() if nodes else ""

    title = sel(".vehicle-title, h2, h3")
    year_match = re.search(r"\b(19|20)\d{2}\b", title)
    if not year_match:
        return None

    year = int(year_match.group())
    parts = title.replace(str(year), "").split()
    make = parts[0].strip() if parts else None
    model = " ".join(parts[1:2]) if len(parts) > 1 else None

    stock = sel(".stock-number, [data-stock]") or attr("[data-stock]", "data-stock")
    vin = sel(".vin, [data-vin]") or attr("[data-vin]", "data-vin")

    price_raw = sel(".price, .asking-price, [data-price]")
    price_clean = re.sub(r"[^\d.]", "", price_raw)
    price = float(price_clean) if price_clean else None

    mileage_raw = sel(".mileage, .odometer")
    mileage_match = re.search(r"[\d,]+", mileage_raw)
    mileage = int(mileage_match.group().replace(",", "")) if mileage_match else None

    colour = sel(".colour, .color, .exterior-colour")
    url = attr("a", "href")

    if not (make and model and stock):
        return None

    return InventoryVehicle(
        stock_number=stock,
        year=year,
        make=make,
        model=model,
        vin=vin or None,
        mileage_km=mileage,
        colour=colour or None,
        price_cad=price,
        url=url or None,
    )


async def _fetch_live() -> list[InventoryVehicle]:
    """Fetch and parse live HillzDealer inventory. Returns [] on failure."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(_BASE_URL)
            resp.raise_for_status()
            return _parse_hillz_html(resp.text)
    except httpx.HTTPError as exc:
        logger.warning("HillzDealer fetch failed: %s", exc)
        return []


# ---------------------------------------------------------------------------
# Matching logic
# ---------------------------------------------------------------------------


def _score_match(
    vehicle: InventoryVehicle,
    vin: str | None,
    stock: str | None,
    hint: str | None,
) -> int:
    """Score how well a vehicle matches the query (higher = better)."""
    score = 0

    if vin and vehicle.vin and vin.upper() == vehicle.vin.upper():
        score += 100  # exact VIN match — definitive

    if stock and vehicle.stock_number and stock.upper() == vehicle.stock_number.upper():
        score += 80

    if hint:
        lower_hint = hint.lower()
        if vehicle.make and vehicle.make.lower() in lower_hint:
            score += 20
        if vehicle.model and vehicle.model.lower() in lower_hint:
            score += 20
        if str(vehicle.year) in lower_hint:
            score += 10
        if vehicle.trim and vehicle.trim.lower() in lower_hint:
            score += 5

    return score


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def lookup_inventory(
    vin: str | None = None,
    stock: str | None = None,
    hint: str | None = None,
) -> InventoryVehicle | None:
    """Return the best-matching vehicle from Fornest's HillzDealer inventory.

    Args:
        vin:   VIN from the ADF payload.
        stock: Stock number from the ADF payload.
        hint:  Free-text hint (e.g. "2020 Honda Accord Sport") for fuzzy match.

    Returns:
        Best-matching InventoryVehicle, or None if nothing scores > 0.
    """
    # 1. Try seeded / cached list first
    vehicles: list[InventoryVehicle] = []
    if _SEEDED:
        vehicles = _SEEDED
    elif _cache_valid():
        vehicles = _get_cached()
    else:
        live = await _fetch_live()
        if live:
            _set_cache(live)
            vehicles = live
        elif _get_cached():
            # Serve stale cache if live fetch fails
            logger.warning("Serving stale HillzDealer cache")
            vehicles = _get_cached()

    if not vehicles:
        logger.warning("No inventory available (seeded or live)")
        return None

    # 2. Score every vehicle and return the best match
    scored = [(v, _score_match(v, vin, stock, hint)) for v in vehicles]
    scored.sort(key=lambda x: x[1], reverse=True)
    best_vehicle, best_score = scored[0]

    if best_score == 0:
        logger.info("No inventory match for vin=%s stock=%s hint=%r", vin, stock, hint)
        return None

    logger.info(
        "Inventory match: %s %s %s (score=%d)",
        best_vehicle.year,
        best_vehicle.make,
        best_vehicle.model,
        best_score,
    )
    return best_vehicle

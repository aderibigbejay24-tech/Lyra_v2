"""Parse inbound lead emails: ADF/XML first, regex fallback.

Spec §4: parse_lead(raw_email) — extract fields from ADF/XML or plain text.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from lxml import etree

from src.models import Lead, LeadSource

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
_PHONE_RE = re.compile(r"(\+?1?\s?[\(\-]?\d{3}[\)\-\s]?\s?\d{3}[\-\s]\d{4})")
_YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")
_PRICE_RE = re.compile(r"\$\s?([\d,]+(?:\.\d{2})?)")
_VIN_RE = re.compile(r"\b[A-HJ-NPR-Z0-9]{17}\b")
_STOCK_RE = re.compile(r"\b(FN|AT|CG)-\d{2}-\d{4}\b", re.IGNORECASE)

_MAKES = [
    "honda", "toyota", "ford", "chevrolet", "chevy", "gmc", "dodge", "ram",
    "jeep", "chrysler", "bmw", "mercedes", "audi", "volkswagen", "vw",
    "hyundai", "kia", "mazda", "subaru", "nissan", "infiniti", "lexus",
    "acura", "volvo", "porsche", "tesla", "cadillac", "buick", "lincoln",
    "mitsubishi", "suzuki",
]


# ---------------------------------------------------------------------------
# Internal result
# ---------------------------------------------------------------------------


@dataclass
class _ParseResult:
    customer_name: str | None = None
    customer_email: str | None = None
    customer_phone: str | None = None
    vehicle_year: int | None = None
    make: str | None = None
    model: str | None = None
    trim: str | None = None
    vin: str | None = None
    stock_number: str | None = None
    listed_price_cad: float | None = None
    message: str = ""
    warnings: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# ADF/XML parser
# ---------------------------------------------------------------------------


def _parse_adf(raw: str) -> _ParseResult | None:
    """Attempt to parse ADF/XML. Returns None if the payload is not ADF."""
    stripped = raw.strip()
    if not (stripped.startswith("<?xml") or "<adf>" in stripped or "<prospect>" in stripped):
        return None

    try:
        root = etree.fromstring(stripped.encode())
    except etree.XMLSyntaxError:
        # Try to salvage by wrapping in adf tags
        try:
            root = etree.fromstring(f"<adf>{stripped}</adf>".encode())
        except etree.XMLSyntaxError:
            return None

    result = _ParseResult()

    def txt(xpath: str) -> str | None:
        nodes = root.xpath(xpath)
        if nodes and nodes[0].text:
            return nodes[0].text.strip() or None
        return None

    # Customer
    result.customer_name = txt(".//customer//name") or txt(".//contact/name")
    result.customer_email = txt(".//customer//email") or txt(".//contact/email")
    result.customer_phone = txt(".//customer//phone") or txt(".//contact/phone")
    result.message = txt(".//customer//comments") or txt(".//comments") or ""

    # Vehicle
    year_str = txt(".//vehicle/year")
    if year_str and year_str.isdigit():
        result.vehicle_year = int(year_str)
    result.make = txt(".//vehicle/make")
    result.model = txt(".//vehicle/model")
    result.trim = txt(".//vehicle/trim")
    result.vin = txt(".//vehicle/vin")
    result.stock_number = txt(".//vehicle/stock")

    price_str = txt(".//vehicle/price")
    if price_str:
        clean = price_str.replace(",", "").replace("$", "").strip()
        try:
            result.listed_price_cad = float(clean)
        except ValueError:
            result.warnings.append(f"Could not parse listed price: {price_str!r}")

    if not result.customer_email:
        result.warnings.append("ADF parsed but no customer email found")

    return result


# ---------------------------------------------------------------------------
# Regex / plain-text fallback
# ---------------------------------------------------------------------------


def _parse_regex(raw: str) -> _ParseResult:
    """Best-effort regex extraction from plain-text email bodies."""
    result = _ParseResult(warnings=["ADF parse failed — regex fallback used"])

    # Email
    emails = _EMAIL_RE.findall(raw)
    if emails:
        # Prefer non-noreply addresses
        result.customer_email = next(
            (e for e in emails if "noreply" not in e and "fornest" not in e.lower()),
            emails[0],
        )
    else:
        result.warnings.append("No email address found in payload")

    # Phone
    phones = _PHONE_RE.findall(raw)
    if phones:
        result.customer_phone = phones[0].strip()

    # VIN
    vins = _VIN_RE.findall(raw)
    if vins:
        result.vin = vins[0]

    # Stock
    stocks = _STOCK_RE.findall(raw)
    if stocks:
        result.stock_number = stocks[0]

    # Year
    years = _YEAR_RE.findall(raw)
    if years:
        result.vehicle_year = int(years[0])

    # Make
    lower = raw.lower()
    for make in _MAKES:
        if make in lower:
            result.make = make.capitalize()
            break

    # Price
    prices = _PRICE_RE.findall(raw)
    if prices:
        try:
            result.listed_price_cad = float(prices[0].replace(",", ""))
        except ValueError:
            pass

    # Message: use the whole body as the message
    result.message = raw.strip()

    if not result.customer_email:
        result.warnings.append("No usable contact information extracted")

    return result


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def parse_lead(
    raw_email_body: str,
    source: LeadSource,
    received_at: datetime | None = None,
    gmail_message_id: str | None = None,
    gmail_thread_id: str | None = None,
) -> Lead:
    """Parse a raw email body into a Lead record.

    Tries ADF/XML first; falls back to regex extraction on plain text.
    All extraction failures surface as parse_warnings — never raise.
    """
    if received_at is None:
        received_at = datetime.utcnow()

    result = _parse_adf(raw_email_body)
    if result is None:
        result = _parse_regex(raw_email_body)

    email = result.customer_email or "unknown@unknown.invalid"

    return Lead(
        source=source,
        received_at=received_at,
        gmail_message_id=gmail_message_id,
        gmail_thread_id=gmail_thread_id,
        customer_name=result.customer_name,
        customer_email=email,
        customer_phone=result.customer_phone,
        vehicle_year=result.vehicle_year,
        make=result.make,
        model=result.model,
        trim=result.trim,
        vin=result.vin,
        stock_number=result.stock_number,
        listed_price_cad=result.listed_price_cad,
        message=result.message,
        parse_warnings=result.warnings,
    )


def is_escalation_trigger(lead: Lead) -> tuple[bool, str]:
    """Check message content for immediate escalation triggers before Claude.

    Returns (should_escalate, reason).
    """
    msg = (lead.message or "").lower()

    triggers: list[tuple[str, str]] = [
        ("amvic", "AMVIC regulatory complaint mentioned"),
        ("bbb", "BBB complaint threat detected"),
        ("lawyer", "Legal representation mentioned"),
        ("lawsuit", "Lawsuit threat detected"),
        ("sue", "Legal action threat detected"),
        ("court", "Court/legal action mentioned"),
        ("price match", "Explicit price-match demand"),
        ("beat the price", "Explicit price-match demand"),
        ("report you", "Regulatory complaint threat"),
        ("consumer protection", "Consumer protection complaint mentioned"),
    ]

    for keyword, reason in triggers:
        if keyword in msg:
            return True, reason

    return False, ""

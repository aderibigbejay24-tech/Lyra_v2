"""Anthropic Messages API wrapper for Lyra draft generation.

Spec §4: draft_reply(lead, vehicle) — generate reply JSON via Claude Haiku 4.5.
Uses prompt caching on the system prompt to minimise cost per call.
"""

from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path

import anthropic
from pydantic import ValidationError

from src.models import ClaudeOutput, InventoryVehicle, Lead, RepName

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (Path(__file__).parent / "prompts" / "system.md").read_text()

_MODEL = "claude-haiku-4-5"
_MAX_TOKENS = 1024

_TIDYCAL: dict[str, str] = {
    "foster": os.getenv("TIDYCAL_FOSTER", "https://tidycal.com/fornest/foster"),
    "ben": os.getenv("TIDYCAL_BEN", "https://tidycal.com/fornest/ben"),
    "sam": os.getenv("TIDYCAL_SAM", "https://tidycal.com/fornest/sam"),
    "justin": os.getenv("TIDYCAL_JUSTIN", "https://tidycal.com/fornest/justin"),
}


# ---------------------------------------------------------------------------
# User message builder
# ---------------------------------------------------------------------------


def _build_user_message(lead: Lead, vehicle: InventoryVehicle | None) -> str:
    """Construct the user-turn message describing this specific lead."""
    parts: list[str] = ["## New inbound lead\n"]

    parts.append(f"**Source:** {lead.source.value}")
    parts.append(f"**Received:** {lead.received_at.isoformat()}")

    parts.append("\n### Customer")
    parts.append(f"- Name: {lead.customer_name or 'Unknown'}")
    parts.append(f"- Email: {lead.customer_email}")
    parts.append(f"- Phone: {lead.customer_phone or 'Not provided'}")

    parts.append("\n### Vehicle of interest (from lead)")
    if lead.vehicle_year or lead.make or lead.model:
        parts.append(
            f"- {lead.vehicle_year or '?'} {lead.make or '?'} {lead.model or '?'} {lead.trim or ''}"
        )
        parts.append(f"- VIN: {lead.vin or 'Not provided'}")
        parts.append(f"- Stock: {lead.stock_number or 'Not provided'}")
        parts.append(
            f"- Listed price: {'${:,.0f} CAD'.format(lead.listed_price_cad) if lead.listed_price_cad else 'Not provided'}"
        )
    else:
        parts.append("- Vehicle not specified in lead")

    parts.append("\n### Customer message")
    parts.append(f'"{lead.message}"')

    if vehicle:
        parts.append("\n### Matched inventory record")
        parts.append(f"- Stock: {vehicle.stock_number}")
        parts.append(
            f"- Vehicle: {vehicle.year} {vehicle.make} {vehicle.model} {vehicle.trim or ''}"
        )
        parts.append(f"- VIN: {vehicle.vin or 'Not on file'}")
        parts.append(
            f"- Mileage: {'{:,} km'.format(vehicle.mileage_km) if vehicle.mileage_km else 'Not listed'}"
        )
        parts.append(f"- Colour: {vehicle.colour or 'Not listed'}")
        parts.append(
            f"- Price: {'${:,.0f} CAD'.format(vehicle.price_cad) if vehicle.price_cad else 'Not listed'}"
        )
        if vehicle.highlights:
            parts.append("- Highlights: " + "; ".join(vehicle.highlights))
    else:
        parts.append("\n### Matched inventory record")
        parts.append("- No inventory match found. Do NOT invent vehicle details.")

    if lead.parse_warnings:
        parts.append("\n### Parse warnings")
        for w in lead.parse_warnings:
            parts.append(f"- {w}")

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# JSON extraction
# ---------------------------------------------------------------------------


def _extract_json(content: str) -> dict:  # type: ignore[type-arg]
    """Extract JSON from Claude's response, stripping any accidental prose."""
    content = content.strip()
    # Try direct parse first
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass
    # Try to find a JSON block
    match = re.search(r"\{.*\}", content, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    raise ValueError(f"No valid JSON in Claude response: {content[:200]!r}")


# ---------------------------------------------------------------------------
# Cost estimation
# ---------------------------------------------------------------------------


def estimate_cost(input_tokens: int, output_tokens: int) -> float:
    """Approximate cost in USD for claude-haiku-4-5 pricing."""
    # Haiku 4.5: $0.80/M input, $4.00/M output (as of 2025)
    return (input_tokens / 1_000_000 * 0.80) + (output_tokens / 1_000_000 * 4.00)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def draft_reply(
    lead: Lead,
    vehicle: InventoryVehicle | None,
    client: anthropic.AsyncAnthropic | None = None,
) -> ClaudeOutput:
    """Call Claude Haiku 4.5 to generate a structured draft reply.

    Uses prompt caching on the system prompt (cache_control: ephemeral).
    Validates the output against the ClaudeOutput schema before returning.

    Raises:
        ValueError: If Claude returns invalid JSON or the schema fails validation.
        anthropic.APIError: On upstream API failures (caller handles retry).
    """
    if client is None:
        client = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    user_message = _build_user_message(lead, vehicle)

    response = await client.messages.create(
        model=_MODEL,
        max_tokens=_MAX_TOKENS,
        system=[
            {
                "type": "text",
                "text": _SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": user_message}],
    )

    raw_text = response.content[0].text if response.content else ""
    logger.debug(
        "Claude response [%d in / %d out tokens]: %s",
        response.usage.input_tokens,
        response.usage.output_tokens,
        raw_text[:200],
    )

    parsed = _extract_json(raw_text)

    # Resolve booking CTA from rep name if Claude omitted it or used wrong key
    rep_key = parsed.get("recommended_rep", "foster").lower()
    if "booking_cta" not in parsed or not parsed["booking_cta"]:
        parsed["booking_cta"] = _TIDYCAL.get(rep_key, _TIDYCAL["foster"])

    try:
        output = ClaudeOutput.model_validate(parsed)
    except ValidationError as exc:
        logger.error("Claude output schema violation: %s\nRaw: %s", exc, raw_text[:500])
        raise ValueError(f"Claude output failed schema validation: {exc}") from exc

    return output

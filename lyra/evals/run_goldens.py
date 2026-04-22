"""Golden lead evaluation runner.

Spec §8: 20 golden leads (10 ADF, 5 plain-text, 5 hostile/edge).
Asserts: JSON valid, vehicle matched, escalation flagged.
Writes JSON report to evals/report.json and prints pass-rate.

Usage:
    make eval
    python evals/run_goldens.py [--no-claude]
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Ensure src/ is importable when running from lyra/
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.hillz_inventory import seed_inventory
from src.lead_parser import is_escalation_trigger, parse_lead
from src.models import InventoryVehicle, LeadSource

GOLDENS_PATH = Path(__file__).parent / "goldens" / "leads.json"
REPORT_PATH = Path(__file__).parent / "report.json"

SAMPLE_VEHICLES = [
    InventoryVehicle(
        stock_number="FN-24-0112", year=2020, make="Honda", model="Accord",
        trim="Sport 1.5T", vin="1HGCV1F34LA012345", price_cad=26995.0,
    ),
    InventoryVehicle(
        stock_number="FN-24-0155", year=2019, make="BMW", model="330i",
        trim="xDrive", vin="WBA8E9G55KNU12345", price_cad=38990.0,
    ),
    InventoryVehicle(
        stock_number="FN-24-0098", year=2021, make="Toyota", model="Tundra",
        trim="SR5 TRD Off-Road", vin="5TFDW5F14MX123456", price_cad=54450.0,
    ),
    InventoryVehicle(
        stock_number="FN-24-0071", year=2022, make="Mazda", model="CX-5",
        trim="GT AWD", price_cad=34200.0,
    ),
]


# ---------------------------------------------------------------------------
# Per-golden evaluation
# ---------------------------------------------------------------------------


async def evaluate_golden(golden: dict, use_claude: bool) -> dict:  # type: ignore[type-arg]
    """Run one golden through parse + escalation + optionally Claude."""
    result: dict = {  # type: ignore[type-arg]
        "id": golden["id"],
        "description": golden["description"],
        "category": golden["category"],
        "assertions_passed": [],
        "assertions_failed": [],
        "errors": [],
        "claude_output": None,
        "latency_ms": 0,
    }

    assertions = golden.get("assertions", {})
    t0 = time.time()

    try:
        source = LeadSource(golden["source"])
        lead = parse_lead(golden["raw"], source)
        should_escalate, _ = is_escalation_trigger(lead)

        # --- Parser assertions ---
        if "parse_email" in assertions:
            if lead.customer_email == assertions["parse_email"]:
                result["assertions_passed"].append("parse_email")
            else:
                result["assertions_failed"].append(
                    f"parse_email: expected={assertions['parse_email']} got={lead.customer_email}"
                )

        if "parse_name" in assertions:
            if lead.customer_name == assertions["parse_name"]:
                result["assertions_passed"].append("parse_name")
            else:
                result["assertions_failed"].append(
                    f"parse_name: expected={assertions['parse_name']} got={lead.customer_name}"
                )

        if "parse_vin" in assertions:
            if lead.vin == assertions["parse_vin"]:
                result["assertions_passed"].append("parse_vin")
            else:
                result["assertions_failed"].append(
                    f"parse_vin: expected={assertions['parse_vin']} got={lead.vin}"
                )

        if "should_escalate" in assertions:
            if should_escalate == assertions["should_escalate"]:
                result["assertions_passed"].append("should_escalate")
            else:
                result["assertions_failed"].append(
                    f"should_escalate: expected={assertions['should_escalate']} got={should_escalate}"
                )

        if assertions.get("no_parse_warnings"):
            if not lead.parse_warnings:
                result["assertions_passed"].append("no_parse_warnings")
            else:
                result["assertions_failed"].append(
                    f"no_parse_warnings: got warnings={lead.parse_warnings}"
                )

        if assertions.get("has_parse_warnings"):
            if lead.parse_warnings:
                result["assertions_passed"].append("has_parse_warnings")
            else:
                result["assertions_failed"].append("has_parse_warnings: expected warnings, got none")

        # --- Optional Claude draft ---
        if use_claude and not should_escalate and os.getenv("ANTHROPIC_API_KEY"):
            from src.claude_client import draft_reply
            from src.hillz_inventory import lookup_inventory

            vehicle = await lookup_inventory(
                vin=lead.vin, stock=lead.stock_number,
                hint=f"{lead.vehicle_year or ''} {lead.make or ''} {lead.model or ''}".strip() or None,
            )
            try:
                output = await draft_reply(lead, vehicle)
                result["claude_output"] = {
                    "recommended_rep": output.recommended_rep.value,
                    "confidence": output.confidence,
                    "escalate_to_human": output.escalate_to_human,
                    "word_count": len(output.body.split()),
                    "subject_preview": output.subject[:60],
                }
                result["assertions_passed"].append("claude_json_valid")
                # Word count assertion
                words = len(output.body.split())
                if 90 <= words <= 140:
                    result["assertions_passed"].append("claude_word_count_90_140")
                else:
                    result["assertions_failed"].append(f"claude_word_count: got {words} words")
            except Exception as exc:  # noqa: BLE001
                result["errors"].append(f"Claude error: {exc}")
                result["assertions_failed"].append("claude_json_valid")

    except Exception as exc:  # noqa: BLE001
        result["errors"].append(f"Evaluation error: {exc}")

    result["latency_ms"] = round((time.time() - t0) * 1000, 1)
    return result


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


async def run_all(use_claude: bool) -> None:
    seed_inventory(SAMPLE_VEHICLES)

    goldens = json.loads(GOLDENS_PATH.read_text())
    print(f"\n{'='*60}")
    print(f"  Lyra Golden Eval — {len(goldens)} leads — {datetime.utcnow().isoformat()[:19]}")
    print(f"  Claude drafts: {'YES' if use_claude else 'NO (pass --claude to enable)'}")
    print(f"{'='*60}\n")

    results = []
    for golden in goldens:
        res = await evaluate_golden(golden, use_claude)
        results.append(res)

        passed = len(res["assertions_passed"])
        failed = len(res["assertions_failed"])
        status = "✓" if failed == 0 and not res["errors"] else "✗"
        print(f"  {status} [{res['id']}] {res['description'][:50]:<50}  {passed}P {failed}F  {res['latency_ms']}ms")
        for f in res["assertions_failed"]:
            print(f"      FAIL: {f}")
        for e in res["errors"]:
            print(f"      ERR:  {e}")

    # Summary
    total_assertions = sum(
        len(r["assertions_passed"]) + len(r["assertions_failed"]) for r in results
    )
    total_passed = sum(len(r["assertions_passed"]) for r in results)
    leads_passed = sum(1 for r in results if not r["assertions_failed"] and not r["errors"])
    pass_rate = leads_passed / len(results) * 100

    print(f"\n{'='*60}")
    print(f"  Leads passed:     {leads_passed}/{len(results)} ({pass_rate:.0f}%)")
    print(f"  Assertions:       {total_passed}/{total_assertions} passed")
    print(f"{'='*60}\n")

    report = {
        "run_at": datetime.utcnow().isoformat(),
        "total_leads": len(results),
        "leads_passed": leads_passed,
        "pass_rate": round(pass_rate, 1),
        "total_assertions": total_assertions,
        "assertions_passed": total_passed,
        "results": results,
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2))
    print(f"  Report written to {REPORT_PATH}\n")

    if pass_rate < 100.0:
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--claude", action="store_true", help="Run live Claude drafts")
    args = parser.parse_args()
    asyncio.run(run_all(use_claude=args.claude))

"""Google Sheets audit log appender.

Spec §4: log_event(row) — append audit trail to Google Sheet.
Spec §5: lead_id | source | channel_used | approver | decision | latency_s | claude_cost_usd | outcome
"""

from __future__ import annotations

import logging
import os
from datetime import datetime

from src.models import AuditRow

logger = logging.getLogger(__name__)

_SPREADSHEET_ID = os.getenv("GSHEET_SPREADSHEET_ID", "")
_WORKSHEET = os.getenv("GSHEET_WORKSHEET", "Audit Log")
_CREDS_PATH = os.getenv("GSHEET_CREDENTIALS_JSON", "secrets/sheets-sa.json")

_HEADERS = [
    "lead_id",
    "source",
    "channel_used",
    "approver",
    "decision",
    "latency_s",
    "claude_cost_usd",
    "outcome",
    "timestamp",
]


def _get_sheet():  # type: ignore[return]
    """Return a gspread Worksheet instance, or None on failure."""
    try:
        import gspread
        from google.oauth2.service_account import Credentials

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive.readonly",
        ]
        creds = Credentials.from_service_account_file(_CREDS_PATH, scopes=scopes)
        gc = gspread.authorize(creds)
        spreadsheet = gc.open_by_key(_SPREADSHEET_ID)
        try:
            return spreadsheet.worksheet(_WORKSHEET)
        except gspread.WorksheetNotFound:
            ws = spreadsheet.add_worksheet(title=_WORKSHEET, rows=1000, cols=len(_HEADERS))
            ws.append_row(_HEADERS)
            return ws
    except Exception as exc:  # noqa: BLE001
        logger.warning("Google Sheets unavailable: %s", exc)
        return None


async def log_event(row: AuditRow) -> bool:
    """Append one audit row to the Google Sheet.

    Returns True on success. Never raises.
    """
    if not _SPREADSHEET_ID:
        logger.debug("GSHEET_SPREADSHEET_ID not set — skipping audit log")
        return False

    ws = _get_sheet()
    if ws is None:
        return False

    values = [
        row.lead_id,
        row.source,
        row.channel_used,
        row.approver,
        row.decision,
        round(row.latency_s, 2),
        round(row.claude_cost_usd, 6),
        row.outcome,
        row.timestamp,
    ]

    try:
        ws.append_row(values, value_input_option="USER_ENTERED")
        logger.info("Audit row logged: lead_id=%s outcome=%s", row.lead_id, row.outcome)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.error("Sheets append failed: %s", exc)
        return False


def build_audit_row(
    lead_id: str,
    source: str,
    channel_used: str,
    approver: str,
    decision: str,
    latency_s: float,
    input_tokens: int,
    output_tokens: int,
    outcome: str,
) -> AuditRow:
    """Construct an AuditRow from pipeline values."""
    from src.claude_client import estimate_cost

    cost = estimate_cost(input_tokens, output_tokens)
    return AuditRow(
        lead_id=lead_id,
        source=source,
        channel_used=channel_used,
        approver=approver,
        decision=decision,
        latency_s=latency_s,
        claude_cost_usd=cost,
        outcome=outcome,
        timestamp=datetime.utcnow().isoformat(),
    )

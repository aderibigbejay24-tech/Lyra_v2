"""First-approver-wins idempotency store.

Holds draft state in memory during the pilot. In production, replace with
Redis or Supabase so multiple server instances share state.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from uuid import UUID

from src.models import ApprovalDecision, DraftRecord

logger = logging.getLogger(__name__)

# draft_id -> DraftRecord
_STORE: dict[UUID, DraftRecord] = {}
_LOCK = asyncio.Lock()


def put(draft: DraftRecord) -> None:
    """Register a new draft. Called immediately after Claude returns."""
    _STORE[draft.draft_id] = draft


def get(draft_id: UUID) -> DraftRecord | None:
    return _STORE.get(draft_id)


def all_drafts() -> list[DraftRecord]:
    return list(_STORE.values())


async def decide(
    draft_id: UUID,
    decision: ApprovalDecision,
    channel: str,
    approver_name: str,
    edited_body: str | None = None,
) -> tuple[bool, str]:
    """Apply an approval decision. Returns (accepted, message).

    First call wins — subsequent calls from any channel are ignored (idempotent).
    """
    async with _LOCK:
        draft = _STORE.get(draft_id)
        if draft is None:
            return False, f"Draft {draft_id} not found"

        if draft.decision is not None:
            already = draft.decided_by_channel or "unknown"
            return False, f"Already decided ({draft.decision.value} via {already})"

        draft.decision = decision
        draft.decided_by_channel = channel
        draft.decided_at = datetime.utcnow()
        if edited_body:
            draft.edited_body = edited_body

        logger.info(
            "Draft %s: %s by %s via %s",
            draft_id,
            decision.value,
            approver_name,
            channel,
        )
        return True, f"Decision recorded: {decision.value}"


def clear() -> None:
    """Clear all drafts — used in tests only."""
    _STORE.clear()

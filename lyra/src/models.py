"""Pydantic v2 data contracts for the Lyra Lead Guardian pipeline."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, EmailStr, Field, HttpUrl, field_validator


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class LeadSource(str, Enum):
    autotrader = "autotrader"
    cargurus = "cargurus"
    web = "web"


class LeadStatus(str, Enum):
    new = "new"
    drafted = "drafted"
    approved = "approved"
    sent = "sent"
    booked = "booked"
    escalated = "escalated"


class RepName(str, Enum):
    foster = "Foster"
    ben = "Ben"
    sam = "Sam"
    justin = "Justin"


class ApprovalDecision(str, Enum):
    approved = "approved"
    edited = "edited"
    denied = "denied"


# ---------------------------------------------------------------------------
# Inbound
# ---------------------------------------------------------------------------


class RawLeadPayload(BaseModel):
    """Payload received from Make.com when a new lead email arrives."""

    source: LeadSource
    raw_email_body: str
    received_at: datetime = Field(default_factory=datetime.utcnow)
    gmail_message_id: str | None = None
    gmail_thread_id: str | None = None


# ---------------------------------------------------------------------------
# Parsed lead
# ---------------------------------------------------------------------------


class Lead(BaseModel):
    lead_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    source: LeadSource
    received_at: datetime
    gmail_message_id: str | None = None
    gmail_thread_id: str | None = None

    # Customer
    customer_name: str | None = None
    customer_email: str
    customer_phone: str | None = None

    # Vehicle interest
    vehicle_year: int | None = None
    make: str | None = None
    model: str | None = None
    trim: str | None = None
    vin: str | None = None
    stock_number: str | None = None
    listed_price_cad: float | None = None
    message: str = ""

    parse_warnings: list[str] = Field(default_factory=list)
    status: LeadStatus = LeadStatus.new


# ---------------------------------------------------------------------------
# Inventory
# ---------------------------------------------------------------------------


class InventoryVehicle(BaseModel):
    stock_number: str
    year: int
    make: str
    model: str
    trim: str | None = None
    vin: str | None = None
    mileage_km: int | None = None
    colour: str | None = None
    price_cad: float | None = None
    url: str | None = None
    highlights: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Claude output contract (§5)
# ---------------------------------------------------------------------------


class ClaudeOutput(BaseModel):
    recommended_rep: RepName
    subject: str = Field(..., min_length=5, max_length=200)
    body: str = Field(..., min_length=50, max_length=800)
    booking_cta: str
    financing_angle: str
    confidence: Annotated[float, Field(ge=0.0, le=1.0)]
    escalate_to_human: bool
    escalation_reason: str | None = None

    @field_validator("body")
    @classmethod
    def body_word_count(cls, v: str) -> str:
        words = len(v.split())
        if not 90 <= words <= 140:
            raise ValueError(f"Body must be 90–140 words, got {words}")
        return v

    @field_validator("escalation_reason")
    @classmethod
    def reason_required_when_escalated(cls, v: str | None, info: object) -> str | None:
        # accessed via info.data in pydantic v2
        return v


# ---------------------------------------------------------------------------
# Draft record (stored in memory / future Supabase)
# ---------------------------------------------------------------------------


class DraftRecord(BaseModel):
    draft_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    lead: Lead
    vehicle: InventoryVehicle | None = None
    output: ClaudeOutput
    created_at: datetime = Field(default_factory=datetime.utcnow)
    decision: ApprovalDecision | None = None
    decided_by_channel: str | None = None
    decided_at: datetime | None = None
    edited_body: str | None = None

    @property
    def final_body(self) -> str:
        return self.edited_body or self.output.body


# ---------------------------------------------------------------------------
# API request / response shapes
# ---------------------------------------------------------------------------


class DraftReplyRequest(BaseModel):
    source: LeadSource
    raw_email_body: str
    received_at: datetime = Field(default_factory=datetime.utcnow)
    gmail_message_id: str | None = None
    gmail_thread_id: str | None = None


class DraftReplyResponse(BaseModel):
    draft_id: uuid.UUID
    lead_id: uuid.UUID
    escalated: bool
    escalation_reason: str | None = None
    recommended_rep: str | None = None
    confidence: float | None = None
    subject: str | None = None


class ApprovalRequest(BaseModel):
    channel: str = Field(..., description="telegram or whatsapp")
    approver_name: str
    edited_body: str | None = None


class ApprovalResponse(BaseModel):
    accepted: bool
    message: str


class BookingWebhookPayload(BaseModel):
    """Incoming TidyCal webhook when a customer books."""

    event: str
    booking_id: str
    rep: str
    customer_name: str
    customer_email: str
    start_time: datetime
    stock_number: str | None = None


class HealthResponse(BaseModel):
    status: str
    version: str = "2.1.0"


# ---------------------------------------------------------------------------
# Audit row
# ---------------------------------------------------------------------------


class AuditRow(BaseModel):
    lead_id: str
    source: str
    channel_used: str
    approver: str
    decision: str
    latency_s: float
    claude_cost_usd: float
    outcome: str
    timestamp: str

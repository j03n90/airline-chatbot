from datetime import datetime
from enum import Enum
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class AirlineCode(str, Enum):
    STA = "STA"
    NSA = "NSA"
    BHA = "BHA"


AIRLINE_NAMES = {
    AirlineCode.STA: "Suntrail Air",
    AirlineCode.NSA: "Northstar Air",
    AirlineCode.BHA: "Bluehaven Airways",
}


class FareType(str, Enum):
    ECONOMY_BASIC = "economy_basic"
    ECONOMY_STANDARD = "economy_standard"
    ECONOMY_FLEX = "economy_flex"


class RouteType(str, Enum):
    DOMESTIC = "domestic"
    INTERNATIONAL = "international"


class SegmentStatus(str, Enum):
    SCHEDULED = "scheduled"
    FLOWN = "flown"
    MISSED = "missed"
    CANCELLED = "cancelled"
    CHANGED = "changed"
    SUSPENDED = "suspended"


class BookingStatus(str, Enum):
    ACTIVE = "active"
    CHANGED = "changed"
    CANCELLED = "cancelled"
    SUSPENDED = "suspended"
    HANDOFF = "handoff"


class RefundType(str, Enum):
    ORIGINAL_PAYMENT = "original_payment"
    TRAVEL_CREDIT = "travel_credit"
    NONE = "none"


class ReasonCode(str, Enum):
    OK = "ok"
    NOT_PERMITTED = "not_permitted"
    HANDOFF_REQUIRED = "handoff_required"
    NOSHOW = "noshow"
    IDENTITY_INSUFFICIENT = "identity_insufficient"
    NOT_FOUND = "not_found"
    NOT_AUTHORIZED = "not_authorized"
    QUOTE_EXPIRED = "quote_expired"
    QUOTE_NOT_FOUND = "quote_not_found"


class TimeWindow(str, Enum):
    EARLY = "early"
    LATE = "late"
    NOSHOW = "noshow"


class QuoteKind(str, Enum):
    CHANGE = "change"
    CANCEL = "cancel"
    DISRUPTION_REFUND = "disruption_refund"
    DISRUPTION_REBOOK = "disruption_rebook"


class ExtraKind(str, Enum):
    CHECKED_BAG = "checked_bag"
    CABIN_BAG = "cabin_bag"
    SEAT = "seat"


class Extra(BaseModel):
    kind: ExtraKind
    amount_usd: float
    passenger_id: str
    segment_ids: list[str] = Field(default_factory=list)
    description: str = ""


class DisruptionNotice(BaseModel):
    segment_id: str
    notice_at_utc: datetime
    original_departure_utc: datetime
    revised_departure_utc: Optional[datetime] = None
    cancelled_by_airline: bool = False


class Segment(BaseModel):
    id: str
    origin: str
    destination: str
    departure_utc: datetime
    arrival_utc: datetime
    route_type: RouteType
    fare_usd: float
    status: SegmentStatus = SegmentStatus.SCHEDULED
    original_departure_utc: Optional[datetime] = None


class Passenger(BaseModel):
    id: str
    first_name: str
    last_name: str
    is_minor: bool = False
    ticket_fare_usd: float
    government_tax_usd: float = 0.0


class Booking(BaseModel):
    pnr: str
    airline: AirlineCode
    fare_type: FareType
    issued_at_utc: datetime
    channel: Literal["direct", "agency"] = "direct"
    status: BookingStatus = BookingStatus.ACTIVE
    passengers: list[Passenger]
    segments: list[Segment]
    extras: list[Extra] = Field(default_factory=list)
    disruption: Optional[DisruptionNotice] = None
    travel_credit_usd: float = 0.0
    notes: str = ""


class SeedPayload(BaseModel):
    now_utc: datetime
    bookings: list[Booking] = Field(default_factory=list)


class LoadRequest(BaseModel):
    now_utc: datetime
    bookings: list[Booking] = Field(default_factory=list)


class ClockResponse(BaseModel):
    now_utc: datetime


class ClockUpdateRequest(BaseModel):
    now_utc: datetime


class LookupRequest(BaseModel):
    pnr: str
    last_name: str
    first_name: Optional[str] = None


class LookupResponse(BaseModel):
    ok: bool
    reason_code: ReasonCode
    booking: Optional[Booking] = None
    verified_passenger_id: Optional[str] = None
    message: str = ""


class ChangedSegmentSpec(BaseModel):
    segment_id: str
    new_departure_utc: datetime
    new_arrival_utc: Optional[datetime] = None
    new_fare_usd: Optional[float] = None


class QuoteChangeRequest(BaseModel):
    pnr: str
    passenger_id: str
    first_name: str
    last_name: str
    changes: list[ChangedSegmentSpec]


class QuoteCancelRequest(BaseModel):
    pnr: str
    passenger_id: str
    first_name: str
    last_name: str
    segment_ids: Optional[list[str]] = None


class QuoteResult(BaseModel):
    ok: bool
    reason_code: ReasonCode
    quote_id: Optional[str] = None
    kind: Optional[QuoteKind] = None
    change_fee_usd: float = 0.0
    fare_difference_usd: float = 0.0
    total_due_usd: float = 0.0
    refund_type: RefundType = RefundType.NONE
    fare_refund_usd: float = 0.0
    tax_refund_usd: float = 0.0
    extras_refundable: bool = False
    extras_refund_usd: float = 0.0
    window: Optional[TimeWindow] = None
    itinerary_route_type: Optional[RouteType] = None
    message: str = ""
    breakdown: list[dict[str, Any]] = Field(default_factory=list)
    handoff_reason: Optional[str] = None


class ConfirmRequest(BaseModel):
    quote_id: str
    passenger_id: str
    first_name: str
    last_name: str


class ConfirmResponse(BaseModel):
    ok: bool
    reason_code: ReasonCode
    booking: Optional[Booking] = None
    quote: Optional[QuoteResult] = None
    message: str = ""


class BookingsResponse(BaseModel):
    now_utc: datetime
    bookings: list[Booking]


class OkMessage(BaseModel):
    ok: bool = True
    message: str = ""


class CreateAssistantSessionRequest(BaseModel):
    mock_session_id: str


class CreateAssistantSessionResponse(BaseModel):
    session_id: str
    mock_session_id: str


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatEvent(BaseModel):
    type: Literal["token", "done", "error"]
    text: str = ""
    handoff: bool = False
    pending_quote: Optional[QuoteResult] = None


class AssistantSessionSummary(BaseModel):
    session_id: str
    mock_session_id: str
    airline: Optional[AirlineCode] = None
    verified: bool = False
    pnr: Optional[str] = None
    pending_quote: Optional[QuoteResult] = None
    handoff: bool = False
    handoff_reason: Optional[str] = None


class TraceItem(BaseModel):
    step: str
    detail: dict[str, Any] = Field(default_factory=dict)


class TraceResponse(BaseModel):
    session_id: str
    items: list[TraceItem]
    retrieval: list[dict[str, Any]] = Field(default_factory=list)
    mock_calls: list[dict[str, Any]] = Field(default_factory=list)
    handoff: Optional[str] = None


class HealthResponse(BaseModel):
    ok: bool
    llm_configured: bool
    faiss_loaded: bool
    model: str
    embedding_model: str

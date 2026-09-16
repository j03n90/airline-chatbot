from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from backend.api.schemas import (
    Booking,
    BookingStatus,
    ChangedSegmentSpec,
    ConfirmResponse,
    LookupResponse,
    QuoteCancelRequest,
    QuoteChangeRequest,
    QuoteKind,
    QuoteResult,
    ReasonCode,
    RefundType,
    SeedPayload,
    SegmentStatus,
)
from backend.policy.engine import quote_cancel, quote_change


def _aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


class SessionState:
    def __init__(self) -> None:
        self.now: datetime = datetime.now(timezone.utc)
        self.bookings: dict[str, Booking] = {}
        self.quotes: dict[str, tuple[QuoteResult, QuoteChangeRequest | QuoteCancelRequest, str]] = {}

    def load(self, payload: SeedPayload) -> None:
        self.now = _aware(payload.now_utc)
        self.bookings = {b.pnr.upper(): deepcopy(b) for b in payload.bookings}
        self.quotes = {}

    def reset(self) -> None:
        self.bookings = {}
        self.quotes = {}
        self.now = datetime.now(timezone.utc)


class MockStore:
    def __init__(self) -> None:
        self._sessions: dict[str, SessionState] = {}

    def session(self, session_id: str) -> SessionState:
        if session_id not in self._sessions:
            self._sessions[session_id] = SessionState()
        return self._sessions[session_id]

    def load(self, session_id: str, payload: SeedPayload) -> SessionState:
        state = self.session(session_id)
        state.load(payload)
        return state

    def reset(self, session_id: str) -> None:
        self.session(session_id).reset()

    def set_clock(self, session_id: str, now: datetime) -> datetime:
        state = self.session(session_id)
        state.now = _aware(now)
        return state.now

    def list_bookings(self, session_id: str) -> list[Booking]:
        return list(self.session(session_id).bookings.values())

    def get_booking(self, session_id: str, pnr: str) -> Optional[Booking]:
        return self.session(session_id).bookings.get(pnr.upper())

    def lookup(self, session_id: str, pnr: str, last_name: str, first_name: Optional[str]) -> LookupResponse:
        booking = self.get_booking(session_id, pnr)
        if booking is None:
            return LookupResponse(ok=False, reason_code=ReasonCode.NOT_FOUND, message="No booking found for that reference.")
        last = last_name.strip().lower()
        if not first_name or not first_name.strip():
            matches = [p for p in booking.passengers if p.last_name.lower() == last]
            if not matches:
                return LookupResponse(ok=False, reason_code=ReasonCode.NOT_FOUND, message="No traveler on this booking matches that surname.")
            return LookupResponse(
                ok=False,
                reason_code=ReasonCode.IDENTITY_INSUFFICIENT,
                message="A booking reference and shared surname are not enough. Name the traveler (first and last name) to view or change a ticket.",
            )
        first = first_name.strip().lower()
        for p in booking.passengers:
            if p.last_name.lower() == last and p.first_name.lower() == first:
                return LookupResponse(ok=True, reason_code=ReasonCode.OK, booking=booking, verified_passenger_id=p.id)
        return LookupResponse(
            ok=False,
            reason_code=ReasonCode.NOT_AUTHORIZED,
            message="That name does not match a traveler on this booking. A payer cannot view another adult's ticket without authorization.",
        )

    def _verified(self, session_id: str, pnr: str, passenger_id: str, first: str, last: str) -> LookupResponse:
        looked = self.lookup(session_id, pnr, last, first)
        if not looked.ok:
            return looked
        if looked.verified_passenger_id != passenger_id:
            return LookupResponse(
                ok=False,
                reason_code=ReasonCode.NOT_AUTHORIZED,
                message="Verified traveler does not match the ticket you asked to change.",
            )
        return looked

    def quote_change(self, session_id: str, req: QuoteChangeRequest) -> QuoteResult:
        looked = self._verified(session_id, req.pnr, req.passenger_id, req.first_name, req.last_name)
        if not looked.ok or looked.booking is None:
            return QuoteResult(ok=False, reason_code=looked.reason_code, message=looked.message)
        result = quote_change(looked.booking, req.passenger_id, req.changes, self.session(session_id).now)
        if result.ok:
            result.quote_id = uuid4().hex
            self.session(session_id).quotes[result.quote_id] = (result, req, req.pnr.upper())
        return result

    def quote_cancel(self, session_id: str, req: QuoteCancelRequest) -> QuoteResult:
        looked = self._verified(session_id, req.pnr, req.passenger_id, req.first_name, req.last_name)
        if not looked.ok or looked.booking is None:
            return QuoteResult(ok=False, reason_code=looked.reason_code, message=looked.message)
        result = quote_cancel(looked.booking, req.passenger_id, self.session(session_id).now, req.segment_ids)
        if result.ok:
            result.quote_id = uuid4().hex
            self.session(session_id).quotes[result.quote_id] = (result, req, req.pnr.upper())
        return result

    def get_quote(self, session_id: str, quote_id: str) -> Optional[QuoteResult]:
        item = self.session(session_id).quotes.get(quote_id)
        return item[0] if item else None

    def confirm(self, session_id: str, quote_id: str, passenger_id: str, first: str, last: str) -> ConfirmResponse:
        state = self.session(session_id)
        packed = state.quotes.get(quote_id)
        if packed is None:
            return ConfirmResponse(ok=False, reason_code=ReasonCode.QUOTE_NOT_FOUND, message="Quote not found or already used.")
        result, req, pnr = packed
        looked = self._verified(session_id, pnr, passenger_id, first, last)
        if not looked.ok or looked.booking is None:
            return ConfirmResponse(ok=False, reason_code=looked.reason_code, message=looked.message)
        booking = looked.booking
        if isinstance(req, QuoteChangeRequest):
            refreshed = quote_change(booking, passenger_id, req.changes, state.now)
            if not refreshed.ok:
                return ConfirmResponse(ok=False, reason_code=refreshed.reason_code, quote=refreshed, message=refreshed.message)
            self._apply_change(booking, req.changes)
            booking.status = BookingStatus.CHANGED
        else:
            refreshed = quote_cancel(booking, passenger_id, state.now, req.segment_ids)
            if not refreshed.ok:
                return ConfirmResponse(ok=False, reason_code=refreshed.reason_code, quote=refreshed, message=refreshed.message)
            if refreshed.kind in (QuoteKind.CANCEL, QuoteKind.DISRUPTION_REFUND):
                self._apply_cancel(booking, passenger_id, refreshed)
        del state.quotes[quote_id]
        refreshed.quote_id = quote_id
        return ConfirmResponse(ok=True, reason_code=ReasonCode.OK, booking=booking, quote=refreshed, message="Request completed.")

    def _apply_change(self, booking: Booking, changes: list[ChangedSegmentSpec]) -> None:
        by_id = {s.id: s for s in booking.segments}
        for spec in changes:
            segment = by_id[spec.segment_id]
            if segment.original_departure_utc is None:
                segment.original_departure_utc = segment.departure_utc
            segment.departure_utc = spec.new_departure_utc
            if spec.new_arrival_utc:
                segment.arrival_utc = spec.new_arrival_utc
            if spec.new_fare_usd is not None:
                segment.fare_usd = spec.new_fare_usd
            segment.status = SegmentStatus.CHANGED

    def _apply_cancel(self, booking: Booking, passenger_id: str, quote: QuoteResult) -> None:
        booking.passengers = [p for p in booking.passengers if p.id != passenger_id]
        booking.extras = [e for e in booking.extras if e.passenger_id != passenger_id]
        if quote.refund_type == RefundType.TRAVEL_CREDIT:
            booking.travel_credit_usd += quote.fare_refund_usd
        if not booking.passengers:
            booking.status = BookingStatus.CANCELLED
            for s in booking.segments:
                s.status = SegmentStatus.CANCELLED
        else:
            booking.notes = f"Passenger {passenger_id} cancelled."


store = MockStore()

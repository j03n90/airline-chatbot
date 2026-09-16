from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from backend.api.schemas import (
    AirlineCode,
    Booking,
    ChangedSegmentSpec,
    Extra,
    ExtraKind,
    FareType,
    QuoteKind,
    QuoteResult,
    ReasonCode,
    RefundType,
    RouteType,
    SegmentStatus,
    TimeWindow,
)
from backend.policy.tables import (
    BAGGAGE,
    BHA_FEE_CUTOVER,
    CANCEL_RULES,
    CHANGE_FEES,
    DISRUPTION_MINUTES,
    NOT_PERMITTED,
)


def ensure_aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def time_window(now: datetime, departure: datetime) -> TimeWindow:
    now = ensure_aware(now)
    departure = ensure_aware(departure)
    delta = departure - now
    if delta <= timedelta(0):
        return TimeWindow.NOSHOW
    if delta >= timedelta(hours=24):
        return TimeWindow.EARLY
    return TimeWindow.LATE


def itinerary_route_type(booking: Booking) -> RouteType:
    if any(s.route_type == RouteType.INTERNATIONAL for s in booking.segments):
        return RouteType.INTERNATIONAL
    return RouteType.DOMESTIC


def travel_has_started(booking: Booking) -> bool:
    return any(s.status == SegmentStatus.FLOWN for s in booking.segments)


def has_noshow(booking: Booking) -> bool:
    return any(s.status in (SegmentStatus.MISSED, SegmentStatus.SUSPENDED) for s in booking.segments)


def passenger_by_id(booking: Booking, passenger_id: str):
    for p in booking.passengers:
        if p.id == passenger_id:
            return p
    return None


def segment_by_id(booking: Booking, segment_id: str):
    for s in booking.segments:
        if s.id == segment_id:
            return s
    return None


def extras_for_passenger(booking: Booking, passenger_id: str) -> list[Extra]:
    return [e for e in booking.extras if e.passenger_id == passenger_id]


def extra_total(booking: Booking, passenger_id: str) -> float:
    return sum(e.amount_usd for e in extras_for_passenger(booking, passenger_id))


def bha_standard_change_fee(issued_at: datetime) -> float:
    cutover = datetime.fromisoformat(BHA_FEE_CUTOVER)
    issued = ensure_aware(issued_at)
    if issued < cutover:
        return 85.0
    return 55.0


def change_fee_one_segment(
    airline: AirlineCode,
    fare: FareType,
    window: TimeWindow,
    route: RouteType,
    issued_at: datetime,
) -> Optional[float]:
    if window == TimeWindow.NOSHOW:
        return NOT_PERMITTED
    table = CHANGE_FEES[airline][fare][window]
    if airline == AirlineCode.STA:
        return table[route]
    if airline == AirlineCode.BHA and fare == FareType.ECONOMY_STANDARD and window == TimeWindow.EARLY:
        return bha_standard_change_fee(issued_at)
    return table


def cancel_rule(
    airline: AirlineCode,
    fare: FareType,
    window: TimeWindow,
    itinerary_route: RouteType,
) -> tuple[str, float]:
    table = CANCEL_RULES[airline][fare][window]
    if airline == AirlineCode.STA:
        return table[itinerary_route]
    return table


def baggage_allowance(airline: AirlineCode, fare: FareType, route: RouteType) -> dict:
    block = BAGGAGE[airline][fare]
    cabin = block["cabin"]
    checked = block["checked"]
    if airline == AirlineCode.STA:
        checked = checked[route]
    extra = {
        "cabin_count": cabin["count"],
        "cabin_kg": cabin["kg"],
        "checked_count": checked["count"],
        "checked_kg": checked["kg"],
        "extra_checked_usd": BAGGAGE[airline]["extra_checked_usd"],
        "extra_checked_kg": BAGGAGE[airline]["extra_checked_kg"],
        "buy_cabin_bag": BAGGAGE[airline]["buy_cabin_bag"],
    }
    if extra["buy_cabin_bag"]:
        extra["buy_cabin_usd"] = BAGGAGE[airline]["buy_cabin_usd"]
        extra["buy_cabin_kg"] = BAGGAGE[airline]["buy_cabin_kg"]
    return extra


def disruption_qualifies(airline: AirlineCode, original: datetime, revised: Optional[datetime], cancelled: bool) -> bool:
    if cancelled:
        return True
    if revised is None:
        return False
    delta = abs((ensure_aware(revised) - ensure_aware(original)).total_seconds()) / 60.0
    return delta >= DISRUPTION_MINUTES[airline]


def quote_change(booking: Booking, passenger_id: str, changes: list[ChangedSegmentSpec], now: datetime) -> QuoteResult:
    passenger = passenger_by_id(booking, passenger_id)
    if passenger is None:
        return QuoteResult(ok=False, reason_code=ReasonCode.NOT_FOUND, message="Passenger not on this booking.")
    if passenger.is_minor:
        return QuoteResult(
            ok=False,
            reason_code=ReasonCode.HANDOFF_REQUIRED,
            handoff_reason="Guardianship requests require service-desk review.",
            message="Requests for a minor must be reviewed by the service desk.",
        )
    if has_noshow(booking):
        return QuoteResult(
            ok=False,
            reason_code=ReasonCode.NOSHOW,
            window=TimeWindow.NOSHOW,
            message="A no-show suspends remaining segments. Contact the service desk; there is no automatic reinstatement.",
        )
    if not changes:
        return QuoteResult(ok=False, reason_code=ReasonCode.NOT_PERMITTED, message="No segments specified to change.")

    fee_total = 0.0
    fare_diff_total = 0.0
    breakdown = []
    worst_window = TimeWindow.EARLY

    for spec in changes:
        segment = segment_by_id(booking, spec.segment_id)
        if segment is None:
            return QuoteResult(ok=False, reason_code=ReasonCode.NOT_FOUND, message=f"Segment {spec.segment_id} not found.")
        if segment.status == SegmentStatus.FLOWN:
            return QuoteResult(
                ok=False,
                reason_code=ReasonCode.HANDOFF_REQUIRED,
                handoff_reason="Flown segments cannot be changed under the standard table.",
                message="Flown segments cannot be changed here. Remaining unflown segments may be reviewed separately.",
            )
        window = time_window(now, segment.departure_utc)
        if window == TimeWindow.NOSHOW:
            return QuoteResult(
                ok=False,
                reason_code=ReasonCode.NOSHOW,
                window=TimeWindow.NOSHOW,
                message="A complete authorized request must arrive before departure. This segment is now treated as a no-show.",
            )
        if window == TimeWindow.LATE:
            worst_window = TimeWindow.LATE
        fee = change_fee_one_segment(
            booking.airline, booking.fare_type, window, segment.route_type, booking.issued_at_utc
        )
        if fee is NOT_PERMITTED:
            return QuoteResult(
                ok=False,
                reason_code=ReasonCode.NOT_PERMITTED,
                window=window,
                message=(
                    f"{booking.airline.value} {booking.fare_type.value} cannot be changed "
                    f"in the {window.value} window on a {segment.route_type.value} segment."
                ),
            )
        new_fare = spec.new_fare_usd if spec.new_fare_usd is not None else segment.fare_usd
        diff = max(0.0, new_fare - segment.fare_usd)
        fee_total += fee
        fare_diff_total += diff
        breakdown.append(
            {
                "segment_id": segment.id,
                "route_type": segment.route_type.value,
                "window": window.value,
                "change_fee_usd": fee,
                "fare_difference_usd": diff,
            }
        )

    return QuoteResult(
        ok=True,
        reason_code=ReasonCode.OK,
        kind=QuoteKind.CHANGE,
        change_fee_usd=fee_total,
        fare_difference_usd=fare_diff_total,
        total_due_usd=fee_total + fare_diff_total,
        window=worst_window,
        itinerary_route_type=itinerary_route_type(booking),
        extras_refundable=False,
        message="Change is permitted if you confirm this quote. Unused extras transfer subject to availability.",
        breakdown=breakdown,
    )


def quote_cancel(
    booking: Booking,
    passenger_id: str,
    now: datetime,
    segment_ids: Optional[list[str]] = None,
) -> QuoteResult:
    passenger = passenger_by_id(booking, passenger_id)
    if passenger is None:
        return QuoteResult(ok=False, reason_code=ReasonCode.NOT_FOUND, message="Passenger not on this booking.")
    if passenger.is_minor:
        return QuoteResult(
            ok=False,
            reason_code=ReasonCode.HANDOFF_REQUIRED,
            handoff_reason="Guardianship requests require service-desk review.",
            message="Requests for a minor must be reviewed by the service desk.",
        )
    if segment_ids:
        wanted = set(segment_ids)
        all_ids = {s.id for s in booking.segments}
        if wanted != all_ids:
            return QuoteResult(
                ok=False,
                reason_code=ReasonCode.HANDOFF_REQUIRED,
                handoff_reason="Selected-segment cancellation requires Section 9 review.",
                message="Cancelling selected segments only is not covered by the whole-ticket table. This needs the service desk.",
            )
    if travel_has_started(booking):
        return QuoteResult(
            ok=False,
            reason_code=ReasonCode.HANDOFF_REQUIRED,
            handoff_reason="Partly used itinerary refunds require Section 9 review.",
            message="Travel has started. A remaining-value refund needs manual review; do not apply the unused-ticket table.",
        )
    if has_noshow(booking):
        tax = passenger.government_tax_usd
        return QuoteResult(
            ok=False,
            reason_code=ReasonCode.NOSHOW,
            window=TimeWindow.NOSHOW,
            refund_type=RefundType.NONE,
            fare_refund_usd=0.0,
            tax_refund_usd=tax,
            extras_refundable=False,
            extras_refund_usd=0.0,
            message="No-show: remaining fare has no standard refund or credit, including Flex. Unused government taxes remain refundable.",
        )

    first = min(booking.segments, key=lambda s: ensure_aware(s.departure_utc))
    window = time_window(now, first.departure_utc)
    if window == TimeWindow.NOSHOW:
        tax = passenger.government_tax_usd
        return QuoteResult(
            ok=False,
            reason_code=ReasonCode.NOSHOW,
            window=TimeWindow.NOSHOW,
            tax_refund_usd=tax,
            extras_refundable=False,
            message="Request arrived at or after departure. No-show rules apply. Unused taxes remain refundable.",
        )

    route = itinerary_route_type(booking)
    refund_kind, fee = cancel_rule(booking.airline, booking.fare_type, window, route)
    fare = passenger.ticket_fare_usd
    fare_refund = max(0.0, fare - fee) if refund_kind != "none" else 0.0
    extras_sum = extra_total(booking, passenger_id)
    disruption = booking.disruption
    if disruption and disruption_qualifies(
        booking.airline,
        disruption.original_departure_utc,
        disruption.revised_departure_utc,
        disruption.cancelled_by_airline,
    ):
        return QuoteResult(
            ok=True,
            reason_code=ReasonCode.OK,
            kind=QuoteKind.DISRUPTION_REFUND,
            refund_type=RefundType.ORIGINAL_PAYMENT,
            fare_refund_usd=fare,
            tax_refund_usd=passenger.government_tax_usd,
            extras_refundable=True,
            extras_refund_usd=extras_sum,
            window=window,
            itinerary_route_type=route,
            message="Qualifying airline disruption: full fare, unused taxes and unused extras refund to the original payment method. No cancellation fee.",
        )

    return QuoteResult(
        ok=True,
        reason_code=ReasonCode.OK,
        kind=QuoteKind.CANCEL,
        refund_type=RefundType(refund_kind),
        fare_refund_usd=fare_refund,
        tax_refund_usd=passenger.government_tax_usd,
        extras_refundable=False,
        extras_refund_usd=0.0,
        change_fee_usd=fee if refund_kind != "none" else 0.0,
        window=window,
        itinerary_route_type=route,
        message=(
            "Voluntary cancellation of a wholly unused ticket. "
            "Purchased extras are not refundable. Unused government taxes return to the original payment method."
        ),
        breakdown=[
            {
                "fare_usd": fare,
                "cancel_fee_usd": fee if refund_kind != "none" else 0.0,
                "refund_type": refund_kind,
                "extras_usd": extras_sum,
            }
        ],
    )

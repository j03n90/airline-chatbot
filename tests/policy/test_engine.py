from datetime import datetime, timedelta, timezone

from backend.api.schemas import (
    AirlineCode,
    Booking,
    ChangedSegmentSpec,
    Extra,
    ExtraKind,
    FareType,
    Passenger,
    ReasonCode,
    RefundType,
    RouteType,
    Segment,
    SegmentStatus,
    TimeWindow,
)
from backend.policy.engine import (
    baggage_allowance,
    disruption_qualifies,
    quote_cancel,
    quote_change,
    time_window,
)


def dt(s: str) -> datetime:
    return datetime.fromisoformat(s).replace(tzinfo=timezone.utc)


NOW = dt("2026-09-16T12:00:00")


def seg(sid, origin, dest, dep, route, fare=200.0, status=SegmentStatus.SCHEDULED) -> Segment:
    departure = dt(dep)
    return Segment(
        id=sid,
        origin=origin,
        destination=dest,
        departure_utc=departure,
        arrival_utc=departure + timedelta(hours=3),
        route_type=route,
        fare_usd=fare,
        status=status,
    )


def pax(pid="p1", fare=400.0, tax=40.0, first="Ada", last="Ng") -> Passenger:
    return Passenger(
        id=pid,
        first_name=first,
        last_name=last,
        ticket_fare_usd=fare,
        government_tax_usd=tax,
    )


def booking(
    airline: AirlineCode,
    fare: FareType,
    segments: list[Segment],
    issued="2026-08-01T00:00:00",
    passengers=None,
    extras=None,
    disruption=None,
) -> Booking:
    return Booking(
        pnr="ABC123",
        airline=airline,
        fare_type=fare,
        issued_at_utc=dt(issued),
        passengers=passengers or [pax()],
        segments=segments,
        extras=extras or [],
        disruption=disruption,
    )


def early_dom():
    return seg("s1", "AST", "BRK", "2026-09-18T12:00:00", RouteType.DOMESTIC)


def early_intl():
    return seg("s2", "AST", "ZUR", "2026-09-18T12:00:00", RouteType.INTERNATIONAL)


def late_dom():
    return seg("s1", "AST", "BRK", "2026-09-16T20:00:00", RouteType.DOMESTIC)


def late_intl():
    return seg("s2", "AST", "ZUR", "2026-09-16T20:00:00", RouteType.INTERNATIONAL)


def test_window_boundaries():
    dep = dt("2026-09-17T12:00:00")
    assert time_window(dt("2026-09-16T12:00:00"), dep) == TimeWindow.EARLY
    assert time_window(dt("2026-09-16T12:00:01"), dep) == TimeWindow.LATE
    assert time_window(dep, dep) == TimeWindow.NOSHOW
    assert time_window(dt("2026-09-17T12:00:01"), dep) == TimeWindow.NOSHOW


def change(b: Booking, segs, now=NOW, new_fare=None):
    specs = [
        ChangedSegmentSpec(segment_id=s.id, new_departure_utc=s.departure_utc + timedelta(days=1), new_fare_usd=new_fare)
        for s in segs
    ]
    return quote_change(b, "p1", specs, now)


# --- Change matrix: STA ---

def test_sta_basic_early_domestic_40():
    q = change(booking(AirlineCode.STA, FareType.ECONOMY_BASIC, [early_dom()]), [early_dom()])
    assert q.ok and q.change_fee_usd == 40


def test_sta_basic_early_international_forbidden():
    q = change(booking(AirlineCode.STA, FareType.ECONOMY_BASIC, [early_intl()]), [early_intl()])
    assert not q.ok and q.reason_code == ReasonCode.NOT_PERMITTED


def test_sta_basic_late_forbidden():
    q = change(booking(AirlineCode.STA, FareType.ECONOMY_BASIC, [late_dom()]), [late_dom()])
    assert not q.ok and q.reason_code == ReasonCode.NOT_PERMITTED


def test_sta_standard_early_mixed_85():
    segs = [
        seg("s1", "AST", "BRK", "2026-09-18T12:00:00", RouteType.DOMESTIC),
        seg("s2", "AST", "ZUR", "2026-09-18T18:00:00", RouteType.INTERNATIONAL),
    ]
    q = change(booking(AirlineCode.STA, FareType.ECONOMY_STANDARD, segs), segs)
    assert q.ok
    assert q.change_fee_usd == 85


def test_sta_standard_late_domestic_50_intl_100():
    segs = [
        seg("s1", "AST", "BRK", "2026-09-16T20:00:00", RouteType.DOMESTIC),
        seg("s2", "AST", "ZUR", "2026-09-16T22:00:00", RouteType.INTERNATIONAL),
    ]
    q = change(booking(AirlineCode.STA, FareType.ECONOMY_STANDARD, segs), segs)
    assert q.ok and q.change_fee_usd == 150


def test_sta_flex_early_zero_either_route():
    segs = [
        seg("s1", "AST", "BRK", "2026-09-18T12:00:00", RouteType.DOMESTIC),
        seg("s2", "AST", "ZUR", "2026-09-18T18:00:00", RouteType.INTERNATIONAL),
    ]
    q = change(booking(AirlineCode.STA, FareType.ECONOMY_FLEX, segs), segs)
    assert q.ok and q.change_fee_usd == 0


def test_sta_flex_late_domestic_0_intl_25():
    segs = [
        seg("s1", "AST", "BRK", "2026-09-16T20:00:00", RouteType.DOMESTIC),
        seg("s2", "AST", "ZUR", "2026-09-16T22:00:00", RouteType.INTERNATIONAL),
    ]
    q = change(booking(AirlineCode.STA, FareType.ECONOMY_FLEX, segs), segs)
    assert q.ok and q.change_fee_usd == 25


# --- Change matrix: NSA ---

def test_nsa_basic_early_70_late_forbidden():
    q = change(booking(AirlineCode.NSA, FareType.ECONOMY_BASIC, [early_dom()]), [early_dom()])
    assert q.ok and q.change_fee_usd == 70
    q2 = change(booking(AirlineCode.NSA, FareType.ECONOMY_BASIC, [late_dom()]), [late_dom()])
    assert not q2.ok


def test_nsa_standard_early_25_late_60():
    q = change(booking(AirlineCode.NSA, FareType.ECONOMY_STANDARD, [early_intl()]), [early_intl()])
    assert q.ok and q.change_fee_usd == 25
    q2 = change(booking(AirlineCode.NSA, FareType.ECONOMY_STANDARD, [late_intl()]), [late_intl()])
    assert q2.ok and q2.change_fee_usd == 60


def test_nsa_flex_always_zero():
    q = change(booking(AirlineCode.NSA, FareType.ECONOMY_FLEX, [early_dom()]), [early_dom()])
    assert q.ok and q.change_fee_usd == 0
    q2 = change(booking(AirlineCode.NSA, FareType.ECONOMY_FLEX, [late_intl()]), [late_intl()])
    assert q2.ok and q2.change_fee_usd == 0


def test_nsa_two_pax_two_segments_example():
    segs = [
        seg("s1", "AST", "BRK", "2026-09-18T12:00:00", RouteType.DOMESTIC, 100),
        seg("s2", "AST", "ZUR", "2026-09-19T12:00:00", RouteType.INTERNATIONAL, 150),
    ]
    q = change(booking(AirlineCode.NSA, FareType.ECONOMY_STANDARD, segs), segs, new_fare=None)
    assert q.change_fee_usd == 50


# --- Change matrix: BHA ---

def test_bha_basic_never():
    q = change(booking(AirlineCode.BHA, FareType.ECONOMY_BASIC, [early_dom()]), [early_dom()])
    assert not q.ok and q.reason_code == ReasonCode.NOT_PERMITTED
    q2 = change(booking(AirlineCode.BHA, FareType.ECONOMY_BASIC, [late_dom()]), [late_dom()])
    assert not q2.ok


def test_bha_standard_issuance_85_vs_55():
    q_old = change(
        booking(AirlineCode.BHA, FareType.ECONOMY_STANDARD, [early_dom()], issued="2026-06-30T23:59:59"),
        [early_dom()],
    )
    q_new = change(
        booking(AirlineCode.BHA, FareType.ECONOMY_STANDARD, [early_dom()], issued="2026-07-01T00:00:00"),
        [early_dom()],
    )
    assert q_old.ok and q_old.change_fee_usd == 85
    assert q_new.ok and q_new.change_fee_usd == 55


def test_bha_standard_late_forbidden():
    q = change(booking(AirlineCode.BHA, FareType.ECONOMY_STANDARD, [late_dom()]), [late_dom()])
    assert not q.ok


def test_bha_flex_early_15_late_45():
    q = change(booking(AirlineCode.BHA, FareType.ECONOMY_FLEX, [early_dom()]), [early_dom()])
    assert q.ok and q.change_fee_usd == 15
    q2 = change(booking(AirlineCode.BHA, FareType.ECONOMY_FLEX, [late_dom()]), [late_dom()])
    assert q2.ok and q2.change_fee_usd == 45


def test_positive_fare_difference_added_lower_fare_no_credit():
    s = early_dom()
    b = booking(AirlineCode.NSA, FareType.ECONOMY_FLEX, [s])
    up = quote_change(
        b,
        "p1",
        [ChangedSegmentSpec(segment_id="s1", new_departure_utc=s.departure_utc + timedelta(days=1), new_fare_usd=230)],
        NOW,
    )
    down = quote_change(
        b,
        "p1",
        [ChangedSegmentSpec(segment_id="s1", new_departure_utc=s.departure_utc + timedelta(days=1), new_fare_usd=100)],
        NOW,
    )
    assert up.ok and up.fare_difference_usd == 30 and up.total_due_usd == 30
    assert down.ok and down.fare_difference_usd == 0


def test_change_at_departure_is_noshow():
    s = seg("s1", "AST", "BRK", "2026-09-16T12:00:00", RouteType.DOMESTIC)
    q = change(booking(AirlineCode.NSA, FareType.ECONOMY_FLEX, [s]), [s], now=dt("2026-09-16T12:00:00"))
    assert not q.ok and q.reason_code == ReasonCode.NOSHOW


# --- Cancel matrix ---

def test_cancel_taxes_always_refundable_when_ok():
    b = booking(AirlineCode.BHA, FareType.ECONOMY_BASIC, [early_dom()])
    q = quote_cancel(b, "p1", NOW)
    assert q.ok
    assert q.refund_type == RefundType.NONE
    assert q.fare_refund_usd == 0
    assert q.tax_refund_usd == 40
    assert q.extras_refundable is False


def test_sta_standard_domestic_credit_25_international_none():
    q = quote_cancel(booking(AirlineCode.STA, FareType.ECONOMY_STANDARD, [early_dom()], passengers=[pax(fare=200)]), "p1", NOW)
    assert q.ok and q.refund_type == RefundType.TRAVEL_CREDIT and q.fare_refund_usd == 175
    q2 = quote_cancel(
        booking(
            AirlineCode.STA,
            FareType.ECONOMY_STANDARD,
            [early_dom(), early_intl()],
            passengers=[pax(fare=400)],
        ),
        "p1",
        NOW,
    )
    assert q2.ok and q2.refund_type == RefundType.NONE and q2.fare_refund_usd == 0
    assert q2.tax_refund_usd == 40


def test_sta_flex_cancel_windows():
    q = quote_cancel(booking(AirlineCode.STA, FareType.ECONOMY_FLEX, [early_dom()], passengers=[pax(fare=200)]), "p1", NOW)
    assert q.refund_type == RefundType.ORIGINAL_PAYMENT and q.fare_refund_usd == 200
    q2 = quote_cancel(booking(AirlineCode.STA, FareType.ECONOMY_FLEX, [early_intl()], passengers=[pax(fare=200)]), "p1", NOW)
    assert q2.refund_type == RefundType.ORIGINAL_PAYMENT and q2.fare_refund_usd == 150
    q3 = quote_cancel(booking(AirlineCode.STA, FareType.ECONOMY_FLEX, [late_dom()], passengers=[pax(fare=200)]), "p1", NOW)
    assert q3.refund_type == RefundType.ORIGINAL_PAYMENT and q3.fare_refund_usd == 180
    q4 = quote_cancel(booking(AirlineCode.STA, FareType.ECONOMY_FLEX, [late_intl()], passengers=[pax(fare=200)]), "p1", NOW)
    assert q4.refund_type == RefundType.TRAVEL_CREDIT and q4.fare_refund_usd == 125


def test_nsa_flex_full_original_payment():
    q = quote_cancel(booking(AirlineCode.NSA, FareType.ECONOMY_FLEX, [late_intl()]), "p1", NOW)
    assert q.ok and q.refund_type == RefundType.ORIGINAL_PAYMENT and q.fare_refund_usd == 400


def test_nsa_standard_credit_40_early_80_late():
    q = quote_cancel(booking(AirlineCode.NSA, FareType.ECONOMY_STANDARD, [early_dom()], passengers=[pax(fare=200)]), "p1", NOW)
    assert q.refund_type == RefundType.TRAVEL_CREDIT and q.fare_refund_usd == 160
    q2 = quote_cancel(booking(AirlineCode.NSA, FareType.ECONOMY_STANDARD, [late_dom()], passengers=[pax(fare=200)]), "p1", NOW)
    assert q2.refund_type == RefundType.TRAVEL_CREDIT and q2.fare_refund_usd == 120


def test_bha_standard_no_fare_flex_early_credit():
    q = quote_cancel(booking(AirlineCode.BHA, FareType.ECONOMY_STANDARD, [early_dom()]), "p1", NOW)
    assert q.refund_type == RefundType.NONE and q.tax_refund_usd == 40
    q2 = quote_cancel(booking(AirlineCode.BHA, FareType.ECONOMY_FLEX, [early_dom()], passengers=[pax(fare=100)]), "p1", NOW)
    assert q2.refund_type == RefundType.TRAVEL_CREDIT and q2.fare_refund_usd == 70
    q3 = quote_cancel(booking(AirlineCode.BHA, FareType.ECONOMY_FLEX, [late_dom()]), "p1", NOW)
    assert q3.refund_type == RefundType.NONE


def test_cancel_fee_cannot_go_below_zero():
    q = quote_cancel(booking(AirlineCode.NSA, FareType.ECONOMY_STANDARD, [late_dom()], passengers=[pax(fare=50)]), "p1", NOW)
    assert q.fare_refund_usd == 0


def test_extras_not_refundable_voluntary():
    extra = Extra(kind=ExtraKind.CHECKED_BAG, amount_usd=50, passenger_id="p1", segment_ids=["s1"])
    q = quote_cancel(
        booking(AirlineCode.NSA, FareType.ECONOMY_FLEX, [early_dom()], extras=[extra]),
        "p1",
        NOW,
    )
    assert q.extras_refundable is False and q.extras_refund_usd == 0


def test_partial_used_handoff():
    segs = [
        seg("s1", "AST", "BRK", "2026-09-10T12:00:00", RouteType.DOMESTIC, status=SegmentStatus.FLOWN),
        seg("s2", "BRK", "ZUR", "2026-09-18T12:00:00", RouteType.INTERNATIONAL),
    ]
    q = quote_cancel(booking(AirlineCode.NSA, FareType.ECONOMY_FLEX, segs), "p1", NOW)
    assert not q.ok and q.reason_code == ReasonCode.HANDOFF_REQUIRED


def test_selected_segment_cancel_handoff():
    segs = [
        seg("s1", "AST", "BRK", "2026-09-18T12:00:00", RouteType.DOMESTIC),
        seg("s2", "BRK", "ZUR", "2026-09-19T12:00:00", RouteType.INTERNATIONAL),
    ]
    q = quote_cancel(booking(AirlineCode.NSA, FareType.ECONOMY_FLEX, segs), "p1", NOW, segment_ids=["s1"])
    assert not q.ok and q.reason_code == ReasonCode.HANDOFF_REQUIRED


def test_minor_handoff():
    minor = pax()
    minor.is_minor = True
    q = quote_cancel(booking(AirlineCode.NSA, FareType.ECONOMY_FLEX, [early_dom()], passengers=[minor]), "p1", NOW)
    assert q.reason_code == ReasonCode.HANDOFF_REQUIRED


def test_baggage_sta_basic_domestic_vs_international():
    d = baggage_allowance(AirlineCode.STA, FareType.ECONOMY_BASIC, RouteType.DOMESTIC)
    i = baggage_allowance(AirlineCode.STA, FareType.ECONOMY_BASIC, RouteType.INTERNATIONAL)
    assert d["checked_count"] == 0
    assert i["checked_count"] == 1 and i["checked_kg"] == 20
    assert d["cabin_kg"] == 7


def test_baggage_bha_basic_none():
    b = baggage_allowance(AirlineCode.BHA, FareType.ECONOMY_BASIC, RouteType.DOMESTIC)
    assert b["cabin_count"] == 0 and b["checked_count"] == 0
    assert b["buy_cabin_bag"] is True and b["buy_cabin_usd"] == 25


def test_disruption_thresholds():
    orig = dt("2026-09-18T12:00:00")
    assert disruption_qualifies(AirlineCode.STA, orig, orig + timedelta(minutes=120), False)
    assert not disruption_qualifies(AirlineCode.STA, orig, orig + timedelta(minutes=119), False)
    assert not disruption_qualifies(AirlineCode.BHA, orig, orig + timedelta(minutes=120), False)
    assert disruption_qualifies(AirlineCode.BHA, orig, orig + timedelta(minutes=180), False)
    assert disruption_qualifies(AirlineCode.NSA, orig, None, True)

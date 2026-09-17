from datetime import datetime, timedelta, timezone

from backend.api.schemas import (
    AirlineCode,
    Booking,
    DisruptionNotice,
    Extra,
    ExtraKind,
    FareType,
    Passenger,
    RouteType,
    SeedPayload,
    Segment,
    SegmentStatus,
)

NOW = datetime(2026, 9, 16, 12, 0, 0, tzinfo=timezone.utc)


def _dt(s: str) -> datetime:
    return datetime.fromisoformat(s).replace(tzinfo=timezone.utc)


def _seg(sid, origin, dest, dep, route, fare=200.0, status=SegmentStatus.SCHEDULED) -> Segment:
    departure = _dt(dep) if isinstance(dep, str) else dep
    return Segment(
        id=sid,
        origin=origin,
        destination=dest,
        departure_utc=departure,
        arrival_utc=departure + timedelta(hours=3),
        route_type=RouteType(route) if isinstance(route, str) else route,
        fare_usd=fare,
        status=status,
    )


def _pax(pid="p1", first="Ada", last="Ng", fare=400.0, tax=40.0, minor=False) -> Passenger:
    return Passenger(
        id=pid,
        first_name=first,
        last_name=last,
        is_minor=minor,
        ticket_fare_usd=fare,
        government_tax_usd=tax,
    )


def seed(bookings: list[Booking], now: datetime = NOW) -> SeedPayload:
    return SeedPayload(now_utc=now, bookings=bookings)


SEED_STA_STANDARD_MIXED = seed(
    [
        Booking(
            pnr="STA85X",
            airline=AirlineCode.STA,
            fare_type=FareType.ECONOMY_STANDARD,
            issued_at_utc=_dt("2026-08-01T00:00:00"),
            passengers=[_pax(fare=400, tax=45)],
            segments=[
                _seg("s1", "AST", "BRK", "2026-09-18T12:00:00", "domestic", 180),
                _seg("s2", "BRK", "ZUR", "2026-09-18T18:00:00", "international", 220),
            ],
        )
    ]
)

SEED_NSA_FLEX = seed(
    [
        Booking(
            pnr="NSAFLX",
            airline=AirlineCode.NSA,
            fare_type=FareType.ECONOMY_FLEX,
            issued_at_utc=_dt("2026-08-01T00:00:00"),
            passengers=[_pax(fare=500, tax=55)],
            segments=[_seg("s1", "AST", "BRK", "2026-09-18T12:00:00", "domestic", 500)],
            extras=[Extra(kind=ExtraKind.SEAT, amount_usd=30, passenger_id="p1", segment_ids=["s1"])],
        )
    ]
)

SEED_BHA_BASIC = seed(
    [
        Booking(
            pnr="BHABSC",
            airline=AirlineCode.BHA,
            fare_type=FareType.ECONOMY_BASIC,
            issued_at_utc=_dt("2026-08-01T00:00:00"),
            passengers=[_pax()],
            segments=[_seg("s1", "AST", "BRK", "2026-09-18T12:00:00", "domestic")],
        )
    ]
)

SEED_BHA_STANDARD_OLD = seed(
    [
        Booking(
            pnr="BHAOLD",
            airline=AirlineCode.BHA,
            fare_type=FareType.ECONOMY_STANDARD,
            issued_at_utc=_dt("2026-06-15T00:00:00"),
            passengers=[_pax()],
            segments=[_seg("s1", "AST", "BRK", "2026-09-18T12:00:00", "domestic", 150)],
        )
    ]
)

SEED_BHA_STANDARD_NEW = seed(
    [
        Booking(
            pnr="BHANEW",
            airline=AirlineCode.BHA,
            fare_type=FareType.ECONOMY_STANDARD,
            issued_at_utc=_dt("2026-07-01T00:00:00"),
            passengers=[_pax()],
            segments=[_seg("s1", "AST", "BRK", "2026-09-18T12:00:00", "domestic", 150)],
        )
    ]
)

SEED_BHA_STANDARD_LATE = seed(
    [
        Booking(
            pnr="BHALTE",
            airline=AirlineCode.BHA,
            fare_type=FareType.ECONOMY_STANDARD,
            issued_at_utc=_dt("2026-08-01T00:00:00"),
            passengers=[_pax()],
            segments=[_seg("s1", "AST", "BRK", "2026-09-16T20:00:00", "domestic", 150)],
        )
    ]
)

SEED_STA_BASIC_BAGS = seed(
    [
        Booking(
            pnr="STABAG",
            airline=AirlineCode.STA,
            fare_type=FareType.ECONOMY_BASIC,
            issued_at_utc=_dt("2026-08-01T00:00:00"),
            passengers=[_pax()],
            segments=[
                _seg("s1", "AST", "BRK", "2026-09-20T12:00:00", "domestic", 90),
                _seg("s2", "BRK", "ZUR", "2026-09-21T12:00:00", "international", 180),
            ],
        )
    ]
)

SEED_MULTI = seed(
    [
        Booking(
            pnr="MULTI1",
            airline=AirlineCode.NSA,
            fare_type=FareType.ECONOMY_FLEX,
            issued_at_utc=_dt("2026-08-01T00:00:00"),
            passengers=[
                _pax("p1", "Ada", "Ng", 300, 30),
                _pax("p2", "Ben", "Ng", 300, 30),
            ],
            segments=[_seg("s1", "AST", "BRK", "2026-09-18T12:00:00", "domestic", 300)],
        )
    ]
)

SEED_PARTIAL = seed(
    [
        Booking(
            pnr="PARTLY",
            airline=AirlineCode.NSA,
            fare_type=FareType.ECONOMY_FLEX,
            issued_at_utc=_dt("2026-07-01T00:00:00"),
            passengers=[_pax()],
            segments=[
                _seg("s1", "AST", "BRK", "2026-09-10T12:00:00", "domestic", 200, SegmentStatus.FLOWN),
                _seg("s2", "BRK", "ZUR", "2026-09-18T12:00:00", "international", 200),
            ],
        )
    ]
)

SEED_NOSHOW = seed(
    [
        Booking(
            pnr="NOSHOW",
            airline=AirlineCode.NSA,
            fare_type=FareType.ECONOMY_FLEX,
            issued_at_utc=_dt("2026-08-01T00:00:00"),
            passengers=[_pax(fare=400, tax=40)],
            segments=[_seg("s1", "AST", "BRK", "2026-09-16T10:00:00", "domestic", 400)],
        )
    ]
)

SEED_STA_INTL_CANCEL = seed(
    [
        Booking(
            pnr="STAINL",
            airline=AirlineCode.STA,
            fare_type=FareType.ECONOMY_STANDARD,
            issued_at_utc=_dt("2026-08-01T00:00:00"),
            passengers=[_pax(fare=400, tax=50)],
            segments=[
                _seg("s1", "AST", "BRK", "2026-09-18T12:00:00", "domestic", 150),
                _seg("s2", "BRK", "ZUR", "2026-09-18T18:00:00", "international", 250),
            ],
        )
    ]
)

SEED_BHA_CANCEL = seed(
    [
        Booking(
            pnr="BHACAN",
            airline=AirlineCode.BHA,
            fare_type=FareType.ECONOMY_STANDARD,
            issued_at_utc=_dt("2026-08-01T00:00:00"),
            passengers=[_pax(fare=180, tax=35)],
            segments=[_seg("s1", "AST", "BRK", "2026-09-18T12:00:00", "domestic", 180)],
        )
    ]
)

SEED_BHA_DISRUPT_120 = seed(
    [
        Booking(
            pnr="BHA120",
            airline=AirlineCode.BHA,
            fare_type=FareType.ECONOMY_BASIC,
            issued_at_utc=_dt("2026-08-01T00:00:00"),
            passengers=[_pax(fare=90, tax=20)],
            segments=[_seg("s1", "AST", "BRK", "2026-09-18T12:00:00", "domestic", 90)],
            disruption=DisruptionNotice(
                segment_id="s1",
                notice_at_utc=_dt("2026-09-16T08:00:00"),
                original_departure_utc=_dt("2026-09-18T12:00:00"),
                revised_departure_utc=_dt("2026-09-18T14:00:00"),
                cancelled_by_airline=False,
            ),
        )
    ]
)

SEED_BHA_DISRUPT_180 = seed(
    [
        Booking(
            pnr="BHA180",
            airline=AirlineCode.BHA,
            fare_type=FareType.ECONOMY_BASIC,
            issued_at_utc=_dt("2026-08-01T00:00:00"),
            passengers=[_pax(fare=90, tax=20)],
            segments=[_seg("s1", "AST", "BRK", "2026-09-18T12:00:00", "domestic", 90)],
            disruption=DisruptionNotice(
                segment_id="s1",
                notice_at_utc=_dt("2026-09-16T08:00:00"),
                original_departure_utc=_dt("2026-09-18T12:00:00"),
                revised_departure_utc=_dt("2026-09-18T15:00:00"),
                cancelled_by_airline=False,
            ),
        )
    ]
)

SEED_EMPTY = seed([])

SEEDS = {
    "change_sta_standard_mixed": SEED_STA_STANDARD_MIXED,
    "change_nsa_flex_free": SEED_NSA_FLEX,
    "change_bha_basic_denied": SEED_BHA_BASIC,
    "change_bha_standard_old": SEED_BHA_STANDARD_OLD,
    "change_bha_standard_new": SEED_BHA_STANDARD_NEW,
    "change_bha_standard_late": SEED_BHA_STANDARD_LATE,
    "cancel_nsa_flex": SEED_NSA_FLEX,
    "cancel_sta_standard_intl": SEED_STA_INTL_CANCEL,
    "cancel_bha_standard": SEED_BHA_CANCEL,
    "lookup_ok": SEED_STA_STANDARD_MIXED,
    "lookup_missing": SEED_STA_STANDARD_MIXED,
    "lookup_surname_only": SEED_STA_STANDARD_MIXED,
    "identity_other_adult": SEED_MULTI,
    "handoff_partial": SEED_PARTIAL,
    "handoff_one_segment": SEED_STA_STANDARD_MIXED,
    "noshow_flex": SEED_NOSHOW,
    "policy_qa_sta_baggage": SEED_STA_BASIC_BAGS,
    "policy_qa_unknown": SEED_EMPTY,
    "policy_qa_pets": SEED_EMPTY,
    "disruption_bha_120": SEED_BHA_DISRUPT_120,
    "disruption_bha_180": SEED_BHA_DISRUPT_180,
}

CASE_CATALOG = [
    {
        "id": "policy_qa_sta_baggage",
        "function": "policy_qa",
        "title": "STA Basic baggage domestic vs international",
        "expected": "Domestic: no checked bag. International: 1 x 20 kg. Cabin 7 kg. Cite Suntrail only.",
        "starterMessage": "I am Ada Ng on STABAG, Economy Basic. What checked bags can I bring on the domestic segment versus the international one?",
        "starterMessageZh": "我是 Ada Ng，订票号 STABAG，经济舱基础票。国内段和国际段分别能托运几件行李？",
    },
    {
        "id": "policy_qa_unknown",
        "function": "policy_qa",
        "title": "Unknown airline must not merge rules",
        "expected": "Assistant says it depends on the airline; does not quote a single fee as universal.",
        "starterMessage": "How much does it cost to change an Economy Basic ticket?",
        "starterMessageZh": "改签经济舱基础票要多少钱？",
    },
    {
        "id": "policy_qa_pets",
        "function": "policy_qa",
        "title": "Pets are not in the policy pack",
        "expected": "Hand off. Do not invent a pet fee.",
        "starterMessage": "Can I bring my dog in the cabin?",
        "starterMessageZh": "我能把狗带进客舱吗？",
    },
    {
        "id": "lookup_ok",
        "function": "lookup",
        "title": "Verified lookup",
        "expected": "Returns STA85X Suntrail Economy Standard with two segments.",
        "starterMessage": "Please look up booking STA85X for Ada Ng.",
        "starterMessageZh": "请查询 Ada Ng 的订票 STA85X。",
    },
    {
        "id": "lookup_missing",
        "function": "lookup",
        "title": "Unknown PNR",
        "expected": "not_found. No invented itinerary.",
        "starterMessage": "Look up booking ZZZZZZ for Ada Ng.",
        "starterMessageZh": "请查询 Ada Ng 的订票 ZZZZZZ。",
    },
    {
        "id": "lookup_surname_only",
        "function": "lookup",
        "title": "PNR + surname is not enough",
        "expected": "identity_insufficient.",
        "starterMessage": "Look up STA85X, last name Ng.",
        "starterMessageZh": "查询 STA85X，姓 Ng。",
    },
    {
        "id": "change_sta_standard_mixed",
        "function": "change",
        "title": "STA Standard mixed-route change = USD 85",
        "expected": "Quote change_fee_usd=85. Booking unchanged until confirm.",
        "starterMessage": "Hi I am Ada Ng, PNR STA85X. Please change both flights one day later.",
        "starterMessageZh": "你好，我是 Ada Ng，PNR STA85X。请把两段航班都改到晚一天。",
    },
    {
        "id": "change_nsa_flex_free",
        "function": "change",
        "title": "NSA Flex early change fee 0",
        "expected": "change_fee_usd=0, still ask to confirm.",
        "starterMessage": "I am Ada Ng, PNR NSAFLX. Change my flight one day later.",
        "starterMessageZh": "我是 Ada Ng，PNR NSAFLX。请把航班改到晚一天。",
    },
    {
        "id": "change_bha_basic_denied",
        "function": "change",
        "title": "BHA Basic cannot change",
        "expected": "not_permitted. Booking stays scheduled.",
        "starterMessage": "I am Ada Ng, PNR BHABSC. I want to change my flight one day later.",
        "starterMessageZh": "我是 Ada Ng，PNR BHABSC。我想把航班改到晚一天。",
    },
    {
        "id": "change_bha_standard_old",
        "function": "change",
        "title": "BHA Standard issued before cutover = USD 85",
        "expected": "change_fee_usd=85 because issued 2026-06-15.",
        "starterMessage": "I am Ada Ng, PNR BHAOLD. Change the flight one day later.",
        "starterMessageZh": "我是 Ada Ng，PNR BHAOLD。请把航班改到晚一天。",
    },
    {
        "id": "change_bha_standard_new",
        "function": "change",
        "title": "BHA Standard issued on cutover = USD 55",
        "expected": "change_fee_usd=55 because issued 2026-07-01.",
        "starterMessage": "I am Ada Ng, PNR BHANEW. Change the flight one day later.",
        "starterMessageZh": "我是 Ada Ng，PNR BHANEW。请把航班改到晚一天。",
    },
    {
        "id": "change_bha_standard_late",
        "function": "change",
        "title": "BHA Standard late window forbidden",
        "expected": "not_permitted.",
        "starterMessage": "I am Ada Ng, PNR BHALTE. Change my flight one day later.",
        "starterMessageZh": "我是 Ada Ng，PNR BHALTE。请把航班改到晚一天。",
    },
    {
        "id": "cancel_nsa_flex",
        "function": "cancel",
        "title": "NSA Flex voluntary cancel original payment",
        "expected": "refund_type=original_payment, fare 500, extras not refundable, tax 55.",
        "starterMessage": "I am Ada Ng, PNR NSAFLX. Please cancel and refund my ticket.",
        "starterMessageZh": "我是 Ada Ng，PNR NSAFLX。请取消机票并退款。",
    },
    {
        "id": "cancel_sta_standard_intl",
        "function": "cancel",
        "title": "STA Standard international itinerary: no fare refund",
        "expected": "refund_type=none, tax_refund_usd=50.",
        "starterMessage": "I am Ada Ng, PNR STAINL. Cancel the whole ticket.",
        "starterMessageZh": "我是 Ada Ng，PNR STAINL。请取消整张机票。",
    },
    {
        "id": "cancel_bha_standard",
        "function": "cancel",
        "title": "BHA Standard: fare none, tax refundable",
        "expected": "refund_type=none, tax_refund_usd=35.",
        "starterMessage": "I am Ada Ng, PNR BHACAN. I want to cancel.",
        "starterMessageZh": "我是 Ada Ng，PNR BHACAN。我要取消。",
    },
    {
        "id": "identity_other_adult",
        "function": "identity",
        "title": "Cannot cancel the other adult",
        "expected": "Ada cannot act on Ben's ticket.",
        "starterMessage": "I am Ada Ng, PNR MULTI1. Cancel Ben Ng's ticket.",
        "starterMessageZh": "我是 Ada Ng，PNR MULTI1。取消 Ben Ng 的机票。",
    },
    {
        "id": "handoff_partial",
        "function": "handoff",
        "title": "Partly flown refund -> desk",
        "expected": "handoff_required. Do not apply unused-ticket table.",
        "starterMessage": "I am Ada Ng, PNR PARTLY. Refund the rest of my trip.",
        "starterMessageZh": "我是 Ada Ng，PNR PARTLY。请退剩余行程。",
    },
    {
        "id": "handoff_one_segment",
        "function": "handoff",
        "title": "Selected-segment cancel -> desk",
        "expected": "If the assistant tries one-segment cancel, mock returns handoff. Otherwise it should still refuse to invent a partial refund.",
        "starterMessage": "I am Ada Ng, PNR STA85X. Cancel just the first flight and keep the second.",
        "starterMessageZh": "我是 Ada Ng，PNR STA85X。只取消第一段，第二段保留。",
    },
    {
        "id": "noshow_flex",
        "function": "noshow",
        "title": "Flex no-show: no fare refund, tax yes",
        "expected": "noshow, fare 0, tax 40.",
        "starterMessage": "I am Ada Ng, PNR NOSHOW. Please cancel and refund.",
        "starterMessageZh": "我是 Ada Ng，PNR NOSHOW。请取消并退款。",
    },
    {
        "id": "disruption_bha_120",
        "function": "disruption",
        "title": "BHA 120-minute change does not qualify",
        "expected": "Voluntary table still applies; 120 < 180.",
        "starterMessage": "I am Ada Ng, PNR BHA120. The flight moved by two hours. Do I get a free refund?",
        "starterMessageZh": "我是 Ada Ng，PNR BHA120。航班变动了两个小时。能免费退款吗？",
    },
    {
        "id": "disruption_bha_180",
        "function": "disruption",
        "title": "BHA 180-minute change qualifies",
        "expected": "Disruption refund of fare+tax+extras with no fee, including Basic.",
        "starterMessage": "I am Ada Ng, PNR BHA180. The flight moved by three hours. I want a refund.",
        "starterMessageZh": "我是 Ada Ng，PNR BHA180。航班变动了三个小时，我要退款。",
    },
]


from backend.api.schemas import AirlineCode, FareType, RouteType, TimeWindow

NOT_PERMITTED = None
BHA_FEE_CUTOVER = "2026-07-01T00:00:00+00:00"

CHANGE_FEES = {
    AirlineCode.STA: {
        FareType.ECONOMY_BASIC: {
            TimeWindow.EARLY: {RouteType.DOMESTIC: 40.0, RouteType.INTERNATIONAL: NOT_PERMITTED},
            TimeWindow.LATE: {RouteType.DOMESTIC: NOT_PERMITTED, RouteType.INTERNATIONAL: NOT_PERMITTED},
        },
        FareType.ECONOMY_STANDARD: {
            TimeWindow.EARLY: {RouteType.DOMESTIC: 20.0, RouteType.INTERNATIONAL: 65.0},
            TimeWindow.LATE: {RouteType.DOMESTIC: 50.0, RouteType.INTERNATIONAL: 100.0},
        },
        FareType.ECONOMY_FLEX: {
            TimeWindow.EARLY: {RouteType.DOMESTIC: 0.0, RouteType.INTERNATIONAL: 0.0},
            TimeWindow.LATE: {RouteType.DOMESTIC: 0.0, RouteType.INTERNATIONAL: 25.0},
        },
    },
    AirlineCode.NSA: {
        FareType.ECONOMY_BASIC: {
            TimeWindow.EARLY: 70.0,
            TimeWindow.LATE: NOT_PERMITTED,
        },
        FareType.ECONOMY_STANDARD: {
            TimeWindow.EARLY: 25.0,
            TimeWindow.LATE: 60.0,
        },
        FareType.ECONOMY_FLEX: {
            TimeWindow.EARLY: 0.0,
            TimeWindow.LATE: 0.0,
        },
    },
    AirlineCode.BHA: {
        FareType.ECONOMY_BASIC: {
            TimeWindow.EARLY: NOT_PERMITTED,
            TimeWindow.LATE: NOT_PERMITTED,
        },
        FareType.ECONOMY_STANDARD: {
            TimeWindow.EARLY: "issuance",
            TimeWindow.LATE: NOT_PERMITTED,
        },
        FareType.ECONOMY_FLEX: {
            TimeWindow.EARLY: 15.0,
            TimeWindow.LATE: 45.0,
        },
    },
}

# Cancellation: fare outcome per passenger per wholly unused itinerary.
# refund_type, fee_usd (subtracted from fare; floor 0)
CANCEL_RULES = {
    AirlineCode.STA: {
        FareType.ECONOMY_BASIC: {
            TimeWindow.EARLY: {RouteType.DOMESTIC: ("none", 0.0), RouteType.INTERNATIONAL: ("none", 0.0)},
            TimeWindow.LATE: {RouteType.DOMESTIC: ("none", 0.0), RouteType.INTERNATIONAL: ("none", 0.0)},
        },
        FareType.ECONOMY_STANDARD: {
            TimeWindow.EARLY: {RouteType.DOMESTIC: ("travel_credit", 25.0), RouteType.INTERNATIONAL: ("none", 0.0)},
            TimeWindow.LATE: {RouteType.DOMESTIC: ("none", 0.0), RouteType.INTERNATIONAL: ("none", 0.0)},
        },
        FareType.ECONOMY_FLEX: {
            TimeWindow.EARLY: {RouteType.DOMESTIC: ("original_payment", 0.0), RouteType.INTERNATIONAL: ("original_payment", 50.0)},
            TimeWindow.LATE: {RouteType.DOMESTIC: ("original_payment", 20.0), RouteType.INTERNATIONAL: ("travel_credit", 75.0)},
        },
    },
    AirlineCode.NSA: {
        FareType.ECONOMY_BASIC: {
            TimeWindow.EARLY: ("none", 0.0),
            TimeWindow.LATE: ("none", 0.0),
        },
        FareType.ECONOMY_STANDARD: {
            TimeWindow.EARLY: ("travel_credit", 40.0),
            TimeWindow.LATE: ("travel_credit", 80.0),
        },
        FareType.ECONOMY_FLEX: {
            TimeWindow.EARLY: ("original_payment", 0.0),
            TimeWindow.LATE: ("original_payment", 0.0),
        },
    },
    AirlineCode.BHA: {
        FareType.ECONOMY_BASIC: {
            TimeWindow.EARLY: ("none", 0.0),
            TimeWindow.LATE: ("none", 0.0),
        },
        FareType.ECONOMY_STANDARD: {
            TimeWindow.EARLY: ("none", 0.0),
            TimeWindow.LATE: ("none", 0.0),
        },
        FareType.ECONOMY_FLEX: {
            TimeWindow.EARLY: ("travel_credit", 30.0),
            TimeWindow.LATE: ("none", 0.0),
        },
    },
}

BAGGAGE = {
    AirlineCode.STA: {
        FareType.ECONOMY_BASIC: {
            "cabin": {"count": 1, "kg": 7},
            "checked": {
                RouteType.DOMESTIC: {"count": 0, "kg": 0},
                RouteType.INTERNATIONAL: {"count": 1, "kg": 20},
            },
        },
        FareType.ECONOMY_STANDARD: {
            "cabin": {"count": 1, "kg": 10},
            "checked": {
                RouteType.DOMESTIC: {"count": 1, "kg": 20},
                RouteType.INTERNATIONAL: {"count": 1, "kg": 23},
            },
        },
        FareType.ECONOMY_FLEX: {
            "cabin": {"count": 1, "kg": 12},
            "checked": {
                RouteType.DOMESTIC: {"count": 2, "kg": 20},
                RouteType.INTERNATIONAL: {"count": 2, "kg": 23},
            },
        },
        "extra_checked_usd": 50.0,
        "extra_checked_kg": 23,
        "buy_cabin_bag": False,
    },
    AirlineCode.NSA: {
        FareType.ECONOMY_BASIC: {
            "cabin": {"count": 1, "kg": 8},
            "checked": {"count": 1, "kg": 23},
        },
        FareType.ECONOMY_STANDARD: {
            "cabin": {"count": 1, "kg": 8},
            "checked": {"count": 1, "kg": 23},
        },
        FareType.ECONOMY_FLEX: {
            "cabin": {"count": 1, "kg": 12},
            "checked": {"count": 2, "kg": 23},
        },
        "extra_checked_usd": 45.0,
        "extra_checked_kg": 23,
        "buy_cabin_bag": False,
    },
    AirlineCode.BHA: {
        FareType.ECONOMY_BASIC: {
            "cabin": {"count": 0, "kg": 0},
            "checked": {"count": 0, "kg": 0},
        },
        FareType.ECONOMY_STANDARD: {
            "cabin": {"count": 1, "kg": 7},
            "checked": {"count": 0, "kg": 0},
        },
        FareType.ECONOMY_FLEX: {
            "cabin": {"count": 1, "kg": 10},
            "checked": {"count": 1, "kg": 20},
        },
        "extra_checked_usd": 40.0,
        "extra_checked_kg": 20,
        "buy_cabin_bag": True,
        "buy_cabin_usd": 25.0,
        "buy_cabin_kg": 7,
    },
}

PERSONAL_ITEM = {"cm": (40, 30, 15), "kg": 3}
CABIN_BAG_CM = (55, 35, 25)
CHECKED_LINEAR_CM = 158

DISRUPTION_MINUTES = {
    AirlineCode.STA: 120,
    AirlineCode.NSA: 120,
    AirlineCode.BHA: 180,
}

CREDIT_DAYS = 365

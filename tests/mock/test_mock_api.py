from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from backend.app import app


client = TestClient(app)
SID = "mock-test"


def utc(s: str) -> str:
    return datetime.fromisoformat(s).replace(tzinfo=timezone.utc).isoformat()


def segment(sid, origin, dest, dep, route, fare=200.0, status="scheduled"):
    departure = datetime.fromisoformat(dep).replace(tzinfo=timezone.utc)
    arrival = departure + timedelta(hours=3)
    return {
        "id": sid,
        "origin": origin,
        "destination": dest,
        "departure_utc": departure.isoformat(),
        "arrival_utc": arrival.isoformat(),
        "route_type": route,
        "fare_usd": fare,
        "status": status,
    }


def passenger(pid="p1", first="Ada", last="Ng", fare=400, tax=40, minor=False):
    return {
        "id": pid,
        "first_name": first,
        "last_name": last,
        "is_minor": minor,
        "ticket_fare_usd": fare,
        "government_tax_usd": tax,
    }


def sta_standard_mixed():
    return {
        "pnr": "STA85X",
        "airline": "STA",
        "fare_type": "economy_standard",
        "issued_at_utc": utc("2026-08-01T00:00:00"),
        "passengers": [passenger()],
        "segments": [
            segment("s1", "AST", "BRK", "2026-09-18T12:00:00", "domestic", 180),
            segment("s2", "BRK", "ZUR", "2026-09-18T18:00:00", "international", 220),
        ],
        "extras": [],
    }


def nsa_flex():
    return {
        "pnr": "NSAFLX",
        "airline": "NSA",
        "fare_type": "economy_flex",
        "issued_at_utc": utc("2026-08-01T00:00:00"),
        "passengers": [passenger(fare=500, tax=55)],
        "segments": [segment("s1", "AST", "BRK", "2026-09-18T12:00:00", "domestic", 500)],
        "extras": [{"kind": "seat", "amount_usd": 30, "passenger_id": "p1", "segment_ids": ["s1"]}],
    }


def bha_basic():
    return {
        "pnr": "BHABSC",
        "airline": "BHA",
        "fare_type": "economy_basic",
        "issued_at_utc": utc("2026-08-01T00:00:00"),
        "passengers": [passenger()],
        "segments": [segment("s1", "AST", "BRK", "2026-09-18T12:00:00", "domestic")],
    }


def multi_pax():
    return {
        "pnr": "MULTI1",
        "airline": "NSA",
        "fare_type": "economy_flex",
        "issued_at_utc": utc("2026-08-01T00:00:00"),
        "passengers": [
            passenger("p1", "Ada", "Ng", 300, 30),
            passenger("p2", "Ben", "Ng", 300, 30),
        ],
        "segments": [segment("s1", "AST", "BRK", "2026-09-18T12:00:00", "domestic", 300)],
    }


def load(bookings, now="2026-09-16T12:00:00"):
    return client.post(
        f"/api/mock/sessions/{SID}/load",
        json={"now_utc": utc(now), "bookings": bookings},
    )


@pytest.fixture(autouse=True)
def _reset():
    client.post(f"/api/mock/sessions/{SID}/reset")
    yield
    client.post(f"/api/mock/sessions/{SID}/reset")


def test_load_and_list():
    r = load([sta_standard_mixed()])
    assert r.status_code == 200
    listed = client.get(f"/api/mock/sessions/{SID}/bookings")
    assert len(listed.json()["bookings"]) == 1
    assert listed.json()["bookings"][0]["pnr"] == "STA85X"


def test_lookup_requires_first_and_last():
    load([sta_standard_mixed()])
    only_last = client.post(f"/api/mock/sessions/{SID}/lookup", json={"pnr": "STA85X", "last_name": "Ng"})
    assert only_last.json()["reason_code"] == "identity_insufficient"
    missing = client.post(
        f"/api/mock/sessions/{SID}/lookup",
        json={"pnr": "NOPE", "last_name": "Ng", "first_name": "Ada"},
    )
    assert missing.json()["reason_code"] == "not_found"
    ok = client.post(
        f"/api/mock/sessions/{SID}/lookup",
        json={"pnr": "STA85X", "last_name": "Ng", "first_name": "Ada"},
    )
    assert ok.json()["ok"] is True
    assert ok.json()["verified_passenger_id"] == "p1"


def test_cannot_act_as_other_adult():
    load([multi_pax()])
    r = client.post(
        f"/api/mock/sessions/{SID}/quote-cancel",
        json={"pnr": "MULTI1", "passenger_id": "p2", "first_name": "Ada", "last_name": "Ng"},
    )
    assert r.json()["reason_code"] == "not_authorized"
    r2 = client.post(
        f"/api/mock/sessions/{SID}/quote-cancel",
        json={"pnr": "MULTI1", "passenger_id": "p2", "first_name": "Ben", "last_name": "Ng"},
    )
    assert r2.json()["ok"] is True


def test_quote_change_does_not_mutate():
    load([sta_standard_mixed()])
    body = {
        "pnr": "STA85X",
        "passenger_id": "p1",
        "first_name": "Ada",
        "last_name": "Ng",
        "changes": [
            {
                "segment_id": "s1",
                "new_departure_utc": utc("2026-09-19T12:00:00"),
                "new_fare_usd": 180,
            },
            {
                "segment_id": "s2",
                "new_departure_utc": utc("2026-09-19T18:00:00"),
                "new_fare_usd": 250,
            },
        ],
    }
    quoted = client.post(f"/api/mock/sessions/{SID}/quote-change", json=body).json()
    assert quoted["ok"] is True
    assert quoted["change_fee_usd"] == 85
    assert quoted["fare_difference_usd"] == 30
    assert quoted["quote_id"]
    before = client.get(f"/api/mock/sessions/{SID}/bookings").json()["bookings"][0]
    assert before["segments"][0]["status"] == "scheduled"


def test_confirm_change_mutates():
    load([sta_standard_mixed()])
    body = {
        "pnr": "STA85X",
        "passenger_id": "p1",
        "first_name": "Ada",
        "last_name": "Ng",
        "changes": [
            {"segment_id": "s1", "new_departure_utc": utc("2026-09-19T12:00:00"), "new_fare_usd": 180},
            {"segment_id": "s2", "new_departure_utc": utc("2026-09-19T18:00:00"), "new_fare_usd": 220},
        ],
    }
    quoted = client.post(f"/api/mock/sessions/{SID}/quote-change", json=body).json()
    confirmed = client.post(
        f"/api/mock/sessions/{SID}/confirm",
        json={
            "quote_id": quoted["quote_id"],
            "passenger_id": "p1",
            "first_name": "Ada",
            "last_name": "Ng",
        },
    ).json()
    assert confirmed["ok"] is True
    booking = confirmed["booking"]
    assert booking["status"] == "changed"
    assert booking["segments"][0]["departure_utc"].startswith("2026-09-19")
    reused = client.post(
        f"/api/mock/sessions/{SID}/confirm",
        json={
            "quote_id": quoted["quote_id"],
            "passenger_id": "p1",
            "first_name": "Ada",
            "last_name": "Ng",
        },
    ).json()
    assert reused["reason_code"] == "quote_not_found"


def test_bha_basic_change_rejected():
    load([bha_basic()])
    r = client.post(
        f"/api/mock/sessions/{SID}/quote-change",
        json={
            "pnr": "BHABSC",
            "passenger_id": "p1",
            "first_name": "Ada",
            "last_name": "Ng",
            "changes": [{"segment_id": "s1", "new_departure_utc": utc("2026-09-19T12:00:00")}],
        },
    ).json()
    assert r["ok"] is False and r["reason_code"] == "not_permitted"


def test_cancel_flex_and_clock_late_window():
    load([nsa_flex()], now="2026-09-16T12:00:00")
    early = client.post(
        f"/api/mock/sessions/{SID}/quote-cancel",
        json={"pnr": "NSAFLX", "passenger_id": "p1", "first_name": "Ada", "last_name": "Ng"},
    ).json()
    assert early["ok"] is True
    assert early["refund_type"] == "original_payment"
    assert early["fare_refund_usd"] == 500
    assert early["extras_refundable"] is False
    client.put(f"/api/mock/sessions/{SID}/clock", json={"now_utc": utc("2026-09-18T12:00:00")})
    noshow = client.post(
        f"/api/mock/sessions/{SID}/quote-cancel",
        json={"pnr": "NSAFLX", "passenger_id": "p1", "first_name": "Ada", "last_name": "Ng"},
    ).json()
    assert noshow["reason_code"] == "noshow"
    assert noshow["tax_refund_usd"] == 55


def test_confirm_cancel_removes_passenger():
    load([multi_pax()])
    quoted = client.post(
        f"/api/mock/sessions/{SID}/quote-cancel",
        json={"pnr": "MULTI1", "passenger_id": "p1", "first_name": "Ada", "last_name": "Ng"},
    ).json()
    confirmed = client.post(
        f"/api/mock/sessions/{SID}/confirm",
        json={
            "quote_id": quoted["quote_id"],
            "passenger_id": "p1",
            "first_name": "Ada",
            "last_name": "Ng",
        },
    ).json()
    names = [p["first_name"] for p in confirmed["booking"]["passengers"]]
    assert names == ["Ben"]
    assert confirmed["booking"]["status"] != "cancelled"


def test_sessions_are_isolated():
    load([bha_basic()])
    other = client.get("/api/mock/sessions/other-session/bookings").json()
    assert other["bookings"] == []

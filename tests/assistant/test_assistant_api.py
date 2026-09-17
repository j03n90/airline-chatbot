import pytest
from fastapi.testclient import TestClient

from backend.app import app
from backend.mock.seeds import CASE_CATALOG


client = TestClient(app)
_CATALOG_BY_ID = {c["id"]: c for c in CASE_CATALOG}
CONFIRM = {"en": "Yes, confirm.", "zh": "是的，确认。"}
UNKNOWN_AIRLINE_HINTS = ("suntrail", "depends", "airline", "航司", "航空公司", "取决于")


def starter(case_id: str, lang: str) -> str:
    case = _CATALOG_BY_ID[case_id]
    return case["starterMessageZh"] if lang == "zh" else case["starterMessage"]


def chat(session_id: str, message: str) -> dict:
    r = client.post(
        "/api/assistant/chat",
        json={"session_id": session_id, "message": message},
        headers={"Accept": "application/json"},
    )
    assert r.status_code == 200, r.text
    return r.json()


def start_case(case_id: str, lang: str = "en") -> tuple[str, str]:
    mock_id = f"eval-{case_id}-{lang}"
    loaded = client.post(f"/api/mock/sessions/{mock_id}/load-preset", params={"preset_id": case_id})
    assert loaded.status_code == 200, loaded.text
    created = client.post("/api/assistant/sessions", json={"mock_session_id": mock_id})
    assert created.status_code == 200
    return mock_id, created.json()["session_id"]


def test_presets_cover_catalog():
    r = client.get("/api/mock/presets")
    ids = {c["id"] for c in r.json()["cases"]}
    assert ids == {c["id"] for c in CASE_CATALOG}
    assert len(ids) >= 10
    assert all(c.get("starterMessageZh") for c in CASE_CATALOG)


@pytest.mark.parametrize("lang", ["en", "zh"])
def test_change_sta_quote_then_confirm(lang):
    mock_id, sid = start_case("change_sta_standard_mixed", lang)
    first = chat(sid, starter("change_sta_standard_mixed", lang))
    session = client.get(f"/api/assistant/sessions/{sid}").json()
    quote = session["pending_quote"]
    assert quote, first
    assert quote["ok"] is True
    assert quote["change_fee_usd"] == 85
    before = client.get(f"/api/mock/sessions/{mock_id}/bookings").json()["bookings"][0]
    assert before["segments"][0]["status"] == "scheduled"
    chat(sid, CONFIRM[lang])
    after = client.get(f"/api/mock/sessions/{mock_id}/bookings").json()["bookings"][0]
    assert after["status"] == "changed"


@pytest.mark.parametrize("lang", ["en", "zh"])
def test_bha_basic_change_denied_no_mutation(lang):
    mock_id, sid = start_case("change_bha_basic_denied", lang)
    chat(sid, starter("change_bha_basic_denied", lang))
    session = client.get(f"/api/assistant/sessions/{sid}").json()
    assert session["pending_quote"] is None
    booking = client.get(f"/api/mock/sessions/{mock_id}/bookings").json()["bookings"][0]
    assert booking["segments"][0]["status"] == "scheduled"


@pytest.mark.parametrize("lang", ["en", "zh"])
def test_unknown_airline_policy_does_not_pick_one_carrier(lang):
    _, sid = start_case("policy_qa_unknown", lang)
    reply = chat(sid, starter("policy_qa_unknown", lang))["text"].lower()
    assert any(hint in reply for hint in UNKNOWN_AIRLINE_HINTS)
    trace = client.get(f"/api/assistant/sessions/{sid}/trace").json()
    airlines = {s["airline"] for s in trace["retrieval"]}
    assert len(airlines) >= 2


@pytest.mark.parametrize("lang", ["en", "zh"])
def test_lookup_surname_insufficient(lang):
    _, sid = start_case("lookup_surname_only", lang)
    reply = chat(sid, starter("lookup_surname_only", lang))["text"].lower()
    assert "first" in reply or "not enough" in reply or "surname" in reply


@pytest.mark.parametrize("lang", ["en", "zh"])
def test_partial_refund_handoff(lang):
    _, sid = start_case("handoff_partial", lang)
    chat(sid, starter("handoff_partial", lang))
    session = client.get(f"/api/assistant/sessions/{sid}").json()
    assert session["handoff"] is True


@pytest.mark.parametrize("lang", ["en", "zh"])
def test_noshow_tax_only(lang):
    _, sid = start_case("noshow_flex", lang)
    chat(sid, starter("noshow_flex", lang))
    session = client.get(f"/api/assistant/sessions/{sid}").json()
    assert session["pending_quote"] is None
    trace = client.get(f"/api/assistant/sessions/{sid}/trace").json()
    cancel_calls = [c for c in trace["mock_calls"] if c["step"] == "quote_cancel"]
    assert cancel_calls
    assert cancel_calls[0]["detail"]["reason_code"] == "noshow"


@pytest.mark.parametrize("lang", ["en", "zh"])
def test_identity_other_adult(lang):
    _, sid = start_case("identity_other_adult", lang)
    chat(sid, starter("identity_other_adult", lang))
    trace = client.get(f"/api/assistant/sessions/{sid}/trace").json()
    cancel_calls = [c for c in trace["mock_calls"] if c["step"] == "quote_cancel"]
    assert cancel_calls
    assert cancel_calls[0]["detail"]["reason_code"] == "not_authorized"


@pytest.mark.parametrize("lang", ["en", "zh"])
def test_bha_issuance_fees(lang):
    _, old_sid = start_case("change_bha_standard_old", lang)
    chat(old_sid, starter("change_bha_standard_old", lang))
    old_q = client.get(f"/api/assistant/sessions/{old_sid}").json()["pending_quote"]
    assert old_q and old_q["change_fee_usd"] == 85
    _, new_sid = start_case("change_bha_standard_new", lang)
    chat(new_sid, starter("change_bha_standard_new", lang))
    new_q = client.get(f"/api/assistant/sessions/{new_sid}").json()["pending_quote"]
    assert new_q and new_q["change_fee_usd"] == 55


@pytest.mark.parametrize("lang", ["en", "zh"])
def test_cancel_nsa_flex_quote(lang):
    _, sid = start_case("cancel_nsa_flex", lang)
    chat(sid, starter("cancel_nsa_flex", lang))
    quote = client.get(f"/api/assistant/sessions/{sid}").json()["pending_quote"]
    assert quote["refund_type"] == "original_payment"
    assert quote["fare_refund_usd"] == 500
    assert quote["extras_refundable"] is False
    assert quote["tax_refund_usd"] == 55


@pytest.mark.parametrize("lang", ["en", "zh"])
def test_disruption_thresholds_via_cancel_quote(lang):
    _, sid120 = start_case("disruption_bha_120", lang)
    chat(sid120, starter("disruption_bha_120", lang))
    q120 = client.get(f"/api/assistant/sessions/{sid120}").json()["pending_quote"]
    assert q120 is None or q120["kind"] != "disruption_refund"
    _, sid180 = start_case("disruption_bha_180", lang)
    chat(sid180, starter("disruption_bha_180", lang))
    q180 = client.get(f"/api/assistant/sessions/{sid180}").json()["pending_quote"]
    assert q180 and q180["kind"] == "disruption_refund"
    assert q180["fare_refund_usd"] == 90

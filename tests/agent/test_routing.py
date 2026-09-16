from backend.agent.routing import classify_intent, extract_from_text
from backend.agent.state import AgentState


def test_confirm_when_quote_open():
    state: AgentState = {"pending_quote": {"quote_id": "x"}, "user_text": "Yes, please confirm."}
    assert classify_intent(state) == "confirm"


def test_change_intent_and_pnr():
    state: AgentState = {"user_text": "Hi I am Ada Ng, PNR STA85X. Change both flights one day later."}
    extract_from_text(state["user_text"], state)
    assert state["pnr"] == "STA85X"
    assert state["first_name"] == "Ada"
    assert classify_intent(state) == "change"


def test_fee_question_without_pnr_is_policy():
    state: AgentState = {"user_text": "How much does it cost to change an Economy Basic ticket?"}
    extract_from_text(state["user_text"], state)
    assert classify_intent(state) == "policy_qa"


def test_surname_only_extract():
    state: AgentState = {"user_text": "Look up STA85X, last name Ng."}
    extract_from_text(state["user_text"], state)
    assert state["pnr"] == "STA85X"
    assert state.get("first_name") is None
    assert state["last_name"] == "Ng"
    assert classify_intent(state) == "lookup"

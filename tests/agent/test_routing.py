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


def test_zh_confirm_when_quote_open():
    state: AgentState = {"pending_quote": {"quote_id": "x"}, "user_text": "是的，确认。"}
    assert classify_intent(state) == "confirm"


def test_zh_change_intent_and_pnr():
    state: AgentState = {
        "user_text": "你好，我是 Ada Ng，PNR STA85X。请把两段航班都改到晚一天。"
    }
    extract_from_text(state["user_text"], state)
    assert state["pnr"] == "STA85X"
    assert state["first_name"] == "Ada"
    assert state["change_new_departure"] == "plus_one_day"
    assert classify_intent(state) == "change"


def test_zh_fee_question_without_pnr_is_policy():
    state: AgentState = {"user_text": "改签经济舱基础票要多少钱？"}
    extract_from_text(state["user_text"], state)
    assert classify_intent(state) == "policy_qa"


def test_zh_surname_only_extract():
    state: AgentState = {"user_text": "查询 STA85X，姓 Ng。"}
    extract_from_text(state["user_text"], state)
    assert state["pnr"] == "STA85X"
    assert state.get("first_name") is None
    assert state["last_name"] == "Ng"
    assert classify_intent(state) == "lookup"


def test_zh_cancel_refund():
    state: AgentState = {"user_text": "我是 Ada Ng，PNR NSAFLX。请取消机票并退款。"}
    extract_from_text(state["user_text"], state)
    assert state["pnr"] == "NSAFLX"
    assert classify_intent(state) == "cancel"

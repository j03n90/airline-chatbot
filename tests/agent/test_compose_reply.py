from backend.agent.nodes import COMPOSE_FACTS_GUARD, compose_reply


def test_compose_includes_recent_history_and_facts_guard(monkeypatch):
    captured: dict[str, str] = {}

    def fake_complete(system: str, user: str) -> str:
        captured["system"] = system
        captured["user"] = user
        return "A short reply."

    monkeypatch.setattr("backend.agent.nodes.complete", fake_complete)
    state = {
        "user_text": "what about the fee?",
        "messages": [
            {"role": "user", "content": "Can I change STA85X?"},
            {"role": "assistant", "content": "Quote is USD 85."},
            {"role": "user", "content": "what about the fee?"},
        ],
        "intent": "policy_qa",
        "pending_quote": {
            "kind": "change",
            "change_fee_usd": 85,
            "fare_difference_usd": 0,
            "refund_type": "none",
            "fare_refund_usd": 0,
            "tax_refund_usd": 0,
            "extras_refundable": False,
            "message": "Quote ready.",
            "quote_id": "q1",
        },
        "last_retrieval": [],
    }
    result = compose_reply(state)
    assert captured["system"]
    assert COMPOSE_FACTS_GUARD in captured["system"]
    assert "must come only from Facts" in captured["system"]
    assert "Recent conversation:" in captured["user"]
    assert "Can I change STA85X?" in captured["user"]
    assert "Quote is USD 85." in captured["user"]
    assert "what about the fee?" in captured["user"]
    assert "Facts:" in captured["user"]
    assert "change_fee_usd=85" in captured["user"]
    assert result["reply"] == "A short reply."
    assert result["messages"][-1] == {"role": "assistant", "content": "A short reply."}

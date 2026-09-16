import pytest

from backend.agent.nodes import _fallback_reply, retrieve_policy
from backend.agent.state import AgentState
from backend.rag.ingest import build_indexes
from backend.rag.retrieve import load_indexes


@pytest.fixture(scope="module")
def built_index(tmp_path_factory):
    index_dir = tmp_path_factory.mktemp("faiss-agent")
    build_indexes(index_dir)
    load_indexes(index_dir)
    return index_dir


def test_retrieve_policy_excludes_bha_before_effective(built_index):
    state: AgentState = {
        "user_text": "How much does it cost to change an Economy Standard ticket?",
        "now_utc": "2026-05-01T00:00:00+00:00",
        "airline": None,
        "last_tool_trace": [],
    }
    retrieve_policy(state)
    codes = {h["airline_code"] for h in state["last_retrieval"]}
    assert "BHA" not in codes
    assert "STA" in codes
    assert "NSA" in codes
    detail = state["last_tool_trace"][-1]["detail"]
    assert detail["as_of"] == state["now_utc"]
    assert all(s.get("version") for s in detail["sources"])
    assert all(s["airline"] != "BHA" for s in detail["sources"])


def test_fallback_empty_policy_qa_does_not_invent():
    state: AgentState = {
        "intent": "policy_qa",
        "now_utc": "2025-12-01T00:00:00+00:00",
        "last_retrieval": [],
    }
    reply = _fallback_reply(state, [])
    lower = reply.lower()
    assert "not yet effective" in lower
    assert "2025-12-01" in reply

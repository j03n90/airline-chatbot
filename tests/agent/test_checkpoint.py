import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver

from backend.agent.graph import GRAPH, build_graph
from backend.api.assistant import _blank_state, load_session_state, run_turn, thread_config
from backend.app import app

client = TestClient(app)

TURN_OVERLAY = {
    "user_text": "",
    "reply": "",
    "last_retrieval": [],
    "last_tool_trace": [],
}


def _sqlite_graph(path: Path):
    conn = sqlite3.connect(str(path), check_same_thread=False)
    saver = SqliteSaver(conn)
    saver.setup()
    return build_graph(saver), conn


def test_unknown_thread_run_turn_raises():
    with pytest.raises(KeyError):
        run_turn("missing-session", "hello")


def test_unknown_session_chat_returns_404():
    response = client.post(
        "/api/assistant/chat",
        json={"session_id": "missing-session", "message": "hello"},
        headers={"Accept": "application/json"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "unknown_session"


def test_create_session_writes_checkpoint_not_dict():
    created = client.post("/api/assistant/sessions", json={"mock_session_id": "mock-check"})
    assert created.status_code == 200
    session_id = created.json()["session_id"]
    values = GRAPH.get_state(thread_config(session_id)).values
    assert values["session_id"] == session_id
    assert values["mock_session_id"] == "mock-check"
    loaded = load_session_state(session_id)
    assert loaded["session_id"] == session_id
    summary = client.get(f"/api/assistant/sessions/{session_id}")
    assert summary.status_code == 200
    assert summary.json()["mock_session_id"] == "mock-check"


def test_threads_do_not_leak_pnr():
    graph = build_graph(InMemorySaver())
    cfg_a = thread_config("thread-a")
    cfg_b = thread_config("thread-b")
    graph.update_state(cfg_a, _blank_state("thread-a", "mock-a"))
    graph.update_state(cfg_b, _blank_state("thread-b", "mock-b"))
    graph.invoke({**TURN_OVERLAY, "user_text": "Hi I am Ada Ng, PNR STA85X."}, cfg_a)
    graph.invoke({**TURN_OVERLAY, "user_text": "Hi I am Ada Ng, PNR NSAFLX."}, cfg_b)
    assert graph.get_state(cfg_a).values.get("pnr") == "STA85X"
    assert graph.get_state(cfg_b).values.get("pnr") == "NSAFLX"
    assert graph.get_state(cfg_a).values.get("mock_session_id") == "mock-a"
    assert graph.get_state(cfg_b).values.get("mock_session_id") == "mock-b"


def test_threads_do_not_leak_pending_quote():
    graph = build_graph(InMemorySaver())
    cfg_a = thread_config("quote-a")
    cfg_b = thread_config("quote-b")
    state_a = _blank_state("quote-a", "mock-a")
    state_a["pending_quote"] = {"quote_id": "qa", "change_fee_usd": 85}
    graph.update_state(cfg_a, state_a)
    graph.update_state(cfg_b, _blank_state("quote-b", "mock-b"))
    assert graph.get_state(cfg_a).values.get("pending_quote")["quote_id"] == "qa"
    assert graph.get_state(cfg_b).values.get("pending_quote") is None


def test_sqlite_reload_keeps_slots(tmp_path: Path):
    db = tmp_path / "checkpoints.sqlite"
    config = thread_config("thread-reload")
    first, conn1 = _sqlite_graph(db)
    first.update_state(config, _blank_state("thread-reload", "mock-reload"))
    first.invoke({**TURN_OVERLAY, "user_text": "Hi I am Ada Ng, PNR STA85X."}, config)
    assert first.get_state(config).values.get("pnr") == "STA85X"
    conn1.close()

    second, conn2 = _sqlite_graph(db)
    restored = second.get_state(config).values
    assert restored.get("session_id") == "thread-reload"
    assert restored.get("mock_session_id") == "mock-reload"
    assert restored.get("pnr") == "STA85X"
    assert restored.get("first_name") == "Ada"
    assert restored.get("last_name") == "Ng"
    conn2.close()

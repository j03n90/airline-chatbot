from __future__ import annotations

import json
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from starlette.requests import Request

from backend.agent.graph import GRAPH
from backend.agent.state import AgentState
from backend.api.schemas import (
    AssistantSessionSummary,
    ChatRequest,
    CreateAssistantSessionRequest,
    CreateAssistantSessionResponse,
    HealthResponse,
    TraceResponse,
)
from backend.config import settings
from backend.rag.retrieve import indexes_ready

router = APIRouter(prefix="/api/assistant", tags=["assistant"])

_sessions: dict[str, AgentState] = {}
_traces: dict[str, list[dict[str, Any]]] = {}


def _blank_state(session_id: str, mock_session_id: str) -> AgentState:
    return AgentState(
        session_id=session_id,
        mock_session_id=mock_session_id,
        user_text="",
        airline=None,
        pnr=None,
        first_name=None,
        last_name=None,
        verified_passenger_id=None,
        booking=None,
        intent="",
        pending_quote=None,
        last_retrieval=[],
        last_tool_trace=[],
        handoff_reason=None,
        reply="",
        messages=[],
    )


def run_turn(session_id: str, message: str) -> AgentState:
    if session_id not in _sessions:
        raise KeyError(session_id)
    prior = _sessions[session_id]
    state: AgentState = {
        **prior,
        "user_text": message,
        "reply": "",
        "last_retrieval": [],
        "last_tool_trace": [],
    }
    result = GRAPH.invoke(state)
    _sessions[session_id] = result
    history = _traces.setdefault(session_id, [])
    history.extend(result.get("last_tool_trace") or [])
    return result


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        ok=True,
        llm_configured=bool(settings.deepseek_api_key),
        faiss_loaded=indexes_ready(),
        model=settings.deepseek_model,
        embedding_model=settings.embedding_model,
    )


@router.post("/sessions", response_model=CreateAssistantSessionResponse)
def create_session(body: CreateAssistantSessionRequest) -> CreateAssistantSessionResponse:
    session_id = uuid4().hex
    _sessions[session_id] = _blank_state(session_id, body.mock_session_id)
    _traces[session_id] = []
    return CreateAssistantSessionResponse(session_id=session_id, mock_session_id=body.mock_session_id)


@router.get("/sessions/{session_id}", response_model=AssistantSessionSummary)
def get_session(session_id: str) -> AssistantSessionSummary:
    state = _sessions.get(session_id)
    if state is None:
        raise HTTPException(status_code=404, detail="unknown_session")
    airline = state.get("airline")
    booking = state.get("booking") or {}
    return AssistantSessionSummary(
        session_id=session_id,
        mock_session_id=state["mock_session_id"],
        airline=airline,
        verified=bool(state.get("verified_passenger_id")),
        pnr=state.get("pnr") or booking.get("pnr"),
        pending_quote=state.get("pending_quote"),
        handoff=bool(state.get("handoff_reason")),
        handoff_reason=state.get("handoff_reason"),
    )


@router.get("/sessions/{session_id}/trace", response_model=TraceResponse)
def get_trace(session_id: str) -> TraceResponse:
    state = _sessions.get(session_id)
    if state is None:
        raise HTTPException(status_code=404, detail="unknown_session")
    items = _traces.get(session_id) or []
    retrieval = []
    mock_calls = []
    for item in items:
        if item.get("step") == "retrieve_policy":
            retrieval.extend(item.get("detail", {}).get("sources") or [])
        if item.get("step") in {"lookup_booking", "quote_change", "quote_cancel", "confirm"}:
            mock_calls.append(item)
    return TraceResponse(
        session_id=session_id,
        items=[{"step": i["step"], "detail": i.get("detail") or {}} for i in items],
        retrieval=retrieval,
        mock_calls=mock_calls,
        handoff=state.get("handoff_reason"),
    )


@router.post("/chat")
async def chat(body: ChatRequest, request: Request):
    try:
        result = run_turn(body.session_id, body.message)
    except KeyError:
        raise HTTPException(status_code=404, detail="unknown_session")
    want_json = "application/json" in (request.headers.get("accept") or "")
    payload = {
        "type": "done",
        "text": result.get("reply") or "",
        "handoff": bool(result.get("handoff_reason")),
        "pending_quote": result.get("pending_quote"),
        "intent": result.get("intent"),
        "reason_hint": (result.get("pending_quote") or {}).get("reason_code")
        if result.get("pending_quote")
        else None,
    }
    if want_json:
        return JSONResponse(payload)

    async def events():
        yield f"data: {json.dumps({'type': 'token', 'text': payload['text']})}\n\n"
        yield f"data: {json.dumps(payload)}\n\n"

    return StreamingResponse(events(), media_type="text/event-stream")

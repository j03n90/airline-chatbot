from typing import Any, Optional, TypedDict


class AgentState(TypedDict, total=False):
    session_id: str
    mock_session_id: str
    user_text: str
    now_utc: str
    airline: Optional[str]
    pnr: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    verified_passenger_id: Optional[str]
    booking: Optional[dict[str, Any]]
    intent: str
    pending_quote: Optional[dict[str, Any]]
    last_retrieval: list[dict[str, Any]]
    last_tool_trace: list[dict[str, Any]]
    handoff_reason: Optional[str]
    reply: str
    change_new_departure: Optional[str]
    change_new_fare: Optional[float]
    cancel_segment_ids: Optional[list[str]]
    messages: list[dict[str, str]]

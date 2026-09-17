from __future__ import annotations

import re
from typing import Any

from backend.agent.llm import complete
from backend.agent.routing import classify_intent, extract_from_text, plus_one_day
from backend.agent.state import AgentState
from backend.api.schemas import ConfirmRequest, QuoteCancelRequest, QuoteChangeRequest
from backend.mock.client import MockClient
from backend.rag.retrieve import retrieve


def _trace(state: AgentState, step: str, detail: dict[str, Any]) -> None:
    items = list(state.get("last_tool_trace") or [])
    items.append({"step": step, "detail": detail})
    state["last_tool_trace"] = items


def _client(state: AgentState) -> MockClient:
    return MockClient(state["mock_session_id"])


def ingest_turn(state: AgentState) -> AgentState:
    messages = list(state.get("messages") or [])
    messages.append({"role": "user", "content": state.get("user_text") or ""})
    state["messages"] = messages
    state["last_tool_trace"] = []
    state["handoff_reason"] = state.get("handoff_reason")
    client = _client(state)
    state["now_utc"] = client.clock().isoformat()
    extract_from_text(state.get("user_text") or "", state)
    _trace(state, "ingest_turn", {"now_utc": state["now_utc"], "pnr": state.get("pnr")})
    return state


def route_intent(state: AgentState) -> AgentState:
    intent = classify_intent(state)
    state["intent"] = intent
    _trace(state, "route_intent", {"intent": intent})
    return state


def branch_after_route(state: AgentState) -> str:
    return state.get("intent") or "policy_qa"


def retrieve_policy(state: AgentState) -> AgentState:
    extra = []
    if state.get("airline"):
        extra.append(f"airline={state['airline']}")
    if state.get("booking"):
        extra.append(f"fare={state['booking'].get('fare_type')}")
    as_of = state.get("now_utc")
    hits = retrieve(
        state.get("user_text") or "",
        airline=state.get("airline"),
        extra_context=" ".join(extra),
        as_of=as_of,
    )
    state["last_retrieval"] = hits
    _trace(
        state,
        "retrieve_policy",
        {
            "airline": state.get("airline"),
            "as_of": as_of,
            "sources": [
                {
                    "airline": h["airline_code"],
                    "section": h["section"],
                    "title": h["title"],
                    "page": h["page"],
                    "version": h.get("version"),
                    "effective_at": h.get("effective_at"),
                }
                for h in hits
            ],
        },
    )
    return state


def lookup_booking(state: AgentState) -> AgentState:
    pnr = state.get("pnr")
    first = state.get("first_name")
    last = state.get("last_name")
    if not pnr:
        state["reply"] = "Please give the booking reference (PNR) and the traveler's first and last name."
        return state
    client = _client(state)
    result = client.lookup(pnr, last or "", first)
    _trace(
        state,
        "lookup_booking",
        {"request": {"pnr": pnr, "first_name": first, "last_name": last}, "reason_code": result.reason_code.value},
    )
    if not result.ok:
        state["reply"] = result.message
        state["verified_passenger_id"] = None
        return state
    state["booking"] = result.booking.model_dump(mode="json") if result.booking else None
    state["verified_passenger_id"] = result.verified_passenger_id
    state["airline"] = result.booking.airline.value if result.booking else state.get("airline")
    return state


def _ensure_verified(state: AgentState) -> bool:
    if state.get("verified_passenger_id") and state.get("booking"):
        return True
    lookup_booking(state)
    return bool(state.get("verified_passenger_id") and state.get("booking"))


def quote_change(state: AgentState) -> AgentState:
    if not _ensure_verified(state):
        if not state.get("reply"):
            state["reply"] = "I need the PNR plus the traveler's first and last name before quoting a change."
        return state
    booking = state["booking"]
    passenger_id = state["verified_passenger_id"]
    changes = []
    for segment in booking["segments"]:
        new_dep = plus_one_day(segment["departure_utc"])
        changes.append(
            {
                "segment_id": segment["id"],
                "new_departure_utc": new_dep,
                "new_fare_usd": segment["fare_usd"],
            }
        )
    req = QuoteChangeRequest(
        pnr=booking["pnr"],
        passenger_id=passenger_id,
        first_name=state["first_name"],
        last_name=state["last_name"],
        changes=changes,
    )
    result = _client(state).quote_change(req)
    _trace(
        state,
        "quote_change",
        {
            "request": req.model_dump(mode="json"),
            "ok": result.ok,
            "reason_code": result.reason_code.value,
            "change_fee_usd": result.change_fee_usd,
            "quote_id": result.quote_id,
        },
    )
    if result.ok:
        state["pending_quote"] = result.model_dump(mode="json")
    else:
        state["pending_quote"] = None
        if result.reason_code.value == "handoff_required":
            state["handoff_reason"] = result.handoff_reason or result.message
        state["reply"] = result.message
    return state


def quote_cancel(state: AgentState) -> AgentState:
    if not _ensure_verified(state):
        if not state.get("reply"):
            state["reply"] = "I need the PNR plus the traveler's first and last name before quoting a cancellation."
        return state
    booking = state["booking"]
    passenger_id = state["verified_passenger_id"]
    text = state.get("user_text") or ""
    speaker_first = (state.get("first_name") or "").lower()
    for p in booking["passengers"]:
        mentioned = re.search(rf"\b{re.escape(p['first_name'])}\b", text, re.I)
        if mentioned and p["first_name"].lower() != speaker_first:
            passenger_id = p["id"]
            break
    target = re.search(r"cancel ([A-Za-z]+)s? ([A-Za-z]+)", text, re.I)
    if target:
        t_first, t_last = target.group(1), target.group(2)
        for p in booking["passengers"]:
            if p["first_name"].lower() == t_first.lower() and p["last_name"].lower() == t_last.lower():
                passenger_id = p["id"]
                break
    segment_ids = state.get("cancel_segment_ids")
    if re.search(
        r"just the first|only one segment|keep the second|selected segment|"
        r"只要第一段|只取消第一程|只取消第一段|保留第二段",
        text,
        re.I,
    ):
        segment_ids = [booking["segments"][0]["id"]]
    req = QuoteCancelRequest(
        pnr=booking["pnr"],
        passenger_id=passenger_id,
        first_name=state["first_name"],
        last_name=state["last_name"],
        segment_ids=segment_ids,
    )
    result = _client(state).quote_cancel(req)
    _trace(
        state,
        "quote_cancel",
        {
            "request": req.model_dump(mode="json"),
            "ok": result.ok,
            "reason_code": result.reason_code.value,
            "refund_type": result.refund_type.value,
            "fare_refund_usd": result.fare_refund_usd,
            "tax_refund_usd": result.tax_refund_usd,
            "quote_id": result.quote_id,
        },
    )
    if result.ok:
        state["pending_quote"] = result.model_dump(mode="json")
    else:
        state["pending_quote"] = None
        if result.reason_code.value in {"handoff_required", "noshow"}:
            state["handoff_reason"] = result.handoff_reason or result.message
        state["reply"] = result.message
    return state


def confirm_or_reject(state: AgentState) -> AgentState:
    intent = state.get("intent")
    quote = state.get("pending_quote")
    if intent == "reject":
        state["pending_quote"] = None
        state["reply"] = "I have discarded the quote. The booking was not changed."
        _trace(state, "reject_quote", {})
        return state
    if not quote or not quote.get("quote_id"):
        state["reply"] = "There is no open quote to confirm."
        return state
    req = ConfirmRequest(
        quote_id=quote["quote_id"],
        passenger_id=state["verified_passenger_id"],
        first_name=state["first_name"],
        last_name=state["last_name"],
    )
    result = _client(state).confirm(req)
    _trace(
        state,
        "confirm",
        {"quote_id": quote["quote_id"], "ok": result.ok, "reason_code": result.reason_code.value},
    )
    if result.ok:
        state["pending_quote"] = None
        state["booking"] = result.booking.model_dump(mode="json") if result.booking else None
        state["reply"] = result.message
    else:
        state["reply"] = result.message
    return state


def handoff(state: AgentState) -> AgentState:
    reason = state.get("handoff_reason") or "This request needs the airline service desk."
    state["handoff_reason"] = reason
    state["reply"] = (
        reason
        + " I will not invent a fee or refund. Please use the airline service desk with the booking reference and traveler identity."
    )
    _trace(state, "handoff", {"reason": reason})
    return state


def compose_reply(state: AgentState) -> AgentState:
    if state.get("reply"):
        messages = list(state.get("messages") or [])
        messages.append({"role": "assistant", "content": state["reply"]})
        state["messages"] = messages
        return state

    retrieval = state.get("last_retrieval") or []
    quote = state.get("pending_quote")
    booking = state.get("booking")
    facts = []
    if booking:
        facts.append(
            f"Airline={booking.get('airline')} fare={booking.get('fare_type')} PNR={booking.get('pnr')} issued={booking.get('issued_at_utc')}"
        )
        if state.get("verified_passenger_id"):
            facts.append("Identity is already verified for this named traveler. Do not ask for identity again.")
    if quote:
        facts.append(
            f"QUOTE (not yet executed): kind={quote.get('kind')} change_fee_usd={quote.get('change_fee_usd')} "
            f"fare_difference_usd={quote.get('fare_difference_usd')} refund_type={quote.get('refund_type')} "
            f"fare_refund_usd={quote.get('fare_refund_usd')} tax_refund_usd={quote.get('tax_refund_usd')} "
            f"extras_refundable={quote.get('extras_refundable')} message={quote.get('message')}"
        )
        facts.append("Ask the traveler to confirm before anything is changed.")
    if retrieval:
        sources = []
        for hit in retrieval[:8]:
            version = hit.get("version") or "?"
            effective = (hit.get("effective_at") or "")[:10] or "unknown"
            sources.append(
                f"[{hit['airline_name']} v{version} effective {effective} section {hit['section']} p.{hit['page']}] {hit['text'][:900]}"
            )
        facts.append("POLICY SOURCES:\n" + "\n\n".join(sources))
        if state.get("now_utc"):
            facts.append(
                f"Request time (as-of): {state['now_utc']}. Use only the policy versions in force at this instant. "
                "Do not use a later version that is not yet effective."
            )
        if not state.get("airline") and len({h["airline_code"] for h in retrieval}) > 1:
            facts.append("Airline is unknown. Explain that rules differ by airline. Do not merge them into one rule.")
    elif state.get("intent") == "policy_qa":
        facts.append(
            f"No in-force passenger policy publication covers a request at {state.get('now_utc') or 'this request time'}. "
            "Do not invent a rule. Do not use a version that is not yet effective."
        )

    if booking and state.get("intent") == "lookup" and not quote:
        segs = ", ".join(
            f"{s['origin']}-{s['destination']} {s['departure_utc']} ({s['route_type']}, {s['status']})"
            for s in booking.get("segments", [])
        )
        facts.append(f"Itinerary: {segs}")

    system = (
        "You are a trial airline service assistant for three fictional airlines: "
        "Suntrail Air (STA), Northstar Air (NSA), Bluehaven Airways (BHA). "
        "Never invent fees. If a quote JSON is present, use those numbers exactly. "
        "Cite airline + version + effective date + section when answering policy. "
        "Only use the provided in-force sources; never answer from a version that is not yet effective. "
        "If sources disagree across airlines, say it depends on the airline. "
        "PNR + surname alone is not enough identity. "
        "Do not claim a booking was changed unless the confirm step succeeded. "
        "Pets, lounge, loyalty, unaccompanied minors: say the policy pack does not cover them and hand off. "
        "Reply in the same language as the user. "
        "Keep the reply short."
    )
    drafted = complete(system, f"User: {state.get('user_text')}\n\nFacts:\n" + "\n".join(facts))
    if not drafted:
        drafted = _fallback_reply(state, facts)
    state["reply"] = drafted
    messages = list(state.get("messages") or [])
    messages.append({"role": "assistant", "content": drafted})
    state["messages"] = messages
    return state


def _fallback_reply(state: AgentState, facts: list[str]) -> str:
    quote = state.get("pending_quote")
    if quote:
        return (
            f"Quote ready (not applied yet). Change fee USD {quote.get('change_fee_usd')}, "
            f"fare difference USD {quote.get('fare_difference_usd')}, "
            f"refund type {quote.get('refund_type')}, fare refund USD {quote.get('fare_refund_usd')}, "
            f"tax refund USD {quote.get('tax_refund_usd')}. "
            f"{quote.get('message')} Reply yes to confirm."
        )
    retrieval = state.get("last_retrieval") or []
    if retrieval and not state.get("airline"):
        return (
            "That depends on the airline. Suntrail Air, Northstar Air and Bluehaven Airways publish different tables. "
            "Tell me which airline you booked, or give a PNR and traveler name so I can look it up."
        )
    if retrieval:
        top = retrieval[0]
        version = top.get("version")
        effective = (top.get("effective_at") or "")[:10]
        if version:
            cite = f"{top['airline_name']} v{version} effective {effective} section {top['section']}"
        else:
            cite = f"{top['airline_name']} section {top['section']}"
        return f"{cite}: {top['text'][:600]}"
    if state.get("intent") == "policy_qa":
        as_of = state.get("now_utc") or "this request time"
        return (
            f"No in-force passenger policy publication covers a request at {as_of}. "
            "I will not invent a rule or use a version that is not yet effective."
        )
    if state.get("booking"):
        b = state["booking"]
        return f"I found booking {b['pnr']} on {b['airline']} ({b['fare_type']}). How can I help?"
    return "Please tell me the airline, or a PNR with the traveler's first and last name."


def needs_compose(state: AgentState) -> str:
    if state.get("handoff_reason") and state.get("intent") not in {"confirm", "reject"}:
        if state.get("pending_quote") is None and state.get("reply") and "service desk" in (state.get("reply") or "").lower():
            return "compose"
    return "compose"

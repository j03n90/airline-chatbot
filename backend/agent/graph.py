from langgraph.graph import END, START, StateGraph

from backend.agent.nodes import (
    compose_reply,
    confirm_or_reject,
    ingest_turn,
    lookup_booking,
    quote_cancel,
    quote_change,
    retrieve_policy,
    route_intent,
)
from backend.agent.state import AgentState


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("ingest_turn", ingest_turn)
    graph.add_node("route_intent", route_intent)
    graph.add_node("retrieve_policy", retrieve_policy)
    graph.add_node("lookup_booking", lookup_booking)
    graph.add_node("quote_change", quote_change)
    graph.add_node("quote_cancel", quote_cancel)
    graph.add_node("confirm_or_reject", confirm_or_reject)
    graph.add_node("compose_reply", compose_reply)

    graph.add_edge(START, "ingest_turn")
    graph.add_edge("ingest_turn", "route_intent")
    graph.add_conditional_edges(
        "route_intent",
        lambda s: s.get("intent") or "policy_qa",
        {
            "policy_qa": "retrieve_policy",
            "lookup": "lookup_booking",
            "change": "quote_change",
            "cancel": "quote_cancel",
            "confirm": "confirm_or_reject",
            "reject": "confirm_or_reject",
        },
    )
    graph.add_edge("retrieve_policy", "compose_reply")
    graph.add_edge("lookup_booking", "compose_reply")
    graph.add_edge("quote_change", "compose_reply")
    graph.add_edge("quote_cancel", "compose_reply")
    graph.add_edge("confirm_or_reject", "compose_reply")
    graph.add_edge("compose_reply", END)
    return graph.compile()


GRAPH = build_graph()

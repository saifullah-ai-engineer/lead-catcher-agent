"""The lead qualification agent, built as a LangGraph graph.

Flow:
  intake -> qualify -> route -> propose_booking -> draft_reply -> end

  intake:           clean up the raw enquiry (strip whitespace, fill defaults)
  qualify:          deterministic score from 0 to 100, with reasons
  route:            hot (70+), warm (40-69), or cold (under 40)
  draft_reply:      a reply matched to the route
  propose_booking:  a slot for hot and warm leads, none for cold leads

State is a plain dict so each node stays small and easy to test.
"""

from datetime import datetime
from typing import TypedDict

from langgraph.graph import END, StateGraph

from .models import Enquiry, LeadResult
from .scoring import route_for_score, score_enquiry
from .tools import draft_reply as draft_reply_text
from .tools import propose_booking_slot


class LeadState(TypedDict, total=False):
    enquiry: Enquiry
    score: int
    reasons: list[str]
    route: str
    reply: str
    booking_slot: str
    now: datetime | None


def intake(state: LeadState) -> LeadState:
    enquiry = state["enquiry"]
    cleaned = Enquiry(
        name=enquiry.name.strip(),
        channel=(enquiry.channel or "web").strip().lower() or "web",
        message=enquiry.message.strip(),
        budget_hint=enquiry.budget_hint.strip(),
        urgency=enquiry.urgency.strip(),
    )
    return {"enquiry": cleaned}


def qualify(state: LeadState) -> LeadState:
    score, reasons = score_enquiry(state["enquiry"])
    return {"score": score, "reasons": reasons}


def route(state: LeadState) -> LeadState:
    return {"route": route_for_score(state["score"])}


def draft_reply(state: LeadState) -> LeadState:
    result = LeadResult(
        enquiry=state["enquiry"],
        score=state["score"],
        reasons=state["reasons"],
        route=state["route"],
        booking_slot=state.get("booking_slot", ""),
    )
    return {"reply": draft_reply_text(result)}


def propose_booking(state: LeadState) -> LeadState:
    if state["route"] == "cold":
        return {"booking_slot": ""}
    return {"booking_slot": propose_booking_slot(state.get("now"))}


def build_graph():
    """Build and compile the LangGraph state graph."""
    graph = StateGraph(LeadState)
    graph.add_node("intake", intake)
    graph.add_node("qualify", qualify)
    graph.add_node("route", route)
    graph.add_node("draft_reply", draft_reply)
    graph.add_node("propose_booking", propose_booking)
    graph.set_entry_point("intake")
    graph.add_edge("intake", "qualify")
    graph.add_edge("qualify", "route")
    graph.add_edge("route", "propose_booking")
    graph.add_edge("propose_booking", "draft_reply")
    graph.add_edge("draft_reply", END)
    return graph.compile()


_GRAPH = None


def run_enquiry(enquiry: Enquiry, now: datetime | None = None) -> LeadResult:
    """Run one enquiry through the graph and return the result."""
    global _GRAPH
    if _GRAPH is None:
        _GRAPH = build_graph()
    final = _GRAPH.invoke({"enquiry": enquiry, "now": now})
    return LeadResult(
        enquiry=final["enquiry"],
        score=final["score"],
        reasons=final["reasons"],
        route=final["route"],
        reply=final["reply"],
        booking_slot=final.get("booking_slot", ""),
    )

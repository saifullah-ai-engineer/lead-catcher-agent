"""lead-catcher-agent: a LangGraph lead qualification agent.

Takes a raw inbound enquiry and runs it through intake, qualify,
route, booking, and reply drafting. No LLM and no paid API by default.
"""

from .graph import build_graph, run_enquiry
from .models import Enquiry, LeadResult
from .scoring import route_for_score, score_enquiry

__all__ = [
    "Enquiry",
    "LeadResult",
    "build_graph",
    "route_for_score",
    "run_enquiry",
    "score_enquiry",
]
__version__ = "0.1.0"

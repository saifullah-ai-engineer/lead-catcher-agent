"""Data models for the lead catcher agent.

Everything here is plain data. No network calls, no LLM calls.
"""

from dataclasses import dataclass, field


@dataclass
class Enquiry:
    """One raw inbound enquiry from a customer."""

    name: str = ""
    channel: str = "web"
    message: str = ""
    budget_hint: str = ""
    urgency: str = ""

    def text(self) -> str:
        """All free text, joined, for scoring."""
        parts = [self.message, self.budget_hint, self.urgency]
        return " ".join(p.strip() for p in parts if p.strip())


@dataclass
class LeadResult:
    """The outcome of running one enquiry through the graph."""

    enquiry: Enquiry
    score: int = 0
    reasons: list[str] = field(default_factory=list)
    route: str = "cold"
    reply: str = ""
    booking_slot: str = ""

    def summary(self) -> str:
        name = self.enquiry.name or "Unknown"
        return f"{name}: score {self.score}, route {self.route}, slot {self.booking_slot or 'none'}"

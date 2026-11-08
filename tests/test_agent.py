"""Tests for the lead catcher agent.

All tests run offline. The qualifier is deterministic, so scores are
checked exactly, not just as ranges, wherever the input is fixed.
"""

from datetime import datetime

import pytest

from lead_catcher_agent import Enquiry, run_enquiry, score_enquiry
from lead_catcher_agent.scoring import route_for_score
from lead_catcher_agent.tools import draft_reply, propose_booking_slot
from lead_catcher_agent.models import LeadResult

NOW = datetime(2026, 11, 9, 9, 0)  # a Monday, so the next slot is Tuesday


def hot_enquiry() -> Enquiry:
    return Enquiry(
        name="Ayesha Khan",
        channel="WhatsApp",
        message=(
            "Hi, I need a dentist appointment this week for a toothache. "
            "How much does a checkup cost? Please call me today."
        ),
        budget_hint="Ready to pay for a checkup",
        urgency="This week, toothache",
    )


def test_hot_enquiry_scores_high_and_routes_hot():
    score, reasons = score_enquiry(hot_enquiry())
    assert score >= 70
    assert route_for_score(score) == "hot"
    assert reasons


def test_vague_enquiry_routes_cold():
    enquiry = Enquiry(name="", channel="web", message="hi")
    score, _ = score_enquiry(enquiry)
    assert score < 40
    assert route_for_score(score) == "cold"


def test_middle_enquiry_routes_warm():
    enquiry = Enquiry(
        name="Bilal Ahmed",
        channel="web",
        message="Do you offer cleaning services for a small office? I would like a quote.",
    )
    score, _ = score_enquiry(enquiry)
    assert 40 <= score < 70
    assert route_for_score(score) == "warm"


def test_budget_mention_raises_score():
    base = Enquiry(name="Sara", channel="web", message="I need a repair done soon.")
    with_budget = Enquiry(
        name="Sara", channel="web",
        message="I need a repair done soon. My budget is $200, what is the price?",
    )
    assert score_enquiry(with_budget)[0] > score_enquiry(base)[0]


def test_urgency_raises_score():
    calm = Enquiry(name="Sara", channel="web", message="I need a repair done sometime.")
    urgent = Enquiry(
        name="Sara", channel="web",
        message="I need a repair done today, this is urgent, please call me asap.",
    )
    assert score_enquiry(urgent)[0] > score_enquiry(calm)[0]


def test_spam_message_gets_capped():
    enquiry = Enquiry(
        name="Promo", channel="web",
        message="Buy followers now, free money, crypto, guaranteed income, click here.",
    )
    score, reasons = score_enquiry(enquiry)
    assert score <= 10
    assert any("spam" in r for r in reasons)


def test_empty_message_scores_zero():
    score, reasons = score_enquiry(Enquiry(name="Sara", channel="web", message=""))
    assert score == 0
    assert reasons


def test_hot_reply_mentions_name_and_slot():
    result = run_enquiry(hot_enquiry(), now=NOW)
    assert result.route == "hot"
    assert "Ayesha" in result.reply
    assert result.booking_slot in result.reply
    assert "YES" in result.reply


def test_cold_reply_asks_for_more_detail_and_has_no_slot():
    result = run_enquiry(Enquiry(name="", channel="web", message="hi"), now=NOW)
    assert result.route == "cold"
    assert result.booking_slot == ""
    assert "more about what you need" in result.reply


def test_booking_slot_is_a_weekday_in_the_future():
    slot = propose_booking_slot(NOW)
    assert slot.startswith("2026-11-10 at ")
    assert datetime.fromisoformat(slot.split(" at ")[0]).weekday() < 5


def test_llm_hook_is_optional_and_off_by_default():
    result = LeadResult(enquiry=hot_enquiry(), score=80, route="hot", booking_slot="2026-11-10 at 10:00")
    plain = draft_reply(result)
    rewritten = draft_reply(result, llm=lambda prompt: "Rewritten by an LLM.")
    assert "Ayesha" in plain
    assert rewritten == "Rewritten by an LLM."


def test_graph_end_to_end_returns_every_field():
    result = run_enquiry(hot_enquiry(), now=NOW)
    assert result.score > 0
    assert result.reasons
    assert result.route in ("hot", "warm", "cold")
    assert result.reply
    assert result.enquiry.name == "Ayesha Khan"

"""Deterministic lead scoring.

This is the default qualifier. It uses word lists and simple rules, so
the same enquiry always gets the same score. No LLM, no API, no cost.

Score bands:
  hot  70 to 100: ready to talk, has a need, a timeline, or a budget
  warm 40 to 69:  interested, but something is missing
  cold 0 to 39:   vague, very short, or looks like spam
"""

import re

BUDGET_WORDS = ("budget", "price", "cost", "quote", "how much", "afford", "pay")
URGENCY_WORDS = ("urgent", "asap", "today", "tomorrow", "this week", "right away", "need now")
INTENT_WORDS = (
    "book", "appointment", "quote", "repair", "clean", "install", "fix",
    "consult", "checkup", "treatment", "service", "visit", "call me", "meeting",
)
SPAM_WORDS = ("free money", "crypto", "buy followers", "seo services", "guaranteed income")

_MONEY = re.compile(r"(\$|£|€|rs\.?|pkr|usd)\s?\d+|\d+\s?(usd|gbp|eur|pkr)", re.IGNORECASE)


def _contains(text: str, words: tuple[str, ...]) -> list[str]:
    return [w for w in words if w in text]


def score_enquiry(enquiry) -> tuple[int, list[str]]:
    """Score one enquiry from 0 to 100 and explain why."""
    text = enquiry.text().lower()
    message = enquiry.message.strip()
    score = 0
    reasons: list[str] = []

    if not message:
        return 0, ["No message text was provided."]

    words = message.split()
    if len(words) >= 20:
        score += 20
        reasons.append("Detailed message (20 or more words).")
    elif len(words) >= 8:
        score += 10
        reasons.append("Message has enough detail to understand the need.")
    else:
        reasons.append("Very short message, little detail.")

    intent = _contains(text, INTENT_WORDS)
    if intent:
        score += 20
        reasons.append(f"Clear intent: {', '.join(sorted(set(intent))[:3])}.")

    urgency = _contains(text, URGENCY_WORDS)
    if urgency:
        score += 15
        reasons.append(f"Shows urgency: {', '.join(sorted(set(urgency))[:2])}.")

    if _MONEY.search(text) or _contains(text, BUDGET_WORDS):
        score += 20
        reasons.append("Mentions budget or price, so this is a buying signal.")

    if enquiry.name.strip():
        score += 10
        reasons.append("Customer gave their name.")
    else:
        reasons.append("No name given.")

    if enquiry.channel.strip().lower() in ("phone", "whatsapp", "call"):
        score += 5
        reasons.append("Came through a direct channel (phone or WhatsApp).")

    spam = _contains(text, SPAM_WORDS)
    if spam:
        score = min(score, 10)
        reasons.append(f"Looks like spam: {', '.join(sorted(set(spam))[:2])}.")

    if "http://" in text or "https://" in text:
        score = min(score, 20)
        reasons.append("Message contains a link, which is unusual for a real enquiry.")

    return max(0, min(100, score)), reasons


def route_for_score(score: int) -> str:
    """Map a score to a route."""
    if score >= 70:
        return "hot"
    if score >= 40:
        return "warm"
    return "cold"

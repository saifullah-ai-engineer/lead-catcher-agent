"""Reply drafting and booking slots.

Replies are templates, not generated text. The business edits the
templates, and the agent fills in the name, the route, and the slot.
An optional `llm` callable can be passed to draft_reply to rewrite the
reply with a language model, but it is off by default and never called
unless the caller passes one in.
"""

from datetime import datetime, timedelta

HOT_REPLY = (
    "Hi {name}, thanks for getting in touch. {first_line} "
    "I can book you in for {slot}. Reply YES to confirm, or tell me another time that suits you."
)
WARM_REPLY = (
    "Hi {name}, thanks for your message. {first_line} "
    "Could you tell me a bit more about what you need and when you would like it done? "
    "If it helps, I have {slot} free."
)
COLD_REPLY = (
    "Hi {name}, thanks for reaching out. Could you share a little more about what you need, "
    "and when you would like it done? That way I can point you to the right person."
)

_FIRST_LINES = {
    "hot": "You sound ready to go, so let us get you booked in.",
    "warm": "That sounds like something we can help with.",
    "cold": "Happy to help.",
}


def propose_booking_slot(now: datetime | None = None) -> str:
    """Propose the next free slot: the next weekday at 10:00 or 14:00.

    Pass `now` to make the result deterministic, which the tests do.
    """
    now = now or datetime.now()
    day = now.date() + timedelta(days=1)
    while day.weekday() >= 5:
        day += timedelta(days=1)
    hour = 14 if now.hour >= 10 else 10
    return f"{day.isoformat()} at {hour:02d}:00"


def draft_reply(result, llm=None) -> str:
    """Draft a reply for a scored, routed lead.

    `llm`, if given, is a callable that takes a prompt string and returns
    a string. It is never used unless the caller passes it.
    """
    name = result.enquiry.name.strip() or "there"
    first_line = _FIRST_LINES.get(result.route, _FIRST_LINES["cold"])
    if result.route == "hot":
        template = HOT_REPLY
    elif result.route == "warm":
        template = WARM_REPLY
    else:
        template = COLD_REPLY
    slot = result.booking_slot or propose_booking_slot()
    reply = template.format(name=name, first_line=first_line, slot=slot)
    if llm is not None:
        prompt = (
            "Rewrite this reply in a friendly, professional tone, keeping "
            "the name, the booking slot, and the call to action:\n\n" + reply
        )
        rewritten = llm(prompt)
        if rewritten and rewritten.strip():
            return rewritten.strip()
    return reply

# lead-catcher-agent

A lead qualification agent for local service businesses, agencies, and clinics. It takes a raw inbound enquiry and turns it into a scored, routed lead with a reply ready to send.

Built with LangGraph by Saif Ullah, Agentic AI Engineer at TechAurah.

## What it does

A customer writes in, on WhatsApp, the web, or the phone. The agent runs five steps:

1. **Intake**: cleans up the raw enquiry.
2. **Qualify**: scores it 0 to 100 and explains the score in plain words.
3. **Route**: hot (70 or more), warm (40 to 69), or cold (under 40).
4. **Book**: proposes the next weekday slot for hot and warm leads. Cold leads get no slot.
5. **Reply**: drafts a reply matched to the route, with the name and the slot filled in.

The point is simple: hot leads get answered fast, warm leads get asked one good question, and cold leads do not eat the team's time.

## 30 second demo

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python examples/demo.py
```

That runs three sample enquiries with no API key, no network, and no cost. You will see something like this:

```text
Enquiry from Ayesha Khan via WhatsApp
  Score: 90/100 (hot)
  Reasons: Detailed message (20 or more words).; Clear intent: appointment, call me, checkup.; Shows urgency: this week, today.; Mentions budget or price, so this is a buying signal.; Customer gave their name.; Came through a direct channel (phone or WhatsApp).
  Booking slot: 2026-11-10 at 10:00
  Reply: Hi Ayesha Khan, thanks for getting in touch. You sound ready to go, so let us get you booked in. I can book you in for 2026-11-10 at 10:00. Reply YES to confirm, or tell me another time that suits you.
```

Use it from your own code like this:

```python
from lead_catcher_agent import Enquiry, run_enquiry

result = run_enquiry(Enquiry(
    name="Ayesha Khan",
    channel="WhatsApp",
    message="I need a dentist appointment this week. How much does a checkup cost?",
))
print(result.score, result.route)
print(result.reply)
```

Or qualify a whole JSON file from the command line:

```bash
python -m lead_catcher_agent examples/sample_enquiries.json
```

## How it works

```text
Enquiry (name, channel, message, budget hint, urgency)
    |
    v
 intake  ->  qualify  ->  route  ->  propose_booking  ->  draft_reply
                |            |              |                   |
           score 0-100   hot/warm/cold   next weekday slot   reply template
           + reasons
```

The graph is a real LangGraph `StateGraph` in `src/lead_catcher_agent/graph.py`. Each node is a small function, and the state is a plain dict, so the flow is easy to read and easy to change.

Scoring is deterministic rules, in `src/lead_catcher_agent/scoring.py`. It looks for clear intent, urgency, budget or price mentions, detail, a name, and a direct channel. It caps the score for spammy messages and messages with links. The same enquiry always gets the same score.

Replies are templates in `src/lead_catcher_agent/tools.py`. The business edits the templates, and the agent fills in the name, the route, and the slot.

## LLM use, optional and off by default

By default this project calls no LLM and no paid API. Scoring and replies are rules and templates, so the demo costs nothing.

If you want an LLM to rewrite the reply, pass a callable to `draft_reply`:

```python
from lead_catcher_agent.tools import draft_reply
reply = draft_reply(result, llm=my_llm_function)
```

Your function takes a prompt string and returns a string. No API key is read from anywhere in this repo, and no key should ever be committed here.

## Tests

```bash
.venv/bin/python -m pytest -q
```

12 tests cover scoring, routing, reply drafting, booking slots, spam, empty messages, the optional LLM hook, and the full graph end to end.

## Honest limits

- The qualifier is keyword rules, not understanding. A well written enquiry in unusual wording can score low, and a pushy message can score high.
- Booking slots are proposed, not real calendar bookings. There is no calendar integration yet.
- There are no measured results behind this project. No stars, users, client results, or revenue are claimed here, because none have been measured.
- It is built for English enquiries from small service businesses. Other languages and long conversations are not handled yet.

## Project layout

```text
src/lead_catcher_agent/
  models.py    Enquiry and LeadResult
  scoring.py   deterministic scoring and routing
  tools.py     reply templates and booking slots
  graph.py     the LangGraph state graph
  __main__.py  command line entry point
tests/         12 tests
examples/      demo.py and sample_enquiries.json
```

## License

MIT. See LICENSE.

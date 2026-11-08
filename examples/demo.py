"""30 second demo: run the agent on 3 sample enquiries.

Usage, from the project root:
    .venv/bin/python examples/demo.py

No API key, no network, no cost. The demo loads
examples/sample_enquiries.json and prints the result for each one.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from lead_catcher_agent import Enquiry, run_enquiry

# Fixed time so the demo output is the same every time you run it.
NOW = datetime(2026, 11, 9, 9, 0)


def main() -> None:
    path = Path(__file__).resolve().parent / "sample_enquiries.json"
    with open(path, encoding="utf-8") as handle:
        items = json.load(handle)
    for item in items:
        result = run_enquiry(Enquiry(**item), now=NOW)
        print("=" * 60)
        print(f"Enquiry from {result.enquiry.name or '(no name)'} via {result.enquiry.channel}")
        print(f"  Message: {result.enquiry.message}")
        print(f"  Score: {result.score}/100 ({result.route})")
        print(f"  Reasons: {'; '.join(result.reasons)}")
        print(f"  Booking slot: {result.booking_slot or 'none, too cold to book'}")
        print(f"  Reply: {result.reply}")
    print("=" * 60)


if __name__ == "__main__":
    main()

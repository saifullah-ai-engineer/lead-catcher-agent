"""Command line entry point: qualify one enquiry from a JSON file.

Usage:
    python -m lead_catcher_agent examples/sample_enquiries.json
"""

import json
import sys

from .graph import run_enquiry
from .models import Enquiry


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        print("Usage: python -m lead_catcher_agent <enquiries.json>")
        return 2
    with open(argv[0], encoding="utf-8") as handle:
        items = json.load(handle)
    for item in items:
        result = run_enquiry(Enquiry(**item))
        print(result.summary())
        print("  Reasons:", "; ".join(result.reasons))
        print("  Reply:", result.reply)
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

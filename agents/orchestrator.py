"""
ORCHESTRATOR — runs the full adversarial loop.

  Round 1: hunter audits the vulnerable app
  Patch:   fixer patches every finding
  Round 2: hunter re-audits the PATCHED app (verification pass)
  Report:  summary comparing round 1 vs round 2

Usage:
  export ANTHROPIC_API_KEY='sk-ant-...'   # or OPENAI_API_KEY
  python3 agents/orchestrator.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hunter import hunt
from fixer import fix


def main() -> None:
    print("=" * 60)
    print("ROUND 1 — hunter vs vulnerable app")
    print("=" * 60)
    r1 = hunt("vulnerable_app/app.py", "round1")
    n1 = len(r1["findings"])

    print()
    print("=" * 60)
    print("PATCH — fixer hardens the app")
    print("=" * 60)
    fixed_path = fix()

    print()
    print("=" * 60)
    print("ROUND 2 — hunter vs patched app (verification)")
    print("=" * 60)
    r2 = hunt(fixed_path, "round2")
    n2 = len(r2["findings"])

    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    summary = (
        f"# Vuln-hunt summary\n\n"
        f"- Round 1 findings (vulnerable app): **{n1}**\n"
        f"- Round 2 findings (patched app): **{n2}**\n"
        f"- Remediation rate: **{(n1 - n2) / n1 * 100:.0f}%**\n\n"
    )
    if n2:
        summary += "## Surviving findings (need human review)\n"
        for v in r2["findings"]:
            summary += f"- {v['title']} ({v['severity']}) — {v['location']}\n"
    else:
        summary += "Clean sweep — the hunter found nothing in the patched app.\n"

    os.makedirs("reports", exist_ok=True)
    with open("reports/summary.md", "w") as f:
        f.write(summary)
    print(summary)
    print("Full reports in reports/")


if __name__ == "__main__":
    main()

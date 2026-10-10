"""
VERIFIER — majority-vote verification.

Runs the hunter N times against the patched app and keeps only the findings
a majority of runs agree on. Lesson from iteration 4: single-run verdicts
are nondeterministic. Votes are not.

Usage:
  python3 agents/verifier.py [path/to/target.py] [rounds]
  VERIFY_ROUNDS=5 python3 agents/verifier.py
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hunter import hunt


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def finding_key(v: dict) -> tuple:
    return (norm(v.get("title")), norm(v.get("location")))


def verify(target_path: str, rounds: int = 3) -> dict:
    rounds = max(1, int(os.environ.get("VERIFY_ROUNDS", rounds)))
    majority = rounds // 2 + 1
    print(f"[verifier] {rounds} passes on {target_path} (majority = {majority})")

    tally: dict = {}
    order: list = []
    for i in range(1, rounds + 1):
        res = hunt(target_path, f"verify_r{i}")
        for v in res["findings"]:
            k = finding_key(v)
            if k not in tally:
                tally[k] = {"finding": v, "votes": 0}
                order.append(k)
            tally[k]["votes"] += 1
        print(f"[verifier] pass {i}/{rounds}: {len(res['findings'])} findings")

    consensus = []
    os.makedirs("reports", exist_ok=True)
    with open("reports/verifier_votes.md", "w") as f:
        f.write(f"# Verifier votes — {rounds} passes, majority = {majority}\n")
        f.write(f"Target: `{target_path}`\n\n")
        for k in order:
            e = tally[k]
            v = e["finding"]
            kept = e["votes"] >= majority
            mark = "KEPT" if kept else "dropped"
            f.write(f"- [{mark}] {e['votes']}/{rounds} — "
                    f"{v['title']} ({v['severity']}) @ {v['location']}\n")
            if kept:
                vc = dict(v)
                vc["votes"] = f"{e['votes']}/{rounds}"
                consensus.append(vc)

    print(f"[verifier] consensus: {len(consensus)} findings survive the vote")
    return {"findings": consensus}


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "vulnerable_app/app_fixed.py"
    rounds = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    verify(target, rounds)

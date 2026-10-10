"""
HUNTER — the attacker agent.

Reads a Python file, audits it like a senior application-security
engineer, and writes structured findings to reports/.

Usage:
  python3 agents/hunter.py [path/to/target.py] [round_label]
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from llm import ask

HUNTER_SYSTEM = """You are a senior application security auditor. You are
thorough, precise, and you never miss the second instance of a bug class.
You know the CWE catalog and OWASP Top 10 by heart."""

HUNTER_PROMPT = """Audit this Python code for security vulnerabilities.

For EVERY vulnerability you find, report:
- title: short name (e.g. "SQL Injection in login()")
- cwe: CWE number if known (e.g. "CWE-89")
- severity: Critical, High, Medium, or Low
- location: function name and approximate line number
- description: what is wrong, in 1-2 sentences
- exploitation: a one-line sketch of how an attacker would abuse it
- fix: one-line remediation guidance

Be thorough: if a bug class appears twice, report BOTH instances.
Do not report the stub db_execute() as a vulnerability — it is test scaffolding.

Return ONLY valid JSON, no markdown fences, in this shape:
{"findings": [{"title": ..., "cwe": ..., "severity": ..., "location": ...,
"description": ..., "exploitation": ..., "fix": ...}]}

CODE:
```python
{code}
```"""


def hunt(target_path: str, label: str = "round1") -> dict:
    with open(target_path) as f:
        code = f.read()
    print(f"[hunter] auditing {target_path} ...")
    raw = ask(HUNTER_SYSTEM, HUNTER_PROMPT.format(code=code))
    findings = json.loads(raw.strip().strip("`"))

    os.makedirs("reports", exist_ok=True)
    with open(os.path.join("reports", f"hunter_{label}.json"), "w") as f:
        json.dump(findings, f, indent=2)
    out = os.path.join("reports", f"hunter_{label}.md")
    with open(out, "w") as f:
        f.write(f"# Hunter findings — {label}\n")
        f.write(f"Target: `{target_path}`\n\n")
        for i, v in enumerate(findings["findings"], 1):
            f.write(f"## {i}. {v['title']} ({v['severity']})\n")
            f.write(f"- **CWE:** {v.get('cwe', 'n/a')} | **Location:** {v['location']}\n")
            f.write(f"- **What:** {v['description']}\n")
            f.write(f"- **Exploit sketch:** {v['exploitation']}\n")
            f.write(f"- **Fix:** {v['fix']}\n\n")
    print(f"[hunter] {len(findings['findings'])} findings -> {out}")
    return findings


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "vulnerable_app/app.py"
    label = sys.argv[2] if len(sys.argv) > 2 else "round1"
    hunt(target, label)

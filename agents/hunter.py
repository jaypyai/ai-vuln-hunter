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

CRITICAL AUDIT DISCIPLINE:
- Audit ONLY executable code. IGNORE all comments and docstrings completely —
  a `# VULN` comment is not evidence of a vulnerability, and a `# SECURE`
  comment is not proof of a fix. Comments lie; code doesn't.
- For each finding you MUST quote the exact code line(s) as evidence.
  No quote, no finding.
- Only cite real CWE numbers from the CWE catalog. Never invent one —
  "CWE- Hack-327" is not a thing. If unsure, write "CWE: n/a".

RECOGNIZING REAL FIXES — do NOT report these as vulnerabilities:
- Parameterized queries: if the SQL string uses ? or %s placeholders AND the
  values are passed SEPARATELY (e.g. cursor.execute(query, params) or
  db_execute(query, params)), the query is SAFE. Only report SQLi when user
  input is interpolated directly into the query string via f-strings, %,
  +, or .format().
- Secrets via os.environ.get("X") are safe; only report hardcoded literals.
- hashlib.pbkdf2_hmac / bcrypt / scrypt with a per-user salt is safe storage;
  unsalted MD5/SHA1 is not.
- subprocess with shell=False and an argument list is safe; shell=True with
  interpolated input is not.
- json.loads is safe deserialization; pickle.loads on untrusted input is not.
- html.escape() on interpolated output is safe; raw interpolation is not.

A fix is real when the dangerous *mechanism* is gone, not when the code
merely looks different. If you cannot point to the live mechanism, do not
report it.

DEDUPLICATE: never report the same vulnerability twice. If two observations
share the same title and location, merge them into ONE finding. Before
finalizing, scan your list for repeats — same (title, location) twice means
you made an error, not found two bugs.

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
    raw = ask(HUNTER_SYSTEM, HUNTER_PROMPT.replace("{code}", code))
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

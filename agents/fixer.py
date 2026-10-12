"""
FIXER, the defender agent.

Takes the hunter's findings plus the original vulnerable code, and produces
a patched version of the file. Writes vulnerable_app/app_fixed.py and a
notes file explaining each patch.

Usage:
  python3 agents/fixer.py
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from llm import ask

FIXER_SYSTEM = """You are a senior secure-coding engineer. You patch
vulnerabilities with minimal, idiomatic changes. You never break working
functionality, and you never introduce new vulnerabilities."""

FIXER_PROMPT = """Patch every vulnerability in the findings below. Rewrite the
ORIGINAL CODE with secure equivalents:

- SQL injection -> parameterized queries (show the pattern with a comment;
  keep the db_execute stub signature)
- Hardcoded secrets -> os.environ lookups with a clear error if unset
- Weak password hashing -> hashlib.pbkdf2_hmac with a per-user salt
- Command injection -> subprocess without shell=True, argument list
- Insecure deserialization -> json.loads with a comment explaining why
  pickle is banned for untrusted input
- XSS -> html.escape() on interpolated output

Rules:
- Keep every function name and signature identical.
- Keep the `if __name__ == "__main__"` block working.
- REMOVE all original `# VULN...` comments, they describe bugs that no longer
  exist, and leftover ones will confuse future audits. Replace them with
  `# SECURE:` comments only.
- Remove STALE CREDENTIAL ARTIFACTS: if the original code contains hardcoded
  hashes, tokens, or secrets your patch no longer uses (e.g. an old MD5 hash
  in a users dict), delete them. Replace with a short comment like
  `# provisioned securely at deploy time`. Dead secrets in source are still
  findings waiting to happen.
- Add a short `# SECURE:` comment above each patched line explaining the fix.

Return ONLY the complete patched Python file, no markdown fences,
no explanation outside the code.

FINDINGS:
```json
{findings}
```

ORIGINAL CODE:
```python
{code}
```"""


def fix() -> str:
    with open("vulnerable_app/app.py") as f:
        code = f.read()
    # Reuse round-1 findings if present; otherwise re-hunt quickly.
    findings_path = "reports/hunter_round1.json"
    if os.path.exists(findings_path):
        with open(findings_path) as f:
            findings = f.read()
    else:
        from hunter import hunt
        findings = json.dumps(hunt("vulnerable_app/app.py", "round1"))

    print("[fixer] patching ...")
    patched = ask(FIXER_SYSTEM, FIXER_PROMPT.format(findings=findings, code=code))
    patched = patched.strip().strip("`").removeprefix("python").strip()

    out = "vulnerable_app/app_fixed.py"
    with open(out, "w") as f:
        f.write(patched + "\n")
    print(f"[fixer] patched code -> {out}")

    # Sanity: the fixed file must at least parse.
    compile(patched, out, "exec")
    print("[fixer] syntax check passed")
    return out


if __name__ == "__main__":
    fix()

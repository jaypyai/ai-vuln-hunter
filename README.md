# AI Vuln Hunter

A multi-agent vulnerability hunting system: an **attacker agent** audits code for security flaws, a **defender agent** patches them, and an **orchestrator** runs the full adversarial loop — hunt, fix, re-hunt to verify.

```
vulnerable_app/app.py ──▶  HUNTER (round 1) ──▶ findings
                                                   │
                                                   ▼
vulnerable_app/app_fixed.py ◀── FIXER ─────────────┘
        │
        ▼
   HUNTER (round 2) ──▶ verification: what survived?
```

## The vuln classes (deliberate targets)

| # | Vulnerability | Where |
|---|---|---|
| 1 | Hardcoded API credential | `API_KEY` |
| 2 | SQL injection (×2 — tests thoroughness) | `login()`, `search_users()` |
| 3 | Weak password storage (unsalted MD5) | `verify_password()` |
| 4 | Command injection | `run_report()` |
| 5 | Insecure deserialization (pickle) | `load_session()` |
| 6 | Reflected XSS | `render_greeting()` |

## Quickstart

```bash
export ANTHROPIC_API_KEY='sk-ant-...'   # or OPENAI_API_KEY
python3 agents/orchestrator.py
```

No dependencies — stdlib only. Reports land in `reports/`.

Run agents individually:

```bash
python3 agents/hunter.py vulnerable_app/app.py round1
python3 agents/fixer.py
```

## What I learned

- **Adversarial self-play works.** The re-hunt (round 2) is the whole point — a fix isn't done until the attacker confirms it.
- **The second instance is the real test.** Any scanner finds the first SQLi; catching the *second* one in `search_users()` separates thorough agents from lucky ones.
- **Verification asymmetry is real.** Finding bugs is easier than proving they're gone — round 2 forces the hunter to re-derive, not just trust the patch notes.
- **Agent identity matters.** Each agent runs with one job and least privilege — the same pattern as production AI deployments (dedicated managed identities, scoped tool access).

## How this was built

Directed and architected by me; implementation assisted by AI — the same loop the project itself demonstrates. I designed the vulnerability set, the agent roles, and the verify-or-it-didn't-happen loop; AI helped type it out. Judgment is the job.

## License

MIT

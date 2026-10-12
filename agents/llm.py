"""
Minimal LLM client, zero dependencies (stdlib urllib only).

Uses whichever key is set:
  ANTHROPIC_API_KEY -> Anthropic Messages API (claude-sonnet-4-5)
  OPENAI_API_KEY    -> OpenAI Chat Completions API (gpt-4o-mini)

Set exactly one. Get a key at https://console.anthropic.com or
https://platform.openai.com. Never commit keys, use a .env file
or export them in your shell.
"""

import json
import os
import urllib.request


def ask(system: str, user: str, max_tokens: int = 3000) -> str:
    if os.environ.get("ANTHROPIC_API_KEY"):
        return _anthropic(system, user, max_tokens)
    if os.environ.get("OPENAI_API_KEY"):
        return _openai(system, user, max_tokens)
    raise SystemExit(
        "No API key found. Set ANTHROPIC_API_KEY or OPENAI_API_KEY first.\n"
        "  export ANTHROPIC_API_KEY='sk-ant-...'"
    )


def _post(url: str, headers: dict, payload: dict) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.load(resp)


def _anthropic(system: str, user: str, max_tokens: int) -> str:
    model = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5")
    data = _post(
        "https://api.anthropic.com/v1/messages",
        {
            "x-api-key": os.environ["ANTHROPIC_API_KEY"],
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        {
            "model": model,
            "max_tokens": max_tokens,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        },
    )
    return "".join(
        b["text"] for b in data["content"] if b["type"] == "text"
    )


def _openai(system: str, user: str, max_tokens: int) -> str:
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    data = _post(
        "https://api.openai.com/v1/chat/completions",
        {
            "Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}",
            "content-type": "application/json",
        },
        {
            "model": model,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        },
    )
    return data["choices"][0]["message"]["content"]

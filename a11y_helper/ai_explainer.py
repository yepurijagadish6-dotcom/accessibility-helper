"""
Uses an AI model (Anthropic's Claude API) to turn technical findings into
plain-language explanations and suggested fixes.

Design choices worth talking about in an interview:
  * The checks are done by normal code, NOT by the AI. The AI only explains.
    That keeps results reliable and repeatable (no "hallucinated" issues).
  * We send only small HTML snippets, never the whole page, to keep cost low
    and avoid sending unnecessary data.
  * We ask for JSON back and validate it. If anything fails, the tool still
    works and simply shows the rule-based explanation (graceful fallback).
  * A human should review AI suggestions before applying them.
"""

from __future__ import annotations

import json
import os

from .checks import Issue

DEFAULT_MODEL = os.environ.get("A11Y_MODEL", "claude-haiku-5-5")

PROMPT_TEMPLATE = """You are a web accessibility expert helping a university web team.
For each issue below, write:
  - "explanation": 1-2 plain-English sentences on who is affected and why it matters.
  - "fix": a short, concrete fix. Include a corrected HTML example when useful.

Do not invent new issues. Only explain the ones listed.
Respond with ONLY a JSON array, no other text, in this exact shape:
[{{"id": "<issue id>", "explanation": "...", "fix": "..."}}]

Issues:
{issues_json}
"""


def build_prompt(issues: list[Issue]) -> str:
    payload = [
        {"id": i.id, "rule": i.rule, "wcag": i.wcag, "element": i.element, "detail": i.detail}
        for i in issues
    ]
    return PROMPT_TEMPLATE.format(issues_json=json.dumps(payload, indent=2))


def parse_response(text: str) -> dict[str, dict]:
    """Parse the model's JSON array into {issue_id: {"explanation":..., "fix":...}}."""
    text = text.strip()
    # Some models wrap JSON in ```json fences; strip them if present.
    if text.startswith("```"):
        text = text.strip("`")
        text = text[text.find("["):]
    start, end = text.find("["), text.rfind("]")
    if start == -1 or end == -1:
        raise ValueError("No JSON array found in AI response")
    items = json.loads(text[start:end + 1])
    return {
        str(item["id"]): {"explanation": str(item.get("explanation", "")), "fix": str(item.get("fix", ""))}
        for item in items if isinstance(item, dict) and "id" in item
    }


def explain_issues(issues: list[Issue], model: str = DEFAULT_MODEL, max_issues: int = 25) -> str:
    """
    Add ai_explanation and ai_fix to each issue (in place).
    Returns a short status message for the user.
    """
    if not issues:
        return "No issues to explain."
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return "AI explanations skipped: ANTHROPIC_API_KEY is not set (see README)."

    try:
        import anthropic  # imported here so the tool works without the package installed
    except ImportError:
        return "AI explanations skipped: run 'pip install anthropic' first."

    batch = issues[:max_issues]  # limit cost on very large pages
    try:
        client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment
        message = client.messages.create(
            model=model,
            max_tokens=4000,
            messages=[{"role": "user", "content": build_prompt(batch)}],
        )
        text = "".join(block.text for block in message.content if getattr(block, "type", "") == "text")
        results = parse_response(text)
    except Exception as exc:  # network error, bad key, bad JSON, etc.
        return f"AI explanations skipped: {exc}"

    for issue in batch:
        if issue.id in results:
            issue.ai_explanation = results[issue.id]["explanation"]
            issue.ai_fix = results[issue.id]["fix"]
    note = f" (first {max_issues} issues only)" if len(issues) > max_issues else ""
    return f"AI explanations added for {sum(1 for i in batch if i.ai_explanation)} issues{note}."

"""
Builds a simple, accessible HTML report from the scan results.
(The report itself follows good practice: lang, title, headings, a real table.)
"""

from __future__ import annotations

import html
from datetime import datetime

from .checks import Issue


def build_html_report(source: str, page_title: str, issues: list[Issue], ai_status: str = "") -> str:
    counts = {s: sum(1 for i in issues if i.severity == s) for s in ("high", "medium", "low")}
    rows = []
    for issue in issues:
        ai_block = ""
        if issue.ai_explanation:
            ai_block = (
                f"<p><strong>Why it matters:</strong> {html.escape(issue.ai_explanation)}</p>"
                f"<p><strong>Suggested fix:</strong></p><pre>{html.escape(issue.ai_fix)}</pre>"
            )
        rows.append(
            "<tr>"
            f"<td class='sev {issue.severity}'>{issue.severity.title()}</td>"
            f"<td>{html.escape(issue.rule)}<br><small>WCAG {html.escape(issue.wcag)}</small></td>"
            f"<td><code>{html.escape(issue.element)}</code><p>{html.escape(issue.detail)}</p>{ai_block}</td>"
            "</tr>"
        )
    table = (
        "<table><caption>Issues found</caption>"
        "<thead><tr><th scope='col'>Severity</th><th scope='col'>Rule</th><th scope='col'>Details</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
        if issues else "<p>No issues found by the automated checks.</p>"
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Accessibility report: {html.escape(page_title)}</title>
<style>
  body {{ font-family: system-ui, Arial, sans-serif; max-width: 1000px; margin: 2rem auto; padding: 0 1rem; color: #1a1a1a; }}
  table {{ border-collapse: collapse; width: 100%; }}
  th, td {{ border: 1px solid #999; padding: .6rem; vertical-align: top; text-align: left; }}
  caption {{ text-align: left; font-weight: bold; margin-bottom: .5rem; }}
  code, pre {{ background: #f2f2f2; padding: .2rem .4rem; white-space: pre-wrap; word-break: break-word; }}
  .sev {{ font-weight: bold; }}
  .high {{ color: #8b0000; }} .medium {{ color: #7a4a00; }} .low {{ color: #1f4e79; }}
</style>
</head>
<body>
<h1>Accessibility report</h1>
<p><strong>Page:</strong> {html.escape(page_title)}<br>
<strong>Source:</strong> {html.escape(source)}<br>
<strong>Scanned:</strong> {datetime.now():%Y-%m-%d %H:%M}</p>
<h2>Summary</h2>
<ul>
  <li>{counts['high']} high</li><li>{counts['medium']} medium</li><li>{counts['low']} low</li>
</ul>
<p>{html.escape(ai_status)}</p>
<p><em>Automated checks find common problems only. A complete audit also needs manual
keyboard, screen reader and color-contrast testing. Review AI suggestions before applying them.</em></p>
<h2>Details</h2>
{table}
</body>
</html>
"""

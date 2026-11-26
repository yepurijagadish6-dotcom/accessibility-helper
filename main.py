"""
Command-line entry point.

Examples:
    python main.py sample/bad_page.html --no-ai
    python main.py https://www.example.edu --out report.html
    python main.py sample/bad_page.html --no-ai --save
"""

from __future__ import annotations

import argparse
import sys

from a11y_helper import db
from a11y_helper.ai_explainer import explain_issues
from a11y_helper.report import build_html_report
from a11y_helper.scanner import scan


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan a web page for common WCAG 2.1 issues.")
    parser.add_argument("source", help="A URL (https://...) or a path to a local .html file")
    parser.add_argument("--out", default="report.html", help="Where to save the HTML report (default: report.html)")
    parser.add_argument("--no-ai", action="store_true", help="Skip AI explanations (no API key needed)")
    parser.add_argument("--save", action="store_true", help="Save this scan to the history database")
    args = parser.parse_args()

    try:
        title, issues = scan(args.source)
    except Exception as exc:
        print(f"Could not scan {args.source}: {exc}")
        return 1

    print(f"Scanned: {title}")
    print(f"Found {len(issues)} issue(s)\n")
    for issue in issues:
        print(f"  [{issue.severity.upper():6}] {issue.rule}  (WCAG {issue.wcag})")

    ai_status = "AI explanations skipped (--no-ai)." if args.no_ai else explain_issues(issues)
    print(f"\n{ai_status}")

    with open(args.out, "w", encoding="utf-8") as f:
        f.write(build_html_report(args.source, title, issues, ai_status))
    print(f"Report saved to {args.out}")

    if args.save:
        conn = db.connect()
        scan_id = db.save_scan(conn, args.source, title, issues)
        print(f"Saved to database as scan #{scan_id} (see: python history.py list)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

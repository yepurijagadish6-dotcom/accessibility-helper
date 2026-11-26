"""
Stage 4: view scan history from the database.

Examples:
    python history.py list
    python history.py show 3
    python history.py top
    python history.py compare sample/bad_page.html
"""

from __future__ import annotations

import argparse
import sys

from a11y_helper import db


def main() -> int:
    parser = argparse.ArgumentParser(description="View saved accessibility scans.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="List recent scans")
    show = sub.add_parser("show", help="Show issues for one scan")
    show.add_argument("scan_id", type=int)
    sub.add_parser("top", help="Most common issues across all scans")
    cmp_ = sub.add_parser("compare", help="Compare the last two scans of a page")
    cmp_.add_argument("source")
    args = parser.parse_args()

    conn = db.connect()

    if args.command == "list":
        scans = db.list_scans(conn)
        if not scans:
            print("No scans saved yet. Run: python main.py <page> --save")
        for s in scans:
            print(f"#{s['id']:<4} {s['scanned_at']}  {s['issue_count']:>3} issues "
                  f"(H{s['high_count']}/M{s['medium_count']}/L{s['low_count']})  {s['source']}")

    elif args.command == "show":
        for i in db.get_scan_issues(conn, args.scan_id):
            print(f"[{i['severity'].upper():6}] {i['rule']} (WCAG {i['wcag']})\n         {i['element']}")

    elif args.command == "top":
        for r in db.summary_by_rule(conn):
            print(f"{r['occurrences']:>4}x  {r['rule']}  (WCAG {r['wcag']}, in {r['scans_affected']} scans)")

    elif args.command == "compare":
        result = db.compare_latest(conn, args.source)
        if result is None:
            print("Need at least two saved scans of this page to compare.")
            return 1
        print(f"Comparing scan #{result['older_scan']} -> #{result['newer_scan']}")
        print(f"  Fixed:     {len(result['fixed'])}")
        print(f"  New:       {len(result['new'])}")
        print(f"  Remaining: {len(result['remaining'])}")
        for rule, element in result["fixed"]:
            print(f"    FIXED: {rule}: {element}")
        for rule, element in result["new"]:
            print(f"    NEW:   {rule}: {element}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""
Stage 4: Database.

Saves every scan and its issues in a SQL database (SQLite, built into Python,
so there is nothing extra to install). This lets you track accessibility over
time: which issues were fixed, which are new, and which are still there.

Tables:
    scans  (one row per scan)
    issues (many rows per scan, linked by scan_id -> foreign key)

Everything here is plain SQL with parameterized queries (the ? placeholders),
which prevents SQL injection.
"""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime

from .checks import Issue

DEFAULT_DB = os.environ.get("A11Y_DB", "a11y_history.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS scans (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    source      TEXT    NOT NULL,
    page_title  TEXT,
    scanned_at  TEXT    NOT NULL,
    issue_count INTEGER NOT NULL,
    high_count  INTEGER NOT NULL,
    medium_count INTEGER NOT NULL,
    low_count   INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS issues (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_id        INTEGER NOT NULL REFERENCES scans(id) ON DELETE CASCADE,
    rule           TEXT NOT NULL,
    wcag           TEXT NOT NULL,
    severity       TEXT NOT NULL,
    element        TEXT NOT NULL,
    detail         TEXT NOT NULL,
    ai_explanation TEXT,
    ai_fix         TEXT
);

CREATE INDEX IF NOT EXISTS idx_scans_source ON scans(source);
CREATE INDEX IF NOT EXISTS idx_issues_scan  ON issues(scan_id);
"""


def connect(path: str = DEFAULT_DB) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row          # rows behave like dictionaries
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)               # creates tables the first time
    return conn


def save_scan(conn: sqlite3.Connection, source: str, page_title: str, issues: list[Issue]) -> int:
    """Insert one scan and all its issues in a single transaction. Returns the new scan id."""
    counts = {s: sum(1 for i in issues if i.severity == s) for s in ("high", "medium", "low")}
    with conn:  # commits on success, rolls back on error
        cur = conn.execute(
            "INSERT INTO scans (source, page_title, scanned_at, issue_count, high_count, medium_count, low_count) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (source, page_title, datetime.now().isoformat(timespec="seconds"),
             len(issues), counts["high"], counts["medium"], counts["low"]),
        )
        scan_id = cur.lastrowid
        conn.executemany(
            "INSERT INTO issues (scan_id, rule, wcag, severity, element, detail, ai_explanation, ai_fix) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [(scan_id, i.rule, i.wcag, i.severity, i.element, i.detail, i.ai_explanation, i.ai_fix) for i in issues],
        )
    return scan_id


def list_scans(conn: sqlite3.Connection, limit: int = 20) -> list[dict]:
    rows = conn.execute(
        "SELECT id, source, page_title, scanned_at, issue_count, high_count, medium_count, low_count "
        "FROM scans ORDER BY id DESC LIMIT ?", (limit,),
    ).fetchall()
    return [dict(r) for r in rows]


def get_scan_issues(conn: sqlite3.Connection, scan_id: int) -> list[dict]:
    rows = conn.execute(
        "SELECT rule, wcag, severity, element, detail, ai_explanation, ai_fix "
        "FROM issues WHERE scan_id = ? ORDER BY id", (scan_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def summary_by_rule(conn: sqlite3.Connection) -> list[dict]:
    """Which problems are most common across all scans? (GROUP BY example)"""
    rows = conn.execute(
        "SELECT rule, wcag, COUNT(*) AS occurrences, COUNT(DISTINCT scan_id) AS scans_affected "
        "FROM issues GROUP BY rule, wcag ORDER BY occurrences DESC"
    ).fetchall()
    return [dict(r) for r in rows]


def compare_latest(conn: sqlite3.Connection, source: str) -> dict | None:
    """
    Compare the two most recent scans of the same page.
    An issue is identified by (rule, element). Returns fixed / new / remaining lists.
    """
    scans = conn.execute(
        "SELECT id, scanned_at FROM scans WHERE source = ? ORDER BY id DESC LIMIT 2", (source,),
    ).fetchall()
    if len(scans) < 2:
        return None
    newer, older = scans[0]["id"], scans[1]["id"]

    def keys(scan_id: int) -> set[tuple[str, str]]:
        return {(r["rule"], r["element"]) for r in
                conn.execute("SELECT rule, element FROM issues WHERE scan_id = ?", (scan_id,))}

    old_set, new_set = keys(older), keys(newer)
    return {
        "older_scan": older, "newer_scan": newer,
        "fixed": sorted(old_set - new_set),
        "new": sorted(new_set - old_set),
        "remaining": sorted(old_set & new_set),
    }

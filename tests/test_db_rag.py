"""Tests for the database (Stage 4) and RAG retrieval (Stage 6)."""

from bs4 import BeautifulSoup

from a11y_helper import checks, db
from a11y_helper.rag import TfidfIndex, build_prompt, load_chunks


def make_issues(html: str):
    return checks.run_all_checks(BeautifulSoup(html, "html.parser"))


def test_save_and_list_scans(tmp_path):
    conn = db.connect(str(tmp_path / "test.db"))
    scan_id = db.save_scan(conn, "page.html", "Test", make_issues('<img src="a.png">'))
    scans = db.list_scans(conn)
    assert scans[0]["id"] == scan_id and scans[0]["issue_count"] >= 1
    assert any(i["rule"] == "Image missing alt attribute" for i in db.get_scan_issues(conn, scan_id))


def test_compare_detects_fixed_issue(tmp_path):
    conn = db.connect(str(tmp_path / "test.db"))
    db.save_scan(conn, "page.html", "v1", make_issues('<html lang="en"><title>T</title><img src="a.png"></html>'))
    db.save_scan(conn, "page.html", "v2", make_issues('<html lang="en"><title>T</title><img src="a.png" alt="Logo"></html>'))
    result = db.compare_latest(conn, "page.html")
    assert any(rule == "Image missing alt attribute" for rule, _ in result["fixed"])
    assert result["new"] == []


def test_summary_by_rule(tmp_path):
    conn = db.connect(str(tmp_path / "test.db"))
    db.save_scan(conn, "a.html", "A", make_issues('<img src="1.png"><img src="2.png">'))
    top = db.summary_by_rule(conn)
    img = next(r for r in top if r["rule"] == "Image missing alt attribute")
    assert img["occurrences"] == 2 and img["scans_affected"] == 1


def test_knowledge_base_chunks_load():
    chunks = load_chunks()
    assert len(chunks) >= 10
    assert any("1.1.1" in c.title for c in chunks)


def test_retrieval_finds_relevant_section():
    index = TfidfIndex(load_chunks())
    top_title = index.search("Do decorative images need alt text?")[0][0].title
    assert "1.1.1" in top_title
    assert "Contrast" in index.search("minimum contrast ratio for normal text")[0][0].title


def test_prompt_includes_passages_and_question():
    chunks = load_chunks()[:2]
    prompt = build_prompt("What is a VPAT?", chunks)
    assert "[1]" in prompt and "What is a VPAT?" in prompt and "ONLY" in prompt

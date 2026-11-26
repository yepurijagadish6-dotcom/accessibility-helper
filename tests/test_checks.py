"""Unit tests for the accessibility checks. Run with:  python -m pytest"""

import json

from bs4 import BeautifulSoup

from a11y_helper import checks
from a11y_helper.ai_explainer import build_prompt, parse_response


def soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def test_image_without_alt_is_flagged():
    assert len(checks.check_images_alt(soup('<img src="a.png">'))) == 1


def test_decorative_image_with_empty_alt_is_ok():
    assert checks.check_images_alt(soup('<img src="a.png" alt="">')) == []


def test_missing_lang_and_title():
    page = soup("<html><head></head><body></body></html>")
    assert checks.check_page_language(page)
    assert checks.check_page_title(page)


def test_good_lang_and_title_pass():
    page = soup('<html lang="en"><head><title>Home</title></head></html>')
    assert checks.check_page_language(page) == []
    assert checks.check_page_title(page) == []


def test_empty_and_vague_links():
    found = checks.check_links(soup('<a href="/x"></a><a href="/y">Click here</a><a href="/z">Contact us</a>'))
    rules = sorted(i.rule for i in found)
    assert rules == ["Link has no accessible name", "Vague link text"]


def test_link_with_image_alt_is_ok():
    assert checks.check_links(soup('<a href="/m"><img src="m.png" alt="Email us"></a>')) == []


def test_button_without_name_is_flagged():
    assert len(checks.check_buttons(soup("<button></button><button>Save</button>"))) == 1


def test_form_labels():
    html = '<label for="n">Name</label><input id="n"><input id="e"><input type="submit">'
    found = checks.check_form_labels(soup(html))
    assert len(found) == 1 and 'id="e"' in found[0].element


def test_heading_skip_and_missing_h1():
    rules = [i.rule for i in checks.check_heading_order(soup("<h2>A</h2><h4>B</h4>"))]
    assert "Page has no h1 heading" in rules and "Heading level skipped" in rules


def test_duplicate_ids():
    assert len(checks.check_duplicate_ids(soup('<div id="a"></div><p id="a"></p>'))) == 1


def test_sample_page_finds_expected_issues():
    with open("sample/bad_page.html", encoding="utf-8") as f:
        issues = checks.run_all_checks(soup(f.read()))
    assert len(issues) >= 9
    assert issues[0].severity == "high"  # most severe first


def test_prompt_contains_issue_ids():
    issue = checks.check_images_alt(soup('<img src="a.png">'))[0]
    assert issue.id in build_prompt([issue])


def test_parse_response_handles_code_fences():
    text = '```json\n' + json.dumps([{"id": "img-alt-1", "explanation": "e", "fix": "f"}]) + '\n```'
    assert parse_response(text) == {"img-alt-1": {"explanation": "e", "fix": "f"}}

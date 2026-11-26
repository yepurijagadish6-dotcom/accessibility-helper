"""
Loads a web page (from a URL or a local file) and runs the accessibility checks.
"""

from __future__ import annotations

from pathlib import Path

import requests
from bs4 import BeautifulSoup

from .checks import Issue, run_all_checks

USER_AGENT = "AccessibilityHelper/1.0 (educational WCAG checker)"


def load_html(source: str, timeout: int = 15) -> str:
    """Return the HTML for a URL (http/https) or a path to a local .html file."""
    if source.startswith(("http://", "https://")):
        response = requests.get(source, headers={"User-Agent": USER_AGENT}, timeout=timeout)
        response.raise_for_status()  # stop with a clear error on 404, 500, etc.
        return response.text
    path = Path(source)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {source}")
    return path.read_text(encoding="utf-8", errors="replace")


def scan(source: str) -> tuple[str, list[Issue]]:
    """Scan a page and return (page_title, issues)."""
    html = load_html(source)
    soup = BeautifulSoup(html, "html.parser")
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else "(no title)"
    return title, run_all_checks(soup)

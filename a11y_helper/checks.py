"""
Accessibility checks.

Each check looks at the parsed HTML (a BeautifulSoup object) and returns a list
of Issue objects. Every issue is tied to a WCAG 2.1 success criterion so the
report can tell people *which rule* was broken and *where*.

These are automated checks, so they catch common problems only. A full audit
still needs manual testing (keyboard, screen reader, color contrast, etc.).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from bs4 import BeautifulSoup, Tag

# Link text that tells the user nothing about where the link goes.
VAGUE_LINK_TEXT = {"click here", "here", "read more", "more", "learn more", "link", "this"}


@dataclass
class Issue:
    """One accessibility problem found on the page."""
    id: str                 # short unique id, e.g. "img-alt-3"
    rule: str               # what we checked, e.g. "Image missing alt text"
    wcag: str               # WCAG success criterion, e.g. "1.1.1 Non-text Content"
    severity: str           # "high", "medium" or "low"
    element: str            # a short snippet of the offending HTML
    detail: str             # plain explanation of what we found
    ai_explanation: str = ""  # filled in later by the AI explainer (optional)
    ai_fix: str = ""          # filled in later by the AI explainer (optional)
    extra: dict = field(default_factory=dict)


def _snippet(tag: Tag, limit: int = 160) -> str:
    """Return a short, single-line version of an element's HTML for the report."""
    text = " ".join(str(tag).split())
    return text if len(text) <= limit else text[:limit] + "..."


def _visible_text(tag: Tag) -> str:
    return " ".join(tag.get_text(" ", strip=True).split())


def check_images_alt(soup: BeautifulSoup) -> list[Issue]:
    """WCAG 1.1.1: every <img> needs an alt attribute (alt="" is OK for decorative images)."""
    issues = []
    for i, img in enumerate(soup.find_all("img"), start=1):
        if not img.has_attr("alt"):
            issues.append(Issue(
                id=f"img-alt-{i}", rule="Image missing alt attribute",
                wcag="1.1.1 Non-text Content", severity="high",
                element=_snippet(img),
                detail="This image has no alt attribute, so screen reader users get no description of it.",
            ))
    return issues


def check_page_language(soup: BeautifulSoup) -> list[Issue]:
    """WCAG 3.1.1: the <html> element should declare the page language."""
    html = soup.find("html")
    if html is None or not html.get("lang", "").strip():
        return [Issue(
            id="html-lang", rule="Page language not set",
            wcag="3.1.1 Language of Page", severity="medium",
            element="<html>",
            detail='The <html> element has no lang attribute (for example lang="en"), so screen readers may use the wrong pronunciation.',
        )]
    return []


def check_page_title(soup: BeautifulSoup) -> list[Issue]:
    """WCAG 2.4.2: every page needs a descriptive <title>."""
    title = soup.find("title")
    if title is None or not title.get_text(strip=True):
        return [Issue(
            id="page-title", rule="Page title missing",
            wcag="2.4.2 Page Titled", severity="medium",
            element="<title>",
            detail="The page has no title, so users cannot tell which page or tab they are on.",
        )]
    return []


def check_links(soup: BeautifulSoup) -> list[Issue]:
    """WCAG 2.4.4: links need text that describes their purpose."""
    issues = []
    for i, a in enumerate(soup.find_all("a", href=True), start=1):
        text = _visible_text(a)
        label = a.get("aria-label", "").strip()
        img_alts = " ".join(img.get("alt", "") for img in a.find_all("img")).strip()
        name = text or label or img_alts
        if not name:
            issues.append(Issue(
                id=f"link-empty-{i}", rule="Link has no accessible name",
                wcag="2.4.4 Link Purpose (In Context)", severity="high",
                element=_snippet(a),
                detail="This link has no text, aria-label or image alt text, so screen readers announce it only as 'link'.",
            ))
        elif name.lower() in VAGUE_LINK_TEXT:
            issues.append(Issue(
                id=f"link-vague-{i}", rule="Vague link text",
                wcag="2.4.4 Link Purpose (In Context)", severity="low",
                element=_snippet(a),
                detail=f'The link text "{name}" does not say where the link goes when read on its own.',
            ))
    return issues


def check_buttons(soup: BeautifulSoup) -> list[Issue]:
    """WCAG 4.1.2: buttons need an accessible name."""
    issues = []
    for i, btn in enumerate(soup.find_all("button"), start=1):
        name = _visible_text(btn) or btn.get("aria-label", "").strip() or btn.get("title", "").strip()
        if not name:
            issues.append(Issue(
                id=f"button-empty-{i}", rule="Button has no accessible name",
                wcag="4.1.2 Name, Role, Value", severity="high",
                element=_snippet(btn),
                detail="This button has no text or aria-label, so screen reader users cannot tell what it does.",
            ))
    return issues


def check_form_labels(soup: BeautifulSoup) -> list[Issue]:
    """WCAG 1.3.1 / 3.3.2: form fields need a label."""
    issues = []
    label_targets = {lab.get("for") for lab in soup.find_all("label") if lab.get("for")}
    skip_types = {"hidden", "submit", "button", "reset", "image"}
    fields = soup.find_all(["input", "select", "textarea"])
    for i, fld in enumerate(fields, start=1):
        if fld.name == "input" and fld.get("type", "text").lower() in skip_types:
            continue
        has_label = (
            (fld.get("id") and fld.get("id") in label_targets)
            or fld.find_parent("label") is not None
            or fld.get("aria-label", "").strip()
            or fld.get("aria-labelledby", "").strip()
        )
        if not has_label:
            issues.append(Issue(
                id=f"form-label-{i}", rule="Form field missing label",
                wcag="3.3.2 Labels or Instructions", severity="high",
                element=_snippet(fld),
                detail="This form field has no label, so users may not know what to enter.",
            ))
    return issues


def check_heading_order(soup: BeautifulSoup) -> list[Issue]:
    """WCAG 1.3.1: headings should not skip levels (for example h2 straight to h4)."""
    issues = []
    headings = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
    if headings and not soup.find("h1"):
        issues.append(Issue(
            id="heading-no-h1", rule="Page has no h1 heading",
            wcag="1.3.1 Info and Relationships", severity="low",
            element=_snippet(headings[0]),
            detail="The page has headings but no main <h1>, which makes the structure harder to navigate.",
        ))
    previous = 0
    for i, h in enumerate(headings, start=1):
        level = int(h.name[1])
        if previous and level > previous + 1:
            issues.append(Issue(
                id=f"heading-skip-{i}", rule="Heading level skipped",
                wcag="1.3.1 Info and Relationships", severity="medium",
                element=_snippet(h),
                detail=f"This heading jumps from h{previous} to h{level}. Screen reader users navigate by headings, so skipped levels are confusing.",
            ))
        previous = level
    return issues


def check_duplicate_ids(soup: BeautifulSoup) -> list[Issue]:
    """WCAG 4.1.1: id values should be unique (labels and ARIA depend on them)."""
    seen: dict[str, int] = {}
    for tag in soup.find_all(id=True):
        seen[tag["id"]] = seen.get(tag["id"], 0) + 1
    return [
        Issue(
            id=f"dup-id-{n}", rule="Duplicate id attribute",
            wcag="4.1.1 Parsing", severity="low",
            element=f'id="{dup}"',
            detail=f'The id "{dup}" is used {count} times. Labels and ARIA references may point to the wrong element.',
        )
        for n, (dup, count) in enumerate(((k, v) for k, v in seen.items() if v > 1), start=1)
    ]


ALL_CHECKS = [
    check_page_language,
    check_page_title,
    check_images_alt,
    check_links,
    check_buttons,
    check_form_labels,
    check_heading_order,
    check_duplicate_ids,
]


def run_all_checks(soup: BeautifulSoup) -> list[Issue]:
    """Run every check and return all issues, most severe first."""
    issues: list[Issue] = []
    for check in ALL_CHECKS:
        issues.extend(check(soup))
    order = {"high": 0, "medium": 1, "low": 2}
    return sorted(issues, key=lambda iss: order.get(iss.severity, 3))

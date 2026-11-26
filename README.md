# Accessibility Helper

A Python tool that scans web pages for common **WCAG 2.1** accessibility problems and
uses an AI model (Anthropic Claude) to explain each problem in plain English and suggest a fix.

**Features**
- Rule-based WCAG checks with an accessible HTML report
- AI explanations and fixes (Claude API) with safe fallback
- **Scan history in a SQL database**: compare scans to see what was fixed
- **"Ask WCAG"**: a RAG (retrieval-augmented generation) assistant that answers accessibility questions from a knowledge base and cites its sources
- REST API (FastAPI), Docker image, and GitHub Actions CI running 22 tests

## What it checks

| Check | WCAG criterion |
|---|---|
| Images missing `alt` | 1.1.1 Non-text Content |
| Page language (`<html lang>`) missing | 3.1.1 Language of Page |
| Page `<title>` missing | 2.4.2 Page Titled |
| Links with no name, or vague text ("click here") | 2.4.4 Link Purpose |
| Buttons with no accessible name | 4.1.2 Name, Role, Value |
| Form fields without labels | 3.3.2 Labels or Instructions |
| Skipped heading levels / no `<h1>` | 1.3.1 Info and Relationships |
| Duplicate `id` values | 4.1.1 Parsing |

> Automated checks catch common issues only. A full audit still needs manual keyboard,
> screen reader and color-contrast testing.

## How it works

```
URL or file ──> scanner.py ──> checks.py (rule-based WCAG checks)
                                   │
                                   ▼
                          ai_explainer.py (Claude explains each issue + suggests a fix)
                                   │
                                   ▼
                  report.py (accessible HTML report)  /  api.py (JSON via FastAPI)
```

The **checks are plain code**, so results are reliable and repeatable. The **AI only explains**
issues that the code already found. If the AI call fails, the tool still works.

## Setup (Windows)

1. Install **Python 3.10+** from python.org (tick "Add Python to PATH" during install).
2. Open **Command Prompt** in this folder and run:

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

(On Mac/Linux use `source .venv/bin/activate`.)

## Run it

**Without AI (no key needed):**
```
python main.py sample/bad_page.html --no-ai
```

**On a real page:**
```
python main.py https://www.example.edu --no-ai --out report.html
```
Open `report.html` in your browser.

**With AI explanations:**
1. Create an API key in the Anthropic Console (console.anthropic.com). Usage costs a small amount per request.
2. Set it for your current Command Prompt window:
```
set ANTHROPIC_API_KEY=your-key-here
python main.py sample/bad_page.html
```
Never put your key in the code or commit it to GitHub.

## Scan history (database)

```
python main.py sample/bad_page.html --no-ai --save
python history.py list            # recent scans
python history.py show 1          # issues in scan #1
python history.py top             # most common issues across all scans
python history.py compare sample/bad_page.html   # fixed / new / remaining since last scan
```
Data is stored in `a11y_history.db` (SQLite). Fix something in a page, scan it again with
`--save`, then run `compare` to see what was fixed.

## Ask WCAG (RAG)

```
python ask.py "Do decorative images need alt text?"
python ask.py "What is a VPAT?"
```
Steps: load `knowledge/wcag_notes.md` -> split into chunks -> find the most relevant chunks
(TF-IDF similarity) -> Claude answers using only those chunks and cites them. Without an API
key it shows the retrieved passages. Next improvement: replace TF-IDF with vector embeddings.

## REST API

```
uvicorn api:app --reload
```
Open http://127.0.0.1:8000/docs and try:
- `GET /scan?url=https://www.example.edu&ai=false&save=true`
- `GET /scans` and `GET /scans/1`
- `GET /ask?q=What is a VPAT?`

## Docker

```
docker build -t accessibility-helper .
docker run -p 8000:8000 accessibility-helper
```
Then open http://127.0.0.1:8000/docs. To use AI, add `-e ANTHROPIC_API_KEY=your-key`.

## Continuous integration

`.github/workflows/tests.yml` runs all tests automatically on GitHub for every push.

## Tests

```
python -m pytest
```

## Project structure

```
a11y_helper/
  checks.py        WCAG checks (one function per rule)
  scanner.py       loads a URL or file and runs the checks
  ai_explainer.py  builds the prompt, calls Claude, parses JSON, falls back safely
  report.py        builds the accessible HTML report
  db.py            SQLite database: save scans, history, compare, GROUP BY summary
  rag.py           RAG: chunking, TF-IDF retrieval, grounded answers with sources
knowledge/         WCAG notes used by Ask WCAG
main.py            command-line scanner (--save stores results)
history.py         view and compare saved scans
ask.py             ask accessibility questions (RAG)
api.py             FastAPI web API
Dockerfile         container image for the API
.github/workflows  CI: runs the tests on every push
tests/             pytest unit tests
sample/            a deliberately broken page for testing
```

## Ideas for future improvements

- Color contrast checking (WCAG 1.4.3)
- Scan several pages from a sitemap
- Vector embeddings and a vector database for Ask WCAG
- A small web dashboard showing trends from the database

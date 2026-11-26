# Your Learning Guide: Accessibility Helper

This guide is for you, Jagadish. Follow it step by step. The goal is not only to have the
project, but to **understand every part** so you can talk about it confidently in interviews.

---

## The plan (4 weekends, ~3-4 hours each)

### Weekend 1: Run it and understand the checks
1. Install Python, set up the virtual environment, install requirements (see README).
2. Run `python main.py sample/bad_page.html --no-ai` and open `report.html`.
3. Run `python -m pytest` and see all tests pass.
4. Open `a11y_helper/checks.py`. Read one check at a time. For each one, ask:
   *What rule is this? How does the code find the problem?*
5. **Do it yourself:** scan 3 real pages (for example usca.edu pages you manage) with `--no-ai`.
   Compare the results with what you know from your manual WCAG audits.
6. Create a **GitHub repository** and push the project (steps below).

**After Weekend 1 you can honestly add to your resume:** *(in progress)*

### Weekend 2: Add the AI part
1. Create an Anthropic API key and add a few dollars of credit.
2. Run with AI on the sample page. Read the explanations in the report.
3. Open `ai_explainer.py`. Understand: the prompt, why we ask for JSON, why we validate it,
   and the fallback when something fails.
4. **Do it yourself:** improve the prompt (for example, ask for the fix to mention the WCAG
   criterion). Run again and compare. Note what changed. This is "prompt engineering".
5. **Do it yourself:** add one new check on your own, for example `<iframe>` without a
   `title` attribute (WCAG 4.1.2). Write a test for it in `tests/test_checks.py`.

### Weekend 3: Database, API, Docker and CI (Stages 4-5)
1. Run `python main.py sample/bad_page.html --no-ai --save`, then `python history.py list`.
2. Fix one issue in `sample/bad_page.html` (for example add alt text), scan again with `--save`,
   then run `python history.py compare sample/bad_page.html`. You just tracked a fix over time.
3. Open `a11y_helper/db.py` and read the SQL: CREATE TABLE, INSERT, SELECT, GROUP BY, the
   foreign key, and the `?` placeholders (they prevent SQL injection).
4. Run `uvicorn api:app --reload` and try every endpoint at http://127.0.0.1:8000/docs.
5. Push to GitHub and open the **Actions** tab: the tests run automatically (that's CI).
6. Optional: install Docker Desktop and run the image (see README).

### Weekend 4: RAG "Ask WCAG" (Stage 6)
1. Run `python ask.py "Do decorative images need alt text?"` (first without a key, then with).
2. Open `a11y_helper/rag.py` and follow the 4 steps: load, chunk, retrieve, generate.
3. **Do it yourself:** add a new section to `knowledge/wcag_notes.md` (for example 2.4.1 Bypass
   Blocks / skip links) and check that `ask.py` finds it.
4. Ask a question the notes can't answer. The model should say it doesn't know. That's
   "grounding", and it's a great interview point.
5. Remove "(in progress)" from your resume and add the GitHub link.

---

## Pushing to GitHub

1. Create a free account at github.com (if you don't have one).
2. Click **New repository**, name it `accessibility-helper`, keep it **Public**, don't add a README.
3. In Command Prompt, in the project folder:
```
git init
git add .
git commit -m "Initial version of Accessibility Helper"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/accessibility-helper.git
git push -u origin main
```
4. Check that `.env` and your API key are **not** on GitHub (the `.gitignore` file prevents this).

---

## How each part works (in simple words)

**checks.py**: Uses BeautifulSoup to read the HTML like a tree. Each function looks for one
problem. Example: `check_images_alt` finds every `<img>` and flags the ones with no `alt`.
Each problem becomes an `Issue` with the WCAG rule, severity and a small HTML snippet.

**scanner.py**: Gets the HTML from a URL (using `requests`) or a local file, then runs all checks.
`raise_for_status()` stops with a clear error if the page returns 404 or 500.

**ai_explainer.py**: Sends only the small snippets (not the whole page) to Claude with
instructions to return JSON. The code parses the JSON and attaches an explanation and a fix
to each issue. If the key is missing, the network fails, or the JSON is bad, the tool still
works and just skips the AI part.

**report.py**: Builds an HTML report. The report itself is accessible: it has `lang`, a
`<title>`, proper headings, and a table with `<caption>` and `scope` on headers.

**api.py**: A FastAPI app with `/health` and `/scan`. FastAPI generates interactive docs automatically.

---

## Interview talking points (practice these out loud)

**"Tell me about a project you built."**
> "I built an Accessibility Helper in Python. It scans a web page for common WCAG 2.1 issues,
> like missing alt text, unlabeled form fields, and skipped headings, and then uses the Claude
> API to explain each issue in plain English and suggest a fix. I built it because I do WCAG
> audits at USC Aiken, and I wanted a faster way to explain issues to non-technical content owners."

**"How did you use AI in it?"**
> "The detection is rule-based code, so it's reliable and repeatable. The AI only explains issues
> the code already found, so it can't invent problems. I send small HTML snippets, ask for JSON,
> validate it, and if the AI call fails, the tool falls back gracefully. And I treat AI fixes as
> suggestions that a person reviews."

**"How do you store and track results?"**
> "Each scan is saved in a SQL database: a scans table and an issues table linked by a foreign
> key. I can compare the last two scans of a page to see which issues were fixed, which are new,
> and which remain, and a GROUP BY query shows the most common problems across all pages."

**"Have you worked with RAG?"**
> "Yes, in this project. 'Ask WCAG' splits a knowledge base into chunks, retrieves the most
> relevant ones for a question, and has Claude answer only from those passages with citations.
> If the answer isn't in the passages, it says it doesn't know. I used TF-IDF for retrieval so
> it runs offline; the next step would be vector embeddings."

**"How do you deploy and test it?"**
> "There's a Dockerfile for the API, and a GitHub Actions workflow runs 22 pytest tests on every push."

**"Did you write all of it yourself?"** (answer honestly)
> "I built it with Claude as an AI coding assistant, which is how I like to work. I made sure I
> understand every part, extended it myself (for example, I added [your own check/notes]), and
> I can walk you through any file."

**"What would you improve?"**
> "Color-contrast checks, scanning a whole site from a sitemap, vector embeddings for the RAG
> part, and a small dashboard on top of the database."

**"What was hard?"**
> Answer this from YOUR real experience after you build it. For example, getting reliable JSON
> back from the model, or handling links that contain only an image.

---

## What to put on your resume

**After Weekend 1 (honest, in progress):**
> **Accessibility Helper** (personal project, in progress): Python tool that scans web pages for
> common WCAG 2.1 issues and generates an accessible HTML report; adding AI-generated
> plain-language remediation guidance using the Claude API.

**After Weekend 4 (finished):**
> **Accessibility Helper** (github.com/your-username/accessibility-helper): Python tool that scans
> web pages for common WCAG 2.1 issues and uses the Claude API to generate plain-language fixes;
> stores scan history in a SQL database to track fixes over time; includes a RAG assistant that
> answers accessibility questions from a knowledge base with citations; FastAPI REST API, Docker,
> and GitHub Actions CI running 22 pytest tests.

**Only list what you have actually done and understand.**

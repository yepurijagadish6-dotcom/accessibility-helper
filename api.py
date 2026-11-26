"""
Optional REST API (Weekend 3).

Run:   uvicorn api:app --reload
Then open http://127.0.0.1:8000/docs to try it in the browser.

Endpoints:
    GET /health                      -> {"status": "ok"}
    GET /scan?url=https://...&ai=false&save=false -> JSON list of issues
    GET /scans                       -> recent saved scans
    GET /scans/{scan_id}             -> issues for one saved scan
    GET /ask?q=...                   -> RAG answer about WCAG with sources
"""

from __future__ import annotations

from dataclasses import asdict

from fastapi import FastAPI, HTTPException, Query

from a11y_helper import db
from a11y_helper.ai_explainer import explain_issues
from a11y_helper.rag import ask as rag_ask
from a11y_helper.scanner import scan

app = FastAPI(title="Accessibility Helper API", version="1.0")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/scan")
def scan_page(url: str = Query(..., description="Page to scan (http or https)"),
              ai: bool = Query(False, description="Add AI explanations"),
              save: bool = Query(False, description="Save the scan to the history database")) -> dict:
    if not url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="url must start with http:// or https://")
    try:
        title, issues = scan(url)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Could not load page: {exc}")
    ai_status = explain_issues(issues) if ai else "AI explanations not requested."
    scan_id = db.save_scan(db.connect(), url, title, issues) if save else None
    return {
        "scan_id": scan_id,
        "page_title": title,
        "issue_count": len(issues),
        "ai_status": ai_status,
        "issues": [asdict(i) for i in issues],
    }


@app.get("/scans")
def recent_scans(limit: int = 20) -> list[dict]:
    return db.list_scans(db.connect(), limit=limit)


@app.get("/scans/{scan_id}")
def scan_details(scan_id: int) -> dict:
    issues = db.get_scan_issues(db.connect(), scan_id)
    if not issues:
        raise HTTPException(status_code=404, detail="Scan not found or has no issues")
    return {"scan_id": scan_id, "issues": issues}


@app.get("/ask")
def ask_wcag(q: str = Query(..., min_length=3, description="Your accessibility question")) -> dict:
    return rag_ask(q)

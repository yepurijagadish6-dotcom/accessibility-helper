"""API tests using FastAPI's TestClient (no server needed)."""

from fastapi.testclient import TestClient

import api

client = TestClient(api.app)


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_scan_rejects_non_http_url():
    assert client.get("/scan", params={"url": "ftp://example.com"}).status_code == 400


def test_ask_returns_sources():
    data = client.get("/ask", params={"q": "What is a VPAT?"}).json()
    assert data["sources"] and "VPAT" in data["sources"][0]["title"]

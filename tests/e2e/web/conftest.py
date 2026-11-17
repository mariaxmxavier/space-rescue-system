"""Shared fixtures for browser journeys against the local static app."""

from __future__ import annotations

import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest
from playwright.sync_api import Page


WEB_ROOT = Path(__file__).resolve().parents[3] / "web"


@pytest.fixture(scope="session")
def web_origin():
    """Serve the feature's static files at an ephemeral loopback port."""

    handler = partial(SimpleHTTPRequestHandler, directory=str(WEB_ROOT))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        yield f"http://{host}:{port}"
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()


@pytest.fixture
def workspace_page(page: Page, web_origin: str):
    """Open the browser app; API calls are intercepted per test."""

    page.goto(web_origin)
    yield page

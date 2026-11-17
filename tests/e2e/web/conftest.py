"""Shared fixtures for browser journeys against the local static app."""

from __future__ import annotations

import socket
import threading
import time
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest
import uvicorn
from playwright.sync_api import Page

from rescue.api.app import create_app

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

    page.goto(f"{web_origin}/?workspace=manual")
    yield page


@pytest.fixture(scope="session")
def live_api_origin(web_origin):
    """Serve the real JSON API for browser integration with explicit local CORS."""
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen()
        port = listener.getsockname()[1]
        server = uvicorn.Server(
            uvicorn.Config(create_app(allowed_origins=(web_origin,)), log_level="error")
        )
        thread = threading.Thread(target=server.run, kwargs={"sockets": [listener]}, daemon=True)
        thread.start()
        deadline = time.monotonic() + 10
        while not server.started and thread.is_alive() and time.monotonic() < deadline:
            time.sleep(0.01)
        if not server.started:
            server.should_exit = True
            thread.join(timeout=5)
            raise RuntimeError("local browser-test API did not start")
        try:
            yield f"http://127.0.0.1:{port}"
        finally:
            server.should_exit = True
            thread.join(timeout=10)


@pytest.fixture
def live_workspace_page(page: Page, web_origin, live_api_origin):
    """Open advanced browser workflows backed by real operations rather than route mocks."""
    page.goto(f"{web_origin}/?workspace=manual&api={live_api_origin}")
    return page


@pytest.fixture
def real_viewer_page(page: Page, web_origin, live_api_origin):
    """Open the default viewer against real bounded case execution."""
    page.goto(f"{web_origin}/?api={live_api_origin}")
    return page

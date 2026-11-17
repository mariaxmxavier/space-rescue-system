"""Start the local rescue API and simulation viewer with one command."""

from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

import uvicorn

from rescue.api.app import create_app


def main() -> None:
    """Serve the browser on port 8001 and its API on port 8000 until interrupted."""
    origin = "http://127.0.0.1:8001"
    handler = partial(SimpleHTTPRequestHandler, directory=str(Path(__file__).parent / "web"))
    with ThreadingHTTPServer(("127.0.0.1", 8001), handler) as web:
        thread = Thread(target=web.serve_forever, daemon=True)
        thread.start()
        print(f"Simulation viewer: {origin}", flush=True)
        try:
            uvicorn.run(create_app(allowed_origins=(origin,)), host="127.0.0.1", port=8000)
        finally:
            web.shutdown()
            thread.join()


if __name__ == "__main__":
    main()

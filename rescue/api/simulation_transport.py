"""Connect simulation clients to the public JSON API without a second server."""

import asyncio

import httpx


class SimulationTransport(httpx.BaseTransport):
    """Dispatch synchronous simulator requests through ASGI when preparing a case.

    The outer case endpoint runs in a worker thread. Each operation still traverses
    the API's codec, origin checks, registry and history, using its JSON contract.
    """

    def __init__(self, app):
        """Retain the owning API application for isolated in-process HTTP calls."""
        self.app = app

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        """Run one API exchange and fully buffer its response before closing the loop."""

        async def exchange():
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=self.app), base_url="http://simulation.internal"
            ) as client:
                response = await client.request(
                    request.method,
                    str(request.url),
                    headers=request.headers,
                    content=request.read(),
                )
                return httpx.Response(
                    response.status_code,
                    headers=response.headers,
                    content=await response.aread(),
                    request=request,
                )

        return asyncio.run(exchange())

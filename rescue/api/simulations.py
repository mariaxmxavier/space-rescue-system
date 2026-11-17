"""Register browser-facing case preparation over the real rescue operation API."""

from uuid import uuid4

import httpx
from fastapi.responses import JSONResponse

from rescue.api.simulation_transport import SimulationTransport


def register_simulations(app):
    """Expose the bounded case catalogue and fresh execution when composing the API."""

    @app.get("/simulations/cases")
    def list_cases():
        """Read built-in cases without creating or mutating any rescue run."""
        from simulations.entrypoints.viewer import catalogue

        return {"cases": catalogue()}

    @app.post("/simulations/cases/{case_id}/runs")
    def prepare_case(case_id: str):
        """Prepare authoritative playback frames in a worker thread on case selection."""
        from simulations.adapters.http.mission_api import HttpMissionApi
        from simulations.entrypoints.viewer import catalogue, execute_case

        if case_id not in {case["id"] for case in catalogue()}:
            return JSONResponse({"detail": "unknown simulation case"}, status_code=404)
        namespace = f"sim-{case_id}-{uuid4().hex}"
        with httpx.Client(
            transport=SimulationTransport(app),
            base_url="http://simulation.internal",
            timeout=httpx.Timeout(10, connect=2, pool=2),
            trust_env=False,
        ) as client:
            return execute_case(case_id, HttpMissionApi(client), namespace)

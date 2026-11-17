"""FastAPI entrypoint for isolated local rescue runs."""

from __future__ import annotations

import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from rescue.api.codec import PayloadError, from_json_value, to_json_value
from rescue.api.operations import OPERATIONS
from rescue.api.origins import origin_is_allowed
from rescue.api.runtime import RunRegistry
from rescue.api.state import read_run_state
from rescue.experiments.models import RescueScenario
from rescue.mobilisation.models import MobilisationPolicy


def create_app(allowed_origins: tuple[str, ...] | None = None) -> FastAPI:
    """Build an isolated API app and its in-memory run registry."""
    if allowed_origins is None:
        allowed_origins = tuple(
            origin.strip()
            for origin in os.environ.get("SPACE_RESCUE_ALLOWED_ORIGINS", "").split(",")
            if origin.strip()
        )
    app = FastAPI(title="Space Rescue API")
    registry = RunRegistry()
    app.state.run_registry = registry
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(allowed_origins),
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    @app.middleware("http")
    async def check_origin(request: Request, call_next):
        if request.method not in {"GET", "HEAD", "OPTIONS"} and not origin_is_allowed(
            request.headers.get("origin"), allowed_origins
        ):
            return JSONResponse({"detail": "origin is not allowed"}, status_code=403)
        return await call_next(request)

    @app.post("/runs", status_code=201)
    async def create_run(request: Request):
        try:
            try:
                payload = await request.json()
            except ValueError:
                return JSONResponse({"detail": "malformed JSON"}, status_code=400)
            if not isinstance(payload, dict) or set(payload) - {
                "application_run_id",
                "central_id",
                "policies",
                "scenarios",
            }:
                raise PayloadError("run fields do not match the contract")
            policies = tuple(
                from_json_value(item, MobilisationPolicy) for item in payload.get("policies", ())
            )
            scenarios = tuple(
                from_json_value(item, RescueScenario) for item in payload.get("scenarios", ())
            )
            record = registry.create(
                payload["application_run_id"],
                payload["central_id"],
                policies=policies,
                scenarios=scenarios,
            )
            return {
                "application_run_id": record.context.application_run_id,
                "central_id": record.context.central_id,
            }
        except KeyError as error:
            return JSONResponse({"detail": f"missing field: {error.args[0]}"}, status_code=400)
        except PayloadError as error:
            return JSONResponse({"detail": str(error)}, status_code=400)
        except ValueError as error:
            status = 409 if "already exists" in str(error) else 400
            return JSONResponse({"detail": str(error)}, status_code=status)
        except (TypeError, KeyError) as error:
            return JSONResponse({"detail": str(error)}, status_code=400)

    @app.post("/runs/{run_id}/operations/{operation}")
    async def invoke(run_id: str, operation: str, request: Request):
        record = registry.get(run_id)
        if record is None:
            return JSONResponse({"detail": "unknown run"}, status_code=404)
        async with _async_lock(record):
            try:
                payload = await request.json()
            except ValueError:
                response, status = {"detail": "malformed JSON"}, 400
                record.append(request.method, request.url.path, None, status, response)
                return JSONResponse(response, status_code=status)
            descriptor = OPERATIONS.get(operation)
            if descriptor is None:
                response, status = {"detail": "unknown operation"}, 404
            else:
                try:
                    args = _arguments(payload, descriptor)
                    result = getattr(record.context.central, descriptor.method)(*args)
                    response, status = to_json_value(result), 200
                except (PayloadError, ValueError, TypeError, KeyError) as error:
                    response, status = {"detail": str(error)}, 400
            record.append(request.method, request.url.path, payload, status, response)
            return JSONResponse(response, status_code=status)

    @app.get("/runs/{run_id}/state")
    async def read_state(run_id: str, request: Request):
        record = registry.get(run_id)
        if record is None:
            return JSONResponse({"detail": "unknown run"}, status_code=404)
        async with _async_lock(record):
            state = read_run_state(record.context.store)
            response = to_json_value(state)
            record.append("GET", request.url.path, None, 200, response)
            return JSONResponse(response)

    @app.get("/runs/{run_id}/history")
    async def read_history(run_id: str, request: Request):
        record = registry.get(run_id)
        if record is None:
            return JSONResponse({"detail": "unknown run"}, status_code=404)
        async with _async_lock(record):
            response = to_json_value(tuple(record.history))
            record.append("GET", request.url.path, None, 200, response)
            return JSONResponse(response)

    return app


class _async_lock:
    """Async-compatible context manager over a record's re-entrant lock."""

    def __init__(self, record):
        self.lock = record.lock

    async def __aenter__(self):
        self.lock.acquire()

    async def __aexit__(self, *_):
        self.lock.release()


def _arguments(payload: object, descriptor) -> tuple[object, ...]:
    if not isinstance(payload, dict):
        raise PayloadError("request body must be an object")
    if descriptor.command is not None:
        if set(payload) != {"command"}:
            raise PayloadError("expected only the command field")
        return (from_json_value(payload["command"], descriptor.command),)
    if set(payload) != set(descriptor.scalar_arguments):
        raise PayloadError("operation arguments do not match the contract")
    return tuple(
        from_json_value(payload[key], expected)
        for key, expected in zip(descriptor.scalar_arguments, descriptor.scalar_types, strict=True)
    )

"""Local HTTP entrypoint for the rescue application."""

from rescue.api.app import create_app

__all__ = ["create_app"]

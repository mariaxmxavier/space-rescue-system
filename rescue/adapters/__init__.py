"""Ports and adapters: the only doors between the rescue system and the outside world.

What: ``ports/`` holds the abstract capabilities the application needs (state store, clock,
ID source); ``memory/`` holds the in-memory implementations of those ports.

When: ports are imported by ``rescue.application`` at import time; adapters are built once per
run by the composition root, ``rescue.bootstrap.new_run``.

Why: the business rules must not depend on how state is kept, how time is read or how IDs are
made. Keeping those details behind ports lets a different store, clock or ID scheme replace the
in-memory one without touching a rule (clean architecture: dependencies point inwards).
"""

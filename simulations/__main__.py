"""Delegate module execution to the simulation CLI without import-time I/O."""

from simulations.entrypoints.cli import main

if __name__ == "__main__":
    raise SystemExit(main())

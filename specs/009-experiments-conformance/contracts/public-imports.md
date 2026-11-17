# Contract: public import paths

Each package `__init__.py` re-exports these names in `__all__`. The architecture test
`tests/architecture/experiments_layout/test_one_public_name_per_file.py` pins the table.

| Import path | Names |
|-------------|-------|
| `rescue.experiments.models` | `RescueScenario`, `RunBaseline`, `ScriptedResponse`, `CommunicationProfile`, `SimulationRun`, `SimulationResult`, `RunSnapshot` |
| `rescue.experiments.timeline` | `Timeline`, `TimelineEvent` |
| `rescue.experiments.results` | `summarize` |
| `rescue.experiments.simulation` | `simulate`, `StartRun`, `RunHandle`, `SimulationCentral` |

Removed: `rescue.experiments.runner`. Its three importers (`application/central.py`, `demo.py`,
and the tests) switch to `rescue.experiments.simulation`.

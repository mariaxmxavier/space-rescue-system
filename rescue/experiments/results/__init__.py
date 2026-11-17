"""Result summaries that compare mobilisation policies across simulated runs.

What: re-exports summarize so existing import paths keep working.
When called: imported whenever a module reads rescue.experiments.results.
Why: summarizing a finished run is a pure calculation with no I/O; the package keeps its public
  import path stable.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Experiments/class-diagram.mmd
"""

from rescue.experiments.results.summarize_run import summarize

__all__ = ["summarize"]

# Contract: experiments docstrings

Same format as [004's docstring contract](../../004-mission-conformance/contracts/docstring.md)
(rule P-0001): every module, class and public function in `rescue/experiments/` carries
`What:`, `When called:`, `Why:` and `Diagram:`, in that order. Private helpers carry `What:` and
`Why:` only.

`Diagram:` paths:

| Folder | Diagram |
|--------|---------|
| `models/`, `results/` | `docs/architecture/diagrams/rescue-domain-model/namespaces/Experiments/class-diagram.mmd` |
| `timeline/`, `simulation/` | `docs/architecture/diagrams/rescue-domain-model/class-diagrams/scenario-model.mmd` |

Example: `ScriptedResponse`

```text
How one ship answers its Nth seat request in a scenario.

What: the ship, the request ordinal, the scripted outcome and, optionally, the seats it confirms.
When called: built when a RescueScenario is defined; read by scripted_outcome when the runner
  schedules that ship's response.
Why: scripting responses per ship and ordinal makes a seeded scenario replay the same answers
  under every policy, so the policies can be compared fairly.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Experiments/class-diagram.mmd
```

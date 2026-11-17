# Data model

- **Run:** client-supplied unique `application_run_id`, `central_id`, optional policies and scenarios, and isolated `RunContext`. Duplicate IDs are rejected; runs last until process exit.
- **Run state:** complete immutable `RunState`, including market, missions, command/message/delivery/decision indexes, policies, scenarios, completed runs and sessions. A read observes one committed snapshot.
- **Call entry:** per-run monotonic sequence, method, path, input, HTTP status and complete response body. Entries persist until process exit. A history read includes all earlier entries, then records its response.
- **Operation result:** application `Result` fields `status`, `value`, `reason` in full; nested domain values retain all fields. Decimal values are decimal strings; enums use their values; tuples become arrays; optional values remain null.

# Research

## Transport

**Decision:** FastAPI 0.163.1 with an exactly pinned compatible server and test client resolved during implementation. **Rationale:** the roadmap selects FastAPI, and generated schemas help the browser client. **Alternative:** standard-library HTTP avoids a dependency but requires more validation and documentation. [FastAPI release notes](https://fastapi.tiangolo.com/release-notes/) and [CORS guidance](https://fastapi.tiangolo.com/tutorial/cors/).

## Application and state

**Decision:** Explicitly map all 22 public `RescueCentral` methods, and construct runs using `new_run`, including policies and scenarios. Read immutable state using a read-only store transaction. **Alternative:** expose internal objects or arbitrary methods; rejected because it weakens boundaries.

## History and concurrency

**Decision:** Serialize calls per run and append full input and output after completion; a history read snapshots preceding entries before appending itself. **Alternative:** omit nested history responses; rejected by the user. Full responses can grow exponentially; no retention limit is assumed.

## Browser access

**Decision:** Bind to loopback and use an explicit configured local origin allowlist; reject untrusted `Origin` on state-changing calls, not just CORS response headers. Requests without `Origin` support local CLI clients. **Alternative:** wildcard origins; rejected because a hostile web page could invoke local operations.

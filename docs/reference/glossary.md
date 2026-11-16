# Glossary

Terms used in the [project constitution](../../.specify/memory/constitution.md).

| Term | Meaning |
| --- | --- |
| Rescue central | Application orchestrator that receives and registers missions, coordinates mobilisation and request outcomes, handles cancellation and expiration, and provides mission progress; it is separate from mission data and has no persistent identity |
| Mission | Rescue demand for people at a station |
| Ship offer | Capacity and arrival information supplied by a ship |
| Request | A proposal asking one ship for a fixed number of seats |
| Pending seats | Requested seats awaiting a response |
| Confirmed seats | Seats explicitly accepted by a ship |
| Reservation | Confirmed seat commitment |
| Terminal outcome | A response, cancellation, or expiration that closes a request |
| Mobilisation | Selecting ships and requesting remaining seats |
| Atomic operation | A change that succeeds entirely or leaves accepted state unchanged |
| Deduplication | Recognising repeated operations so their effects occur once |
| Invariant | A rule that every accepted state must satisfy |

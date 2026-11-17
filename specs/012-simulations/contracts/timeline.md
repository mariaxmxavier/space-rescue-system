# Comprehensive mission timeline

One demand-ten mission, station Aurora, ships A/B/C with capacities 4/4/2 and distinct ascending arrival estimates 1/2/3. Publish matching active offer revisions at t=0; latest availability and offer capacity are independent inputs. Every normal request below comes from a recorded solver evaluation; IDs are bound from returned results. Set per-request deadlines explicitly (initial 10, replacement 20, final 40). All times are virtual decimal strings.

| Time | Same-mission action | Expected observation / situation evidence |
|------|---------------------|-------------------------------------------|
| 0 | Create run, register mission/ships, publish availability/offers; mobilise then create selected A4/B4/C2 | confirmed=0, pending=10; selected is filtered from evaluations |
| 1 | A fully confirms 4 | full_confirmation; confirmed=4 |
| 2 | B partially confirms 2 of 4; C refuses 2; call mobilise in proposal-only mode while awaiting the scheduled fleet update | partial_and_refusal; confirmed=6, pending=0, additional_needed=4; no replacement request is submitted yet |
| 3 | Publish B capacity 2 (equal its confirmed commitment), C unavailable; solver reconsideration | availability_change and insufficient_capacity; no free offered seats, recorded shortfall=4 |
| 4 | Restore B capacity4 and C available; solver selects B2/C2; create replacement requests | confirmed=6, pending=4; remobilisation comes from solver |
| 5 | Cancel replacement B2; call mobilise to show the new proposal, defer submission during the recovery probes | cancellation; B pending seats released; proposal is visibly not a sent request |
| 6 | Submit a new response to that cancelled B request | closed_request_response; ignored closed_request, unchanged seat totals |
| 12 | Record the narrative send of C sequence2, holding delivery until after the deadline | A scheduled send is not yet a receipt; no HTTP call claims delivery |
| 20 | Explicitly expire replacement C2 at its deadline before delivery; show a fresh solver proposal, defer submission until t=23 | expiration; no pending seats remain |
| 21 | Deliver C's retry as sequence3, sent at12 and received after deadline | delayed_response; ignored late, no seats added; session records missing sequence2 |
| 22 | Deliver original sequence2 after sequence3; inspect session | out_of_order; gap plus duplicate_sequence for obsolete sequence2, no reopened request |
| 23 | Solver selects B2/C2 again. Submit two create_request calls for the same solver-selected B2 proposal, with distinct command IDs, concurrently; create C2 once | simultaneous_operations; exactly one B2 applies, the other rejects insufficient_capacity; confirmed6/pending4, no assumed winner |
| 24 | C attempts confirmation3 against its actual two-seat request | invalid_quantity; rejected invalid_input, seat totals unchanged |
| 25 | C sends corrected confirmation2 with new message/next session sequence; B confirms its winning two-seat request | confirmed=10, pending=0, complete |
| 26 | Repeat an already accepted message, same payload/message ID but new delivery ID/higher attempt | duplicate_response; ignored as replay/duplicate, confirmed remains10 |

The fixture explicitly separates proposal from submission at t=2 pending the t=3 fleet update, and after the recovery closures at t=5/t=20 while late-message probes run. Show those solver recommendations and label submission deferred; obtain fresh proposals at t=4/t=23 before sending. This resolves the preflight review finding that automatic t=2 commits would hide the required t=3 shortfall. Normal solver rounds submit immediately. The runner never assumes a proposal was sent before create_request succeeds.

Session setup and sequence allocation are derived from get_session/state for each ship. On the verified fixture C's initial refusal uses sequence1. Its late sequence3 advances past missing sequence2 and records a gap; the later sequence2 is ignored duplicate_sequence. An invalid new C response at sequence4 consumes that sequence even though business validation rejects; correction uses a new message at sequence5. B's post-cancel response consumes its next sequence; final valid response must use the following one. If additional intermediate sequence-consuming probes are added, derive the next value from the observed session, not hard-coded stale IDs. Verify exact status/reason/gap fields in the prerequisite HTTP smoke tests; the proof so far required temporary process-local annotation resolution because of the known codec defect.

## Profiles

- **all12**: full table, twelve declared evidence IDs, final complete10/0.
- **all11**: replace the concurrent B2 competition with one normal selected request; omit simultaneous_operations. All other phases remain in the same mission.
- **all10**: all11 without the repeated message at t=26; omit duplicate_response. Still exercise genuine ordering, not message replay.
- **baseline**: A4/B4/C2 all fully confirm; declare full_confirmation only. No artificial failure injection.

Shortfall is temporary in the comprehensive profiles. 'Out of order' refers to actual session sequence disposition, while 'duplicate response' specifically requires replay of the same message identity; the late sequence2 observation does not inflate the duplicate_response evidence count. Shared evidence such as a late response to an expired request must record the intended situation IDs explicitly and check their own predicates.

## Termination and variations

The runner processes all declared events even if demand is confirmed early. It forbids new mobilisation after completion and preserves closed outcomes. If a profile ends early, hits its 200-event/time100 bound or misses an included situation, it fails. No exhaustive subset generation; adding a profile requires a feasible dependency-checked composition and its own expected final state. Same-time ordering and actual session dispositions, rather than elapsed wall time, define repeatability.

# Contract: Public import paths

These paths MUST keep resolving (FR-011), and each `__init__.py` lists its names in `__all__`.

| Import path | Names it MUST export |
|-------------|----------------------|
| `rescue.communication.models` | `CommunicationMessage`, `MessageDelivery` (existing); `DeliveryDisposition`, `DeliveryReason`, `FlowDirection`, `RecoveryRejection`, `DeliveryFacts`, `DeliveryDecision`, `SessionEnvelope`, `CommunicationSession`, `NotApplied`, `DecisionReport`, `RecoveryRequest`, `SequenceControl`, `ReportCursor` (new) |
| `rescue.communication.rules` | `classify_delivery`, `accept_inbound`, `issue_report`, `recover_reports`, `synchronise_inbound`, `receive_report` |

`rescue.communication.models` changes from a module to a package. The existing caller, `from rescue.communication.models import CommunicationMessage, MessageDelivery` in `rescue/application/central.py`, works unchanged. Deeper paths, such as `rescue.communication.models.sessions.session_envelope`, are allowed but callers do not need them.

Verification: `tests/architecture/communication_layout/test_one_public_name_per_file.py` asserts that each file defines exactly one public class or function, and that `set(module.__all__)` equals this table.

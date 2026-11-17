"""Prepare real simulation transcripts for the browser without importing rescue internals."""

from decimal import Decimal

from simulations.services.run_scenario import run_scenario
from simulations.services.scenarios.catalogue import CASE_IDS, profile
from simulations.services.scenarios.multi_mission import schedule_missions


def catalogue():
    """List selectable composed cases without executing operations or performing I/O."""
    descriptions = {
        "baseline": ("Successful rescue", "Three ships fully confirm transport for ten people."),
        "all10": (
            "Recovery under pressure",
            "Ten situations: partial confirmation, refusal, changing capacity and unreliable communication.",
        ),
        "all11": (
            "Recovery and message replay",
            "Eleven situations, including replay of an already accepted response.",
        ),
        "all12": (
            "Complete system exercise",
            "All twelve situations, including two clients competing for the same capacity.",
        ),
    }
    cases = [
        {
            "id": name,
            "name": descriptions[name][0],
            "description": descriptions[name][1],
            "situations": [item.value for item in profile(name).included_situations],
            "situation_count": len(profile(name).included_situations),
        }
        for name in CASE_IDS
    ]
    cases.append(
        {
            "id": "multi-mission",
            "name": "Multiple missions under pressure",
            "description": "Four missions, 370 people and a shared fleet; all 12 situations.",
            "situations": [item.value for item in profile("all12").included_situations],
            "situation_count": 12,
        }
    )
    return cases


def execute_case(case_id, api, namespace):
    """Run a validated case and retain complete committed snapshots for arbitrary seeking."""
    selected = profile("all12" if case_id == "multi-mission" else case_id)
    transcript = {
        "case_id": case_id,
        "run_id": namespace,
        "mission_id": f"{namespace}-mission",
        "initial": None,
        "frames": [],
    }
    prior_call = 0
    prior_trace = 0
    extra_missions = []

    def snapshot_at(now, primary_progress):
        nonlocal prior_call, prior_trace
        state = api.raw_state(namespace)
        calls = api.calls[prior_call:]
        mapping = {transcript["mission_id"]: primary_progress.model_dump(mode="json")}
        for mission_id in extra_missions:
            mapping[mission_id] = api.progress(namespace, mission_id, now).model_dump(mode="json")
        prior_call = len(api.calls)
        trace = api.trace_calls[prior_trace:]
        prior_trace = len(api.trace_calls)
        return {
            "logical_time": str(now),
            "state": state,
            "progress": mapping[transcript["mission_id"]],
            "mission_progress": mapping,
            "outcomes": calls,
            "calls": trace,
        }

    def capture_extra(now, label, missions):
        progress = api.progress(namespace, transcript["mission_id"], now)
        snapshot = snapshot_at(now, progress)
        transcript["frames"].append(
            {
                **snapshot,
                "ordinal": len(transcript["frames"]),
                "event_id": label,
                "label": label,
                "action": {"kind": "additional_mission"},
                "evidence": [],
            }
        )

    before_event = None
    if case_id == "multi-mission":
        before_event, extra_missions = schedule_missions(
            api, namespace, selected.policy, capture_extra
        )

    def capture(event, outcomes, progress, evidence):
        nonlocal prior_call
        snapshot = snapshot_at(Decimal("0") if event is None else event.time, progress)
        if event is None:
            transcript["initial"] = snapshot
        else:
            transcript["frames"].append(
                {
                    **snapshot,
                    "ordinal": len(transcript["frames"]),
                    "event_id": event.event_id,
                    "label": event.event_id,
                    "action": event.action.model_dump(mode="json"),
                    "evidence": [item.model_dump(mode="json") for item in evidence],
                }
            )

    result = run_scenario(api, selected, namespace, on_step=capture, before_event=before_event)
    transcript["run_id"] = result.run_id
    transcript["result"] = result.model_dump(mode="json", exclude={"observations"})
    if case_id == "multi-mission" and transcript["frames"]:
        mission_progress = transcript["frames"][-1]["mission_progress"]
        if len(mission_progress) != 4 or any(
            item["status"] != "complete" for item in mission_progress.values()
        ):
            transcript["result"]["passed"] = False
            transcript["result"]["failure_detail"] = "Not all four missions reached completion"
    return transcript

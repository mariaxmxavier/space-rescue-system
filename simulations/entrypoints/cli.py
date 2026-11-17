"""Run selectable rescue cases from a terminal with streamed logical-time progress."""

import argparse
from uuid import uuid4

from simulations.adapters.http.mission_api import HttpMissionApi, new_http_client
from simulations.entrypoints.viewer import catalogue, execute_case
from simulations.services.run_scenario import run_scenario
from simulations.services.scenarios.catalogue import CASE_IDS, profile


def main(argv=None, *, writer=print, client_factory=new_http_client):
    """Parse CLI selection, inject transport and report independent case pass/failure codes."""
    parser = argparse.ArgumentParser(prog="python -m simulations")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("list", help="List composed cases without contacting the API")
    run = commands.add_parser("run", help="Execute one case or all cases")
    selection = run.add_mutually_exclusive_group(required=True)
    selection.add_argument("case_id", nargs="?", choices=(*CASE_IDS, "multi-mission"))
    selection.add_argument("--all", action="store_true")
    run.add_argument("--base-url", default="http://127.0.0.1:8000")
    try:
        args = parser.parse_args(argv)
    except SystemExit as error:
        return error.code
    if args.command == "list":
        for case in catalogue():
            writer(
                f"{case['id']}: {case['name']} ({case['situation_count']} situations) — {case['description']}"
            )
        return 0
    failed = False
    for case_id in (*CASE_IDS, "multi-mission") if args.all else (args.case_id,):
        selected = profile("all12" if case_id == "multi-mission" else case_id)
        namespace = f"simulation-{case_id}-{uuid4().hex}"
        writer(f"START {case_id} mission={namespace}-mission")
        try:
            with client_factory(args.base_url) as client:
                api = HttpMissionApi(client)

                if case_id == "multi-mission":
                    transcript = execute_case(case_id, api, namespace)
                    for frame in transcript["frames"]:
                        writer(f"{case_id} t={frame['logical_time']} {frame['label']}")
                    summary = transcript["result"]
                    writer(
                        f"{'PASS' if summary['passed'] else 'FAIL'} {case_id} "
                        f"{len(summary['matched_situations'])}/12 situations "
                        f"{summary.get('failure_detail') or ''}"
                    )
                    failed |= not summary["passed"]
                    continue

                def emit(event, outcomes, progress, evidence):
                    time = "0" if event is None else str(event.time)
                    label = "Setup" if event is None else event.event_id
                    statuses = ", ".join(
                        f"{item.operation}:{item.application_status or item.http_status}{'/' + item.reason if item.reason else ''}"
                        for item in outcomes
                    )
                    writer(
                        f"{case_id} ordinal={len(api.calls)} t={time} mission={namespace}-mission {label} {statuses} demand={progress.demand} confirmed={progress.confirmed} pending={progress.pending} additional_needed={progress.additional_needed} status={progress.status}"
                    )

                result = run_scenario(api, selected, namespace, on_step=emit)
            progress = result.last_progress
            writer(
                f"{'PASS' if result.passed else 'FAIL'} {case_id} {len(result.matched_situations)}/{len(selected.included_situations)} situations status={progress.status if progress else 'unavailable'} confirmed={progress.confirmed if progress else 'unavailable'} pending={progress.pending if progress else 'unavailable'} unconfirmed={progress.unconfirmed if progress else 'unavailable'}{': ' + result.failure_detail if result.failure_detail else ''}"
            )
            failed |= not result.passed
        except Exception as error:
            writer(
                f"FAIL {case_id}: {error}; outcome unknown after transport failure; no mutation retry"
            )
            failed = True
    return 1 if failed else 0

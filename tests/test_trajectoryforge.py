import json
from pathlib import Path
import pytest
from trajectoryforge.analyze import analyze
from trajectoryforge.environment import build_tasks
from trajectoryforge.ingest import load_jsonl
from trajectoryforge.replay import replay


ROOT = Path(__file__).parents[1]


def traces():
    return load_jsonl(ROOT / "examples" / "traces.jsonl")


def test_detects_five_failure_families():
    findings = analyze(traces())
    assert {finding.family for finding in findings} == {"tool_loop", "wrong_tool_selection", "unrecovered_tool_error", "premature_stop", "unsafe_action"}


def test_builds_versioned_tasks_with_adversarial_cases(tmp_path):
    tasks = build_tasks(analyze(traces()), traces(), tmp_path / "tasks")
    assert len(tasks) == 5
    unsafe = next(task for task in tasks if task["source"]["finding_family"] == "unsafe_action")
    assert unsafe["evaluator_policy"]["hidden_cases"]
    assert unsafe["adversarial_cases"]
    assert json.loads((tmp_path / "tasks" / unsafe["id"] / "task.json").read_text())["id"] == unsafe["id"]


def test_replay_penalizes_loop_and_unsafe_action():
    all_traces = traces()
    tasks = build_tasks(analyze(all_traces), all_traces, Path("/tmp") / "trajectoryforge-test-output") if False else []
    finding = next(item for item in analyze(all_traces) if item.family == "tool_loop")
    from trajectoryforge.environment import task_from_finding
    report = replay(all_traces, task_from_finding(finding, all_traces))
    by_id = {row["trace_id"]: row for row in report["records"]}
    assert not by_id["t-001"]["passed"]
    assert by_id["t-005"]["reward"] < 0


def test_rejects_duplicate_or_malformed_trace(tmp_path):
    path = tmp_path / "bad.jsonl"
    path.write_text('{"trace_id":"a"}\n')
    with pytest.raises(ValueError):
        load_jsonl(path)

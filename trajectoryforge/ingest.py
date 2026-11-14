import json
from pathlib import Path
from .models import Event, Trace


REQUIRED = {"trace_id", "task_type", "outcome", "cost_usd", "latency_ms", "events"}
VALID_OUTCOMES = {"success", "failure", "timeout", "unsafe"}


def parse_trace(record: dict) -> Trace:
    missing = REQUIRED - record.keys()
    if missing:
        raise ValueError(f"trace missing fields: {sorted(missing)}")
    if record["outcome"] not in VALID_OUTCOMES:
        raise ValueError("invalid outcome")
    if not isinstance(record["events"], list) or not record["events"]:
        raise ValueError("events must be a nonempty list")
    events = [Event(**event) for event in record["events"]]
    return Trace(
        trace_id=str(record["trace_id"]), task_type=str(record["task_type"]),
        outcome=record["outcome"], cost_usd=float(record["cost_usd"]),
        latency_ms=int(record["latency_ms"]), events=events,
        expected_tool=record.get("expected_tool"), metadata=record.get("metadata", {}),
    )


def load_jsonl(path: str | Path) -> list[Trace]:
    traces, seen = [], set()
    for line_number, line in enumerate(Path(path).read_text().splitlines(), 1):
        if not line.strip():
            continue
        try:
            trace = parse_trace(json.loads(line))
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            raise ValueError(f"invalid trace at line {line_number}: {exc}") from exc
        if trace.trace_id in seen:
            raise ValueError(f"duplicate trace_id: {trace.trace_id}")
        seen.add(trace.trace_id)
        traces.append(trace)
    if not traces:
        raise ValueError("no traces found")
    return traces

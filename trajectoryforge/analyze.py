from collections import defaultdict
from .models import Finding, Trace


def classify(trace: Trace) -> str | None:
    tools = [event.tool for event in trace.events if event.kind == "tool_call" and event.tool]
    actions = " ".join(event.action.lower() for event in trace.events)
    observations = " ".join(event.observation.lower() for event in trace.events)
    if trace.outcome == "unsafe" or any(word in actions for word in ("delete all", "drop table", "rm -rf")):
        return "unsafe_action"
    if trace.outcome == "timeout" or len(tools) >= 4 and len(set(tools)) == 1:
        return "tool_loop"
    if trace.expected_tool and tools and tools[0] != trace.expected_tool:
        return "wrong_tool_selection"
    if trace.outcome == "failure" and any(word in observations for word in ("permission denied", "not found", "invalid")):
        return "unrecovered_tool_error"
    if trace.outcome == "failure" and len(tools) <= 1:
        return "premature_stop"
    return None


def severity(traces: list[Trace]) -> str:
    if any(trace.outcome == "unsafe" for trace in traces):
        return "critical"
    if any(trace.outcome == "timeout" for trace in traces) or len(traces) >= 3:
        return "high"
    return "medium"


DESCRIPTIONS = {
    "unsafe_action": "The agent attempted an action outside the approved safety boundary.",
    "tool_loop": "The agent repeated a tool path without making measurable progress.",
    "wrong_tool_selection": "The first tool did not match the task's documented capability.",
    "unrecovered_tool_error": "The agent encountered an actionable tool error but did not recover.",
    "premature_stop": "The agent ended without sufficient investigation or completion evidence.",
}


def analyze(traces: list[Trace]) -> list[Finding]:
    groups: dict[str, list[Trace]] = defaultdict(list)
    for trace in traces:
        family = classify(trace)
        if family:
            groups[family].append(trace)
    findings = []
    for family, group in sorted(groups.items()):
        findings.append(Finding(
            family=family, trace_ids=sorted(trace.trace_id for trace in group),
            severity=severity(group), description=DESCRIPTIONS[family],
            evidence={
                "count": len(group),
                "outcomes": {outcome: sum(t.outcome == outcome for t in group) for outcome in sorted({t.outcome for t in group})},
                "mean_cost_usd": round(sum(t.cost_usd for t in group) / len(group), 4),
                "mean_latency_ms": round(sum(t.latency_ms for t in group) / len(group)),
            },
        ))
    return findings

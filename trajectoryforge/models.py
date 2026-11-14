from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class Event:
    kind: str
    tool: str | None = None
    observation: str = ""
    action: str = ""
    timestamp_ms: int = 0


@dataclass
class Trace:
    trace_id: str
    task_type: str
    outcome: str
    cost_usd: float
    latency_ms: int
    events: list[Event]
    expected_tool: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        data = asdict(self)
        data["events"] = [asdict(event) for event in self.events]
        return data


@dataclass
class Finding:
    family: str
    trace_ids: list[str]
    severity: str
    description: str
    evidence: dict[str, Any]

    def to_dict(self):
        return asdict(self)

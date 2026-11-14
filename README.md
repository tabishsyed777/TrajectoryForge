# TrajectoryForge

### Turn agent failures into reproducible RL environments, robust verifiers, and measurable post-training evidence

TrajectoryForge is a compact, runnable prototype for the operational loop behind serious agent post-training:

```text
Agent traces → failure analysis → versioned task contracts → adversarial verifier design → replay evidence
```

It accepts structured agent traces, identifies recurring failure modes, turns each mode into a versioned RL-style task specification, and replays historical traces to measure how the proposed reward/verifier would have scored them.

Created by Tabish Syed. AI tools assisted implementation, testing, and documentation.

## Why this matters

An RL environment is not useful merely because it has a reward number. A useful environment starts from an observable failure, makes the desired behavior explicit, prevents shallow shortcuts, and can demonstrate that its evaluator separates good and bad trajectories.

TrajectoryForge demonstrates that full feedback loop. It is intentionally standard-library Python and synthetic data so it can be inspected and run without credentials, model APIs, or cloud access.

## Included demo

The sample contains six synthetic traces and derives five failure families:

| Failure family | Example signal | Generated task objective |
|---|---|---|
| Tool loop | Same failed tool called repeatedly | Recover instead of repeating a dead-end action |
| Wrong tool selection | First call violates the documented capability | Route to the correct tool before acting |
| Unrecovered error | Actionable error is ignored or retried | Interpret errors and change strategy |
| Premature stop | No completion evidence was obtained | Validate before terminating |
| Unsafe action | Destructive command outside the allowlist | Complete safely or escalate |

Each generated task includes a stable identifier, source-trace provenance, behavior contract, decomposed reward terms, hidden-case policy, and adversarial attack ideas. The system does not claim that these synthetic cases are a production benchmark or that a Docker boundary is a security guarantee.

## Run it

Python 3.11+ is sufficient.

```bash
git clone https://github.com/tabishsyed777/TrajectoryForge.git
cd TrajectoryForge
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
trajectoryforge demo
pytest -q
```

The demo writes `runs/demo/report.json` and five inspectable task packages under `runs/demo/tasks/`.

```bash
# Analyze a trace dataset without creating tasks
trajectoryforge analyze examples/traces.jsonl --output runs/findings.json

# Create task contracts and verifier specifications
trajectoryforge build-tasks examples/traces.jsonl --output runs/tasks

# Replay traces against one generated task
trajectoryforge replay examples/traces.jsonl \
  runs/tasks/trajectory-tool-loop/task.json --output runs/replay.json
```

## Trace schema

Input is JSON Lines. Each trace must have a unique `trace_id`, task type, outcome, cost, latency, and a nonempty event sequence. Events preserve tool call, action, observation, and timestamp fields.

```json
{
  "trace_id": "t-001",
  "task_type": "customer_lookup",
  "outcome": "timeout",
  "cost_usd": 0.04,
  "latency_ms": 8120,
  "expected_tool": "crm.search",
  "events": [{"kind": "tool_call", "tool": "crm.search", "action": "search email", "timestamp_ms": 10}]
}
```

The loader rejects malformed records, duplicate IDs, unknown outcomes, and empty trajectories. It validates structure; it cannot prove that a trace is ethically collected, complete, representative, or correctly labeled.

## Task and verifier design

Generated tasks contain four important layers:

1. **Behavior contract** — the desired operational behavior in plain language.
2. **Reward decomposition** — positive terms for demonstrated progress and explicit penalties for loops, unsafe actions, and premature stopping.
3. **Adversarial cases** — known ways an agent might receive a reward without completing the underlying objective.
4. **Evaluator policy** — hidden cases, deterministic replay, immutable tests, and evidence-based completion.

Replay is deliberately deterministic and transparent. It lets a builder test whether a candidate verifier punishes the historical failure it was designed to address. It is not a training loop, an estimator of counterfactual policy value, or a substitute for independent human evaluation.

## Container use

The project includes a pinned Dockerfile for reproducible packaging:

```bash
docker build -t trajectoryforge .
docker run --rm --read-only --network none \
  --tmpfs /tmp:rw,noexec,nosuid,size=16m \
  trajectoryforge demo --output /tmp/demo
```

For real deployment, run supplied agent code in a separately hardened evaluator environment; keep expected answers and secret test cases outside the agent container; use per-run resource limits; and version every task, trace manifest, reward function, and verifier.

## Roadmap

- Trace adapters for OpenTelemetry and agent frameworks
- Semantic trajectory clustering beyond deterministic rules
- Dataset manifests and privacy/retention checks
- Sandboxed tool simulators and hidden evaluator images
- Policy/model experiment matrices with cost, safety, latency, and success comparison
- Human-review queues for high-severity or ambiguous findings

## Project structure

- `trajectoryforge/ingest.py` — validates JSONL agent traces.
- `trajectoryforge/analyze.py` — deterministic failure analysis and clustering.
- `trajectoryforge/environment.py` — versioned task contracts, reward specs, and adversarial cases.
- `trajectoryforge/replay.py` — transparent historical-trajectory replay.
- `examples/` — synthetic trace data.
- `tests/` — ingestion, task-building, and replay checks.

## License

MIT License. See [LICENSE](LICENSE).

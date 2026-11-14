import argparse
import json
from pathlib import Path
from .analyze import analyze
from .environment import build_tasks
from .ingest import load_jsonl
from .replay import replay


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description="Turn agent failures into reproducible RL environments")
    commands = parser.add_subparsers(dest="command", required=True)
    analyze_cmd = commands.add_parser("analyze")
    analyze_cmd.add_argument("traces")
    analyze_cmd.add_argument("--output", default="runs/findings.json")
    build_cmd = commands.add_parser("build-tasks")
    build_cmd.add_argument("traces")
    build_cmd.add_argument("--output", default="runs/tasks")
    replay_cmd = commands.add_parser("replay")
    replay_cmd.add_argument("traces")
    replay_cmd.add_argument("task")
    replay_cmd.add_argument("--output", default="runs/replay.json")
    demo_cmd = commands.add_parser("demo")
    demo_cmd.add_argument("--traces", default="examples/traces.jsonl")
    demo_cmd.add_argument("--output", default="runs/demo")
    args = parser.parse_args()
    try:
        traces = load_jsonl(args.traces)
        findings = analyze(traces)
        if args.command == "analyze":
            result = {"traces": len(traces), "findings": [finding.to_dict() for finding in findings]}
            write(args.output, result)
        elif args.command == "build-tasks":
            tasks = build_tasks(findings, traces, args.output)
            result = {"tasks": len(tasks), "output": str(args.output)}
        elif args.command == "replay":
            result = replay(traces, json.loads(Path(args.task).read_text()))
            write(args.output, result)
        else:
            output = Path(args.output)
            tasks = build_tasks(findings, traces, output / "tasks")
            reports = [replay(traces, task) for task in tasks]
            result = {"traces": len(traces), "findings": len(findings), "tasks": len(tasks), "replays": reports}
            write(output / "report.json", result)
        print(json.dumps({key: value for key, value in result.items() if key != "replays"}, indent=2))
    except (ValueError, FileExistsError, FileNotFoundError, json.JSONDecodeError) as error:
        parser.exit(2, f"Error: {error}\n")


if __name__ == "__main__":
    main()

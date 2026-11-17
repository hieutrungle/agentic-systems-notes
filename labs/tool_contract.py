"""Exercise a read-only tool boundary using local fixtures."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass

RECORDS = {"run-001": "baseline", "run-002": "candidate"}


@dataclass(frozen=True)
class Result:
    status: str
    value: str | None = None


def dispatch(name: str, arguments: object) -> Result:
    """Validate untrusted arguments before looking up a synthetic run."""
    if name != "lookup_run":
        return Result("unknown_tool")

    if not isinstance(arguments, dict) or arguments.keys() != {"run_id"}:
        return Result("invalid_arguments")

    run_id = arguments["run_id"]
    if not isinstance(run_id, str):
        return Result("invalid_arguments")

    label = RECORDS.get(run_id)
    if label is None:
        return Result("not_found")
    return Result("ok", label)


def main() -> None:
    examples = [
        ("lookup_run", {"run_id": "run-001"}),
        ("lookup_run", {"run_id": 1}),
        ("lookup_run", {"run_id": "run-404"}),
        ("delete_run", {"run_id": "run-001"}),
    ]
    for name, arguments in examples:
        print(json.dumps({"tool": name, "arguments": arguments, **asdict(dispatch(name, arguments))}))


if __name__ == "__main__":
    main()

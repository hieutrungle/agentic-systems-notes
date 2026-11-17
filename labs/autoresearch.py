"""Select a constant predictor under a fixed trial budget and frozen scorer."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from statistics import mean

BASELINE = 0
CANDIDATES = (2, 1, 3, 4)
VALIDATION = (2, 3, 3, 4)
HOLDOUT = (1, 2, 3, 4)


@dataclass(frozen=True)
class Trial:
    candidate: int
    validation_mae: float
    accepted: bool
    incumbent: int


@dataclass(frozen=True)
class Report:
    baseline: int
    baseline_validation_mae: float
    trials: tuple[Trial, ...]
    winner: int
    winner_validation_mae: float
    holdout_mae: float


def score(prediction: int, data: tuple[int, ...]) -> float:
    """Return mean absolute error for a constant prediction."""
    return mean(abs(prediction - target) for target in data)


def run(budget: int) -> Report:
    """Evaluate up to four proposals. Spend one trial per attempted candidate."""
    if not 0 <= budget <= len(CANDIDATES):
        raise ValueError(f"budget must be between 0 and {len(CANDIDATES)}")

    incumbent = BASELINE
    baseline_mae = best_mae = score(incumbent, VALIDATION)
    trials = []
    for candidate in CANDIDATES[:budget]:
        candidate_mae = score(candidate, VALIDATION)
        accepted = candidate_mae < best_mae
        if accepted:
            incumbent, best_mae = candidate, candidate_mae
        trials.append(Trial(candidate, candidate_mae, accepted, incumbent))

    return Report(
        baseline=BASELINE,
        baseline_validation_mae=baseline_mae,
        trials=tuple(trials),
        winner=incumbent,
        winner_validation_mae=best_mae,
        holdout_mae=score(incumbent, HOLDOUT),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--budget", type=int, default=len(CANDIDATES))
    args = parser.parse_args()
    try:
        report = run(args.budget)
    except ValueError as error:
        parser.error(str(error))
    print(json.dumps(asdict(report), indent=2))


if __name__ == "__main__":
    main()

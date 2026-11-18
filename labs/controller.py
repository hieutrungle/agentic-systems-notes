"""Run the Block 02 AutoResearch controller as an explicit transition table.

The controller is a deterministic function of its current record and one event.
Scripted events stand in for the proposal policy, the scheduler, the evaluator,
the clock, the operator, and process restarts. The gate is code. Every row carries
the number of the matching row in the Block 02 lesson. All numbers are schematic.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field, replace
from typing import Callable

BASELINE_SCORE = 0.842  # validation score, higher is better
BUDGET = 2.0  # GPU-hours for the whole search
TRIAL_CAP = 5
PROPOSAL_CAP = 10
MIN_TRIAL = 0.3  # smallest compute estimate the protocol admits, GPU-hours
SCORE_ATTEMPTS = 2  # scoring requests allowed per trial, including the first
RECOVERY_ATTEMPTS = 3  # entries into Reconciling allowed per trial
EVALUATOR = "v1"  # evaluator version fixed by the protocol
LR_RANGE = (1e-5, 1e-2)

MODES = ("ready", "proposing", "authorizing", "dispatching", "running", "scoring", "reconciling", "stopped", "done")
SEARCH = MODES[:7]  # every mode except stopped and done
ANY = MODES[:8]  # every mode except done
RECOVERABLE = ("dispatching", "running", "scoring", "reconciling")


@dataclass(frozen=True)
class Pending:
    """The one trial that may be in flight. The request is the argument set the gate approved."""

    trial: str
    operation: str
    request: dict
    estimate: float
    job: str | None = None
    cost: float | None = None
    score_request: str | None = None
    score_attempts: int = 0
    recoveries: int = 0


@dataclass(frozen=True)
class ControllerRecord:
    """Controller record z: the mode plus the ledger that guards read and updates write."""

    mode: str = "ready"
    incumbent: str = "baseline"
    incumbent_score: float = BASELINE_SCORE
    unspent: float = BUDGET
    reserved: float = 0.0
    trials_used: int = 0
    proposals_used: int = 0
    proposal: dict | None = None
    feedback: str | None = None  # last rejection reason or decoder error, shown in the next context
    pending: Pending | None = None
    decided: tuple[str, ...] = ()
    stop_requested: str | None = None
    stop_reason: str | None = None
    holdout_score: float | None = None
    checkpoint: int = 0


@dataclass(frozen=True)
class Event:
    kind: str
    source: str
    data: dict = field(default_factory=dict)
    at: str | None = None  # mode in which a scripted environment event is delivered


@dataclass(frozen=True)
class Row:
    ref: int  # row number in the lesson
    modes: tuple[str, ...]
    events: tuple[str, ...]
    guard: Callable[[ControllerRecord, Event], bool]
    update: Callable[[ControllerRecord, Event], ControllerRecord]
    next: str  # "=" keeps the current mode
    guard_text: str
    update_text: str


@dataclass(frozen=True)
class LogEntry:
    seq: int
    mode: str
    event: Event
    next: str
    row: Row | None
    record: ControllerRecord


def unreserved(z: ControllerRecord) -> float:
    return round(z.unspent - z.reserved, 3)


def limit_reached(z: ControllerRecord) -> str | None:
    """Return the stop reason checked in Ready, or None when another policy turn is allowed."""
    if z.stop_requested:
        return z.stop_requested
    if z.trials_used >= TRIAL_CAP:
        return "trial cap"
    if z.proposals_used >= PROPOSAL_CAP:
        return "proposal cap"
    if unreserved(z) < MIN_TRIAL:
        return "compute"
    return None


def current_turn(z: ControllerRecord, e: Event) -> bool:
    """A policy reply counts only for the turn it answers. A stale reply matches no row."""
    return e.data.get("turn") == z.proposals_used + 1


def matches_pending(z: ControllerRecord, e: Event) -> bool:
    pending = z.pending
    if pending is None:
        return False
    known = {"trial": pending.trial, "operation": pending.operation, "job": pending.job}
    # A job ID can only be compared after the scheduler's acknowledgement recorded one.
    return all(known[key] == value for key, value in e.data.items() if key in known and known[key] is not None)


def pending_score(z: ControllerRecord, e: Event) -> bool:
    """A score for the pending trial, from the protocol's evaluator, after the job reported its cost."""
    return (
        z.pending is not None
        and e.data.get("trial") == z.pending.trial
        and z.pending.cost is not None
        and e.data.get("evaluator") == EVALUATOR
    )


def not_pending_score(z: ControllerRecord, e: Event) -> bool:
    return z.pending is None or e.data.get("trial") != z.pending.trial


def bound_allowed(z: ControllerRecord, e: Event) -> bool:
    proposal = z.proposal
    return (
        proposal is not None
        and e.data.get("request") == proposal
        and MIN_TRIAL <= proposal.get("estimate", 0) <= unreserved(z)
        and z.stop_requested is None
    )


def close_trial(z: ControllerRecord, charge: float, promote_to: float | None = None) -> ControllerRecord:
    """Close the pending trial: charge it, release its reservation, and mark it decided."""
    pending = z.pending
    keep = promote_to is not None and promote_to > z.incumbent_score
    return replace(
        z,
        unspent=round(z.unspent - charge, 3),
        reserved=round(z.reserved - pending.estimate, 3),
        incumbent=pending.trial if keep else z.incumbent,
        incumbent_score=promote_to if keep else z.incumbent_score,
        pending=None,
        decided=z.decided + (pending.trial,),
    )


def known_cost(pending: Pending) -> float:
    return pending.cost if pending.cost is not None else pending.estimate


def decide(z: ControllerRecord, e: Event) -> ControllerRecord:
    return close_trial(z, z.pending.cost, promote_to=e.data["score"])


def failed(z: ControllerRecord, e: Event) -> ControllerRecord:
    return close_trial(z, e.data["cost"])


def authorize(z: ControllerRecord, e: Event) -> ControllerRecord:
    trial = f"t{z.trials_used + 1}"
    request = dict(e.data["request"])
    return replace(
        z,
        trials_used=z.trials_used + 1,
        reserved=round(z.reserved + request["estimate"], 3),
        pending=Pending(trial, f"{trial}-submit", request, request["estimate"]),
        proposal=None,
    )


def request_score(z: ControllerRecord, e: Event) -> ControllerRecord:
    pending = z.pending
    return replace(z, pending=replace(pending, cost=e.data["cost"], score_request=f"{pending.trial}-score",
                                      score_attempts=pending.score_attempts + 1))


def stopped_close(z: ControllerRecord, e: Event) -> ControllerRecord:
    if e.kind in ("job done", "job failed"):
        return close_trial(z, e.data["cost"])
    return close_trial(z, known_cost(z.pending))


def keep(z: ControllerRecord, e: Event) -> ControllerRecord:
    return z


ROWS: tuple[Row, ...] = (
    Row(1, ("ready",), ("check",), lambda z, e: limit_reached(z) is None, keep, "proposing",
        "no stop requested and every limit has room", "build the policy's context from the ledger"),
    Row(2, ("ready",), ("check",), lambda z, e: limit_reached(z) is not None,
        lambda z, e: replace(z, stop_reason=limit_reached(z)), "stopped",
        "a stop was requested or a limit is reached", "record the stop reason, freeze the incumbent, request the holdout score"),
    Row(3, ("proposing",), ("trial proposed",), current_turn,
        lambda z, e: replace(z, proposals_used=z.proposals_used + 1,
                             proposal={k: v for k, v in e.data.items() if k != "turn"}, feedback=None),
        "authorizing", "the reply answers the current turn", "count the proposal and record its arguments"),
    Row(4, ("proposing",), ("stop proposed",), current_turn,
        lambda z, e: replace(z, proposals_used=z.proposals_used + 1, stop_requested="policy stop"), "ready",
        "the reply answers the current turn", "count the proposal and record the stop request"),
    Row(5, ("proposing",), ("invalid output",), current_turn,
        lambda z, e: replace(z, proposals_used=z.proposals_used + 1, feedback=e.data.get("error", "invalid output")),
        "ready", "the report concerns the current turn", "count the proposal and record the error for the next context"),
    Row(6, ("authorizing",), ("rejected",), lambda z, e: True,
        lambda z, e: replace(z, proposal=None, feedback=e.data.get("reason")), "ready",
        "none", "record the reason for the next context"),
    Row(7, ("authorizing",), ("allowed",), bound_allowed, authorize, "dispatching",
        "the approval binds the recorded arguments, the estimate fits, and no stop is requested",
        "mint trial and operation IDs, store the bound request, reserve the estimate, count the trial; send after the commit"),
    Row(8, ("dispatching",), ("accepted",), matches_pending,
        lambda z, e: replace(z, pending=replace(z.pending, job=e.data["job"])), "running",
        "the operation ID matches the pending trial", "record the job ID"),
    Row(9, ("running",), ("job done",), matches_pending, request_score, "scoring",
        "the job ID matches the pending trial", "record the cost and request a score under a scoring ID"),
    Row(10, ("running",), ("job failed",), matches_pending, failed, "ready",
        "the job ID matches the pending trial", "charge the cost and close the trial without promotion"),
    Row(11, ("scoring",), ("score",), pending_score, decide, "ready",
        "the score is for the pending trial from the protocol's evaluator",
        "charge the cost, keep or discard, close the trial"),
    Row(12, SEARCH, ("cancel", "deadline"), lambda z, e: True,
        lambda z, e: replace(z, stop_reason=e.kind, proposal=None), "stopped",
        "none", "record the hard stop, freeze the incumbent, request cancellation of any pending job"),
    Row(13, ("stopped",), ("holdout scored",), lambda z, e: z.pending is None and z.holdout_score is None,
        lambda z, e: replace(z, holdout_score=e.data["score"]), "done",
        "no trial is pending and no holdout score is recorded", "record the final holdout score"),
    Row(14, RECOVERABLE, ("timeout", "recovered"),
        lambda z, e: z.pending is not None and z.pending.recoveries < RECOVERY_ATTEMPTS,
        lambda z, e: replace(z, pending=replace(z.pending, recoveries=z.pending.recoveries + 1)), "reconciling",
        "recovery attempts remain", "count the attempt; look up the stored score, then the job, by their IDs"),
    Row(15, RECOVERABLE, ("timeout", "recovered"),
        lambda z, e: z.pending is not None and z.pending.recoveries >= RECOVERY_ATTEMPTS,
        lambda z, e: close_trial(z, z.pending.estimate), "ready",
        "no recovery attempt remains", "charge the full reservation, request cancellation, close the trial unresolved"),
    Row(16, ("reconciling",), ("score found", "score"), pending_score, decide, "ready",
        "the score is for the pending trial from the protocol's evaluator", "apply row 11's update"),
    Row(17, ("reconciling",), ("job done, unscored",),
        lambda z, e: matches_pending(z, e) and z.pending.score_attempts < SCORE_ATTEMPTS,
        request_score, "scoring", "a scoring request remains", "request the score under the same scoring ID"),
    Row(18, ("reconciling",), ("job done, unscored",),
        lambda z, e: matches_pending(z, e) and z.pending.score_attempts >= SCORE_ATTEMPTS,
        lambda z, e: close_trial(z, e.data["cost"]), "ready",
        "no scoring request remains", "charge the cost and close the trial unresolved"),
    Row(19, ("reconciling",), ("job failed",), matches_pending, failed, "ready",
        "the job ID matches the pending trial", "apply row 10's update"),
    Row(20, ("reconciling",), ("job running",), matches_pending,
        lambda z, e: replace(z, pending=replace(z.pending, job=e.data["job"])), "running",
        "the scheduler reports the pending job", "resume waiting for completion"),
    Row(20, ("reconciling",), ("not found",), lambda z, e: z.pending is not None and z.pending.job is None,
        keep, "dispatching",
        "no job ID is recorded and the scheduler has none for the operation ID",
        "resend the stored request under the same operation ID"),
    Row(21, ("proposing",), ("recovered",), lambda z, e: True,
        lambda z, e: replace(z, proposals_used=z.proposals_used + 1, feedback="policy call lost in a restart"), "ready",
        "none", "count the lost call as a proposal"),
    Row(22, ANY, ("score",), not_pending_score, keep, "=",
        "the score is not for a pending trial", "log and ignore"),
    Row(23, ("stopped",), ("job done", "job failed", "score"),
        lambda z, e: matches_pending(z, e) and (e.kind != "score" or e.data.get("trial") == z.pending.trial),
        stopped_close, "=", "the report is for the pending trial",
        "charge the reported or known cost and close the trial without promotion"),
    Row(23, ("stopped",), ("timeout",), lambda z, e: z.pending is not None,
        lambda z, e: close_trial(z, z.pending.estimate), "=", "a trial is still pending",
        "charge the full reservation and close the trial without promotion"),
)


def step(z: ControllerRecord, e: Event, rows: tuple[Row, ...] = ROWS) -> LogEntry:
    """Fire the one enabled row, or log the event and leave the record unchanged."""
    enabled = [row for row in rows if z.mode in row.modes and e.kind in row.events and row.guard(z, e)]
    if len(enabled) > 1:
        raise AssertionError(f"Nondeterministic table: {z.mode} on {e.kind}, rows {[r.ref for r in enabled]}")
    if not enabled:
        return LogEntry(0, z.mode, e, z.mode, None, z)
    row = enabled[0]
    nxt = z.mode if row.next == "=" else row.next
    # Every fired row is appended to the durable run log before the runtime acts on it.
    updated = replace(row.update(z, e), mode=nxt, checkpoint=z.checkpoint + 1)
    return LogEntry(0, z.mode, e, nxt, row, updated)


def gate(z: ControllerRecord) -> Event:
    """Validate the recorded proposal and bind the approval to its arguments. The gate is code, never the policy."""
    proposal = z.proposal or {}
    lr = proposal.get("lr", LR_RANGE[0])
    valid = (
        LR_RANGE[0] <= lr <= LR_RANGE[1]
        and isinstance(proposal.get("seed"), int)
        and MIN_TRIAL <= proposal.get("estimate", 0) <= unreserved(z)
        and z.stop_requested is None
    )
    if valid:
        return Event("allowed", "gate", {"request": dict(proposal)})
    return Event("rejected", "gate", {"reason": "arguments or compute estimate outside the protocol"})


@dataclass(frozen=True)
class Scenario:
    name: str
    proposals: tuple[Event, ...]
    environment: tuple[Event, ...]
    policy_turns: int | None = None  # pause after this many policy events


def run(scenario: Scenario, max_steps: int = 200) -> list[LogEntry]:
    """Drive the controller. Each event comes from the source that owns the current mode."""
    z = ControllerRecord()
    proposals = list(scenario.proposals)
    environment = list(scenario.environment)
    log: list[LogEntry] = []
    turns = 0
    for seq in range(1, max_steps + 1):
        if environment and environment[0].at == z.mode:
            event = environment.pop(0)
        elif z.mode == "ready":
            event = Event("check", "controller")
        elif z.mode == "proposing":
            if not proposals or (scenario.policy_turns is not None and turns >= scenario.policy_turns):
                break
            reply = proposals.pop(0)
            event = replace(reply, data={**reply.data, "turn": z.proposals_used + 1})
            turns += 1
        elif z.mode == "authorizing":
            event = gate(z)
        else:
            break
        entry = step(z, event)
        log.append(replace(entry, seq=seq))
        z = entry.record
        if z.mode == "authorizing" and scenario.policy_turns is not None and turns >= scenario.policy_turns:
            break
        if z.mode == "done":
            break
    return log


def env(kind: str, at: str, source: str, **data) -> Event:
    return Event(kind, source, data, at)


TRIAL_1 = Event("trial proposed", "policy", {"lr": 3e-4, "seed": 7, "estimate": 0.7})
REPLICATE = Event("trial proposed", "policy", {"replicate": "t1", "seed": 11, "estimate": 0.7})
JOB_42 = (
    env("accepted", "dispatching", "scheduler", operation="t1-submit", job="#42"),
    env("job done", "running", "scheduler", job="#42", cost=0.6),
)

SCENARIOS = {
    "ordinary": Scenario(
        "ordinary",
        (TRIAL_1, REPLICATE),
        JOB_42 + (env("score", "scoring", "evaluator", trial="t1", score=0.851, evaluator=EVALUATOR),),
        policy_turns=2,
    ),
    "lost-score": Scenario(
        "lost-score",
        (TRIAL_1, REPLICATE),
        JOB_42 + (
            env("timeout", "scoring", "clock"),
            env("score found", "reconciling", "evaluator store", trial="t1", score=0.851, evaluator=EVALUATOR),
            env("score", "ready", "evaluator", trial="t1", score=0.851, evaluator=EVALUATOR),
        ),
        policy_turns=2,
    ),
    "restart": Scenario(
        "restart",
        (TRIAL_1, REPLICATE),
        JOB_42 + (
            env("recovered", "scoring", "runtime"),
            env("score found", "reconciling", "evaluator store", trial="t1", score=0.851, evaluator=EVALUATOR),
        ),
        policy_turns=2,
    ),
    "cancel": Scenario(
        "cancel",
        (TRIAL_1,),
        (
            JOB_42[0],
            env("cancel", "running", "operator"),
            env("job failed", "stopped", "scheduler", job="#42", cost=0.4, reason="cancelled"),
            env("holdout scored", "stopped", "fixed evaluator", score=0.835),
        ),
    ),
}


def describe(z: ControllerRecord) -> str:
    pending = "none"
    if z.pending:
        parts = [z.pending.trial, z.pending.operation]
        if z.pending.job:
            parts.append(f"job {z.pending.job}")
        pending = " ".join(parts)
    text = (f"incumbent {z.incumbent} {z.incumbent_score:.3f} | unspent {z.unspent:.1f} GPU-h, "
            f"reserved {z.reserved:.1f} | trials {z.trials_used}/{TRIAL_CAP} | "
            f"proposals {z.proposals_used}/{PROPOSAL_CAP} | pending {pending} | checkpoint {z.checkpoint}")
    if z.stop_reason:
        text += f" | stopped: {z.stop_reason}"
    if z.holdout_score is not None:
        text += f" | holdout {z.holdout_score:.3f}"
    return text


def format_event(e: Event) -> str:
    details = ", ".join(f"{key} {value}" for key, value in e.data.items())
    return f"{e.kind} ({e.source}{': ' + details if details else ''})"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--scenario", choices=sorted(SCENARIOS), default="ordinary")
    parser.add_argument("--table", action="store_true", help="print the transition table and exit")
    args = parser.parse_args()
    if args.table:
        for row in ROWS:
            nxt = "(unchanged)" if row.next == "=" else row.next
            modes = "any mode in Search" if row.modes == SEARCH else "any mode" if row.modes == ANY else ", ".join(row.modes)
            print(f"{row.ref:>2}. {modes} | {' or '.join(row.events)} | {row.guard_text} | {row.update_text} | {nxt}")
        return
    print(f"Scenario {args.scenario} (schematic inputs)")
    for entry in run(SCENARIOS[args.scenario]):
        if entry.row:
            arrow = f"{entry.mode} -> {entry.next} (row {entry.row.ref})"
        else:
            arrow = f"{entry.mode} (no row, logged)"
        print(f"{entry.seq:>2}. {arrow:<38} {format_event(entry.event)}")
        print(f"    {describe(entry.record)}")


if __name__ == "__main__":
    main()

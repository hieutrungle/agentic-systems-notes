import random
import unittest
from dataclasses import replace
from functools import reduce

from labs.controller import (
    BUDGET, PROPOSAL_CAP, RECOVERY_ATTEMPTS, ROWS, SCENARIOS, TRIAL_CAP, ControllerRecord, Event, Pending,
    Scenario, env, run, step,
)

IN_FLIGHT = ("dispatching", "running", "scoring", "reconciling")


def same_record(a: ControllerRecord, b: ControllerRecord) -> bool:
    """Compare controller records while ignoring the log sequence number."""
    return replace(a, checkpoint=0) == replace(b, checkpoint=0)


def record_at(mode: str, **changes) -> ControllerRecord:
    """A record with trial t1 pending, as after checkpoint 3 of the ordinary trace."""
    pending = Pending("t1", "t1-submit", {"lr": 3e-4, "seed": 7, "estimate": 0.7}, 0.7)
    base = ControllerRecord(mode=mode, reserved=0.7, trials_used=1, proposals_used=1, pending=pending)
    return replace(base, **changes)


class OrdinaryTrialTests(unittest.TestCase):
    def test_trial_one_is_kept_and_policy_chooses_again(self):
        log = run(SCENARIOS["ordinary"])
        self.assertEqual([(e.mode, e.next, e.row.ref) for e in log], [
            ("ready", "proposing", 1), ("proposing", "authorizing", 3), ("authorizing", "dispatching", 7),
            ("dispatching", "running", 8), ("running", "scoring", 9), ("scoring", "ready", 11),
            ("ready", "proposing", 1), ("proposing", "authorizing", 3)])
        final = log[-1].record
        self.assertEqual((final.incumbent, final.incumbent_score), ("t1", 0.851))
        self.assertEqual((final.unspent, final.reserved, final.trials_used, final.proposals_used), (1.4, 0.0, 1, 2))
        self.assertEqual(final.proposal, {"replicate": "t1", "seed": 11, "estimate": 0.7})
        self.assertEqual([e.record.checkpoint for e in log], list(range(1, 9)))

    def test_policy_events_take_effect_only_in_proposing(self):
        for name in SCENARIOS:
            for entry in run(SCENARIOS[name]):
                if entry.event.source == "policy" and entry.row:
                    self.assertEqual(entry.mode, "proposing")

    def test_checkpoint_three_stores_the_bound_request_before_any_reply(self):
        allowed = next(e for e in run(SCENARIOS["ordinary"]) if e.event.kind == "allowed")
        pending = allowed.record.pending
        self.assertEqual((pending.operation, pending.job), ("t1-submit", None))
        self.assertEqual(pending.request, {"lr": 3e-4, "seed": 7, "estimate": 0.7})
        self.assertEqual(allowed.record.reserved, 0.7)


class AuthorizationTests(unittest.TestCase):
    def setUp(self):
        self.z = ControllerRecord(mode="authorizing", proposals_used=1,
                                  proposal={"lr": 3e-4, "seed": 7, "estimate": 0.7})

    def test_approval_must_bind_the_recorded_arguments(self):
        forged = Event("allowed", "gate", {"request": {"lr": 5.0, "seed": 7, "estimate": 1.9}})
        entry = step(self.z, forged)
        self.assertIsNone(entry.row)
        self.assertEqual(entry.record, self.z)

    def test_approval_cannot_exceed_unreserved_compute(self):
        z = replace(self.z, unspent=0.6)
        entry = step(z, Event("allowed", "gate", {"request": dict(z.proposal)}))
        self.assertIsNone(entry.row)

    def test_no_approval_after_a_stop_request(self):
        z = replace(self.z, stop_requested="policy stop")
        self.assertIsNone(step(z, Event("allowed", "gate", {"request": dict(z.proposal)})).row)


class LostScoreTests(unittest.TestCase):
    def test_reconciliation_reaches_the_ordinary_record(self):
        ordinary, lost = run(SCENARIOS["ordinary"]), run(SCENARIOS["lost-score"])
        first_close = lambda log: next(e.record for e in log if e.next == "ready" and e.record.decided)
        self.assertTrue(same_record(first_close(ordinary), first_close(lost)))
        self.assertTrue(same_record(ordinary[-1].record, lost[-1].record))
        self.assertEqual([e.row.ref for e in lost[5:8]], [14, 16, 22])

    def test_decide_once_holds_without_the_log_row(self):
        lost = run(SCENARIOS["lost-score"])
        duplicate = next(e for e in lost if e.mode == "ready" and e.event.kind == "score")
        before = lost[lost.index(duplicate) - 1].record
        without_log_row = tuple(row for row in ROWS if row.ref != 22)
        entry = step(before, duplicate.event, without_log_row)
        self.assertIsNone(entry.row)
        self.assertEqual(entry.record, before)

    def test_restart_in_scoring_reconciles_like_a_timeout(self):
        ordinary, restart = run(SCENARIOS["ordinary"]), run(SCENARIOS["restart"])
        self.assertEqual([e.row.ref for e in restart[5:7]], [14, 16])
        self.assertTrue(same_record(ordinary[-1].record, restart[-1].record))

    def test_no_trial_is_issued_while_reconciling(self):
        log = run(SCENARIOS["lost-score"])
        modes = [e.mode for e in log]
        start = modes.index("reconciling")
        self.assertNotEqual(log[start].event.kind, "allowed")
        self.assertEqual(log[start].next, "ready")

    def test_score_lookup_after_dispatch_timeout_does_not_crash(self):
        z = record_at("reconciling")
        entry = step(z, Event("score found", "evaluator store", {"trial": "t1", "score": 0.9, "evaluator": "v1"}))
        self.assertIsNone(entry.row)

    def test_recovery_attempts_are_bounded(self):
        z = record_at("running")
        refs = []
        for kind in ("timeout", "job running", "timeout", "job running", "timeout", "job running", "timeout"):
            entry = step(z, Event(kind, "clock", {"job": "#42"} if kind == "job running" else {}))
            refs.append(entry.row.ref)
            z = entry.record
        self.assertEqual(refs, [14, 20, 14, 20, 14, 20, 15])
        self.assertEqual((z.mode, z.pending, z.unspent, z.reserved), ("ready", None, 1.3, 0.0))
        self.assertEqual(RECOVERY_ATTEMPTS, 3)

    def test_scoring_requests_are_bounded_after_a_running_timeout(self):
        z = record_at("running", pending=replace(record_at("running").pending, job="#42"))
        refs = []
        for event in (Event("timeout", "clock"), Event("job done, unscored", "scheduler", {"job": "#42", "cost": 0.6}),
                      Event("timeout", "clock"), Event("job done, unscored", "scheduler", {"job": "#42", "cost": 0.6}),
                      Event("timeout", "clock"), Event("job done, unscored", "scheduler", {"job": "#42", "cost": 0.6})):
            entry = step(z, event)
            refs.append(entry.row.ref)
            z = entry.record
        self.assertEqual(refs, [14, 17, 14, 17, 14, 18])
        self.assertEqual((z.mode, z.unspent, z.incumbent), ("ready", 1.4, "baseline"))


class StopTests(unittest.TestCase):
    def test_cancel_closes_the_trial_before_done(self):
        log = run(SCENARIOS["cancel"])
        stop_index = next(i for i, e in enumerate(log) if e.next == "stopped")
        self.assertFalse(any(e.event.kind in ("allowed", "trial proposed") for e in log[stop_index:]))
        final = log[-1].record
        self.assertEqual((final.mode, final.incumbent, final.unspent, final.reserved), ("done", "baseline", 1.6, 0.0))
        self.assertIsNone(final.pending)

    def test_late_score_after_stop_closes_the_trial_without_promotion(self):
        z = record_at("stopped", stop_reason="deadline",
                      pending=replace(record_at("stopped").pending, job="#42", cost=0.6, score_request="t1-score"))
        z = step(z, Event("score", "evaluator", {"trial": "t1", "score": 0.9, "evaluator": "v1"})).record
        self.assertEqual((z.incumbent, z.unspent, z.reserved, z.pending), ("baseline", 1.4, 0.0, None))

    def test_holdout_waits_for_the_pending_trial(self):
        z = record_at("stopped", stop_reason="cancel")
        self.assertIsNone(step(z, Event("holdout scored", "fixed evaluator", {"score": 0.8})).row)
        z = step(z, Event("timeout", "clock")).record
        self.assertEqual((z.pending, z.unspent), (None, 1.3))
        self.assertEqual(step(z, Event("holdout scored", "fixed evaluator", {"score": 0.8})).next, "done")

    def test_stopped_rejects_new_policy_events(self):
        stopped = replace(ControllerRecord(), mode="stopped", stop_reason="cancel")
        entry = step(stopped, Event("trial proposed", "policy", {"lr": 3e-4, "seed": 1, "estimate": 0.5, "turn": 1}))
        self.assertIsNone(entry.row)
        self.assertEqual(entry.record, stopped)

    def test_rejection_loop_ends_at_proposal_cap(self):
        bad = Event("trial proposed", "policy", {"lr": 1.0, "seed": 1, "estimate": 0.5})
        final = run(Scenario("reject", (bad,) * 20, ()))[-1].record
        self.assertEqual((final.mode, final.stop_reason), ("stopped", "proposal cap"))
        self.assertEqual((final.trials_used, final.proposals_used), (0, PROPOSAL_CAP))
        self.assertEqual(final.feedback, "arguments or compute estimate outside the protocol")

    def test_trial_cap_ends_the_search(self):
        proposals, environment = [], []
        for n in range(1, TRIAL_CAP + 1):
            proposals.append(Event("trial proposed", "policy", {"lr": 1e-4 * n, "seed": n, "estimate": 0.3}))
            environment += [
                env("accepted", "dispatching", "scheduler", operation=f"t{n}-submit", job=f"#{40 + n}"),
                env("job done", "running", "scheduler", job=f"#{40 + n}", cost=0.2),
                env("score", "scoring", "evaluator", trial=f"t{n}", score=0.84 + n / 1000, evaluator="v1"),
            ]
        proposals.append(proposals[0])
        final = run(Scenario("cap", tuple(proposals), tuple(environment)))[-1].record
        self.assertEqual((final.mode, final.stop_reason, final.trials_used), ("stopped", "trial cap", TRIAL_CAP))
        self.assertEqual((final.incumbent, final.unspent), ("t5", 1.0))

    def test_policy_stop_is_a_request_checked_in_ready(self):
        log = run(Scenario("policy-stop", (Event("stop proposed", "policy"),), ()))
        self.assertEqual([(e.mode, e.next) for e in log],
                         [("ready", "proposing"), ("proposing", "ready"), ("ready", "stopped")])
        self.assertEqual(log[-1].record.stop_reason, "policy stop")

    def test_failed_job_with_zero_cost_charges_nothing(self):
        z = record_at("running", pending=replace(record_at("running").pending, job="#42"))
        z = step(z, Event("job failed", "scheduler", {"job": "#42", "cost": 0.0})).record
        self.assertEqual((z.mode, z.unspent, z.reserved, z.decided), ("ready", 2.0, 0.0, ("t1",)))


class TableTests(unittest.TestCase):
    def test_replaying_recorded_events_rebuilds_the_record(self):
        for name in SCENARIOS:
            with self.subTest(name=name):
                log = run(SCENARIOS[name])
                rebuilt = reduce(lambda z, e: step(z, e.event).record, log, ControllerRecord())
                self.assertEqual(rebuilt, log[-1].record)

    def test_stale_policy_reply_matches_no_row(self):
        z = ControllerRecord(mode="proposing", proposals_used=1)
        stale = Event("trial proposed", "policy", {"lr": 3e-4, "seed": 7, "estimate": 0.7, "turn": 1})
        self.assertIsNone(step(z, stale).row)
        self.assertEqual(step(z, replace(stale, data={**stale.data, "turn": 2})).row.ref, 3)

    def test_every_waiting_mode_has_a_timeout_and_hard_stop_rows(self):
        for mode in IN_FLIGHT:
            kinds = {kind for row in ROWS if mode in row.modes for kind in row.events}
            self.assertTrue({"timeout", "recovered", "cancel", "deadline"} <= kinds, mode)
        self.assertIn("recovered", {k for row in ROWS if "proposing" in row.modes for k in row.events})
        self.assertIn("timeout", {k for row in ROWS if "stopped" in row.modes for k in row.events})

    def test_random_event_sequences_preserve_the_invariants(self):
        rng = random.Random(20261118)
        kinds = ["check", "trial proposed", "stop proposed", "invalid output", "allowed", "rejected", "accepted",
                 "job done", "job failed", "score", "score found", "job done, unscored", "job running", "not found",
                 "timeout", "recovered", "cancel", "deadline", "holdout scored"]
        for _ in range(400):
            z = ControllerRecord()
            for _ in range(150):
                kind = rng.choice(kinds)
                trial = rng.choice([f"t{z.trials_used}", f"t{z.trials_used + 1}", "t9"])
                data = {"turn": z.proposals_used + rng.choice([0, 1]), "lr": rng.choice([3e-4, 1.0]),
                        "seed": 7, "estimate": rng.choice([0.3, 0.7, 1.9]), "trial": trial,
                        "operation": f"{trial}-submit", "job": rng.choice(["#1", "#2"]),
                        "cost": rng.choice([0.0, 0.2, 0.6]), "score": rng.random(), "evaluator": rng.choice(["v1", "v0"])}
                if z.pending:  # the scheduler caps each trial at its reservation
                    data["cost"] = min(data["cost"], z.pending.estimate)
                if kind == "allowed":
                    data = {"request": z.proposal if rng.random() < 0.8 else {"lr": 5.0}}
                before = z
                z = step(z, Event(kind, "fuzz", data)).record
                self.assertGreaterEqual(z.reserved, -1e-9)
                self.assertGreaterEqual(round(z.unspent - z.reserved, 3), -1e-9)
                self.assertLessEqual(z.trials_used, TRIAL_CAP)
                self.assertLessEqual(z.proposals_used, PROPOSAL_CAP)
                self.assertEqual(len(z.decided), len(set(z.decided)))
                if z.pending:
                    self.assertNotIn(z.pending.trial, z.decided)
                    self.assertIn(z.mode, IN_FLIGHT + ("stopped",))
                    self.assertAlmostEqual(z.reserved, z.pending.estimate)
                else:
                    self.assertNotIn(z.mode, IN_FLIGHT)
                    self.assertAlmostEqual(z.reserved, 0.0)
                if before.mode in ("stopped", "done"):
                    self.assertIn(z.mode, ("stopped", "done"))
                    self.assertEqual(z.trials_used, before.trials_used)
                    self.assertEqual((z.incumbent, z.incumbent_score), (before.incumbent, before.incumbent_score))
                if z.mode == "done":
                    self.assertIsNone(z.pending)
                if z.holdout_score is not None:
                    self.assertEqual(z.mode, "done")
                self.assertGreaterEqual(z.unspent, -1e-9)
                self.assertLessEqual(z.unspent, BUDGET)


if __name__ == "__main__":
    unittest.main()

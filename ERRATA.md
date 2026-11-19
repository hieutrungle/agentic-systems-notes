# Errata

Record corrections to published material here, newest first. Include the date, page and section, prior claim, corrected claim, and supporting source or reproducible check.

## 2026-11-19 · Block 01, Figure 2

The opening card labeled the goal, ledger, and observation as initial inputs without identifying each value. The first card now states the goal. Step forward once to see the initial ledger and the evaluator’s baseline score of 0.842, each paired with its symbol. After job #42 completes, the feedback step likewise distinguishes its reported score and cost from the updated ledger. [Figure 2 and text walkthrough](https://hieutrungle.github.io/agentic-systems-notes/curriculum/01-agent-fundamentals.html#fig-agent-runtime)

## 2026-11-19 · Block 02, lost replies and the launch lookup in §7 and §12

The prior §7 said the score reply never arrived, although the trace delivers it after the lookup. The reply misses the scoring deadline and later arrives after the trial is closed. The prior §12 inferred the crash happened before launch from an empty host lookup. The lookup leaves open whether the original request is still in transit. A resend uses the same run ID and relies on the host to deduplicate it. See [the lost-score trace](https://hieutrungle.github.io/agentic-systems-notes/curriculum/02-agent-loop-state-machines.html#trace-2-a-lost-score-reply) and run `python -m labs.controller --scenario lost-score` or `python -m labs.controller --table` for the recovery rules.

## 2026-11-19 · Block 02, rows 12, 15, 17, 20, 23 and §12

A fresh-context review of the published lesson found five gaps. (1) No row requested the holdout score after a hard stop: row 2 requested it, but rows 12 and 23 did not, so a cancelled run could wait in Stopped. Row 12 now requests the holdout score when no trial is pending, and row 23 requests it after closing the pending trial. (2) §7 listed the close-once guards without row 15, and row 15's guard text omitted the pending trial. (3) §7 said each lookup result has exactly one row; rows 20 and 23 each hold two rules, and a result can match no row, so the lesson now says at most one row fires and defines the grouped rows in §1 and §4. (4) §12 introduced a failed evaluation without a row to handle it; the redesign now adds one. (5) Row 17's text said "the same scoring ID", but a trial reconciled from Dispatching or Running has not requested a score; it now says the trial's scoring ID. Row numbers and lab behaviour are unchanged: `labs/controller.py` changed only in row text, and `python -m labs.controller --table` prints the corrected rows. See [the transition table](https://hieutrungle.github.io/agentic-systems-notes/curriculum/02-agent-loop-state-machines.html#the-transition-table).

## 2026-11-18 · Block 01, criteria table in §5

The table defined the runtime success criterion as accepting "a candidate that beats the baseline on the selection metric." That merged two different rules. Promotion compares a candidate with the current incumbent: a candidate becomes the incumbent only if it strictly beats the incumbent's validation score, which is how the §3 walkthrough and Figure 4 behave. Run success is judged once at the end: the frozen final selection improves on the baseline when both are scored on the holdout. The revised table lists the promotion rule and the run success criterion as separate rows. See [the criteria table](https://hieutrungle.github.io/agentic-systems-notes/curriculum/01-agent-fundamentals.html#the-rl-mdp-and-pomdp-connection).

## 2026-11-18 · Block 02, loop summary, state machines, and checkpoints

The initial draft summarized the loop as `observe → update state → choose action → execute`, which merged proposal, authorization, dispatch, and execution. The revised lesson keeps them as separate modes and events (Proposing, Authorizing, Dispatching, and the scheduler's acknowledgement), consistent with the Block 01 correction below. The draft also said an explicit state machine specifies "deterministic routing." A state machine fixes which transitions are legal, and a policy can still choose among the legal edges. Determinism describes the transition taken for a given record and event. Finally, the draft advised persisting the pending operation ID "before yielding control." The revised lesson commits the trial and operation ID before dispatch and explains that this checkpoint proves only that the request may have been sent. `python -m labs.controller --scenario lost-score` and `tests/test_controller.py` reproduce the corrected behavior. See [the transition table](https://hieutrungle.github.io/agentic-systems-notes/curriculum/02-agent-loop-state-machines.html#the-transition-table).

## 2026-11-17 · Block 01, runtime model and Figure 2

The previous model equated dispatch with the operation applied by the environment, and Figure 2 labeled submission as execution. Dispatch is an attempt. The scheduler can accept a request even if the acknowledgement is lost, and a dispatched request may never reach the scheduler. The controller records its evidence separately from the operation the scheduler actually applied. In [the revised figure](https://hieutrungle.github.io/agentic-systems-notes/curriculum/01-agent-fundamentals.html#fig-agent-runtime), step through dispatch, scheduler acceptance, and job completion to inspect the three events.

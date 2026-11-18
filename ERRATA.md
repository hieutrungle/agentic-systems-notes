# Errata

Record corrections to published material here, newest first. Include the date, page and section, prior claim, corrected claim, and supporting source or reproducible check.

## 2026-11-18 · Block 01, criteria table in §5

The table defined the runtime success criterion as accepting "a candidate that beats the baseline on the selection metric." That merged two different rules. Promotion compares a candidate with the current incumbent: a candidate becomes the incumbent only if it strictly beats the incumbent's validation score, which is how the §3 walkthrough and Figure 4 behave. Run success is judged once at the end: the frozen final selection improves on the baseline when both are scored on the holdout. The revised table lists the promotion rule and the run success criterion as separate rows. See [the criteria table](https://hieutrungle.github.io/agentic-systems-notes/curriculum/01-agent-fundamentals.html#the-rl-mdp-and-pomdp-connection).

## 2026-11-18 · Block 02, loop summary, state machines, and checkpoints

The initial draft summarized the loop as `observe → update state → choose action → execute`, which merged proposal, authorization, dispatch, and execution. The revised lesson keeps them as separate modes and events (Proposing, Authorizing, Dispatching, and the scheduler's acknowledgement), consistent with the Block 01 correction below. The draft also said an explicit state machine specifies "deterministic routing." A state machine fixes which transitions are legal, and a policy can still choose among the legal edges. Determinism describes the transition taken for a given record and event. Finally, the draft advised persisting the pending operation ID "before yielding control." The revised lesson commits the trial and operation ID before dispatch and explains that this checkpoint proves only that the request may have been sent. `python -m labs.controller --scenario lost-score` and `tests/test_controller.py` reproduce the corrected behavior. See [the transition table](https://hieutrungle.github.io/agentic-systems-notes/curriculum/02-agent-loop-state-machines.html#the-transition-table).

## 2026-11-17 · Block 01, runtime model and Figure 2

The previous model equated dispatch with the operation applied by the environment, and Figure 2 labeled submission as execution. Dispatch is an attempt. The scheduler can accept a request even if the acknowledgement is lost, and a dispatched request may never reach the scheduler. The controller records its evidence separately from the operation the scheduler actually applied. In [the revised figure](https://hieutrungle.github.io/agentic-systems-notes/curriculum/01-agent-fundamentals.html#fig-agent-runtime), step through dispatch, scheduler acceptance, and job completion to inspect the three events.

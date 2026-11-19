"""Generate the Block 02 controller figures from one data source.

Run from the repository root:

    python docs/assets/diagrams/controller_figures.py

The script writes four HTML includes under docs/curriculum/_figures/:

- controller-overview.html  Figure 1, interactive overview of modes, groups, and event sources
- controller-states.html    Figure 2, stepped build of transition rows 1-13
- controller-trace.html     Figure 3, stepped traces (ordinary, lost score reply, cancel)
- controller-upstream.html  Figure 4, stepped walk through the upstream AutoResearch loop

Row text is the lesson's wording. Every trace value (row number, mode, incumbent,
compute, counters, checkpoint) is computed by running labs.controller, and the script
stops if an authored stage disagrees with the lab. Without JavaScript, each stepped
figure shows its steps as an ordered list.
"""
from __future__ import annotations

import sys
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from labs import controller as lab  # noqa: E402

OUT = ROOT / "docs" / "curriculum" / "_figures"

# ---------------------------------------------------------------------------
# Row text. Lesson wording, verified against the lab's rows (same numbers).
# ROWS: number -> (from, to, owner, event, guard, update, note)
# UPSTREAM: rows rewritten for the upstream loop -> (event, guard, update, change note)
# ---------------------------------------------------------------------------

OWNER = {'controller': 'Controller rule',
 'policy': 'Policy',
 'decoder': 'Decoder',
 'gate': 'Gate',
 'scheduler': 'Scheduler',
 'evaluator': 'Evaluator',
 'stop': 'Operator or clock',
 'holdout': 'Fixed evaluator',
 'recovery': 'Clock or process host',
 'lookup': 'Lookup',
 'host': 'Process host'}

ROWS = {1: ('Ready',
     'Proposing',
     'controller',
     'Limits checked (controller)',
     'No stop requested, fewer than 5 trials, fewer than 10 proposals, and at least 0.3 GPU-h unreserved',
     "Build the policy's context from the ledger",
     'Ready is the only mode that starts a policy turn, so this check runs before every turn.'),
 2: ('Ready',
     'Stopped',
     'controller',
     'Limits checked (controller)',
     'A stop was requested or a limit is reached',
     'Record the stop reason, freeze the incumbent, and request the holdout score',
     'Rows 1 and 2 share a mode and an event. Their guards exclude each other, so exactly one fires.'),
 3: ('Proposing',
     'Authorizing',
     'policy',
     'Trial proposed (policy)',
     'The reply answers the current turn',
     'Count the proposal and record its arguments',
     "One of the policy's two choices. A stale reply from an earlier turn fails the guard and matches no row."),
 4: ('Proposing',
     'Ready',
     'policy',
     'Stop proposed (policy)',
     'The reply answers the current turn',
     'Count the proposal and record the stop request',
     'A stop proposal is a request. Row 2 acts on it in Ready. The policy can ask to stop early, but it cannot keep '
     'the run going past a limit.'),
 5: ('Proposing',
     'Ready',
     'decoder',
     'Invalid output (decoder)',
     'The report concerns the current turn',
     'Count the proposal and record the error for the next context',
     'A reply the decoder cannot use, or one that misses its deadline, still counts against the 10-proposal cap.'),
 6: ('Authorizing',
     'Ready',
     'gate',
     'Rejected (gate)',
     'None',
     'Record the reason for the next context',
     'Nothing was sent. The policy sees the reason on its next turn.'),
 7: ('Authorizing',
     'Dispatching',
     'gate',
     'Allowed (gate)',
     'The approval binds the recorded arguments, the estimate fits the unreserved compute, and no stop is requested',
     'Mint trial and operation IDs, store the approved request, reserve the estimate, and count the trial. Commit, '
     'then send.',
     'Commit before sending. A crash after the commit leaves evidence that the request may have been sent. The text '
     'below explains why.'),
 8: ('Dispatching',
     'Running',
     'scheduler',
     'Accepted (scheduler)',
     'The operation ID matches the pending trial',
     'Record the job ID',
     ''),
 9: ('Running',
     'Scoring',
     'scheduler',
     'Job done (scheduler)',
     'The job ID matches the pending trial',
     'Record the cost and request a score under a scoring ID',
     ''),
 10: ('Running',
      'Ready',
      'scheduler',
      'Job failed (scheduler)',
      'The job ID matches the pending trial',
      'Charge the cost and close the trial without promotion',
      'Closing a trial charges its cost, releases its reservation, and moves its ID from the pending slot to the '
      'closed set, all in one update.'),
 11: ('Scoring',
      'Ready',
      'evaluator',
      'Score (evaluator)',
      'The score is for the pending trial and comes from evaluator <code>v1</code>',
      'Charge the cost, keep or discard the candidate, and close the trial',
      'Promotion happens only here and in row 16. The policy cannot produce a score event, so it cannot promote a '
      'candidate.'),
 12: ('Any mode in Search',
      'Stopped',
      'stop',
      'Cancel or deadline (operator, clock)',
      'None',
      'Record the hard stop, freeze the incumbent, request cancellation of any pending job, and request the holdout '
         'score if no trial is pending',
      'Applies at any moment in the search. The policy cannot prevent it.'),
 13: ('Stopped',
      'Done',
      'holdout',
      'Holdout scored (fixed evaluator)',
      'No trial is pending and no holdout score is recorded',
      'Record the final score',
      'The only edge out of Stopped. The holdout score enters the record only here.'),
 14: ('Dispatching, Running, Scoring, or Reconciling',
      'Reconciling',
      'recovery',
      'Timeout (clock) or recovered after a restart (process host)',
      'Recovery attempts remain',
      'Count the attempt. Look up the stored score by scoring ID, if one exists, then the job by operation ID.',
      'The reservation stays in place and no new trial is issued. In Trace 2 the scoring timeout fires this row.'),
 15: ('Dispatching, Running, Scoring, or Reconciling',
      'Ready',
      'recovery',
      'Timeout or recovered',
      'A trial is pending and no recovery attempt remains',
      'Charge the full reservation, request cancellation, and close the trial unresolved',
      'The scheduler caps a trial at its reservation, so the full reservation bounds what the trial spent.'),
 16: ('Reconciling',
      'Ready',
      'lookup',
      'Score found by lookup, or a late score (evaluator)',
      'The score is for the pending trial, its cost is known, and it comes from <code>v1</code>',
      "Apply row 11's update",
      'In Trace 2 the lookup finds t1 = 0.851 under <code>t1-score</code>, and this row keeps t1.'),
 17: ('Reconciling',
      'Scoring',
      'lookup',
      'Job done, no stored score (lookup)',
      'A scoring request remains',
      'Request the score under the trial\'s scoring ID',
      'Reusing the scoring ID lets the evaluator return a stored score instead of computing a second one.'),
 18: ('Reconciling',
      'Ready',
      'lookup',
      'Job done, no stored score (lookup)',
      'No scoring request remains',
      'Charge the cost and close the trial unresolved',
      ''),
 19: ('Reconciling',
      'Ready',
      'lookup',
      'Job failed (lookup)',
      'The job ID matches the pending trial',
      "Apply row 10's update",
      ''),
 20: ('Reconciling',
      'Running or Dispatching',
      'lookup',
      'Job running, or no job for the operation ID (lookup)',
      'The job matches the pending trial, or no job ID has been recorded yet',
      'Resume waiting, or resend the stored request under the same operation ID',
      'Resending under the same operation ID lets the scheduler deduplicate a request that did arrive.'),
 21: ('Proposing',
      'Ready',
      'host',
      'Recovered (process host)',
      'None',
      'Count the lost call as a proposal',
      'A restart in Proposing loses the model call. Authorizing needs no restart row, because the gate is '
      'deterministic code that runs again on the recorded proposal.'),
 22: ('Any mode except Done',
      'Unchanged',
      'evaluator',
      'Score (evaluator)',
      'The score is not for a pending trial',
      'Log and ignore',
      'In Trace 2 the original reply arrives late and lands here. The pending-trial guards on the closing rows already '
      'enforce close once. This row makes the log-and-ignore decision explicit.'),
 23: ('Stopped',
      'Stopped',
      'recovery',
      'Job done, job failed, score, or timeout for the pending trial',
      'A trial is pending',
      'Charge the reported cost, the known cost, or the full reservation, close the trial without promotion, and '
          'then request the holdout score',
      'Late evidence pays for the trial, and the frozen selection stays frozen.')}

UPSTREAM = {1: ('Limits checked (controller)',
     'Fewer than 60 trials and 120 proposals, and no stop requested',
     'Build the context from the ledger: the incumbent commit and its <code>val_bpb</code>, recent results, and the '
     'last diff and log tail of any idea awaiting a fix',
     "The compute check moves to the process host's per-run cap and the 8-hour deadline in row 12."),
 2: ('Limits checked (controller)',
     'A stop was requested, or 60 trials or 120 proposals are reached',
     'Record the stop reason, freeze the incumbent commit, and request the holdout score',
     "Replaces upstream's instruction never to stop."),
 3: ('Patch proposed (policy)',
     'The reply answers the current turn',
     'Count the proposal. Record the diff, its hash, and whether it is a new idea or a fix of an earlier idea.',
     'The proposal is now a patch to <code>train.py</code> instead of a configuration.'),
 6: ('Rejected (gate)',
     'The diff touches another file, adds a dependency, or does not apply to the incumbent commit, or it fixes an idea '
     'that has used three attempts',
     'Record the reason for the next context',
     'Upstream\'s "edit only <code>train.py</code>" and "a few attempts" become guards.'),
 7: ('Allowed (gate)',
     'The approval binds the recorded diff hash, <code>prepare.py</code> and the lock file match their pinned hashes, '
     'and no stop is requested',
     'Mint trial and run IDs. Create the candidate commit on its own ref, and record it with the base commit. Count '
     'the trial and reserve one 7-minute run slot. Commit the checkpoint, then ask the process host to launch.',
     'The branch does not move here. Only a promotion in row 11 moves it.'),
 9: ('Run done (process host)',
     'The run ID matches the pending trial, the exit status is 0, and the weights were saved',
     "Record the training time and peak memory. Request a score under the trial's scoring ID.",
     'Scoring leaves <code>train.py</code>: a pinned evaluator scores the saved weights.'),
 10: ('Run failed (process host)',
      'The run ID matches the pending trial',
      'Covers a nonzero exit, missing weights, or a kill at the 7-minute cap. Store the diff and log tail for a '
      'possible fix, charge the slot, and close the trial as a crash.',
      'The process host enforces the time cap, not the agent.'),
 11: ('Score (pinned evaluator)',
      'The score is for the pending trial and the causality check passed',
      "Charge the slot. If <code>val_bpb</code> is strictly lower than the incumbent's, record the candidate commit as "
      'the incumbent. Close the trial. After the checkpoint, set the branch to the incumbent commit.',
      'Keep or reset is a row fired by the pinned evaluator, not a decision the agent writes.'),
 12: ('Cancel or 8-hour deadline (operator, clock)',
      'None',
      'Record the hard stop, freeze the incumbent commit, and ask the process host to stop any run',
      "A person's interrupt becomes a cancel event instead of killing the agent mid-command.")}


# ---------------------------------------------------------------------------
# Shared diagram. One geometry for Figures 1-3, sized so that 1 viewBox unit is
# about 1 CSS pixel at a 390 px viewport. Edges are orthogonal polylines.
# ---------------------------------------------------------------------------

VB_W, VB_H = 320, 416
NW, NH = 112, 28
CX = 156  # x of the main column's vertical edges
MODES = {  # key: (label, x, y, w, kind)
    "stopped": ("Stopped", 100, 16, NW, ""),
    "done": ("Done", 10, 16, 60, "terminal"),
    "ready": ("Ready", 100, 78, NW, ""),
    "proposing": ("Proposing", 100, 124, NW, "policy"),
    "authorizing": ("Authorizing", 100, 170, NW, "gate"),
    "dispatching": ("Dispatching", 100, 220, NW, ""),
    "running": ("Running", 100, 266, NW, ""),
    "scoring": ("Scoring", 100, 312, NW, ""),
    "reconciling": ("Reconciling", 100, 372, NW, ""),
}
GROUPS = {  # key: (label lines, x, y, w, h, label x, label y)
    "search": (["Search"], 46, 62, 268, 350, 296, 79),
    "flight": (["Trial in", "flight"], 84, 206, 172, 146, 252, 221),
}
TRUNK_X, READY_IN_Y = 300, 86
LANE_X, LANE_IN_Y = 282, 99  # Proposing's returns, so the policy's thick edge has its own line
FLIGHT_BOTTOM = 206 + 146


def mid_y(mode: str) -> int:
    return MODES[mode][2] + NH // 2


def right(mode: str) -> int:
    return MODES[mode][1] + MODES[mode][3]


def down(a: str, b: str) -> list[tuple[int, int]]:
    return [(CX, MODES[a][2] + NH), (CX, MODES[b][2])]


def beside(a: str, b: str) -> list[tuple[int, int]]:
    """Badge position beside a vertical edge from mode a down to mode b."""
    return [(172, (MODES[a][2] + NH + MODES[b][2]) // 2)]


def back_to_ready(mode: str) -> list[tuple[int, int]]:
    y = mid_y(mode)
    if mode == "proposing":
        return [(right(mode), y), (LANE_X, y), (LANE_X, LANE_IN_Y), (right("ready") + 1, LANE_IN_Y)]
    return [(right(mode), y), (TRUNK_X, y), (TRUNK_X, READY_IN_Y), (right("ready") + 1, READY_IN_Y)]


SY, RY, PY = mid_y("stopped"), mid_y("reconciling"), mid_y("proposing")
GAP = (FLIGHT_BOTTOM + MODES["reconciling"][2]) // 2  # between Trial in flight and Reconciling
STOP_TOP = MODES["stopped"][2]
READY_LOOP = (MODES["ready"][2] + 7, MODES["ready"][2] + 21)

# Row -> (polyline, [badge (x, y)], style). Rows that share a path draw the same
# polyline; the current row is raised and drawn in the accent colour.
EDGES = {
    1: (down("ready", "proposing"), beside("ready", "proposing"), ""),
    2: ([(CX, MODES["ready"][2]), (CX, STOP_TOP + NH)], [(172, (STOP_TOP + NH + MODES["ready"][2]) // 2)], ""),
    3: (down("proposing", "authorizing"), beside("proposing", "authorizing"), "policy"),
    4: (back_to_ready("proposing"), [(228, PY)], "policy"),
    5: (back_to_ready("proposing"), [(249, PY)], ""),
    6: (back_to_ready("authorizing"), [(272, mid_y("authorizing"))], ""),
    7: (down("authorizing", "dispatching"), beside("authorizing", "dispatching"), ""),
    8: (down("dispatching", "running"), beside("dispatching", "running"), ""),
    9: (down("running", "scoring"), beside("running", "scoring"), ""),
    10: (back_to_ready("running"), [(276, mid_y("running"))], ""),
    11: (back_to_ready("scoring"), [(276, mid_y("scoring"))], ""),
    12: ([(306, GROUPS["search"][2]), (306, SY), (213, SY)], [(260, SY)], "stop"),
    13: ([(100, SY), (71, SY)], [(85, SY)], ""),
    14: ([(200, FLIGHT_BOTTOM), (200, MODES["reconciling"][2])], [(216, GAP)], ""),
    15: (back_to_ready("reconciling"), [(224, RY)], ""),
    16: (back_to_ready("reconciling"), [(244, RY)], ""),
    17: ([(118, MODES["reconciling"][2]), (118, MODES["scoring"][2] + NH + 1)], [(104, GAP)], ""),
    18: (back_to_ready("reconciling"), [(264, RY)], ""),
    19: (back_to_ready("reconciling"), [(284, RY)], ""),
    # Row 20 resumes in Running or resends from Dispatching: one line with two arrowheads.
    20: ([[(100, RY), (66, RY), (66, mid_y("dispatching")), (99, mid_y("dispatching"))],
          [(66, mid_y("running")), (99, mid_y("running"))]], [(66, 330)], ""),
    21: (back_to_ready("proposing"), [(268, PY)], ""),
    22: ([(100, READY_LOOP[0]), (80, READY_LOOP[0]), (80, READY_LOOP[1]), (99, READY_LOOP[1])],
         [(66, sum(READY_LOOP) // 2)], "loop"),
    23: ([(140, STOP_TOP), (140, STOP_TOP - 12), (172, STOP_TOP - 12), (172, STOP_TOP - 1)], [(190, STOP_TOP - 8)], "loop"),
}


def path_d(points: list[tuple[int, int]]) -> str:
    (x0, y0), rest = points[0], points[1:]
    return f"M{x0} {y0}" + "".join(f"L{x} {y}" for x, y in rest)


def arrow_head(points: list[tuple[int, int]]) -> str:
    (x1, y1), (x2, y2) = points[-2], points[-1]
    dx, dy = (x2 > x1) - (x2 < x1), (y2 > y1) - (y2 < y1)
    # Tip at the end point, 8 units long, 4 units half-width.
    bx, by = x2 - 8 * dx, y2 - 8 * dy
    px, py = -dy * 4, dx * 4
    return f"M{x2} {y2}L{bx + px} {by + py}L{bx - px} {by - py}Z"


def svg_diagram(prefix: str, rows: list[int], badges: bool, label: str, desc_id: str, nodes: bool = True) -> str:
    """The controller diagram. Edge groups carry data-row; nodes carry data-mode."""
    out = [f'<svg class="cm-svg" viewBox="0 0 {VB_W} {VB_H}" role="img" aria-labelledby="{prefix}-svg-title" '
           f'aria-describedby="{desc_id}">', f'<title id="{prefix}-svg-title">{escape(label)}</title>']
    for key, (lines, x, y, w, h, lx, ly) in GROUPS.items():
        out.append(f'<rect class="cm-group cm-group-{key}" x="{x}" y="{y}" width="{w}" height="{h}" rx="9"/>')
        if nodes:
            out.append(f'<text class="cm-group-label" x="{lx}" y="{ly}" text-anchor="end">'
                       + "".join(f'<tspan x="{lx}" dy="{0 if i == 0 else 12}">{t}</tspan>' for i, t in enumerate(lines))
                       + "</text>")
    out.append('<g class="cm-edges">')
    for row in rows:
        points, _, style = EDGES[row]
        lines = points if isinstance(points[0], list) else [points]
        cls = "cm-edge" + (f" is-{style}" if style else "")
        body = "".join(f'<path class="cm-line" d="{path_d(line)}"/><path class="cm-head" d="{arrow_head(line)}"/>'
                       for line in lines)
        out.append(f'<g class="{cls}" data-row="{row}">{body}</g>')
    out.append("</g>")
    if badges:
        out.append('<g class="cm-badges">')
        for row in rows:
            for bx, by in EDGES[row][1]:
                out.append(f'<g class="cm-badge" data-row="{row}"><circle cx="{bx}" cy="{by}" r="9"/>'
                           f'<text x="{bx}" y="{by}" dy="0.35em" text-anchor="middle">{row}</text></g>')
        out.append("</g>")
    if nodes:
        for key, (text, x, y, w, kind) in MODES.items():
            cls = "cm-node" + (f" is-{kind}" if kind else "")
            inner = f'<rect class="cm-node-inner" x="{x + 3}" y="{y + 3}" width="{w - 6}" height="{NH - 6}" rx="3"/>' if kind == "policy" else ""
            out.append(f'<g class="{cls}" data-mode="{key}"><rect x="{x}" y="{y}" width="{w}" height="{NH}" rx="5"/>{inner}'
                       f'<text x="{x + w / 2:g}" y="{y + NH / 2:g}" dy="0.35em" text-anchor="middle">{text}</text></g>')
    out.append("</svg>")
    return "\n".join(out)


def controls(label: str, region: str) -> str:
    return f"""<div class="agent-controls cm-controls" data-controls hidden role="group" aria-label="{label} controls">
  <div class="agent-buttons">
    <button type="button" data-restart aria-controls="{region}">Restart</button>
    <button type="button" data-previous aria-label="Previous step" aria-controls="{region}">← Step</button>
    <button type="button" data-play aria-controls="{region}">Play</button>
    <button type="button" data-next aria-label="Next step" aria-controls="{region}">Step →</button>
  </div>
  <div class="agent-timeline">
    <input type="range" min="0" step="1" value="0" data-seek aria-label="{label} step" aria-controls="{region}">
    <p data-status role="status"></p>
  </div>
</div>"""


def dl(items: list[tuple[str, str]], cls: str = "cm-rule") -> str:
    return f'<dl class="{cls}">' + "".join(f"<div><dt>{k}</dt><dd>{v}</dd></div>" for k, v in items if v) + "</dl>"


def owner_chip(owner_key: str | None, text: str | None = None) -> str:
    if owner_key is None and text is None:
        return ""
    label = text or ("Policy's choice" if owner_key == "policy" else "Fired by: " + OWNER[owner_key])
    cls = "cm-owner" + (" is-policy" if owner_key == "policy" else "")
    return f'<span class="{cls}">{label}</span>'


def row_title(row: int, frm: str | None = None, to: str | None = None) -> str:
    frm = frm or ROWS[row][0]
    to = to or ROWS[row][1]
    return f"Row {row} · {frm} → {to}"

# ---------------------------------------------------------------------------
# Figure 1. The controller at a glance: modes, groups, and who fires the edges.
# Hover, focus, or tap an item to read it. Selecting an event source lights the
# edges it can fire. No row-level detail.
# ---------------------------------------------------------------------------

OVERVIEW_MODES = {  # key: (kind, what happens here, where the lesson develops it)
    "ready": ("Mode", "Between policy turns. The controller checks its limits here before every turn. If no stop is "
              "requested and every limit has room, it builds the policy's context and moves to Proposing. Otherwise "
              "it moves to Stopped. Every return path ends in Ready. The small loop logs and ignores a late "
              "reply for a trial that is already closed.", "Figure 2, steps 2–3"),
    "proposing": ("Mode · the policy's turn", "The policy proposes a trial with its arguments, or asks to stop. A reply "
                  "the decoder cannot use, or one that misses its deadline, counts as invalid output. These are the "
                  "only edges the policy chooses.", "Figure 2, steps 4–6"),
    "authorizing": ("Mode", "The gate checks the proposed trial against the protocol. If it allows the trial, the "
                    "controller records it and reserves compute before anything is sent. If it rejects the trial, "
                    "the reason goes back to Ready.", "Figure 2, steps 7–8"),
    "dispatching": ("Mode", "The approved request may have left the process. The controller waits for the scheduler "
                    "to acknowledge the job.", "Figure 2, step 9"),
    "running": ("Mode", "The scheduler accepted the job. The controller waits for it to finish or fail.",
                "Figure 2, steps 10–11"),
    "scoring": ("Mode", "The job finished, and a score is requested. Only the evaluator's score can promote a "
                "candidate.", "Figure 2, step 12"),
    "reconciling": ("Mode", "A reply went missing, or the process restarted. The controller looks up stored results "
                    "by their IDs before it decides anything, and it starts no new trial.",
                    "Figure 3, Lost score reply"),
    "stopped": ("Mode", "The search is over and the incumbent is frozen. A trial can still be pending, and late "
                "evidence closes it along the small loop. No edge leads back to a new trial.", "Figure 3, Cancel mid-run"),
    "done": ("Mode", "The holdout score is recorded, once. No transition leaves Done.", "Figure 2, step 14"),
}
OVERVIEW_GROUPS = {
    "search": ("Group", "Every mode from Ready to Reconciling. A cancellation or the deadline moves the run to Stopped "
               "from any of them, and the policy cannot prevent it.", "Figure 2, step 13"),
    "flight": ("Group", "Dispatching, Running, and Scoring: the modes that wait on the scheduler or the evaluator. A "
               "timeout or a restart in any of them moves the run to Reconciling.", "Figure 3, Lost score reply"),
}
SOURCES = {  # key: (label, rows it fires, can the runtime refuse it, text)
    "policy": ("Policy", [3, 4, 5], "Yes. The gate or a guard can reject the request.",
               "Proposes a trial or asks to stop, only in Proposing and only for the current turn. Those are its two "
               "choices. Its decoder reports a reply it cannot use as invalid output, the third exit from "
               "Proposing, which returns to Ready."),
    "gate": ("Gate", [6, 7], "Not applicable. The gate is runtime code.",
             "Allows or rejects the proposed trial. An approval binds the exact arguments it checked."),
    "scheduler": ("Scheduler", [8, 9, 10, 17, 18, 19, 20, 23], "No. The job runs whether or not the controller "
                  "still wants it.", "Accepts, finishes, or fails a job, and answers lookups by operation ID or job ID."),
    "evaluator": ("Evaluator", [11, 13, 16, 22], "No. A score can arrive late or twice.",
                  "Returns a score, or a stored score on lookup. It also scores the holdout once at the end. "
                  "Only a score can promote a candidate."),
    "clock": ("Clock, operator, host", [12, 14, 15, 21], "No. The runtime must absorb these events.",
              "Timeouts, the deadline, a cancellation, and the recovered event after a restart."),
    "controller": ("Controller", [1, 2], "It is the runtime's own rule.",
                   "Checks the limits in Ready, then starts a policy turn or stops the search."),
}


def overview_html() -> str:
    pct = lambda v, total: f"{v * 100 / total:.4g}%"  # noqa: E731
    buttons, panels = [], []
    for key, (label, rows, refuse, text) in SOURCES.items():
        buttons.append(f'<button type="button" class="cm-source" aria-controls="ov-{key}" data-rows="{" ".join(map(str, rows))}" disabled>{label}</button>')
        panels.append(f'<section id="ov-{key}" data-overview-panel><p class="cm-ov-kind">Event source</p>'
                      f'<p class="cm-ov-title">{label}</p><p>{text}</p>'
                      f'<p class="cm-ov-meta"><b>Can the runtime refuse it?</b> {refuse}</p>'
                      f'<p class="cm-ov-meta">Edges it fires are highlighted.</p></section>')
    graph_buttons = []
    for key, (kind, text, where) in {**OVERVIEW_MODES, **OVERVIEW_GROUPS}.items():
        if key in MODES:
            label, x, y, w, k = MODES[key]
            h, cls = NH, "cm-ov-node" + (f" is-{k}" if k else "")
        else:
            lines, gx, gy, gw, gh, lx, ly = GROUPS[key]
            label = " ".join(lines)
            w = 50 if key == "search" else 46
            h = 18 if key == "search" else 30
            x, y, cls = lx - w + 3, ly - 13, "cm-ov-group"
        style = f"left: {pct(x, VB_W)}; top: {pct(y, VB_H)}; width: {pct(w, VB_W)}; height: {pct(h, VB_H)}"
        graph_buttons.append(f'<button type="button" class="{cls}" style="{style}" aria-controls="ov-{key}" disabled>{label}</button>')
        title = label if key in MODES else ("Search" if key == "search" else "Trial in flight")
        panels.append(f'<section id="ov-{key}" data-overview-panel><p class="cm-ov-kind">{kind}</p>'
                      f'<p class="cm-ov-title">{title}</p><p>{text}</p>'
                      f'<p class="cm-ov-meta"><b>Developed in</b> {where}</p></section>')
    # Reading order for keyboard users: modes down the center, then groups, then sources.
    order = ["ready", "proposing", "authorizing", "dispatching", "running", "scoring", "reconciling", "stopped",
             "done", "search", "flight"]
    graph_buttons = [b for k in order for b in graph_buttons if f'aria-controls="ov-{k}"' in b]
    first = [p for p in panels if 'id="ov-ready"' in p]
    rest = [p for p in panels if 'id="ov-ready"' not in p]
    desc = ("Nine modes. Ready leads to Proposing, where the policy proposes a trial or asks to stop. A proposed trial "
            "goes to Authorizing, where the gate allows it into the Trial in flight group (Dispatching, Running, "
            "Scoring) or rejects it back to Ready. Every closed trial, rejection, invalid reply, and stop request "
            "returns to Ready along the right side. A timeout or restart in flight leads to Reconciling, which "
            "resumes the trial or resolves it back to Ready. From Ready, or on a cancel or deadline anywhere in "
            "Search, the run moves to Stopped, and the holdout score moves it to Done.")
    svg = svg_diagram("ov", list(range(1, 24)), badges=False, label="AutoResearch controller overview",
                      desc_id="ov-desc", nodes=False)
    return f"""<div class="agent-animation cm-overview" data-cm-overview>
  <p class="cm-hint" data-overview-hint hidden>Hover, focus, or tap a mode, a group, or an event source.</p>
  <div class="cm-ov-sources" role="group" aria-label="Event sources">
    <span class="cm-ov-sources-label" aria-hidden="true">Who fires the edges</span>
    {chr(10).join(buttons)}
  </div>
  <div class="cm-ov-layout">
    <div class="cm-ov-graph" role="group" aria-label="Controller modes and groups">
      <p id="ov-desc" class="visually-hidden">{desc}</p>
      {svg}
      {chr(10).join(graph_buttons)}
    </div>
    <div class="cm-ov-info" data-overview-info>
      {chr(10).join(first + rest)}
    </div>
  </div>
  <ul class="cm-legend" aria-label="Legend">
    <li><span class="cm-swatch is-policy"></span>Thick line: the policy chooses this edge</li>
    <li><span class="cm-swatch is-stop"></span>Dashed line: a hard stop from any mode in Search</li>
  </ul>
</div>
"""

# ---------------------------------------------------------------------------
# Stepped figures share one markup: a visual, a live card, controls, and one
# ordered list of steps per scenario. Each <li> holds the step's card and the
# state of the visual as data attributes. JavaScript reads the lists, hides
# them, and plays the steps; without JavaScript the lists are the figure.
# ---------------------------------------------------------------------------


def step_li(title: str, card: str, extra: str = "", **state: str) -> str:
    attrs = "".join(f' data-{k.replace("_", "-")}="{escape(v)}"' for k, v in state.items() if v is not None)
    return f'<li data-title="{escape(title)}"{attrs}><div class="cm-card-body">{card}</div>{extra}</li>'


def row_card(row: int, note: str, new: bool = False, guard: str | None = None, frm: str | None = None,
             to: str | None = None, event: str | None = None, update: str | None = None, owner: str | None = None) -> str:
    r_from, r_to, r_owner, r_event, r_guard, r_update, _ = ROWS[row]
    tag = '<span class="cm-new">New row</span>' if new else ""
    return (f'<p class="cm-kicker">{owner_chip(owner or r_owner)}{tag}</p>'
            f'<p class="cm-title">{row_title(row, frm, to)}</p>'
            + dl([("Event", event or r_event), ("Guard", guard or r_guard), ("Update", update or r_update)])
            + f'<p class="cm-note">{note}</p>')


def text_card(title: str, note: str, kicker: str = "") -> str:
    k = f'<p class="cm-kicker"><span class="cm-owner">{kicker}</span></p>' if kicker else ""
    return f'{k}<p class="cm-title">{title}</p><p class="cm-note">{note}</p>'


# Figure 2: build the main cycle in execution order. At each mode the row the run
# usually takes comes first, then the alternatives that leave the same mode.
BUILD = [
    # (row or None, status title, narration)
    (None, "Nine modes, no rows yet",
     "A mode says where the run is. A row says how it may move: in this mode, on this event, if the guard holds, "
     "apply the update and go to the next mode. Each step adds one row, in the order a run meets them."),
    (1, "Row 1: the limits have room", ROWS[1][6]),
    (2, "Row 2: a limit is reached", ROWS[2][6]),
    (3, "Row 3: the policy proposes a trial", ROWS[3][6]),
    (4, "Row 4: the policy asks to stop", ROWS[4][6]),
    (5, "Row 5: the reply is unusable", ROWS[5][6]),
    (7, "Row 7: the gate allows the trial",
     "A crash after the commit leaves evidence that the request may have been sent."),
    (6, "Row 6: the gate rejects the trial", "Row 6 comes after row 7 here because a run usually meets an approval "
     "first. " + ROWS[6][6]),
    (8, "Row 8: the scheduler accepts the job",
     "The controller now knows that the scheduler has the job. Completion arrives as a separate event."),
    (9, "Row 9: the job finishes",
     "The cost is recorded but not yet charged. The reservation still covers it."),
    (10, "Row 10: the job fails", ROWS[10][6]),
    (11, "Row 11: the score arrives", ROWS[11][6]),
    (12, "Row 12: a cancel or the deadline", ROWS[12][6]),
    (13, "Row 13: the holdout is scored", ROWS[13][6]),
    (None, "The policy owns two edges",
     "The policy's reply can fire only the rows leaving Proposing: rows 3 and 4 are its choices, and row 5 records "
     "an unusable reply. The gate, scheduler, evaluator, clock, operator, and the controller's own check fire every "
     "other row."),
]


def build_html() -> str:
    items, shown = [], []
    for i, (row, title, note) in enumerate(BUILD):
        if row is not None:
            shown.append(row)
            frm, to = ROWS[row][0], ROWS[row][1]
            mode = to.lower() if row != 12 else "stopped"
            card = row_card(row, note)
            current = str(row)
        elif i == 0:
            mode, current = "ready", ""
            card = text_card("Start in Ready", note)
        else:
            mode, current = "proposing", "3 4"
            card = text_card("Where the policy chooses", note)
        items.append(step_li(f"{title}", card, mode=mode, current=current, shown=" ".join(map(str, shown))))
    desc = ("The controller's nine modes drawn as boxes, with Stopped and Done at the top, Ready to Reconciling down "
            "the center, and returns to Ready along the right. The steps below add rows 1 to 13 one at a time.")
    svg = svg_diagram("build", list(range(1, 14)), badges=True, label="Transition rows 1 to 13", desc_id="build-desc")
    return f"""<div class="agent-animation cm-stepper cm-build" data-cm-stepper data-variant="build">
  <p class="agent-figure-kicker">Rows 1–13 · built in the order a run meets them</p>
  <div class="cm-layout">
    <div class="cm-visual"><p id="build-desc" class="visually-hidden">{desc}</p>{svg}</div>
    <div class="cm-card" id="build-card" data-card aria-live="polite" hidden></div>
  </div>
  {controls("Main cycle", "build-card")}
  <ol class="cm-steps" data-steps aria-label="Steps">
    {chr(10).join(items)}
  </ol>
  <ul class="cm-legend" aria-label="Legend">
    <li><span class="cm-swatch is-accent"></span>Blue: the row in the current step</li>
    <li><span class="cm-swatch is-policy"></span>Thick line: the policy chooses this edge</li>
    <li><span class="cm-swatch is-stop"></span>Dashed line: a hard stop from any mode in Search</li>
  </ul>
</div>
"""

# ---------------------------------------------------------------------------
# Figure 3. Three runs of trial t1. Numbers in the controller record come from
# running labs.controller; authored text (events, notes, external state, and
# context) is checked against the lab's row, modes, and pending trial.
# ---------------------------------------------------------------------------

NB = "\u2011"  # non-breaking hyphen keeps IDs such as t1-submit on one line
T1_SUBMIT, T1_SCORE = f"t1{NB}submit", f"t1{NB}score"
NO_CONTEXT = "Not built. A context exists only for a policy turn."
CONTEXT_1 = ("Goal: beat the incumbent on validation.\nIncumbent: baseline 0.842.\n2.0 GPU-h and 5 trials left.\n"
             "Operations: propose a trial, propose stop.")
CONTEXT_2 = ("Goal: beat the incumbent on validation.\nIncumbent: t1 0.851 (baseline 0.842).\n1.4 GPU-h and 4 trials "
             "left.\nOperations: propose a trial, propose stop.")
START_EXTERNAL = {"scheduler": "No job for this run", "evaluator": "baseline · 0.842 (v1)"}

PREFIX = [
    dict(owner="Controller rule", event="Limits checked",
         guard="0 of 5 trials, 0 of 10 proposals, 2.0 GPU-h unreserved, no stop requested ✓",
         update="Build context c₁ from the ledger.",
         note="Ready is the only mode that starts a policy turn, so the stop rule runs here every time.",
         pending="None", context=CONTEXT_1, tag="c₁ · built for policy turn 1"),
    dict(owner="Policy's choice", event="Trial proposed: lr 3e-4, seed 7, estimate 0.7 GPU-h",
         guard="The reply answers turn 1 ✓", update="Count proposal 1 of 10. Record the arguments.",
         note="This is the policy's only choice in the trial. Nothing has been sent.",
         pending="None", tag="c₁ · used by proposal 1, now stale", stale=True),
    dict(owner="Gate", event="Allowed",
         guard="The approval binds lr 3e-4, seed 7, estimate 0.7. 0.7 ≤ 2.0 GPU-h unreserved. No stop requested ✓",
         update=f"Mint trial t1 and operation {T1_SUBMIT}. Store the approved request. Reserve 0.7 GPU-h. Count trial "
                "1 of 5. Commit checkpoint 3, then send.",
         note="Checkpoint 3 proves the request may have been sent. It cannot prove that the scheduler received it.",
         pending=f"t1 · operation {T1_SUBMIT} · no job yet", external={"scheduler": f"Has not seen {T1_SUBMIT} yet"}),
    dict(owner="Scheduler", event=f"Accepted: job #42 for {T1_SUBMIT}", guard="The operation ID matches the pending trial ✓",
         update="Record job #42.",
         note="The controller now knows that the scheduler accepted the job. Completion arrives as a separate event.",
         pending="t1 · job #42", external={"scheduler": "Job #42 accepted and running"}),
    dict(owner="Scheduler", event="Job done: #42, cost 0.6 GPU-h", guard="The job ID matches the pending trial ✓",
         update=f"Record the cost. Request a score with scoring ID {T1_SCORE}.",
         note="The cost is recorded but not yet charged. The reservation still covers it.",
         pending=f"t1 · job #42 · score requested ({T1_SCORE})",
         external={"scheduler": "Job #42 complete · weights stored", "evaluator": f"Scoring t1 for request {T1_SCORE}"}),
]


def next_turn(notes: list[str]) -> list[dict]:
    return [
        dict(owner="Controller rule", event="Limits checked",
             guard="1 of 5 trials, 1 of 10 proposals, 1.4 GPU-h unreserved, no stop requested ✓",
             update="Build context c₂ from the ledger.", note=notes[0], pending="None · t1 closed",
             context=CONTEXT_2, tag="c₂ · built for policy turn 2", stale=False),
        dict(owner="Policy's choice", event="Trial proposed: replicate t1 with seed 11, estimate 0.7 GPU-h",
             guard="The reply answers turn 2 ✓", update="Count proposal 2 of 10. Record the arguments.",
             note=notes[1], pending="None · t1 closed", tag="c₂ · used by proposal 2, now stale", stale=True),
    ]


SCORED = dict(owner="Evaluator", event="Score: t1 = 0.851 (v1)",
              guard="The score is for pending trial t1 and comes from v1 ✓",
              update="Charge 0.6 GPU-h and release the 0.7 reservation. 0.851 > 0.842, so keep t1. Close t1.",
              note="Promotion is a rule in code: strict improvement on validation.", pending="None · t1 closed",
              external={"evaluator": "Stored t1 = 0.851 (v1)"})

TRACES = {
    "ordinary": ("Ordinary trial", PREFIX + [SCORED] + next_turn([
        "The context is rebuilt from the record, so a restart would produce the same evidence.",
        "The policy chooses again. The gate checks this request next.",
    ])),
    "lost-score": ("Lost score reply", PREFIX + [
        dict(owner="Clock", event="Timeout: no score within 10 min", guard="A recovery attempt remains (1 of 3) ✓",
             update=f"Keep the 0.7 GPU-h reservation. Look up the stored score under {T1_SCORE}, then operation {T1_SUBMIT} "
                    "(job #42).",
             note=f"Known: job #42 finished and {T1_SCORE} was requested. Unknown: whether a score exists. No new "
                  "trial can start.",
             pending=f"t1 · job #42 · score unknown ({T1_SCORE})",
             external={"evaluator": "Stored t1 = 0.851 (v1). The reply was lost."}, new=True),
        dict(owner="Evaluator store", event=f"Score found: the lookup of {T1_SCORE} returns 0.851 (v1)",
             guard="The score is for pending trial t1, its cost is known, and it comes from v1 ✓",
             update="Apply row 11's update: charge 0.6, release 0.7, keep t1, close t1.",
             note="Reconciliation reads the evaluator's stored record instead of scoring again.",
             pending="None · t1 closed", new=True),
        dict(owner="Evaluator", event="Score: late reply t1 = 0.851 (v1)",
             guard="t1 is no longer pending, so only the log-and-ignore row matches", update="Log and ignore the late reply.",
             note="Rows 11 and 16 cannot fire because no trial is pending. Row 22 logs the reply as checkpoint 8 and "
                  "changes no ledger field. A callback that charged every score would leave 0.8 GPU-h.", pending="None · t1 closed", new=True),
    ] + next_turn([
        "The ledger now matches the ordinary trace, two checkpoints later, so the policy sees the same evidence.",
        "Same evidence and the same choice. The lost reply cost a lookup, not a trial.",
    ])),
    "cancel": ("Cancel mid-run", PREFIX[:4] + [
        dict(owner="Operator", event="Cancel", guard="None. A cancel applies in any mode of Search ✓",
             update="Record the hard stop and freeze the incumbent. Ask the scheduler to cancel job #42.",
             note="The policy cannot prevent this row. t1 is still pending, so the run cannot end yet.",
             pending="t1 · job #42 · cancel requested", external={"scheduler": "Job #42 running · cancel requested"}),
        dict(owner="Scheduler", event="Job failed: #42 cancelled, cost 0.4 GPU-h",
             guard="The report is for pending trial t1 ✓",
             update="Charge 0.4 GPU-h, release the 0.7 reservation, close t1 without promotion, and request the holdout "
                    "score.",
             note="Late evidence pays for the trial, and the frozen selection stays frozen. 1.6 GPU-h are unspent, "
                  "but no row leaves Stopped toward a new trial.",
             pending="None · t1 closed", external={"scheduler": "Job #42 cancelled after 0.4 GPU-h"}, new=True),
        dict(owner="Fixed evaluator", event="Holdout scored: baseline 0.835",
             guard="No trial is pending and no holdout score is recorded ✓", update="Record the final holdout score.",
             note="The frozen selection, still the baseline, is scored on the holdout once. The holdout enters the "
                  "record only through this row, and the run is Done.",
             pending="None · t1 closed", external={"evaluator": "Holdout: baseline 0.835 (fixed evaluator)"}),
    ]),
}

FIELDS = [("mode", "Mode"), ("incumbent", "Incumbent"), ("compute", "Compute"), ("counters", "Counters"),
          ("pending", "Pending")]
EXTERNAL = [("scheduler", "Scheduler"), ("evaluator", "Evaluator store")]


def record_fields(z: lab.ControllerRecord) -> dict[str, str]:
    mode = z.mode.capitalize() + (f" · {z.stop_reason}" if z.mode == "stopped" and z.stop_reason else "")
    incumbent = f"{z.incumbent} · {z.incumbent_score:.3f}"
    if z.holdout_score is not None:
        incumbent += f" · holdout {z.holdout_score:.3f}"
    return {
        "mode": mode,
        "incumbent": incumbent,
        "compute": f"{z.unspent:.1f} GPU-h unspent · {z.reserved:.1f} reserved",
        "counters": f"{z.trials_used} of {lab.TRIAL_CAP} trials · {z.proposals_used} of {lab.PROPOSAL_CAP} proposals",
    }


def trace_stages(name: str) -> list[dict]:
    """Merge authored stages with the lab's log. Raises if they disagree."""
    label, authored = TRACES[name]
    log = lab.run(lab.SCENARIOS[name])
    assert len(log) == len(authored), (name, len(log), len(authored))
    z0 = lab.ControllerRecord()
    stages = [dict(row=None, frm=None, to="Ready", owner="Start", record={**record_fields(z0), "pending": "None"},
                   external=dict(START_EXTERNAL), context=NO_CONTEXT, tag="", stale=False, checkpoint=0,
                   event="None yet", guard="None yet", update="The ledger holds the baseline as the incumbent.",
                   note="No trial is in flight, and no context exists yet.", new=False)]
    for entry, a in zip(log, authored):
        prev = stages[-1]
        z = entry.record
        assert entry.row is not None, (name, entry)
        pending = a["pending"]
        if z.pending is None:
            assert pending.startswith("None"), (name, entry.row.ref, pending)
        else:
            assert pending.startswith(z.pending.trial), (name, entry.row.ref, pending)
            if z.pending.job:
                assert z.pending.job in pending, (name, entry.row.ref, pending)
        stages.append(dict(
            row=entry.row.ref, frm=entry.mode.capitalize(), to=entry.next.capitalize(), owner=a["owner"],
            record={**record_fields(z), "pending": pending},
            external={**prev["external"], **a.get("external", {})},
            context=a.get("context", prev["context"]), tag=a.get("tag", prev["tag"]),
            stale=a.get("stale", prev["stale"]), checkpoint=z.checkpoint, event=a["event"], guard=a["guard"],
            update=a["update"], note=a["note"], new=a.get("new", False)))
    return stages


def trace_state_html(s: dict, changed: list[str]) -> str:
    mark = lambda k: ' class="is-changed"' if k in changed else ""  # noqa: E731
    rows = [f'<div data-field="{k}"{mark(k)}><dt>{t}</dt><dd>{escape(s["record"][k])}</dd></div>' for k, t in FIELDS]
    rows += [f'<div data-field="{k}"{mark(k)}><dt>{t}</dt><dd>{escape(s["external"][k])}</dd></div>' for k, t in EXTERNAL]
    ctx = escape(s["context"])
    rows.append(f'<div data-field="context"{mark("context")}><dt>Policy context</dt><dd>{ctx}</dd></div>')
    return (f'<dl class="cm-state" data-checkpoint="{s["checkpoint"]}" data-tag="{escape(s["tag"])}" '
            f'data-stale="{str(s["stale"]).lower()}">' + "".join(rows) + "</dl>")


def trace_html() -> str:
    lists, first_names = [], []
    for name, (label, _) in TRACES.items():
        stages = trace_stages(name)
        items, visited, prev = [], [], None
        for s in stages:
            if s["row"] is None:
                card = (f'<p class="cm-kicker"><span class="cm-owner">Start</span></p><p class="cm-title">Start in Ready</p>'
                        + dl([("Event", s["event"]), ("Guard", s["guard"]), ("Update", s["update"])])
                        + f'<p class="cm-note">{s["note"]}</p>')
                title, current = "Start in Ready", ""
            else:
                visited.append(s["row"])
                owner = "policy" if s["owner"] == "Policy's choice" else None
                tag = '<span class="cm-new">New row</span>' if s["new"] else ""
                card = (f'<p class="cm-kicker">{owner_chip(owner, None if owner else "Fired by: " + s["owner"])}{tag}</p>'
                        f'<p class="cm-title">{row_title(s["row"], s["frm"], s["to"])}</p>'
                        + dl([("Event", escape(s["event"])), ("Guard", escape(s["guard"])), ("Update", escape(s["update"]))])
                        + f'<p class="cm-note">{escape(s["note"])}</p>')
                title, current = f"Row {s['row']} · {s['frm']} → {s['to']}", str(s["row"])
            changed = [k for k, _ in FIELDS + EXTERNAL] + ["context"]
            if prev is not None:
                changed = [k for k, _ in FIELDS if s["record"][k] != prev["record"][k]]
                changed += [k for k, _ in EXTERNAL if s["external"][k] != prev["external"][k]]
                if s["context"] != prev["context"]:
                    changed.append("context")
            mode = s["to"].lower()
            items.append(step_li(title, card, trace_state_html(s, changed), mode=mode, current=current,
                                 visited=" ".join(map(str, visited)),
                                 changed=" ".join(changed) if prev is not None else ""))
            prev = s
        lists.append(f'<div class="cm-scenario-steps"><p class="cm-steps-label">{label}</p>\n'
                     f'<ol class="cm-steps" data-steps data-scenario="{name}" aria-label="{label}">\n'
                     + "\n".join(items) + "\n</ol></div>")
        first_names.append((name, label))
    buttons = "\n".join(
        f'<button type="button" data-scenario="{n}" aria-pressed="{"true" if i == 0 else "false"}" '
        f'aria-controls="trace-card">{lbl}</button>' for i, (n, lbl) in enumerate(first_names))
    layer = lambda key, title, fields: (  # noqa: E731
        f'<section class="cm-layer" aria-labelledby="trace-layer-{key}"><p class="cm-layer-title" id="trace-layer-{key}">'
        f'{title}</p><dl>' + "".join(f'<div data-field="{k}"><dt>{t}</dt><dd></dd></div>' for k, t in fields) + "</dl></section>")
    layers = (layer("record", 'Controller record <i>z</i> · <span data-live="checkpoint"></span>', FIELDS)
              + layer("external", "External state <i>x</i>", EXTERNAL)
              + '<section class="cm-layer" aria-labelledby="trace-layer-context"><p class="cm-layer-title" '
                'id="trace-layer-context">Policy context <i>c</i><span class="cm-context-tag" data-live="tag"></span></p>'
                '<div data-field="context"><p class="cm-context"></p></div></section>')
    desc = ("The controller diagram with all 23 rows. In each step, the mode the run is in and the row that just "
            "fired are highlighted, and the rows already taken stay drawn.")
    svg = svg_diagram("trace", list(range(1, 24)), badges=True, label="Controller trace", desc_id="trace-desc")
    return f"""<div class="agent-animation cm-stepper cm-trace" data-cm-stepper data-variant="trace">
  <p class="agent-figure-kicker">Schematic values · reproduced by <code>labs.controller</code></p>
  <div class="loop-scenarios" role="group" aria-label="Trace scenario" data-scenarios hidden>
    {buttons}
  </div>
  <div class="cm-layout">
    <div class="cm-visual"><p id="trace-desc" class="visually-hidden">{desc}</p>{svg}</div>
    <div class="cm-card" id="trace-card" data-card aria-live="polite" hidden></div>
    <div class="cm-layers" data-layers hidden>{layers}</div>
    {controls("Trace", "trace-card")}
  </div>
  {chr(10).join(lists)}
</div>
"""

# ---------------------------------------------------------------------------
# Figure 4. One upstream experiment, in execution order. Each step moves one rule
# from the agent's lane to the runtime's lane, or shows a choice the agent keeps.
# 5 and 10 minutes are upstream parameters; 7 minutes, 3 fixes, 60 trials,
# 120 proposals, and 8 hours are schematic.
# ---------------------------------------------------------------------------

LANES = [  # key, agent-lane label, runtime-lane label (None: the agent keeps it)
    ("change", "Choose the code change", None),
    ("diff", "Edit only <code>train.py</code>", "Gate checks the diff"),
    ("commit", "Commit the change", "Row 7 commits a ref"),
    ("time", "5- and 10-minute limits", "Host kills at 7 min"),
    ("fix", "Choose a fix", None),
    ("tries", "Give up after a few tries", "Gate allows 3 fixes"),
    ("measure", "Read <code>val_bpb</code> from the log", "Pinned evaluator"),
    ("keep", "Keep if lower, else reset", "Row 11 promotes"),
    ("log", "Append to <code>results.tsv</code>", "Report from the ledger"),
    ("stop", "Never stop", "Rows 2 and 12 stop"),
    ("holdout", "No holdout", "Holdout once, row 13"),
]
STOP_AFTER = "Ask to stop, row 4"


def compare(upstream: list[tuple[str, str]], redesign: list[tuple[str, str]]) -> str:
    """Two compact lines, upstream and redesign, then the rewritten row text the step changes."""
    u, r = dict(upstream), dict(redesign)
    end = lambda text: text if text.endswith(".") else text + "."  # noqa: E731
    quotes = [(k, v) for k, v in redesign if k not in ("Rows", "Enforced by")]
    return (f'<p class="cm-line"><span class="cm-line-label">Upstream</span> {end(u["Rule"])} '
            f'<span class="cm-meta">Enforced by: {u["Enforced by"]}. State: {u["State lives in"]}.</span></p>'
            f'<p class="cm-line"><span class="cm-line-label">Redesign</span> {end(r["Enforced by"])} '
            f'<span class="cm-meta">{"Row" if r["Rows"].split(",")[0].split(" ")[0].isdigit() and len(r["Rows"].split()) == 1 else "Rows"} {r["Rows"]}.</span></p>'
            + "".join(f'<div class="cm-quote"><p class="cm-quote-label">{k}</p><p>{v}</p></div>' for k, v in quotes))


U = UPSTREAM
UPSTREAM_STEPS = [  # (status title, moved key, current keys, card body)
    ("The loop as written", None, "",
     '<p class="cm-title">The loop as written</p>'
     + compare([("Rule", "Edit, run, read the score, log, keep or reset, and repeat until a person interrupts"),
                ("Enforced by", "The agent, following <code>program.md</code>"),
                ("State lives in", "Git, <code>run.log</code>, <code>results.tsv</code>, and the agent's context")],
               [("Rows", "1–23"),
                ("Enforced by", "The gate, the process host, the pinned evaluator, and the controller")])
     + '<p class="cm-note">At commit <code>228791f</code>, the policy carries out every rule, including the rules that '
       "judge its own work. The steps follow one experiment and move each rule that must hold whatever the policy "
       "proposes.</p>"),
    ("Propose a patch", None, "change",
     '<p class="cm-title">Propose a patch</p>'
     + compare([("Rule", "Edit <code>train.py</code> with an experimental idea"), ("Enforced by", "The agent"),
                ("State lives in", "Git branch")],
               [("Rows", "3"), ("Enforced by", "The policy chooses, and the gate checks"), ("Update, row 3", U[3][2])])
     + '<p class="cm-note">This choice stays with the policy. Judgment pays here, and the gate can check that the '
       "patch is legal before anything runs.</p>"),
    ("Check the diff", "diff", "diff",
     '<p class="cm-title">Check the diff</p>'
     + compare([("Rule", "Edit only <code>train.py</code>, and add no packages"), ("Enforced by", "The agent"),
                ("State lives in", "The diff")],
               [("Rows", "6 and 7"), ("Enforced by", "The gate"), ("Guard, row 7", U[7][1])])
     + '<p class="cm-note">The rule becomes a guard on the diff, and the approval binds the diff\'s hash. Row 6 '
       "rejects a patch that touches another file before anything is committed.</p>"),
    ("Commit the candidate", "commit", "commit",
     '<p class="cm-title">Commit the candidate</p>'
     + compare([("Rule", "Commit the edit with <code>git commit</code>"), ("Enforced by", "The agent"),
                ("State lives in", "Git branch")],
               [("Rows", "7"), ("Enforced by", "The controller"), ("Update, row 7", U[7][2])])
     + f'<p class="cm-note">{U[7][3]} As in Figure 2, step 7, the checkpoint is committed before anything is sent.</p>'),
    ("Run under a time cap", "time", "time",
     '<p class="cm-title">Run under a time cap</p>'
     + compare([("Rule", "Stop training after 5 minutes, and kill a run after 10"),
                ("Enforced by", "A <code>break</code> in <code>train.py</code>, and the agent"),
                ("State lives in", "Code the agent edits, and the agent's shell session")],
               [("Rows", "10"), ("Enforced by", "The process host, which kills the run at 7 minutes"),
                ("Update, row 10", U[10][2])])
     + '<p class="cm-note">5 and 10 minutes are upstream parameters. The 7-minute cap is schematic: the budget plus '
       "an allowance for startup and saving. A run that deletes the <code>break</code> can still train for up to "
       "that allowance.</p>"),
    ("Choose a fix, within a limit", "tries", "fix tries",
     '<p class="cm-title">Choose a fix, within a limit</p>'
     + compare([("Rule", "Read the stack trace, try a fix, and give up after a few attempts"),
                ("Enforced by", "The agent's judgment"), ("State lives in", "The agent's context")],
               [("Rows", "3 and 6"), ("Enforced by", "The policy picks the fix, and the gate counts attempts"),
                ("Rejection reasons, row 6", U[6][1])])
     + '<p class="cm-note">A fix is a complete diff against the incumbent, labeled with the idea it fixes. A policy '
       "could mislabel a fix as a new idea, so the trial cap is the bound that actually holds.</p>"),
    ("Measure with a pinned evaluator", "measure", "measure",
     '<p class="cm-title">Measure with a pinned evaluator</p>'
     + compare([("Rule", "Read <code>val_bpb</code> from <code>run.log</code>, and treat an empty result as a crash"),
                ("Enforced by", "The agent, reading text that <code>train.py</code> prints"),
                ("State lives in", "<code>run.log</code>")],
               [("Rows", "9 and 11"), ("Enforced by", "A pinned evaluator that scores the saved weights"),
                ("Guard, row 9", U[9][1])])
     + '<p class="cm-note">Upstream, the loss comes from the model code in <code>train.py</code>. The pinned evaluator '
       "computes bits per byte from the candidate's logits after a causality check, and training runs without the "
       "validation or holdout shard mounted.</p>"),
    ("Keep or reset by rule", "keep", "keep",
     '<p class="cm-title">Keep or reset by rule</p>'
     + compare([("Rule", "Keep the commit if <code>val_bpb</code> is lower, otherwise reset"),
                ("Enforced by", "The agent"), ("State lives in", "Branch head")],
               [("Rows", "11"), ("Enforced by", "The controller, on the pinned evaluator's score"),
                ("Update, row 11", U[11][2])])
     + f'<p class="cm-note">{U[11][3]}</p>'),
    ("Record from the ledger", "log", "log",
     '<p class="cm-title">Record from the ledger</p>'
     + compare([("Rule", "Append a row to <code>results.tsv</code>"), ("Enforced by", "The agent"),
                ("State lives in", "A file outside git")],
               [("Rows", "10 and 11 close trials"), ("Enforced by", "The controller's ledger"),
                ("Report", "<code>results.tsv</code> is regenerated from the ledger, one row per closed trial")])
     + '<p class="cm-note">A restart cannot append a second row for the same trial, because the report is rebuilt '
       "from closed trials.</p>"),
    ("Stop by rule", "stop", "stop",
     '<p class="cm-title">Stop by rule</p>'
     + compare([("Rule", "Never stop, and never ask whether to continue"), ("Enforced by", "A person who interrupts"),
                ("State lives in", "Nowhere")],
               [("Rows", "2, 4, and 12"), ("Enforced by", "The stop rule, the clock, and the operator"),
                ("Guard, row 2", U[2][1])])
     + '<p class="cm-note">Row 12 stops the search on a cancel or the 8-hour deadline; the limits are schematic. '
       "The policy gains a request it did not have: it can ask to stop (row 4). A cancel leaves a record and a "
       "frozen incumbent, where killing the agent mid-command could leave a commit neither kept nor reset.</p>"),
    ("Score a holdout once", "holdout", "holdout",
     '<p class="cm-title">Score a holdout once</p>'
     + compare([("Rule", "None. Every shard except one pinned validation shard trains."), ("Enforced by", "Nothing"),
                ("State lives in", "<code>prepare.py</code>")],
               [("Rows", "13"), ("Enforced by", "The fixed evaluator, once, after the search stops, as row 13 already does"),
                ("Setup", "Reserve a shard in <code>prepare.py</code> before its hash is pinned")])
     + '<p class="cm-note">Model code still runs during scoring, so the holdout remains the backstop against a gamed '
       "metric.</p>"),
    ("What the agent keeps", None, "change fix stop:agent",
     '<p class="cm-title">What the agent keeps</p><p class="cm-note">The policy keeps three choices: the patch, the '
     "fix to try after a crash, and a request to stop. Measurement, promotion, crash accounting, time limits, the "
     "record, and the stop itself now fire on events from the gate, the process host, the evaluator, the clock, or "
     "the operator.</p>"),
]


def upstream_html() -> str:
    lane_rows = []
    for key, agent, runtime in LANES:
        if key == "stop":
            agent_html = (f'<span class="cm-token is-agent"><span class="cm-before">{agent}</span>'
                          f'<span class="cm-after">{STOP_AFTER}</span></span>')
        else:
            cls = "cm-token is-agent" + (" is-absent" if key == "holdout" else "")
            agent_html = f'<span class="{cls}"><span>{agent}</span></span>'
        runtime_html = (f'<span class="cm-token is-runtime"><span>{runtime}</span></span>' if runtime
                        else '<span class="cm-slot"></span>')
        lane_rows.append(f'<li data-rule="{key}">{agent_html}{runtime_html}</li>')
    items, moved = [], []
    for title, move, current, card in UPSTREAM_STEPS:
        if move:
            moved.append(move)
        items.append(step_li(title, card, moved=" ".join(moved), current=current))
    desc = ("Two lanes list the rules of one upstream experiment. The left lane holds rules the agent enforces in "
            "program.md. The right lane names what enforces each rule in the redesign. Rules the agent keeps have "
            "no entry on the right.")
    return f"""<div class="agent-animation cm-stepper cm-upstream" data-cm-stepper data-variant="lanes">
  <p class="agent-figure-kicker">Upstream <code>karpathy/autoresearch</code> at <code>228791f</code> · redesign limits are schematic</p>
  <div class="cm-layout">
    <div class="cm-visual cm-lanes" role="group" aria-label="Who enforces each rule" aria-describedby="lanes-desc">
      <p id="lanes-desc" class="visually-hidden">{desc}</p>
      <p class="cm-lane-head" aria-hidden="true"><span>Enforced by the agent</span><span>Enforced by the runtime</span></p>
      <ol class="cm-lane-rows">
        {chr(10).join(lane_rows)}
      </ol>
    </div>
    <div class="cm-card" id="upstream-card" data-card aria-live="polite" hidden></div>
  </div>
  {controls("Upstream loop", "upstream-card")}
  <ol class="cm-steps" data-steps aria-label="Steps">
    {chr(10).join(items)}
  </ol>
</div>
"""


# ---------------------------------------------------------------------------

FIGURES = {
    "controller-overview.html": overview_html,
    "controller-states.html": build_html,
    "controller-trace.html": trace_html,
    "controller-upstream.html": upstream_html,
}


def render() -> dict[str, str]:
    return {name: make() for name, make in FIGURES.items()}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, text in render().items():
        (OUT / name).write_text(text, encoding="utf-8")
        print("wrote", (OUT / name).relative_to(ROOT))


if __name__ == "__main__":
    main()

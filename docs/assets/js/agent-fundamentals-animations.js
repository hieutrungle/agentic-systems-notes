const BASELINE = ["Baseline", "0.842", "2.0 GPU-h", "0"];
const PENDING = ["Baseline", "0.842", "2.0 GPU-h", "1"];
const UPDATED = ["Candidate from #42", "0.851", "1.4 GPU-h", "0"];

const goal = "Improve the validation score within 2 GPU-hours.";
const initialInputs = "Goal g — " + goal + "\nLedger z₀ — Baseline is the incumbent, 2.0 GPU-hours remain, and no jobs are pending.\nObservation o₀ — The evaluator reports a baseline score of 0.842.";
const context0 = "Find settings that beat 0.842. You have 2.0 GPU-hours and no pending jobs.";
const proposal0 = "run_experiment(lr = 3e-4, seed = 7)";
const result1 = "Job #42 scored 0.851 and used 0.6 GPU-hours.";
const feedback1 = "Ledger z₁ — Job #42’s settings are the incumbent, 1.4 GPU-hours remain, and no jobs are pending.\nObservation o₁ — " + result1;
const context1 = "Job #42 scored 0.851 with learning rate 0.0003 and seed 7, up from 0.842. You have 1.4 GPU-hours for the next trial.";
const proposal1 = "replicate(config_from_job = 42, seed = 11)";

function runtimeStage(title, node, edge, message, value, detail, state, duration) {
  return { title, tracks: [{ node, edge }], message, value, detail, state, duration };
}

const runtimeStages = [
  runtimeStage("Read the goal", null, null, "Goal · g", goal,
    "Follow one trial down the left and its result back up the right.", BASELINE, 2000),
  runtimeStage("Read goal, state, and observation", "inputs", null, "Input packet · g, z₀, o₀", initialInputs,
    "The controller starts with the goal, its current record, and the baseline observation.", BASELINE, 2400),
  runtimeStage("Construct context", "context", "inputs-context", "Constructed context · c₀", context0,
    "The context builder selects the evidence the policy will see.", BASELINE, 3000),
  runtimeStage("Propose a trial", "policy", "context-policy", "PROPOSED ACTION · ã₀", proposal0,
    "The policy picks a candidate. Nothing has been submitted.", BASELINE, 3000),
  runtimeStage("Validate the proposal", "gate", "policy-gate", "Permission checks · Γ",
    "✓ Tool permitted\n✓ Parameters valid\n✓ Estimated cost within budget\n✓ No approval required",
    "The runtime checks the request before authorizing it.", BASELINE, 4100),
  runtimeStage("Authorize the operation", "gate", "gate-executor", "AUTHORIZED ACTION · aᵃᵘᵗʰ₀", proposal0,
    "Authorization binds to these parameters. The executor has yet to submit the job.", BASELINE, 3200),
  runtimeStage("Dispatch the authorized request", "executor", null, "Dispatch attempt", "Send the approved request to the scheduler.",
    "The runtime is waiting for evidence that the scheduler accepted the request.", BASELINE, 2700),
  runtimeStage("Scheduler accepts job #42", "environment", "executor-environment", "Applied operation · u₀", "The scheduler enqueues job #42.",
    "The acknowledgement lets the runtime record one pending job.", PENDING, 3100),
  runtimeStage("Job #42 finishes", "environment", null, "Environment · x₀ → x₁", "Job #42 finishes training.",
    "The runtime still lists the job as pending while it waits for the result.", PENDING, 2400),
  runtimeStage("Receive score 0.851 and cost 0.6 GPU-h", "observation", "environment-observation", "Observation · o₁", result1,
    "The result travels back. The runtime has yet to reconcile its state.", PENDING, 3200),
  runtimeStage("Record the incumbent and continue", "update", "observation-update", "Updated ledger · z₁ and stop check · D",
    "Promote #42’s settings because 0.851 beats 0.842. Close the job and deduct 0.6 GPU-hours.",
    "The stop check returns “continue” with 1.4 GPU-hours and four trials left.", UPDATED, 3500),
  runtimeStage("Feed the update into the next turn", "inputs", "feedback", "Feedback · z₁ and o₁", feedback1,
    "The context builder reads the updated ledger and the result alongside the original goal.", UPDATED, 3800),
  runtimeStage("Construct the second context", "context", "inputs-context", "Constructed context · c₁", context1,
    "The policy now has a measured improvement and a smaller remaining budget.", UPDATED, 3100),
  runtimeStage("Propose replication after the validation gain", "policy", "context-policy", "Proposed action · ã₁", proposal1,
    "Check whether the gain repeats with a new seed. Authorization comes next.", UPDATED, 3700),
  runtimeStage("Feedback changed the next proposal", "policy", null, "Why propose replication?",
    "The gain from 0.842 to 0.851 gives the model a reason to try the same settings with a new seed.",
    "With the same 1.4 GPU-hours left, a flat or worse score could have prompted a different learning rate.", UPDATED, 5100),
];

const fixedTrials = [["A", "0.81"], ["B", "0.79"], ["C", "0.83"]];
const adaptiveTrials = [["A", "0.81"], ["B′", "0.84"], ["C′", "0.82"]];
const choices = [
  "Start with A. Later configurations are still undecided.",
  "A scored 0.81. Use that result to choose B′.",
  "B′ scored 0.84. Use that result to choose the targeted follow-up C′.",
];

function comparisonStage(title, fixedNode, fixedEdge, adaptiveNode, adaptiveEdge, completed, chosen, active, fixed, adaptive, duration = 2800) {
  return {
    title, tracks: [{ node: fixedNode, edge: fixedEdge }, { node: adaptiveNode, edge: adaptiveEdge }],
    completed, chosen, active, fixed, adaptive, duration,
  };
}

function comparisonStages() {
  const stages = [
    comparisonStage("Plan and choose the first trial", "choose", null, "choose", null, 0, 1, [0, 0],
      "A, B, and C are already on the schedule.", choices[0]),
  ];

  for (const [index, [config, score]] of fixedTrials.entries()) {
    const [adaptiveConfig, adaptiveScore] = adaptiveTrials[index];
    const trial = index + 1;
    stages.push(
      comparisonStage("Run trial " + trial, "run", "choose-run", "run", "choose-run",
        index, trial, [index, index], "Run " + config + " from the fixed list.", "Run the chosen configuration " + adaptiveConfig + "."),
      comparisonStage("Observe trial " + trial, "observe", "run-observe", "observe", "run-observe",
        trial, trial, [index, index], config + " scored " + score + ". The schedule is unchanged.",
        adaptiveConfig + " scored " + adaptiveScore + ". Return it to the controller."),
      comparisonStage("Record / update trial " + trial + " result", "record", "observe-record", "update", "observe-update",
        trial, trial, [index, index], "Record " + config + " = " + score + " for final selection.",
        "Update state with " + adaptiveConfig + " = " + adaptiveScore + "."),
    );

    if (trial < fixedTrials.length) {
      stages.push(comparisonStage("Choose trial " + (trial + 1), "choose", null, "choose", "feedback",
        trial, trial + 1, [trial, trial], fixedTrials[trial][0] + " was chosen before execution.", choices[trial], 3600));
    }
  }

  stages.push(comparisonStage("Trial cap reached — stop and select", "end", "record-end", "end", "update-end",
    3, 3, [2, 1], "Stop at three trials and select C (0.83).",
    "Stop at three trials and select B′ (0.84).", 3200));

  return stages;
}

function mountTrack(svg) {
  const nodes = new Map([...svg.querySelectorAll("[data-node]")].map(node => [node.dataset.node, node]));
  const edges = new Map([...svg.querySelectorAll("[data-edge]")].map(edge => [edge.dataset.edge, edge]));
  const token = svg.querySelector("[data-packet]");
  let activeNode;
  let activeEdge;
  let length = 0;

  return {
    select({ node, edge }) {
      activeNode?.classList.remove("is-active");
      activeEdge?.classList.remove("is-active");
      activeNode = nodes.get(node);
      activeEdge = edges.get(edge);
      activeNode?.classList.add("is-active");
      activeEdge?.classList.add("is-active");
      length = activeEdge?.getTotalLength() ?? 0;
    },
    position(progress) {
      token.setAttribute("visibility", activeEdge ? "visible" : "hidden");
      if (activeEdge) {
        const point = activeEdge.getPointAtLength(length * progress);
        token.setAttribute("transform", "translate(" + point.x + " " + point.y + ")");
      }
    },
  };
}

function runtimeReadout(root) {
  const transfer = root.querySelector("[data-transfer]");
  const message = root.querySelector("[data-message]");
  const value = root.querySelector("[data-value]");
  const detail = root.querySelector("[data-detail]");
  const state = [...root.querySelectorAll("[data-state]")];
  transfer.hidden = false;
  return (stage, shown) => {
    const nextTurn = stage.state === UPDATED;
    const packets = {
      "inputs-context": nextTurn ? "g, z₁, o₁ · incumbent 0.851" : "g, z₀, o₀ · baseline 0.842",
      "context-policy": nextTurn ? "c₁ · score 0.851, budget 1.4 GPU-h" : "c₀ · score 0.842, budget 2.0 GPU-h",
      "policy-gate": "ã₀ · lr 3e-4, seed 7",
      "gate-executor": "aᵃᵘᵗʰ₀ · lr 3e-4, seed 7",
      "executor-environment": "Authorized request · lr 3e-4, seed 7",
      "environment-observation": "o₁ · score 0.851, cost 0.6 GPU-h",
      "observation-update": "o₁ · result for job #42",
      feedback: "z₁, o₁ · candidate from #42, 1.4 GPU-h unspent",
    };
    const packet = packets[stage.tracks[0].edge];
    transfer.textContent = packet ? "Packet · " + packet : "";
    message.textContent = shown.message;
    value.textContent = shown.value;
    detail.textContent = shown.detail;
    state.forEach((field, index) => { field.textContent = shown.state[index]; });
  };
}

function experimentReadout(root) {
  const [fixed, adaptive] = root.querySelectorAll("[data-experiment-message]");
  const configs = [...root.querySelectorAll("[data-config]")];
  const scores = [...root.querySelectorAll("[data-score]")];
  const trials = [...root.querySelectorAll(".agent-trials li")];
  return (stage, shown) => {
    fixed.textContent = stage.fixed;
    adaptive.textContent = shown !== stage && stage.tracks[1].edge === "feedback"
      ? "The last score travels back to the chooser."
      : stage.adaptive;
    configs.forEach((field, index) => {
      field.textContent = index < shown.chosen ? adaptiveTrials[index][0] : "Undecided";
    });
    [...fixedTrials, ...adaptiveTrials].forEach(([, score], index) => {
      const trial = index % fixedTrials.length;
      const panel = Math.floor(index / fixedTrials.length);
      scores[index].textContent = trial < shown.completed ? score : "—";
      if (trial === stage.active[panel]) trials[index].setAttribute("aria-current", "step");
      else trials[index].removeAttribute("aria-current");
    });
  };
}

// Keep a figure's shape fixed while the reader steps through it. For each panel
// whose text changes, measure its height in every stage at the current width and
// reserve the tallest, so spare space collects at the bottom of the panel. The
// figure then changes shape only when the page width does.
function reserveSpace(root, selector, visit) {
  let width = -1;
  let frame = 0;

  function regions() {
    const nodes = [...root.querySelectorAll(selector)].map(node =>
      getComputedStyle(node).display === "inline" ? node.parentElement : node);
    return [...new Set(nodes)];
  }

  function measure() {
    const nodes = regions();
    const tallest = nodes.map(() => 0);
    root.setAttribute("aria-busy", "true");
    for (const node of nodes) node.style.minHeight = "";
    visit(() => nodes.forEach((node, i) => {
      tallest[i] = Math.max(tallest[i], node.getBoundingClientRect().height);
    }));
    nodes.forEach((node, i) => { node.style.minHeight = Math.ceil(tallest[i]) + "px"; });
    root.removeAttribute("aria-busy");
  }

  new ResizeObserver(([entry]) => {
    const next = Math.round(entry.contentRect.width);
    if (next === width) return;
    width = next;
    cancelAnimationFrame(frame);
    frame = requestAnimationFrame(measure);
  }).observe(root);
  document.fonts?.ready.then(() => requestAnimationFrame(measure));
}

const reducedMotion = matchMedia("(prefers-reduced-motion: reduce)");

function mountAnimation(root, stages, readout) {
  const tracks = [...root.querySelectorAll("[data-track]")].map(mountTrack);
  const controls = root.querySelector("[data-controls]");
  const play = controls.querySelector("[data-play]");
  const previous = controls.querySelector("[data-previous]");
  const next = controls.querySelector("[data-next]");
  const seek = controls.querySelector("[data-seek]");
  const status = controls.querySelector("[data-status]");
  const label = play.getAttribute("aria-label").slice("Play ".length);
  const last = stages.length - 1;
  let index = 0;
  let playing = false;
  let elapsed = 0;
  let startedAt = 0;
  let frame = 0;
  let timer = 0;
  let shown;

  const stage = () => stages[index];

  function travelTime() {
    if (reducedMotion.matches) return 0;
    if (stage().tracks.some(track => track.edge === "feedback")) return 1800;
    return stage().tracks.some(track => track.edge) ? 950 : 0;
  }

  function positionPackets() {
    const travel = travelTime();
    const readoutStage = elapsed >= travel ? stage() : stages[index - 1];
    if (shown !== readoutStage) {
      shown = readoutStage;
      readout(stage(), shown);
    }
    // Keep a packet just clear of the arrowhead while paused or reading.
    const progress = travel ? Math.min(elapsed / travel, 0.93) : 0.93;
    tracks.forEach(track => track.position(progress));
  }

  function renderStage() {
    stage().tracks.forEach((track, trackIndex) => tracks[trackIndex].select(track));
    shown = null;
    seek.value = index;
    seek.setAttribute("aria-valuetext", stage().title);
    status.textContent = statusText(index);
    previous.setAttribute("aria-disabled", index === 0);
    next.setAttribute("aria-disabled", index === last);
    positionPackets();
  }

  function statusText(i) {
    return "Stage " + (i + 1) + " of " + stages.length + " · " + stages[i].title;
  }

  function updatePlayButton() {
    play.textContent = playing ? "Pause" : "Play";
    play.setAttribute("aria-label", (playing ? "Pause " : "Play ") + label);
  }

  function pause() {
    if (!playing) return;
    elapsed = Math.min(performance.now() - startedAt, stage().duration);
    playing = false;
    cancelAnimationFrame(frame);
    clearTimeout(timer);
    positionPackets();
    updatePlayButton();
  }

  function advance(now) {
    if (!playing) return;
    elapsed = Math.min(now - startedAt, stage().duration);
    if (elapsed === stage().duration) {
      if (index === last) {
        pause();
        return;
      }
      index += 1;
      elapsed = 0;
      startedAt = now;
      renderStage();
    } else {
      positionPackets();
    }

    // Hold readable stages without running frames when the packet is still.
    if (elapsed < travelTime()) frame = requestAnimationFrame(advance);
    else timer = setTimeout(() => advance(performance.now()), stage().duration - elapsed);
  }

  function goTo(target) {
    pause();
    index = target;
    elapsed = travelTime();
    renderStage();
  }

  controls.querySelector("[data-restart]").addEventListener("click", () => {
    goTo(0);
  });
  previous.addEventListener("click", () => { if (index > 0) goTo(index - 1); });
  next.addEventListener("click", () => { if (index < last) goTo(index + 1); });
  seek.max = last;
  seek.addEventListener("input", () => goTo(Number(seek.value)));
  play.addEventListener("click", () => {
    if (playing) {
      pause();
      return;
    }
    if (index === last) goTo(0);
    playing = true;
    startedAt = performance.now() - elapsed;
    updatePlayButton();
    advance(performance.now());
  });

  reducedMotion.addEventListener("change", () => {
    pause();
    positionPackets();
  });
  new IntersectionObserver(([entry]) => {
    if (!entry.isIntersecting) pause();
  }).observe(root);
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) pause();
  });

  renderStage();
  controls.hidden = false;
  reserveSpace(root, "[data-transfer], [data-message], [data-value], [data-detail], [data-state], "
    + "[data-experiment-message], [data-config], [data-score], [data-status]", (measure) => {
    stages.forEach((item, i) => {
      for (const readoutStage of i > 0 ? [item, stages[i - 1]] : [item]) {
        readout(item, readoutStage);
        status.textContent = statusText(i);
        measure();
      }
    });
    shown = null;
    status.textContent = statusText(index);
    positionPackets();
  });
}

const designStages = [
  ["The ticket arrives", "One ticket reaches five designs. Each has the same model, order lookup, handlers, and refund rule. What differs is who picks the next step."],
  ["First model call", "The single call, the pipeline, and the workflow use the model to write or extract text. The router and the agent use it to choose an operation."],
  ["What each design does next", "The single call is finished. The workflow's rule reads the extracted fields and picks Escalate. The router's Refund choice fails its precondition because there is no order number. The agent receives the lookup result."],
  ["Handlers and a proposal", "The workflow runs Escalate, and code falls back to Escalate for the router. The agent uses the lookup result to propose a refund for order #1043."],
  ["The refund is checked", "The pipeline ends after its three fixed steps, and a person takes over the escalated tickets. The runtime checks the agent's proposal against the $100 and 30-day rule. Order #1043 passes."],
  ["The refund runs", "The runtime dispatches the refund handler for order #1043."],
  ["Evidence returns", "The payment system returns a receipt. Until it does, the runtime cannot treat the refund as done."],
  ["The agent proposes to stop", "With the receipt in its context, the agent drafts a reply and proposes to stop. A stop proposal is a request, not a decision."],
  ["The runtime ends the run", "The runtime accepts the stop because the refund has a receipt and the reply is ready."],
  ["Compare the designs", "Only in the agent did the model choose the next operation after seeing a result from the environment. Compare who picked each next step, what it cost, and what could go wrong."],
];

function mountDesignComparison(root) {
  const items = [...root.querySelectorAll("[data-step]")];
  const narration = root.querySelector("[data-narration]");
  const controls = root.querySelector("[data-controls]");
  const play = controls.querySelector("[data-play]");
  const previous = controls.querySelector("[data-previous]");
  const next = controls.querySelector("[data-next]");
  const seek = controls.querySelector("[data-seek]");
  const status = controls.querySelector("[data-status]");
  const last = designStages.length - 1;
  let index = last;
  let playing = false;
  let timer = 0;

  function render() {
    const [title, text] = designStages[index];
    for (const item of items) {
      const step = Number(item.dataset.step);
      item.classList.toggle("is-pending", step > index);
      item.classList.toggle("is-current", step === index);
    }
    narration.textContent = text;
    seek.value = index;
    seek.setAttribute("aria-valuetext", title);
    status.textContent = "Stage " + (index + 1) + " of " + designStages.length + " · " + title;
    previous.setAttribute("aria-disabled", index === 0);
    next.setAttribute("aria-disabled", index === last);
  }

  function updatePlayButton() {
    play.textContent = playing ? "Pause" : "Play";
    play.setAttribute("aria-label", (playing ? "Pause" : "Play") + " design comparison");
  }

  function pause() {
    if (!playing) return;
    playing = false;
    clearTimeout(timer);
    updatePlayButton();
  }

  function schedule() {
    timer = setTimeout(() => {
      if (!playing) return;
      if (index === last) {
        pause();
        return;
      }
      index += 1;
      render();
      schedule();
    }, 2000 + 20 * designStages[index][1].length);
  }

  function goTo(target) {
    pause();
    index = Math.max(0, Math.min(target, last));
    render();
  }

  controls.querySelector("[data-restart]").addEventListener("click", () => goTo(0));
  previous.addEventListener("click", () => { if (index > 0) goTo(index - 1); });
  next.addEventListener("click", () => { if (index < last) goTo(index + 1); });
  seek.max = last;
  seek.addEventListener("input", () => goTo(Number(seek.value)));
  play.addEventListener("click", () => {
    if (playing) {
      pause();
      return;
    }
    if (index === last) index = 0;
    playing = true;
    updatePlayButton();
    render();
    schedule();
  });
  new IntersectionObserver(([entry]) => {
    if (!entry.isIntersecting) pause();
  }).observe(root);
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) pause();
  });

  render();
  narration.hidden = false;
  controls.hidden = false;
  reserveSpace(root, ".agent-design-steps, [data-narration], [data-status]", (measure) => {
    const kept = index;
    for (index = 0; index <= last; index += 1) {
      render();
      measure();
    }
    index = kept;
    render();
  });
}

for (const comparison of document.querySelectorAll("[data-agent-designs]")) {
  mountDesignComparison(comparison);
}

function mountLessonToc() {
  const disclosure = document.querySelector(".agent-lesson-toc");
  const sections = document.querySelectorAll("#TOC > ul > li > a[href^='#']");
  if (!disclosure || !sections.length) return;

  const list = document.createElement("ul");
  for (const section of sections) {
    const item = document.createElement("li");
    const link = document.createElement("a");
    link.href = section.getAttribute("href");
    link.textContent = section.textContent;
    item.append(link);
    list.append(item);
  }
  disclosure.append(list);
  disclosure.hidden = false;
}

function mountOverview(overview) {
  const nodes = [...overview.querySelectorAll("button[aria-controls]")];
  const panels = overview.querySelectorAll("[data-overview-panel]");
  let selected = nodes[0];
  let displayed;

  function show(node) {
    displayed = node;
    const panelId = node.getAttribute("aria-controls");
    for (const item of nodes) {
      item.classList.toggle("is-active", item === node);
      item.setAttribute("aria-pressed", item === selected);
    }
    for (const panel of panels) panel.hidden = panel.id !== panelId;
  }

  for (const node of nodes) {
    node.setAttribute("aria-describedby", node.getAttribute("aria-controls"));
    node.disabled = false;
    node.addEventListener("pointerenter", (event) => {
      if (event.pointerType === "mouse") show(node);
    });
    node.addEventListener("focus", () => show(node));
    node.addEventListener("click", () => {
      selected = node;
      show(node);
    });
  }

  overview.addEventListener("pointerleave", () => show(selected));
  overview.addEventListener("focusout", (event) => {
    if (!overview.contains(event.relatedTarget)) show(selected);
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && displayed !== selected) show(selected);
  });

  overview.querySelector("[data-overview-hint]").hidden = false;
  show(selected);
  reserveSpace(overview, ".agent-overview-info", (measure) => {
    const kept = displayed;
    for (const node of nodes) {
      show(node);
      measure();
    }
    show(kept);
  });
}

for (const overview of document.querySelectorAll("[data-agent-overview]")) {
  mountOverview(overview);
}

mountLessonToc();

for (const root of document.querySelectorAll("[data-agent-animation]")) {
  if (root.dataset.agentAnimation === "runtime") {
    mountAnimation(root, runtimeStages, runtimeReadout(root));
  } else {
    mountAnimation(root, comparisonStages(), experimentReadout(root));
  }
}

const BASELINE = ["Baseline", "0.842", "2.0 GPU-h", "0"];
const PENDING = ["Baseline", "0.842", "2.0 GPU-h", "1"];
const UPDATED = ["Candidate #42", "0.851", "1.4 GPU-h", "0"];

const initialInputs = "Goal: improve validation within 2 GPU-h.\nBaseline: 0.842 · metrics available.";
const context0 = "Baseline 0.842 · budget 2.0 GPU-h\nNo experiment pending.";
const proposal0 = "run_experiment(lr = 3e-4, seed = 7)";
const result1 = "Validation 0.851 · cost 0.6 GPU-h.";
const context1 = "Incumbent #42 scored 0.851.\nBudget 1.4 GPU-h · no job pending.";
const proposal1 = "replicate(config = #42, seed = 11)";

function runtimeStage(title, node, edge, message, value, detail, state, duration) {
  return { title, tracks: [{ node, edge }], message, value, detail, state, duration };
}

const runtimeStages = [
  runtimeStage("Read the architecture", null, null, "Initial inputs · g, z₀, o₀", initialInputs,
    "Decisions move down the left. Observations and updated state return up the right.", BASELINE, 2000),
  runtimeStage("Read goal, state, and observation", "inputs", null, "Input packet · g, z₀, o₀", initialInputs,
    "The controller starts with the goal, its current record, and the baseline observation.", BASELINE, 2400),
  runtimeStage("Construct context", "context", "inputs-context", "Constructed context · c₀", context0,
    "The context builder selects the evidence the policy will see.", BASELINE, 3000),
  runtimeStage("Propose a trial", "policy", "context-policy", "PROPOSED ACTION · ã₀", proposal0,
    "The policy picks a candidate. Nothing has been submitted.", BASELINE, 3000),
  runtimeStage("Validate the proposal", "gate", "policy-gate", "Proposal under review · Γ",
    "✓ Tool permitted\n✓ Parameters valid\n✓ Estimated cost within budget\n✓ No approval required",
    "The runtime checks the request before authorizing it.", BASELINE, 4100),
  runtimeStage("Authorize the operation", "gate", "gate-executor", "AUTHORIZED ACTION · aᵃᵘᵗʰ₀", proposal0,
    "Authorization binds to these parameters. The executor has yet to submit the job.", BASELINE, 3200),
  runtimeStage("Submit the job", "executor", null, "EXECUTED ACTION · u₀", "Job #42 submitted.",
    "The scheduler now has a job. The runtime records one pending experiment.", PENDING, 2650),
  runtimeStage("Run the experiment", "environment", "executor-environment", "Environment · x₀ → x₁", "Job #42 running → complete.",
    "Training runs in the environment. It produces a validation score and a compute charge.", PENDING, 2850),
  runtimeStage("Receive the result", "observation", "environment-observation", "Observation · o₁", result1,
    "The result travels back. The runtime has yet to reconcile its state.", PENDING, 3200),
  runtimeStage("Update state and check for stop", "update", "observation-update", "State update · z₁",
    "Keep candidate #42. Charge 0.6 GPU-h.\nD(…) → continue.",
    "The controller records the new incumbent and clears the pending job.", UPDATED, 3500),
  runtimeStage("Feed the update into the next turn", "inputs", "feedback", "Feedback · z₁ and o₁", context1,
    "The observation changes the information available for the next decision.", UPDATED, 3800),
  runtimeStage("Construct the second context", "context", "inputs-context", "Constructed context · c₁", context1,
    "The policy now has a measured improvement and a smaller remaining budget.", UPDATED, 3100),
  runtimeStage("Propose a different action", "policy", "context-policy", "PROPOSED ACTION · ã₁", proposal1,
    "Replicate the improved configuration with a new seed. This second proposal has not been authorized or run.", UPDATED, 3700),
  runtimeStage("Feedback changed the trajectory", "policy", null, "Feedback changed the trajectory",
    "o₁ changed z₁ → z₁ changed c₁ → c₁ changed ã₁.",
    "The architectural shift is delegated control over a trajectory.", UPDATED, 3200),
];

const fixedTrials = [["A", "0.81"], ["B", "0.79"], ["C", "0.83"]];
const adaptiveTrials = [["A", "0.81"], ["B′", "0.84"], ["C′", "0.82"]];
const choices = [
  "Start with A. Later configurations are still undecided.",
  "A scored 0.81. Use that result to choose B′.",
  "B′ scored 0.84. Choose a replication, C′, with a new seed.",
];

function comparisonStage(title, fixedNode, fixedEdge, adaptiveNode, adaptiveEdge, completed, chosen, active, fixed, adaptive, duration = 2800) {
  return {
    title, tracks: [{ node: fixedNode, edge: fixedEdge }, { node: adaptiveNode, edge: adaptiveEdge }],
    completed, chosen, active, fixed, adaptive, duration,
  };
}

function comparisonStages() {
  const stages = [
    comparisonStage("Set the experiment horizon", "choose", null, "choose", null, 0, 1, 0,
      "A, B, and C are already on the schedule.", choices[0]),
  ];

  for (const [index, [config, score]] of fixedTrials.entries()) {
    const [adaptiveConfig, adaptiveScore] = adaptiveTrials[index];
    const trial = index + 1;
    stages.push(
      comparisonStage("Run trial " + trial, "run", "choose-run", "run", "choose-run",
        index, trial, index, "Run " + config + " from the fixed list.", "Run the chosen configuration " + adaptiveConfig + "."),
      comparisonStage("Observe trial " + trial, "observe", "run-observe", "observe", "run-observe",
        trial, trial, index, config + " scored " + score + ". The schedule is unchanged.",
        adaptiveConfig + " scored " + adaptiveScore + ". Return it to the controller."),
      comparisonStage("Record trial " + trial, "observe", null, "update", "observe-update",
        trial, trial, index, "Record the score for final selection.",
        "Update the controller’s record with " + adaptiveConfig + " = " + adaptiveScore + "."),
    );

    if (trial < fixedTrials.length) {
      stages.push(comparisonStage("Choose trial " + (trial + 1), "choose", null, "choose", "feedback",
        trial, trial + 1, trial, fixedTrials[trial][0] + " was chosen before execution.", choices[trial], 3600));
    }
  }

  stages.push(comparisonStage("Reach the fixed horizon", "end", "observe-end", "update", null,
    3, 3, -1, "Stop at three trials and select C (0.83).",
    "Stop at three trials and select B′ (0.84). Feedback already shaped the trajectory.", 3200));

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
      "executor-environment": "u₀ · submit job #42",
      "environment-observation": "o₁ · score 0.851, cost 0.6 GPU-h",
      "observation-update": "o₁ · result for job #42",
      feedback: "z₁, o₁ · incumbent #42, budget 1.4 GPU-h",
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
    fixed.textContent = shown.fixed;
    adaptive.textContent = shown !== stage && stage.tracks[1].edge === "feedback"
      ? "The last score travels back to the chooser."
      : shown.adaptive;
    configs.forEach((field, index) => {
      field.textContent = index < shown.chosen ? adaptiveTrials[index][0] : "Undecided";
    });
    [...fixedTrials, ...adaptiveTrials].forEach(([, score], index) => {
      const trial = index % fixedTrials.length;
      scores[index].textContent = trial < shown.completed ? score : "—";
      if (trial === shown.active) trials[index].setAttribute("aria-current", "step");
      else trials[index].removeAttribute("aria-current");
    });
  };
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
    status.textContent = "Stage " + (index + 1) + " of " + stages.length + " · " + stage().title;
    previous.setAttribute("aria-disabled", index === 0);
    next.setAttribute("aria-disabled", index === last);
    positionPackets();
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
}

for (const root of document.querySelectorAll("[data-agent-animation]")) {
  if (root.dataset.agentAnimation === "runtime") {
    mountAnimation(root, runtimeStages, runtimeReadout(root));
  } else {
    mountAnimation(root, comparisonStages(), experimentReadout(root));
  }
}

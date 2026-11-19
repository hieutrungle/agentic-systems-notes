// Block 02 controller trace. Values match `python -m labs.controller --scenario ordinary|lost-score`.

const START_RECORD = {
  mode: "Ready",
  incumbent: "baseline · 0.842",
  compute: "2.0 GPU-h unspent · 0.0 reserved",
  trials: "0 of 5 trials · 0 of 10 proposals",
  pending: "None",
};
const START_EXTERNAL = { scheduler: "No job for this run", evaluator: "baseline · 0.842 (v1)" };
const NO_CONTEXT = "Not built. A context exists only for a policy turn.";
const CONTEXT_0 = "Goal: beat the incumbent on validation.\nIncumbent: baseline 0.842.\n2.0 GPU-h and 5 trials left.\nOperations: propose a trial, propose stop.";
const CONTEXT_1 = "Goal: beat the incumbent on validation.\nIncumbent: t1 0.851 (baseline 0.842).\n1.4 GPU-h and 4 trials left.\nOperations: propose a trial, propose stop.";
const KEPT = {
  incumbent: "t1 · 0.851",
  compute: "1.4 GPU-h unspent · 0.0 reserved",
  pending: "None · t1 closed",
};

function stage(base, change) {
  return {
    ...base,
    ...change,
    record: { ...base.record, ...change.record },
    external: { ...base.external, ...change.external },
  };
}

function buildPrefix() {
  const s0 = {
    chip: "Ready", from: null, to: "Ready", owner: "Start", event: "None yet", guard: "None yet",
    update: "The ledger holds the baseline as the incumbent.",
    note: "No trial is in flight, and no context exists yet.",
    record: START_RECORD, external: START_EXTERNAL, context: null, contextTag: "", stale: false, checkpoint: 0, changed: [],
  };
  const s1 = stage(s0, {
    chip: "Proposing", from: "Ready", to: "Proposing", row: 1, owner: "Controller rule", event: "Limits checked",
    guard: "0 of 5 trials, 0 of 10 proposals, 2.0 GPU-h unreserved, no stop requested ✓",
    update: "Build context c₁ from the ledger.",
    note: "Ready is the only mode that starts a policy turn, so the stop rule runs here every time.",
    record: { mode: "Proposing" }, context: CONTEXT_0, contextTag: "c₁ · built for policy turn 1", stale: false,
    checkpoint: 1, changed: ["mode", "context"],
  });
  const s2 = stage(s1, {
    chip: "Authorizing", from: "Proposing", to: "Authorizing", row: 3, owner: "Policy",
    event: "Trial proposed: lr 3e-4, seed 7, estimate 0.7 GPU-h",
    guard: "The reply answers turn 1 ✓",
    update: "Count proposal 1 of 10. Record the arguments.",
    note: "This is the policy's only choice in the trial. Nothing has been sent.",
    record: { mode: "Authorizing", trials: "0 of 5 trials · 1 of 10 proposals" },
    contextTag: "c₁ · used by proposal 1, now stale", stale: true, checkpoint: 2, changed: ["mode", "trials"],
  });
  const s3 = stage(s2, {
    chip: "Dispatching", from: "Authorizing", to: "Dispatching", row: 7, owner: "Gate", event: "Allowed",
    guard: "The approval binds lr 3e-4, seed 7, estimate 0.7. 0.7 ≤ 2.0 GPU-h unreserved. No stop requested ✓",
    update: "Mint trial t1 and operation t1‑submit. Store the approved request. Reserve 0.7 GPU-h. Count trial 1 of 5. Commit checkpoint 3, then send.",
    note: "Checkpoint 3 proves the request may have been sent. It cannot prove that the scheduler received it.",
    record: {
      mode: "Dispatching", compute: "2.0 GPU-h unspent · 0.7 reserved",
      trials: "1 of 5 trials · 1 of 10 proposals", pending: "t1 · operation t1‑submit · no job yet",
    },
    external: { scheduler: "Has not seen t1‑submit yet" },
    checkpoint: 3, changed: ["mode", "compute", "trials", "pending", "scheduler"],
  });
  const s4 = stage(s3, {
    chip: "Running", from: "Dispatching", to: "Running", row: 8, owner: "Scheduler", event: "Accepted: job #42 for t1‑submit",
    guard: "The operation ID matches the pending trial ✓",
    update: "Record job #42.",
    note: "The controller now knows that the scheduler accepted the job. Completion arrives as a separate event.",
    record: { mode: "Running", pending: "t1 · job #42" },
    external: { scheduler: "Job #42 accepted and running" },
    checkpoint: 4, changed: ["mode", "pending", "scheduler"],
  });
  const s5 = stage(s4, {
    chip: "Scoring", from: "Running", to: "Scoring", row: 9, owner: "Scheduler", event: "Job done: #42, cost 0.6 GPU-h",
    guard: "The job ID matches the pending trial ✓",
    update: "Record the cost. Request a score with scoring ID t1‑score.",
    note: "The cost is recorded but not yet charged. The reservation still covers it.",
    record: { mode: "Scoring", pending: "t1 · job #42 · score requested (t1‑score)" },
    external: { scheduler: "Job #42 complete · weights stored", evaluator: "Scoring t1 for request t1‑score" },
    checkpoint: 5, changed: ["mode", "pending", "scheduler", "evaluator"],
  });
  return [s0, s1, s2, s3, s4, s5];
}

function nextTurn(base, checkpoint, notes) {
  const check = stage(base, {
    chip: "Proposing", from: "Ready", to: "Proposing", row: 1, owner: "Controller rule", event: "Limits checked",
    guard: "1 of 5 trials, 1 of 10 proposals, 1.4 GPU-h unreserved, no stop requested ✓",
    update: "Build context c₂ from the ledger.",
    note: notes[0],
    record: { mode: "Proposing" }, context: CONTEXT_1, contextTag: "c₂ · built for policy turn 2", stale: false,
    checkpoint, changed: ["mode", "context"],
  });
  const propose = stage(check, {
    chip: "Authorizing", from: "Proposing", to: "Authorizing", row: 3, owner: "Policy",
    event: "Trial proposed: replicate t1 with seed 11, estimate 0.7 GPU-h",
    guard: "The reply answers turn 2 ✓",
    update: "Count proposal 2 of 10. Record the arguments.",
    note: notes[1],
    record: { mode: "Authorizing", trials: "1 of 5 trials · 2 of 10 proposals" },
    contextTag: "c₂ · used by proposal 2, now stale", stale: true, checkpoint: checkpoint + 1, changed: ["mode", "trials"],
  });
  return [check, propose];
}

function buildScenarios() {
  const prefix = buildPrefix();
  const s5 = prefix[5];

  const scored = stage(s5, {
    chip: "Ready", from: "Scoring", to: "Ready", row: 11, owner: "Evaluator", event: "Score: t1 = 0.851 (v1)",
    guard: "The score is for pending trial t1 and comes from v1 ✓",
    update: "Charge 0.6 GPU-h and release the 0.7 reservation. 0.851 > 0.842, so keep t1. Close t1.",
    note: "Promotion is a rule in code: strict improvement on validation.",
    record: { mode: "Ready", ...KEPT },
    external: { evaluator: "Stored t1 = 0.851 (v1)" },
    checkpoint: 6, changed: ["mode", "incumbent", "compute", "pending", "evaluator"],
  });
  const ordinary = [...prefix, scored, ...nextTurn(scored, 7, [
    "The context is rebuilt from the record, so a restart would produce the same evidence.",
    "The policy chooses again. The gate checks this request next.",
  ])];

  const timeout = stage(s5, {
    chip: "Reconciling", from: "Scoring", to: "Reconciling", row: 14, owner: "Clock", event: "Timeout: no score within 10 min",
    guard: "A recovery attempt remains (1 of 3) ✓",
    update: "Keep the 0.7 GPU-h reservation. Look up the stored score under t1‑score, then job #42.",
    note: "Known: job #42 finished and t1‑score was requested. Unknown: whether a score exists. No new trial can start.",
    record: { mode: "Reconciling", pending: "t1 · job #42 · score unknown (t1‑score)" },
    external: { evaluator: "Stored t1 = 0.851 (v1). The reply was lost." },
    checkpoint: 6, changed: ["mode", "pending", "evaluator"],
  });
  const found = stage(timeout, {
    chip: "Ready", from: "Reconciling", to: "Ready", row: 16, owner: "Evaluator store",
    event: "Score found: the lookup of t1‑score returns 0.851 (v1)",
    guard: "The score is for pending trial t1, its cost is known, and it comes from v1 ✓",
    update: "Apply row 11's update: charge 0.6, release 0.7, keep t1, close t1.",
    note: "Reconciliation reads the evaluator's stored record instead of scoring again.",
    record: { mode: "Ready", ...KEPT },
    checkpoint: 7, changed: ["mode", "incumbent", "compute", "pending"],
  });
  const duplicate = stage(found, {
    chip: "Ready ↺", chipLabel: "Ready, late reply logged", from: "Ready", to: "Ready", row: 22, owner: "Evaluator",
    event: "Score: late reply t1 = 0.851 (v1)",
    guard: "t1 is no longer pending, so only the log-and-ignore row matches",
    update: "Log and ignore the late reply.",
    note: "No update can fire because no trial is pending. A callback that charged every score it received would charge 0.6 GPU-h again and leave 0.8.",
    checkpoint: 8, changed: [],
  });
  const lost = [...prefix, timeout, found, duplicate, ...nextTurn(duplicate, 9, [
    "The ledger now matches the ordinary trace, two checkpoints later, so the policy sees the same evidence.",
    "Same evidence and the same choice. The lost reply cost a lookup, not a trial.",
  ])];

  return { ordinary, "lost-score": lost };
}

const scenarios = buildScenarios();
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

function mountTrace(root) {
  const controls = root.querySelector("[data-controls]");
  const play = controls.querySelector("[data-play]");
  const previous = controls.querySelector("[data-previous]");
  const next = controls.querySelector("[data-next]");
  const seek = controls.querySelector("[data-seek]");
  const status = controls.querySelector("[data-status]");
  const scenarioGroup = root.querySelector("[data-scenarios]");
  const scenarioButtons = [...scenarioGroup.querySelectorAll("[data-scenario]")];
  const path = root.querySelector("[data-path]");
  const text = name => root.querySelector("[data-" + name + "]");
  const fields = new Map([...root.querySelectorAll("[data-field]")].map(node => [node.dataset.field, node]));
  let scenario = "ordinary";
  let index = 0;
  let playing = false;
  let timer = 0;

  const stages = () => scenarios[scenario];
  const current = () => stages()[index];

  function renderPath() {
    path.replaceChildren(...stages().map((item, i) => {
      const chip = document.createElement("li");
      const label = document.createElement("span");
      label.textContent = item.chip;
      chip.append(label);
      if (item.chipLabel) chip.setAttribute("aria-label", item.chipLabel);
      if (item.to === "Proposing") chip.classList.add("is-policy-mode");
      chip.classList.add(i < index ? "is-past" : i === index ? "is-current" : "is-future");
      if (i === index) chip.setAttribute("aria-current", "step");
      return chip;
    }));
  }

  function setField(name, value, changed) {
    const node = fields.get(name);
    if (!node) return;
    const target = node.querySelector("dd") ?? node.querySelector(".loop-context") ?? node;
    target.textContent = value;
    node.classList.toggle("is-changed", changed);
    node.classList.toggle("is-empty", name === "context" && value === NO_CONTEXT);
  }

  function render() {
    const item = current();
    const last = stages().length - 1;
    text("owner").textContent = item.owner;
    text("owner").dataset.owner = item.owner === "Policy" ? "policy" : "runtime";
    text("transition").textContent = item.from ? item.from + " → " + item.to + " · row " + item.row : "Start in Ready";
    text("event").textContent = item.event;
    text("guard").textContent = item.guard;
    text("update").textContent = item.update;
    text("note").textContent = item.note;
    for (const [name, value] of Object.entries(item.record)) setField(name, value, item.changed.includes(name));
    for (const [name, value] of Object.entries(item.external)) setField(name, value, item.changed.includes(name));
    setField("context", item.context ?? NO_CONTEXT, item.changed.includes("context"));
    fields.get("context").classList.toggle("is-stale", item.stale);
    text("context-tag").textContent = item.contextTag ? " · " + item.contextTag : "";
    setField("checkpoint", "checkpoint " + item.checkpoint, false);
    root.classList.toggle("is-animated", !reducedMotion.matches);
    renderPath();
    seek.max = last;
    seek.value = index;
    const title = item.from ? item.from + " → " + item.to + " (row " + item.row + ") · " + item.event : "Start in Ready";
    seek.setAttribute("aria-valuetext", title);
    status.textContent = "Stage " + (index + 1) + " of " + (last + 1) + " · " + title;
    previous.setAttribute("aria-disabled", index === 0);
    next.setAttribute("aria-disabled", index === last);
  }

  function updatePlayButton() {
    play.textContent = playing ? "Pause" : "Play";
    play.setAttribute("aria-label", (playing ? "Pause" : "Play") + " controller trace");
  }

  function pause() {
    if (!playing) return;
    playing = false;
    clearTimeout(timer);
    updatePlayButton();
  }

  function dwell() {
    const item = current();
    return 2200 + 22 * (item.update.length + item.note.length);
  }

  function schedule() {
    timer = setTimeout(() => {
      if (!playing) return;
      if (index === stages().length - 1) {
        pause();
        return;
      }
      index += 1;
      render();
      schedule();
    }, dwell());
  }

  function goTo(target) {
    pause();
    index = Math.max(0, Math.min(target, stages().length - 1));
    render();
  }

  for (const button of scenarioButtons) {
    button.addEventListener("click", () => {
      scenario = button.dataset.scenario;
      for (const other of scenarioButtons) other.setAttribute("aria-pressed", other === button);
      goTo(index);
    });
  }
  controls.querySelector("[data-restart]").addEventListener("click", () => goTo(0));
  previous.addEventListener("click", () => { if (index > 0) goTo(index - 1); });
  next.addEventListener("click", () => { if (index < stages().length - 1) goTo(index + 1); });
  seek.addEventListener("input", () => goTo(Number(seek.value)));
  play.addEventListener("click", () => {
    if (playing) {
      pause();
      return;
    }
    if (index === stages().length - 1) index = 0;
    playing = true;
    updatePlayButton();
    render();
    schedule();
  });

  reducedMotion.addEventListener("change", render);
  new IntersectionObserver(([entry]) => {
    if (!entry.isIntersecting) pause();
  }).observe(root);
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) pause();
  });

  render();
  scenarioGroup.hidden = false;
  controls.hidden = false;
  reserveSpace(root, ".loop-path, .loop-step, .loop-layer, [data-status]", (measure) => {
    const kept = [scenario, index];
    for (scenario of Object.keys(scenarios)) {
      for (index = 0; index < stages().length; index += 1) {
        render();
        measure();
      }
    }
    [scenario, index] = kept;
    render();
  });
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

mountLessonToc();

// Figures 1, 3, and 4: select a mode or group to list the rows that leave it, then
// a row to read its event, guard, and update. The selected row's edge is highlighted.
function mountControllerMap(root) {
  const modes = [...root.querySelectorAll("[data-map-mode]")];
  const sections = new Map([...root.querySelectorAll("[data-map-section]")]
    .map(section => [section.dataset.mapSection, section]));
  const wires = [...root.querySelectorAll(".loop-map-wires [data-rows]")];
  const chosen = new Map();
  let current = root.dataset.defaultMode;

  const rowButtons = section => [...section.querySelectorAll("[data-map-row]")];

  function highlight(row) {
    for (const wire of wires) {
      wire.classList.toggle("is-active", row !== null && wire.dataset.rows.split(" ").includes(row));
    }
  }

  function showRow(section, row) {
    for (const button of rowButtons(section)) button.setAttribute("aria-pressed", button.dataset.mapRow === row);
    for (const detail of section.querySelectorAll("[data-map-detail]")) detail.hidden = detail.dataset.mapDetail !== row;
    chosen.set(section.dataset.mapSection, row);
    highlight(row);
  }

  function showMode(key) {
    current = key;
    for (const button of modes) {
      const on = button.dataset.mapMode === key;
      button.classList.toggle("is-active", on);
      button.setAttribute("aria-pressed", on);
    }
    for (const [name, section] of sections) section.hidden = name !== key;
    const section = sections.get(key);
    const buttons = rowButtons(section);
    if (buttons.length) showRow(section, chosen.get(key) ?? buttons[0].dataset.mapRow);
    else highlight(null);
  }

  for (const button of modes) {
    button.disabled = false;
    button.addEventListener("click", (event) => {
      showMode(button.dataset.mapMode);
      // Keyboard activation moves focus to the mode's selected row.
      if (event.detail === 0) sections.get(current).querySelector("[data-map-row][aria-pressed='true']")?.focus();
    });
  }
  for (const section of sections.values()) {
    for (const button of rowButtons(section)) {
      button.disabled = false;
      button.addEventListener("click", () => showRow(section, button.dataset.mapRow));
    }
  }

  const defaultSection = sections.get(current);
  if (defaultSection && root.dataset.defaultRow) chosen.set(current, root.dataset.defaultRow);
  showMode(current);
  root.querySelector("[data-map-hint]").hidden = false;

  reserveSpace(root, "[data-map-info]", (measure) => {
    const keep = [current, new Map(chosen)];
    for (const [name, section] of sections) {
      showMode(name);
      const buttons = rowButtons(section);
      if (!buttons.length) measure();
      for (const button of buttons) {
        showRow(section, button.dataset.mapRow);
        measure();
      }
    }
    chosen.clear();
    for (const [name, row] of keep[1]) chosen.set(name, row);
    showMode(keep[0]);
  });
}

for (const root of document.querySelectorAll("[data-controller-map]")) {
  mountControllerMap(root);
}

for (const root of document.querySelectorAll("[data-loop-trace]")) {
  mountTrace(root);
}

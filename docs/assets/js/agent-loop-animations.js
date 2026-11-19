// Block 02 figures. Figure 1 is an interactive overview; Figures 2-4 are stepped
// animations. docs/assets/diagrams/controller_figures.py generates their markup:
// each step is an <li> in an ordered list that holds the step's card and the state
// of the visual. Without JavaScript the lists are the figure.

const reducedMotion = matchMedia("(prefers-reduced-motion: reduce)");
const words = value => (value ?? "").split(" ").filter(Boolean);

// Keep a figure's shape fixed while the reader steps through it. For each panel
// whose text changes, measure its height in every step at the current width and
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

// Highlight a set of rows in a controller diagram. The current rows are raised
// so a shared return line shows the current row's path on top.
function diagramParts(root) {
  const byRow = selector => {
    const map = new Map();
    for (const node of root.querySelectorAll(selector)) {
      const row = node.dataset.row;
      if (!map.has(row)) map.set(row, []);
      map.get(row).push(node);
    }
    return map;
  };
  return {
    edges: byRow(".cm-edge"),
    badges: byRow(".cm-badge"),
    modes: new Map([...root.querySelectorAll(".cm-node")].map(node => [node.dataset.mode, node])),
  };
}

function raise(nodes) {
  for (const node of nodes) node.parentNode.append(node);
}

// Figure 1: hover, focus, or tap an item to read it. Clicking selects it; the
// displayed item returns to the selection when the pointer or focus leaves.
function mountOverview(root) {
  const items = [...root.querySelectorAll("button[aria-controls]")];
  const panels = [...root.querySelectorAll("[data-overview-panel]")];
  const parts = diagramParts(root);
  let selected = items.find(item => item.getAttribute("aria-controls") === "ov-ready") ?? items[0];
  let displayed;

  function show(item) {
    displayed = item;
    const panelId = item.getAttribute("aria-controls");
    for (const other of items) {
      other.classList.toggle("is-current", other === item);
      other.setAttribute("aria-pressed", other === selected);
    }
    for (const panel of panels) panel.hidden = panel.id !== panelId;
    const rows = new Set(words(item.dataset.rows));
    for (const [row, nodes] of parts.edges) {
      const on = rows.has(row);
      for (const node of nodes) node.classList.toggle("is-current", on);
      if (on) raise(nodes);
    }
  }

  for (const item of items) {
    item.disabled = false;
    item.addEventListener("pointerenter", (event) => {
      if (event.pointerType === "mouse") show(item);
    });
    item.addEventListener("focus", () => show(item));
    item.addEventListener("click", () => {
      selected = item;
      show(item);
    });
  }
  root.addEventListener("pointerleave", () => show(selected));
  root.addEventListener("focusout", (event) => {
    if (!root.contains(event.relatedTarget)) show(selected);
  });
  root.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && displayed !== selected) show(selected);
  });

  root.classList.add("is-enhanced");
  root.querySelector("[data-overview-hint]").hidden = false;
  show(selected);
  reserveSpace(root, "[data-overview-info]", (measure) => {
    const kept = displayed;
    for (const item of items) {
      show(item);
      measure();
    }
    show(kept);
  });
}

// Figures 2-4: Restart, ← Step, Play/Pause, Step →, and a slider. The status line
// reads "Step n of N · title". Playback pauses when the figure leaves the view.
function mountStepper(root) {
  const variant = root.dataset.variant;
  const lists = [...root.querySelectorAll("[data-steps]")];
  const scenarios = new Map(lists.map(list => [list.dataset.scenario ?? "main", [...list.children]]));
  const card = root.querySelector("[data-card]");
  const controls = root.querySelector("[data-controls]");
  const play = controls.querySelector("[data-play]");
  const previous = controls.querySelector("[data-previous]");
  const next = controls.querySelector("[data-next]");
  const seek = controls.querySelector("[data-seek]");
  const status = controls.querySelector("[data-status]");
  const scenarioGroup = root.querySelector("[data-scenarios]");
  const scenarioButtons = scenarioGroup ? [...scenarioGroup.querySelectorAll("[data-scenario]")] : [];
  const layers = root.querySelector("[data-layers]");
  const fields = layers ? new Map([...layers.querySelectorAll("[data-field]")].map(node => [node.dataset.field, node])) : new Map();
  const live = name => layers?.querySelector(`[data-live="${name}"]`);
  const lanes = new Map([...root.querySelectorAll("[data-rule]")].map(node => [node.dataset.rule, node]));
  const parts = diagramParts(root);
  let scenario = scenarios.keys().next().value;
  let index = 0;
  let playing = false;
  let timer = 0;

  const steps = () => scenarios.get(scenario);
  const current = () => steps()[index];

  function renderDiagram(step) {
    const now = new Set(words(step.dataset.current));
    const seen = new Set(words(step.dataset.shown ?? step.dataset.visited));
    for (const map of [parts.edges, parts.badges]) {
      for (const [row, nodes] of map) {
        const on = now.has(row);
        for (const node of nodes) {
          node.classList.toggle("is-current", on);
          node.classList.toggle("is-visited", seen.has(row) && !on);
          node.classList.toggle("is-hidden", !seen.has(row) && !on);
        }
        if (on) raise(nodes);
      }
    }
    for (const [mode, node] of parts.modes) node.classList.toggle("is-current", mode === step.dataset.mode);
  }

  function renderLanes(step) {
    const moved = new Set(words(step.dataset.moved));
    const now = words(step.dataset.current);
    for (const [rule, node] of lanes) {
      // "rule:agent" marks the agent's side of a rule that has also moved.
      const agentSide = now.includes(rule + ":agent");
      node.classList.toggle("is-moved", moved.has(rule));
      node.classList.toggle("is-current", agentSide || now.includes(rule));
      node.classList.toggle("is-current-agent", agentSide);
    }
  }

  function renderLayers(step) {
    const state = step.querySelector(".cm-state");
    if (!layers || !state) return;
    const changed = new Set(words(step.dataset.changed));
    for (const source of state.querySelectorAll("[data-field]")) {
      const target = fields.get(source.dataset.field);
      if (!target) continue;
      const value = source.querySelector("dd").textContent;
      (target.querySelector("dd") ?? target.querySelector(".cm-context")).textContent = value;
      target.classList.toggle("is-changed", changed.has(source.dataset.field));
    }
    live("checkpoint").textContent = "checkpoint " + state.dataset.checkpoint;
    live("tag").textContent = state.dataset.tag ? " · " + state.dataset.tag : "";
    const context = fields.get("context");
    context.classList.toggle("is-stale", state.dataset.stale === "true");
    context.classList.toggle("is-empty", !state.dataset.tag);
  }

  function render() {
    const step = current();
    const last = steps().length - 1;
    card.innerHTML = step.querySelector(".cm-card-body").innerHTML;
    if (parts.edges.size) renderDiagram(step);
    if (lanes.size) renderLanes(step);
    renderLayers(step);
    root.classList.toggle("is-animated", !reducedMotion.matches);
    seek.max = last;
    seek.value = index;
    const title = step.dataset.title;
    seek.setAttribute("aria-valuetext", `Step ${index + 1} of ${last + 1}, ${title}`);
    status.textContent = `Step ${index + 1} of ${last + 1} · ${title}`;
    previous.setAttribute("aria-disabled", index === 0);
    next.setAttribute("aria-disabled", index === last);
  }

  function updatePlayButton() {
    play.textContent = playing ? "Pause" : "Play";
  }

  function pause() {
    if (!playing) return;
    playing = false;
    clearTimeout(timer);
    updatePlayButton();
  }

  // Long enough to read the narration; the row's fields stay on screen while paused.
  function dwell() {
    const note = card.querySelector(".cm-note")?.textContent ?? "";
    return 2600 + 24 * note.length;
  }

  function schedule() {
    timer = setTimeout(() => {
      if (!playing) return;
      if (index === steps().length - 1) {
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
    index = Math.max(0, Math.min(target, steps().length - 1));
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
  next.addEventListener("click", () => { if (index < steps().length - 1) goTo(index + 1); });
  seek.addEventListener("input", () => goTo(Number(seek.value)));
  play.addEventListener("click", () => {
    if (playing) {
      pause();
      return;
    }
    if (index === steps().length - 1) index = 0;
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

  root.classList.add("is-enhanced");
  card.hidden = false;
  if (layers) layers.hidden = false;
  if (scenarioGroup) scenarioGroup.hidden = false;
  controls.hidden = false;
  render();
  reserveSpace(root, ".cm-card, .cm-layer, [data-status]", (measure) => {
    const kept = [scenario, index];
    for (scenario of scenarios.keys()) {
      for (index = 0; index < steps().length; index += 1) {
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

for (const root of document.querySelectorAll("[data-cm-overview]")) {
  mountOverview(root);
}

for (const root of document.querySelectorAll("[data-cm-stepper]")) {
  mountStepper(root);
}

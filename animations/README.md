# Manim scenes

Use Python 3.12 with uv. Install the native Cairo, Pango, and FFmpeg prerequisites for your platform. On Ubuntu, the packages are `build-essential python3-dev pkg-config libcairo2-dev libpango1.0-dev ffmpeg`. See the [Manim installation guide](https://docs.manim.community/en/stable/installation.html).

From the repository root, render the example:

```bash
uv run --no-project --python 3.12 --with-requirements animations/requirements.txt \
  python -m manim -ql animations/autoresearch_loop.py AutoResearchLoop
```

Manim writes the preview to `media/videos/autoresearch_loop/480p15/AutoResearchLoop.mp4`. Use `-qm` for a 720p render. The scene reads trial values from the same Python lab used by the case study. Its panels show a proposed constant predictor, the validation MAE, and whether the proposal became the incumbent. The [case study](../docs/case-studies/autoresearch.qmd) provides a text walkthrough and static diagrams.

To update the clip embedded in the case study, copy the 720p render to `docs/assets/animations/autoresearch-loop.mp4` and review the text walkthrough alongside it.

## Block 01 · Delegated control

Run from the repository root.

```bash
uv run --no-project --python 3.12 --with-requirements animations/requirements.txt \
  python -m manim -qm animations/agent_control_loop.py AgentControlLoop
cp media/videos/agent_control_loop/720p30/AgentControlLoop.mp4 \
  docs/assets/animations/agent-control-loop.mp4
```

The silent scene starts with a single answer and a program-owned workflow. A learned policy then proposes an experiment, the runtime authorizes the operation, and feedback leads to a different proposal for the second trial. The examples are illustrative. [Block 01](../docs/curriculum/01-agent-fundamentals.qmd#agent-control-animation) provides a text walkthrough and links to the static diagrams.

# Manim scenes

Use Python 3.12 with uv. Install the native Cairo, Pango, and FFmpeg prerequisites for your platform. On Ubuntu, the packages are `build-essential python3-dev pkg-config libcairo2-dev libpango1.0-dev ffmpeg`. See the [Manim installation guide](https://docs.manim.community/en/stable/installation.html).

From the repository root, render the example:

```bash
uv run --no-project --python 3.12 --with-requirements animations/requirements.txt \
  python -m manim -ql animations/autoresearch_loop.py AutoResearchLoop
```

Manim writes the preview to `media/videos/autoresearch_loop/480p15/AutoResearchLoop.mp4`. Use `-qm` for a 720p render. The scene reads trial values from the same Python lab used by the case study. Its panels show a proposed constant predictor, the validation MAE, and whether the proposal became the incumbent. The [case study](../docs/case-studies/autoresearch.qmd) provides a text walkthrough and static diagrams.

To update the clip embedded in the case study, copy the 720p render to `docs/assets/animations/autoresearch-loop.mp4` and review the text walkthrough alongside it.

The [Block 01 figures](../docs/curriculum/01-agent-fundamentals.qmd#fig-agent-runtime) animate directly in the browser. Their SVG markup is under `docs/curriculum/_figures/`, with playback in `docs/assets/js/agent-fundamentals-animations.js`.

The [Block 02 figures](../docs/curriculum/02-agent-loop-state-machines.qmd#fig-controller-overview) are generated from one data source. Run `python docs/assets/diagrams/controller_figures.py` from the repository root to rewrite the four includes under `docs/curriculum/_figures/`. The script runs `labs.controller` for every trace value and stops if an authored step disagrees with the lab. `tests/test_controller_figures.py` checks that the committed includes match the generator and the lab. Playback is in `docs/assets/js/agent-loop-animations.js`.

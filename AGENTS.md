# Agentic Systems Notes contributor guide

## Working in this repository

- Run commands from the repository root. Keep changes scoped here. The adjacent `llm-post-training-notes` repository is a read-only reference.
- Publish curated writing under `docs/`. Keep dated exploratory notes in `notes/raw/`. Record substantive post-publication corrections in `ERRATA.md` with evidence and a page or section.
- Keep curriculum filenames stable as `docs/curriculum/NN-topic.qmd` for blocks 01–14. Each block opens with a study question and includes concepts, a study task, and a deliverable. Update the curriculum index when titles or navigation change.
- Place cross-block design exercises under `docs/exercises/` and the shared AutoResearch narrative under `docs/case-studies/`. Link to them with relative `.qmd` paths so links work under a GitHub Pages project prefix.

## Research writing

- Store source metadata once in `docs/references.bib` with a stable `authoryearkeyword` key. Cite in Quarto as `[@key]`. Verify authors, venue, year, and the DOI, arXiv version, or original repository URL against the primary source.
- Use `docs/literature/papers/<bib-key>.qmd` for individual paper notes. Record the question, method, evidence, limitations, and a follow-up. Use `docs/literature/` for reviews that compare claims across sources.
- Mark illustrative, reproduced, and author-reported results clearly. For a numerical claim, identify the lab, fixture or data version, budget or seed where applicable, and rerun command. Pin external experiment inputs to a version. Keep essential examples reproducible from repository fixtures.
- Keep AutoResearch proposals, evaluation, and promotion decisions distinct. State the baseline, selection metric, budget, and final holdout protocol in each experiment. Keep holdout outcomes out of proposal logic.

## Code and assets

- Add small executable Python modules under `labs/` and run them with `python -m labs.<module>`. Use the standard library for core labs where practical. Update `pyproject.toml` and `uv.lock` together when adding a core dependency.
- Exercise behavior with `unittest` in `tests/`. Default examples use deterministic, local fixtures and require no service credentials. Keep secrets and locally generated run output out of Git.
- Use inline Quarto `{mermaid}` for short flows. Keep larger Graphviz sources under `docs/assets/diagrams/` and embed them with a Quarto `{dot}` cell. Give each diagram a caption and text alternative.
- Put Manim scenes and optional dependencies under `animations/`. Add a render command and a text description of what changes in the scene. Keep working renders in ignored `media/`. Put any intentionally published clips under `docs/assets/`, with a transcript or static alternative nearby.

## Verify before handoff

Run all three commands from the root for changes to a lab, the site, or content shared by both.

```bash
python -m unittest discover -s tests -v
quarto render docs --fail-if-warnings
python tests/test_site.py docs/_site
```

Rerender modified Manim scenes with the command in `animations/README.md`. Keep the Quarto build independent of lab execution and optional media tooling. The workflow deploys to GitHub Pages from `main` after testing and the site build succeed.

# Agentic Systems Notes contributor guide

## Working in this repository

- Run commands from the repository root. Keep changes scoped here.
- Publish curated writing under `docs/`. Keep dated exploratory notes in `notes/raw/`. Record substantive post-publication corrections in `ERRATA.md` with evidence and a page or section.
- The canonical 14-block curriculum in `docs/curriculum/index.qmd` is a project invariant. Improve material within the blocks. Change block identities, order, or stable `docs/curriculum/NN-topic.qmd` filenames only at the project owner's explicit request. Preserve published URLs with Quarto aliases when a route changes.
- Place cross-block design exercises under `docs/exercises/` and the shared AutoResearch narrative under `docs/case-studies/`. Link to them with relative `.qmd` paths so links work under a GitHub Pages project prefix.

## Parent sites and publishing

- [Hieu T. Le](https://hieutrungle.github.io/) is the main identity. The [blog](https://hieutrungle.github.io/blog/) and its [Learning hub](https://hieutrungle.github.io/blog/learning/) provide public discovery. The [Agentic Systems gateway](https://hieutrungle.github.io/blog/series/agentic-systems/) introduces the series. The [standalone Quarto site](https://hieutrungle.github.io/agentic-systems-notes/) publishes the full curriculum, literature, labs, exercises, and case study from this repository.
- Use [`hieutrungle/llm-post-training-notes`](https://github.com/hieutrungle/llm-post-training-notes) as a read-only precedent for keeping exploratory notes separate from publishable material, checking results and figures, centralizing citations, and recording errata. Use [`hieutrungle/blog`](https://github.com/hieutrungle/blog) as the visual reference for colors, typography, and parent navigation. Adapt those choices to Quarto's components.
- Keep the blog gateway concise. When a curriculum title or URL changes, coordinate the roadmap in the blog's `_data/series/agentic-systems.yml` with the curriculum index here.
- The site's visual system is stable. Preserve its typography, palette, navigation, layout, and theme architecture unless the project owner explicitly requests a redesign. Prioritize course content, research, labs, diagrams, and learning materials.

## Teaching protocol

- Open each block with a study question and include a study task and deliverable. Develop intuition, then show an architecture or diagram. Formalize where useful and connect the design to machine learning, reinforcement learning, control, or distributed systems. Identify which ideas are general concepts and which belong to a particular framework implementation.
- Use original research, realistic examples, failure modes, production implications, and credible alternatives or disagreements. Connect the block to AutoResearch. Include approximately five conceptual questions.
- Use the sequence **lesson → student answers → critique → model answers**. Keep full answers out of the main lesson so students can reason through the questions before reading a critique.

## Reference policy

1. **Foundations.** Use established machine learning, reinforcement learning, distributed systems, control, and state-machine concepts to define the problem and its assumptions.
2. **Primary book companions.** *AI Agents in Action, Second Edition: Intelligent workflows with LLMs, MCP, A2A, and more* and *Building Applications with AI Agents* supply practical context. Add short companion reading sections where relevant and check chapter numbers in the publisher's table of contents. The 14 blocks follow their own research and design sequence.
3. **Original research.** Cite original papers, benchmarks, and technical reports for reported findings. Identify the conditions and limitations of each result.
4. **Current systems and specifications.** Use primary documentation, versioned specifications such as MCP, and source code for claims about agent runtimes and deployed coding or research systems.
5. **Course synthesis.** Label design patterns, recommendations, and system-design interpretations as engineering judgments and state the conditions that make them useful.

For major technical claims, distinguish established concepts, original research evidence, current systems evidence, and engineering interpretation. Ask what the architectural contribution is, what changed in the model, tools, context, search, compute, orchestration, or evaluation, what baseline was used, what the improvement cost, and whether the evidence justifies the claim.

## Research writing

- Store source metadata once in `docs/references.bib` with a stable `authoryearkeyword` key. Cite in Quarto as `[@key]`. Verify authors, venue, year, and the DOI, arXiv version, or original repository URL against the primary source.
- Use `docs/literature/papers/<bib-key>.qmd` for individual paper notes. Record the question, method, evidence, limitations, and a follow-up. Use `docs/literature/` for reviews that compare claims across sources.
- Mark illustrative, reproduced, and author-reported results clearly. For a numerical claim, identify the lab, fixture or data version, budget or seed where applicable, and rerun command. Pin external experiment inputs to a version. Keep essential examples reproducible from repository fixtures.
- Generate published numbers and figures from versioned inputs using a rerunnable check or experiment. Link the inputs, command, and output from the lesson or nearby asset documentation.
- Use AutoResearch as the running case study. Begin with a hypothesis, an experiment, metrics, and a decision. Later blocks can study research planning, repository inspection, literature search, experiment management, compute budgets, durable state and an experiment ledger, replanning, failure recovery, bounded parallel execution, evaluation, stopping conditions, and observability.
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
python tests/check_curriculum.py --site docs/_site
```

Rerender modified Manim scenes with the command in `animations/README.md`. Keep the Quarto build independent of lab execution and optional media tooling. The workflow deploys to GitHub Pages from `main` after testing and the site build succeed.

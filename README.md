# Agentic Systems Notes

A 14-block research and study curriculum on tool-using AI systems. Follow the [curriculum](docs/curriculum/index.qmd), read the [literature reviews and paper notes](docs/literature/index.qmd), and apply each block to the [AutoResearch case study](docs/case-studies/autoresearch.qmd).

The [Agentic Systems series gateway](https://hieutrungle.github.io/blog/series/agentic-systems/) on Hieu T. Le's blog introduces the series. This repository is the technical source for the [standalone Quarto site](https://hieutrungle.github.io/agentic-systems-notes/), including its course material, runnable labs, and corrections.

## How the course uses references

Foundations in machine learning, reinforcement learning, distributed systems, and control frame the design questions. The two primary book companions are *AI Agents in Action, Second Edition: Intelligent workflows with LLMs, MCP, A2A, and more* and *Building Applications with AI Agents*. They supply practical examples alongside the independent 14-block sequence. The [study site](docs/index.qmd#primary-book-companions) introduces both books, and lessons point to relevant chapters.

Original research and benchmarks support empirical claims. Current runtimes and specifications document what deployed systems implement. Course recommendations identify their assumptions and trade-offs as engineering synthesis. The [shared bibliography](docs/references.bib) holds the source records. Keep exploratory notes in `notes/raw/`, reproduce published results from versioned inputs and scripts, and record substantive corrections in [ERRATA.md](ERRATA.md).

## Run the labs

Use Python 3.11 or newer. The core labs and tests use the standard library.

```bash
python -m labs.tool_contract
python -m labs.autoresearch --budget 4
python -m unittest discover -s tests -v
```

With uv, run `uv sync --locked` to create the local Python 3.12 environment, then substitute `uv run --locked python` for `python` in these commands.

## Render the site

Install [Quarto](https://quarto.org/docs/download/) 1.11.9 to match CI. From the repository root, run the preview or build commands.

```bash
quarto preview docs
```

```bash
quarto render docs --fail-if-warnings
python tests/test_site.py docs/_site
```

The site builds without executing Python labs or rendering Manim scenes. Quarto renders Mermaid and Graphviz as part of the HTML build. See [animations](animations/README.md) for the separate Manim setup and render command.

## Publish with GitHub Pages

Push the repository to a GitHub project with Pages enabled. In the repository settings, set **Pages → Build and deployment → Source** to **GitHub Actions**. The [workflow](.github/workflows/ci.yml) tests and builds pull requests. A push to `main` or a manual run on `main` deploys the artifact after both jobs succeed. See the [GitHub Pages workflow documentation](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages).

## Layout

| Path | Contents |
|---|---|
| `docs/curriculum/` | Numbered study blocks with concepts, tasks, and deliverables |
| `docs/literature/` and `docs/references.bib` | Reviews, paper notes, and the shared bibliography |
| `docs/case-studies/` and `docs/exercises/` | Running case study and cross-block design exercises |
| `docs/assets/` and `animations/` | Diagram and animation sources |
| `labs/` and `tests/` | Executable examples and verification |
| `notes/raw/` and `ERRATA.md` | Exploratory notes and published corrections |

See [AGENTS.md](AGENTS.md) for contributor conventions.

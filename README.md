# AI Document Processing — Construction Submittals POC

A modular monolith demonstrating the architecture for an AI-driven document understanding and workflow platform in the construction submittals / permits / drawings domain.

This repository accompanies a technical proposal for a Senior Software Architect engagement. See **[PROPOSAL.md](./PROPOSAL.md)** for the narrative; see **[docs/architecture.md](./docs/architecture.md)** for the system diagram.

## What it does (the vertical slice)

```
Submittal PDF  →  Parse (pages + bboxes)  →  LLM extraction with citations
                                                      ↓
                                           Reviewer workbench (split view)
                                                      ↓
                                       Approve → state machine advances
                                                      ↓
                                       Routing event → (stub) print/label
```

## Quickstart

### Docker path (no local Python needed)

Requirements: Docker, Make, an `OPENAI_API_KEY` (optional — tests stub the LLM).

```bash
cp .env.example .env       # set OPENAI_API_KEY if running `make demo`
make dev                   # postgres + redis + minio + app + worker + web
make seed                  # create demo org/project/users + CSI vocab
```

Then open `http://localhost:5173` (login: `reviewer@demo` / `demo`).

### Local path (running tests, the demo CLI, or hacking on the code)

Requirements: [`uv`](https://docs.astral.sh/uv/) (Python package manager — install with `curl -LsSf https://astral.sh/uv/install.sh | sh`), Python 3.12.

```bash
uv venv --python 3.12 .venv     # one-time
source .venv/bin/activate
make install                    # uv pip install -e ".[dev]"
make test                       # pytest, full suite, LLM stubbed
make demo                       # run extraction against real OpenAI on the sample fixture
```

> **Why `uv`?** Faster resolver, deterministic lockfile, drop-in for `pip`/`venv`. Nothing here is `uv`-specific — `python -m venv` + `pip install -e ".[dev]"` works identically. The CI workflow uses `uv` for the same reasons.

## Repository tour

| Path | What lives here |
|---|---|
| [`PROPOSAL.md`](./PROPOSAL.md) | The proposal narrative for the founder |
| [`docs/adr/`](./docs/adr/) | 10 Architecture Decision Records |
| [`docs/architecture.md`](./docs/architecture.md) | System diagram, module map, state machine |
| [`docs/extraction-workstream.md`](./docs/extraction-workstream.md) | The AI workstream — interface, deployment, eval |
| [`docs/hiring-rubric-ai-ml.md`](./docs/hiring-rubric-ai-ml.md) | Scoping + interview rubric for the AI/ML hire |
| [`app/workflow/`](./app/workflow/) | Document lifecycle state machine — the spine |
| [`app/extraction/`](./app/extraction/) | AI workstream — schemas, prompts, LLM client, citation grounder, eval |
| [`app/review/`](./app/review/) | Human-in-the-loop review |
| [`web/src/routes/ReviewWorkbench.tsx`](./web/src/routes/ReviewWorkbench.tsx) | The reviewer UI |

## Architectural posture (one paragraph)

Modular monolith with strict internal boundaries (import-linter enforced). The document lifecycle is an explicit state machine — not booleans scattered across the schema. Citations are first-class and non-optional — every extracted field carries `(page, bbox, source_text)`. The extraction module is the AI/ML hire's lane, sealed behind a single Python interface (`ExtractionService`). No agent framework — the LLM is a stateless function call inside a system we own (see [ADR-010](./docs/adr/ADR-010-no-agent-framework.md)).

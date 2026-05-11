# Technical Proposal — Senior Software Architect

**Engagement:** AI-driven document understanding and workflow platform, construction vertical
**Author:** Suvro Banerjee
**Date:** 2026-05-11
**Companion artifact:** this repository (architecture scaffold + vertical slice)

---

## 1. Restating the brief

You are building a B2B SaaS platform that takes complex multi-page construction documents — submittals, specifications, drawings, contracts — runs LLM-driven structured extraction with citations, and routes the results through a multi-stage workflow involving multiple user roles, controlled vocabularies (CSI MasterFormat, permit types, AHJ-specific rules), regulated output requirements, and downstream printing/labeling integrations. The platform exists, has working mockups and a developer, and is at the stage where the lifecycle and state model must be designed properly *now* — not retrofitted later. You need shared technical leadership: architecture audit in the first 30 days, ownership of the AI extraction workstream as a distinct hire-able module, and a partnership posture with your existing developer.

I understand this brief. This proposal is structured around how I would actually approach it — not a generic resume restatement.

---

## 2. The four risks I can already see in this build

These are the failure modes I have watched derail comparable products. Each is observable without seeing your code, because they are structural — driven by the shape of the problem, not the shape of any one implementation.

### 2.1 Lifecycle and state sprawl

> Boolean columns multiply: `is_extracted`, `is_reviewed`, `needs_revision`, `is_approved`, `is_routed`, `is_printed`. The "state" of a document becomes the unspoken sum of seven columns plus a `status` string, mutated from any code path that reaches the row.

This always happens unless the lifecycle is modeled as a **first-class state machine** with named transitions, role guards, and an append-only transition log. In a regulated industry where auditors will ask "who approved this, when, and on what basis?", reconstructing that from booleans is not feasible.

**What I'd do:** ADR-004 in this scaffold — explicit state machine (`python-statemachine`), every transition guarded, every transition emits an audit row. The state machine *is* the spine; everything else hangs off it.

### 2.2 Citation drift

> The LLM returns extracted fields and verbatim quotes. The UI shows the quotes. The PDF underneath has shifted in pagination, or the quote came from a paraphrase, or the bounding box is approximate. Reviewers approve. Six months later, an AHJ challenges a submittal and the citation can't be re-grounded to the source page.

In a regulated workflow, **citations that look right but can't be re-verified are worse than no citations**. The structural fix is to treat `(page, bbox, source_text)` as a hard contract on every field — non-null FK, schema-validated, *grounded back to the parsed page tokens at extraction time*. If grounding fails, the field is rejected and re-extracted, not surfaced as "low confidence."

**What I'd do:** ADR-003 in this scaffold — citations are non-optional, validated, and grounded server-side via a `CitationGrounder` that matches against the indexed page tokens captured at parse time.

### 2.3 Extraction-module ownership ambiguity

> You hire an AI/ML engineer. They start "owning extraction." But their changes touch the API layer, the data model, the prompt repo, the UI's confidence-display logic, and the eval harness. The existing developer is now reviewing AI PRs and the AI engineer is reviewing FastAPI PRs. Two months in, neither party owns anything cleanly, and prompt-versioning is happening through git commits with no eval signal.

The structural fix is to **define the extraction module as a sealed workstream with a typed interface**, the way you'd scope a separately-deployable service even if it ships in-process today. The AI/ML engineer owns the interior: schemas, prompts, model selection, eval. The platform owns the exterior: when extractions are invoked, what's stored, how citations are rendered.

**What I'd do:** ADR-002 in this scaffold. The interface (`ExtractionService.run(request) -> ExtractionResult`) is small and stable. The AI/ML engineer can change anything inside that boundary without coordinating with the platform team. I would draft both the **scoping doc** ([`docs/extraction-workstream.md`](./docs/extraction-workstream.md)) and the **hiring rubric** ([`docs/hiring-rubric-ai-ml.md`](./docs/hiring-rubric-ai-ml.md)) in the first two weeks of the engagement.

### 2.4 Controlled-vocabulary drift

> The CSI MasterFormat division for "Tiling" was `09 30 00` when the project was set up. A year later, the spec library is updated, a code changes, and historical submittals now show a vocabulary mismatch — or worse, silently re-map to a different category. AHJs reject filings; nobody knows why; the database can't tell you what the vocab looked like at the time of the original approval.

Controlled vocabularies in regulated industries are versioned reality. The structural fix: **vocab versions are immutable, every reference snapshots the version ID, and the UI displays the version**. Adding a vocab entry is a versioned change, not an update.

**What I'd do:** ADR-006 in this scaffold. Vocabularies have versions. Foreign keys reference `(term_id, version_id)`. The CSI seeder writes a labeled version.

---

## 3. 30-day architecture-review plan

The first 30 days are an audit, not a rewrite. The product exists; my job is to find structural risk before it becomes technical debt, not to assert opinions for their own sake.

### Week 1 — Listen and read
- 90-minute pairing session with founder: product narrative, customer interviews, the one or two existing customer pilots, what surprised you.
- 90-minute pairing session with existing developer: codebase tour, where they feel the weight, where they've patched twice, where they're proud.
- Read all source code at low altitude. No PRs yet. No opinions externalized.
- Read mockups and specs end-to-end. Map them to current code.

### Week 2 — Map and measure
- Produce a one-page **module map** of the current system: what calls what, where state is stored, where prompts live, where the workflow logic actually executes.
- Produce a **lifecycle/state inventory**: every place document state is read or written.
- Produce a **data-model audit**: nullable fields, FK directions, what's append-only vs. mutable, what's versioned vs. not.
- Run the test suite, the linter, the build. Record what's missing — not as criticism, as backlog.

### Week 3 — ADR backlog
- Draft 5–8 ADRs against the *current* code (not a hypothetical rewrite). Each ADR: what we do today, what risk it carries, what I'd change, what it costs to change, what we lose by changing.
- Workshop the ADR set with the founder and the developer. Prioritize. Some land as "agreed, do later"; some land as "do this quarter."

### Week 4 — Workstream definition
- Define the **AI extraction workstream** as a hire-able unit: interface, ownership boundary, deployment posture, eval harness target metrics, the hiring rubric.
- Help with first-pass JD and screening calls for the AI/ML hire.
- Deliver a **technical roadmap** the founder can take to a board or investor conversation.

What I will **not** do in the first 30 days: large refactors, framework swaps, declaring patterns the team must adopt before I've earned trust, or shipping ADRs the developer didn't have a chance to argue with.

---

## 4. This scaffold — a guided tour

This repository is a working scaffold of the architecture I would propose for your platform. It is not a starting codebase for *your* product — your code already exists. It is a **portfolio piece** that demonstrates concretely how I think, so you can evaluate the thinking before the engagement begins.

The vertical I chose is construction submittals (the closest plausible match to "contracts, technical specifications, drawings + regulated printing"). The vertical slice that actually runs end-to-end is the submittal review flow.

**Ten ADRs** under [`docs/adr/`](./docs/adr/) capture the core decisions. The two I most want you to read are:

- [ADR-002 — Extraction is a separable workstream](./docs/adr/ADR-002-extraction-workstream.md)
- [ADR-004 — Document lifecycle is an explicit state machine](./docs/adr/ADR-004-state-machine.md)
- [ADR-010 — No agent framework for orchestration](./docs/adr/ADR-010-no-agent-framework.md)

The **vertical slice** (in [`tests/e2e/test_vertical_slice.py`](./tests/e2e/test_vertical_slice.py)) drives the full path: upload a submittal PDF, parse it, run extraction with citations (LLM stubbed), open the reviewer workbench, edit a field, approve, observe the state machine transition and the routing event emitted.

What's deliberately deferred and why:

| Deferred | Why it's okay for now |
|---|---|
| Real auth provider (Auth0/Clerk) | JWT + seed users prove the role-guard pattern. Provider is a swap. |
| Multi-tenant row-level enforcement (RLS) | Schema is tenant-aware; API enforces. RLS is a hardening pass. |
| Drawings/CAD parsing | The pipeline architecture is identical; drawings are a different parser plug-in. |
| Real print-shop integration | `pdf_transmittal.py` adapter generates a stamped PDF — the integration seam is what matters here. |
| Frontend auth pages | Dev token shortcut; the workbench is the slice's actual purpose. |

---

## 5. The AI extraction workstream — in detail

See [`docs/extraction-workstream.md`](./docs/extraction-workstream.md) for the full document. The short version:

**Interface (the contract the AI/ML hire cannot break):**

```python
class ExtractionService:
    def run(self, req: ExtractionRequest) -> ExtractionResult: ...
```

```python
class ExtractionRequest:
    document_id: UUID
    schema_id: str          # e.g. "submittal_v1"
    page_range: tuple[int, int] | None
    prompt_version: str | None  # optional pin for reproducibility

class ExtractionResult:
    extraction_id: UUID
    schema_id: str
    schema_version: str
    model: str
    model_version: str
    prompt_version: str
    fields: list[ExtractionField]   # each with citations (non-empty)
    raw_response: dict              # archived verbatim
```

**Deployment posture (a slider, not a one-way door):**

1. *Today:* in-process Celery worker. Lowest ops cost.
2. *When extraction work outgrows app-tier capacity:* dedicated worker pool, same code.
3. *When extraction needs GPUs or a different release cadence:* standalone service over gRPC. Interface unchanged.

**Quality measurement (non-negotiable, ships with the module):**

- Schema validity rate (does the LLM return valid structured output?)
- Citation grounding rate (do the cited quotes match indexed page tokens?)
- Field-level accuracy on a golden set (`app/extraction/eval/golden/*.expected.json`)
- Reviewer edit distance (signal collected from `review_revisions`)

CI runs eval as a **non-blocking** report initially — we collect data before we set thresholds.

**Owned surface area:** `app/extraction/{schemas,prompts,llm,eval}/`. Everything else is shared.

**Hiring:** I would draft the JD, define the screening signal, and run the first technical conversations. Rubric in [`docs/hiring-rubric-ai-ml.md`](./docs/hiring-rubric-ai-ml.md).

---

## 6. Partnership model with your existing developer

Shared technical leadership only works if the seams are explicit. My proposed model:

- **They own:** application code they've already built, all PR review for that surface, customer-facing feature velocity.
- **I own:** architecture decisions (drafted as ADRs, workshopped, never imposed), the extraction workstream interface, the hiring spec for the AI/ML engineer.
- **We share:** the data model, the state machine, the review of cross-cutting PRs.
- **Escalation:** when we disagree, founder breaks the tie. I draft a one-page memo with both positions so the founder isn't choosing blind.
- **Mentorship cadence:** one weekly 1:1 with the developer (separate from standup); informal pairing whenever they ask; no top-down "you should be doing X."

What I will not do: review every PR, gate-keep on style, or volunteer architectural opinions about code that already works. Time spent on those is time stolen from the structural risks in §2.

---

## 7. Optional development contribution

Starting commitment 20–30 hrs/week, weighted toward architecture and the extraction workstream definition. If, after the first 30 days, scaling my hours into hands-on development is useful — building the extraction module foundation before the AI/ML hire lands, or pairing on the state-machine refactor — I am open to it. The default assumption is that I am most useful to you in an architect role with measured, surgical code contributions; we should make that decision based on what the first month reveals.

---

## 8. What I'd want to learn in our first call

Short list — questions whose answers will most shape my actual recommendations:

1. Who is the design partner / first paying customer, and what specifically about your product causes them to renew vs. churn?
2. What's the current document volume per customer per month, and what's the steady-state target? (Drives extraction-tier sizing.)
3. Which downstream printing/labeling system is the real integration target? Is it owned by your customers, by an industry vendor, or both?
4. Where does the existing developer feel the most weight today — what's the part of the codebase they're patching twice a quarter?
5. What's the regulatory shape — is there a specific regime (e.g., AIA, ANSI/AISC, jurisdiction permit codes) the platform must satisfy, or is "regulated" mostly customer/auditor pressure?
6. What's the funding posture — is the next milestone an investor narrative (which biases toward visible architecture documents and demos) or a customer milestone (which biases toward shipped flows)?
7. Have you had a prior architecture engagement, and if so, what didn't work?

---

## Appendix — How to evaluate this scaffold quickly

If you have 15 minutes:

1. Read this `PROPOSAL.md`. (You're doing it.)
2. Read [`docs/architecture.md`](./docs/architecture.md) — one page, with diagrams.
3. Read [`docs/adr/ADR-002-extraction-workstream.md`](./docs/adr/ADR-002-extraction-workstream.md), [`ADR-004-state-machine.md`](./docs/adr/ADR-004-state-machine.md), [`ADR-010-no-agent-framework.md`](./docs/adr/ADR-010-no-agent-framework.md).
4. Skim [`app/workflow/state_machine.py`](./app/workflow/state_machine.py) and [`app/extraction/__init__.py`](./app/extraction/__init__.py).

If you have 45 minutes, also run:

```bash
cp .env.example .env && make dev && make seed && make test
```

…and read [`tests/e2e/test_vertical_slice.py`](./tests/e2e/test_vertical_slice.py).

I'm available for a 30-minute video call at your convenience.

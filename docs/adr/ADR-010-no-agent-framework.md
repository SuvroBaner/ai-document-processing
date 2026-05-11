# ADR-010 — No agent framework for orchestration

**Status:** Accepted
**Date:** 2026-05-11

## Context

Agent frameworks (LangGraph, CrewAI, AutoGen, Anthropic Agents SDK, OpenAI Agents SDK, Pydantic AI) are increasingly the default reach in AI-startup codebases. They are well-suited to autonomous, multi-step, tool-using agents whose trajectory is chosen by the model.

**This product is not that.** It is *structured extraction + human-in-the-loop business workflow*. The LLM call shape is bounded:

> `(parsed pages, JSON schema, prompt template) → structured fields + citations`

The cross-step "workflow" is a **business process state machine** across multiple humans and system steps. That belongs in Postgres under our control (ADR-004) — not inside an agent framework's runtime.

## Decision

We do not adopt an agent framework. Orchestration is:

- **`LLMClient` Protocol** (ADR-008) — direct provider SDK calls.
- **Our `DocumentLifecycle` state machine** (ADR-004) — the business workflow.
- **Celery** — fixed async pipelines (parse → extract → ground citations).

The LLM is a **stateless function call** inside a system we own.

## Costs of adopting a framework prematurely

- Two state machines to reason about (ours + the framework's).
- Prompts and retries buried inside opaque abstractions.
- Audit trail entangled with a third-party runtime.
- Test surface exploded — we'd be testing the framework's control flow.
- Model / provider swaps become the framework's problem, not a one-line change.

## When an agent harness *legitimately* enters

Evaluated at the boundary of a genuinely agentic sub-task, always subordinate to the business state machine, always inside a single module with a typed I/O contract (same posture as today's `ExtractionService`):

| Future sub-problem | Likely candidate framework |
|---|---|
| **RFI response drafting** — search prior drawings, spec sections, transmittals, email threads to draft a response | **Pydantic AI** (lightweight, typed; fits our Pydantic-everywhere stack) |
| **Multi-document submittal package assembly** — decide which exhibits and prior approvals to bundle | **Anthropic Agents SDK** if we shift to Claude for long-context multi-doc reasoning; else home-grown loop |
| **Drawing/spec cross-referencing** — reconcile spec section callouts against drawing sheet references; flag inconsistencies | Home-grown tool-using loop on top of `LLMClient`; framework only if graph complexity warrants |
| **Permit-package preflight against AHJ rules** — check approved packages against jurisdiction checklists before submission | **LangGraph** *only if* the rule graph genuinely needs explicit state nodes; otherwise deterministic checker with LLM-assisted rule interpretation |

## Decision rule for future adoption

Introduce an agent framework when **all three** are true:

1. The sub-task has ≥ 3 LLM-driven decision points with branching.
2. Human-in-the-loop is genuinely interleaved with model decisions (not just terminal review).
3. We have a measured cost/quality baseline from a non-framework prototype to compare against.

Until then: the LLM is a function call, and orchestration is ours.

## Alternatives considered

- **LangGraph from the start.** Rejected for the reasons above.
- **CrewAI for the review workflow.** Rejected: the review workflow is a human workflow, not an agent workflow. CrewAI would impose model-led coordination on a process that is human-led by design.
- **AutoGen.** Rejected: same reasoning, plus less production maturity.
- **No abstraction at all (just OpenAI SDK calls everywhere).** Rejected: we still want the `LLMClient` Protocol (ADR-008) for provider neutrality.

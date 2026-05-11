# AI/ML Engineer — Scoping & Interview Rubric

The companion document to [extraction-workstream.md](./extraction-workstream.md). This defines what the role is, what to screen for, and how to evaluate candidates.

## Role one-liner

> Owns the AI extraction module end-to-end: schemas, prompts, model selection, citation grounding, and the eval harness. Ships against a measurable quality bar.

## What this role is

- Owner of `app/extraction/{schemas,prompts,llm,eval}`.
- First reviewer on any PR touching that surface.
- Author of the prompt-versioning, eval-set, and model-upgrade processes.
- Voice at the table on extraction-related product decisions.

## What this role is not

- A general full-stack hire. (We have other surface area for that.)
- The owner of the state machine, the UI, the data model, or the workflow logic.
- A research role. We are shipping a product against an LLM API; we are not training models.

## Must-have signal

1. **They've shipped an LLM-in-production system before.** Not a demo, not a prompt-engineering side project — a system where prompt changes, model upgrades, or schema changes have to survive contact with reviewers and customers.
2. **They understand structured outputs deeply.** When asked "what happens when the model returns invalid JSON," the answer is concrete (retry strategy, schema-aware repair, fall-back model, what gets logged), not hand-wavy.
3. **They have measured extraction quality before.** They have actually computed accuracy on a golden set. They have opinions on golden-set construction. They have made a model upgrade decision with data, not vibes.
4. **They write production Python.** Type hints, tests, pydantic, async. Their code does not look like a notebook.
5. **They can articulate when *not* to use an agent.** This filters for engineering judgment. Anyone enthusiastic about LangGraph for everything is wrong for this product (see [ADR-010](./adr/ADR-010-no-agent-framework.md)).

## Nice-to-have signal

- Document understanding background (table extraction, OCR pipelines, layout-aware models).
- Regulated-industry experience (any of: legal, medical, financial, construction, pharma).
- Prompt-caching, structured output schema design, function/tool calling.
- Experience with eval harness tools (Promptfoo, Braintrust, OpenAI Evals, etc.) — but not required; we will build our own thin one.

## Disqualifying signal

- Treats prompt engineering as an unversioned art. ("I just kept tweaking the prompt until it worked.")
- Cannot describe a single time they were wrong about model behavior and how they found out.
- Cannot defend any technical opinion without appealing to authority ("X company does it this way").
- Wants to "introduce LangChain / CrewAI / AutoGen" before they have read the code.

## Screening flow

### Step 1 — 30-min intro call (founder or me)

- 5 min: company pitch.
- 15 min: their last LLM-in-production system. We are listening for: ownership, measurement, surprise (what did they not expect that turned out to matter).
- 10 min: their questions about us.

Reject if: signal #1 or #2 above is missing.

### Step 2 — 60-min technical conversation (me)

- 15 min: walk through `app/extraction/__init__.py`. Ask them to critique the interface.
- 20 min: present them a fictional eval result with a regression. They have to diagnose and propose investigation steps.
- 15 min: design exercise — "we want to add `drawing_v1` extraction. Walk me through the schema, prompt, eval-set creation, and ship plan."
- 10 min: their questions.

We are evaluating: technical depth, system thinking, ability to defend opinions without dogma, ability to scope work.

### Step 3 — Paid take-home (4–6 hours, paid)

- Provided: 5 sample submittal PDFs, the `submittal_v1` schema, the `LLMClient` Protocol.
- Asked: produce a working extraction implementation against the provided schema, plus a written one-pager on accuracy and what they'd do next.
- Evaluated on: correctness, code quality, how they handled the cases the samples expose (missing fields, ambiguous data, multi-page tables), and the one-pager's quality of thought.

### Step 4 — Founder final + reverse interview

- Founder-only call, optional second technical pairing.
- Reverse interview: candidate gets time with the existing developer, no founders or architects in the room. Trust signal both ways.

## Expected ramp

| Week | Milestone |
|---|---|
| 1 | Local environment, run the slice, read the ADRs, identify three questions about the current implementation. |
| 2 | First small PR (schema or prompt change with a corresponding eval-set sample). |
| 3 | First model-comparison: run the eval harness against an alternative model, write up the result. |
| 4 | Own the first cross-functional decision (e.g., "should we add multimodal vision to the parse step?"). |

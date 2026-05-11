# ADR-008 — LLM client is a Protocol; OpenAI is the default impl

**Status:** Accepted
**Date:** 2026-05-11

## Context

We do not want to be locked to a single LLM provider. We also do not want to pay the abstraction tax of a heavy framework (LangChain, LiteLLM in production) that introduces its own versioning, breaking changes, and opinions about retries, tracing, and tooling.

## Decision

- A thin `LLMClient` Protocol in `app/extraction/llm/client.py` defines the operations we use: `extract_structured(schema, content) -> StructuredOutput`.
- Concrete `OpenAIClient` is the default implementation.
- Provider-agnostic surface is small — schema validation lives in our code, prompt rendering lives in our code, retry policy lives in our code. The Protocol is just the call.
- Swapping providers means adding a new file; existing code is untouched.

## Consequences

- **Positive:** No framework lock-in. No surprise breaking changes from an abstraction layer we don't control.
- **Positive:** Provider swap is a tiny PR.
- **Negative:** We re-implement basics (retry, timeout, structured output handling) that some frameworks provide. We consider this a feature: we own behavior we depend on.

## Alternatives considered

- **LangChain.** Rejected: pays for abstractions we don't need, costs us control we do need.
- **LiteLLM.** Considered. Acceptable as a Protocol implementation later; not adopted today.
- **Direct OpenAI SDK calls with no Protocol.** Rejected: makes provider swap a much larger change.

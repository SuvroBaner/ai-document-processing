# Architecture

One-page system overview. For deeper rationale, see [ADRs](./adr/). For data, see [data-model.md](./data-model.md).

## System diagram

```mermaid
flowchart LR
    subgraph Client
      UI[React Reviewer Workbench]
    end

    subgraph API[FastAPI Monolith]
      ING[ingestion]
      EXT[extraction]
      REV[review]
      WF[workflow]
      VOC[vocabulary]
      PLN[plans]
      OUT[output]
      PROJ[projects]
      COM[(common: events, audit, auth, storage)]
    end

    subgraph Workers
      CEL[Celery Workers]
    end

    subgraph Data
      PG[(Postgres)]
      RD[(Redis)]
      S3[(S3 / MinIO)]
    end

    subgraph External
      LLM[OpenAI API]
    end

    UI -->|REST| API
    API --> PG
    API --> S3
    API -->|enqueue| RD
    CEL -->|consume| RD
    CEL --> PG
    CEL --> S3
    CEL -->|extract_structured| LLM
    API -->|emit DomainEvent| COM
    CEL -->|emit DomainEvent| COM
```

## Module map

The monolith has nine domain modules and one cross-cutting `common` package. Boundaries are enforced by `import-linter` (see `pyproject.toml`).

| Module | Responsibility | Owns |
|---|---|---|
| `app.projects` | Tenancy: org, project, user, membership | tenant primitives |
| `app.ingestion` | Upload, validate, parse PDF, persist pages | `Document`, `DocumentPage` |
| `app.extraction` | LLM-driven structured extraction with citations | `Extraction`, `ExtractionField`, `Citation` |
| `app.review` | Human-in-the-loop edits and approvals | `ReviewSession`, `ReviewRevision` |
| `app.workflow` | Document lifecycle state machine | `WorkflowTransition` |
| `app.vocabulary` | Controlled vocabularies, versioned | `Vocabulary`, `VocabularyVersion`, `VocabularyTerm` |
| `app.plans` | AI-assisted downstream plan generation | `Plan` |
| `app.output` | Printing / labeling adapters | `PrintJob` |
| `app.common` | Events, audit, auth, storage, telemetry | none — leaf only |

Rule: domain modules do not import each other directly. They communicate through `app.common.events.EventBus` (in-proc pub/sub today, queue-backed later). The `workflow` module is the one exception — it is the spine and is invoked from API handlers in other modules.

## Document lifecycle state machine

```mermaid
stateDiagram-v2
    [*] --> UPLOADED
    UPLOADED --> PARSING: parse_started
    PARSING --> PARSED: parse_succeeded
    PARSING --> PARSE_FAILED: parse_failed
    PARSED --> EXTRACTING: extraction_started
    EXTRACTING --> EXTRACTED: extraction_succeeded
    EXTRACTING --> EXTRACTION_FAILED: extraction_failed
    EXTRACTED --> IN_REVIEW: review_opened
    IN_REVIEW --> NEEDS_REVISION: changes_requested
    NEEDS_REVISION --> IN_REVIEW: revisions_submitted
    IN_REVIEW --> APPROVED: approved
    APPROVED --> ROUTED: routed
    ROUTED --> PLAN_GENERATING: plan_generation_started
    PLAN_GENERATING --> PLAN_READY: plan_generation_succeeded
    PLAN_READY --> PRINTED: printed
    PRINTED --> ARCHIVED: archived
    PARSE_FAILED --> [*]
    EXTRACTION_FAILED --> [*]
```

Every transition:
1. Requires a role-guard (`Reviewer`, `Approver`, `System`).
2. Emits a typed `DomainEvent` on `EventBus`.
3. Writes a row to `workflow_transitions` (append-only).
4. Is covered by a unit test in `tests/test_state_machine.py`.

## Request shape — the vertical slice

```
1. POST /documents                        →  state: UPLOADED
2. Celery: parse_document.delay(doc_id)   →  state: PARSING → PARSED
3. Celery: run_extraction.delay(...)      →  state: EXTRACTING → EXTRACTED → IN_REVIEW
4. GET /review/queue                      →  reviewer sees doc
5. GET /review/{doc_id}                   →  PDF + fields + citations
6. PATCH /review/{doc_id}/fields/{path}   →  creates review_revision row
7. POST /review/{doc_id}/approve          →  state: APPROVED → ROUTED
                                          →  DomainEvent: DocumentApproved
                                          →  output module logs "would print"
```

## Cross-cutting concerns

| Concern | Where it lives |
|---|---|
| AuthN | `app/common/auth.py` (JWT, swappable for OIDC) |
| AuthZ | role guards in `app/workflow/transitions.py` + FastAPI dependency in `app/common/auth.py` |
| Audit | `app/common/audit.py` writes append-only rows; subscribes to `EventBus` |
| Observability | `app/common/telemetry.py` (structlog + OTel hooks) |
| Storage | `app/common/storage.py` (S3-compatible) |
| Background work | Celery; tasks defined in `app/extraction/tasks.py` and `app/ingestion/tasks.py` |
| Events | `app/common/events.py` — in-proc pub/sub today, swap to Redis Streams later |

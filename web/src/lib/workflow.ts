// Mirrors app/workflow/state_machine.py — keep these in sync.
// Source of truth is the Python state machine; this is a typed view for UI labels.

export const DOCUMENT_STATES = [
  "UPLOADED",
  "PARSING",
  "PARSED",
  "PARSE_FAILED",
  "EXTRACTING",
  "EXTRACTED",
  "EXTRACTION_FAILED",
  "IN_REVIEW",
  "NEEDS_REVISION",
  "APPROVED",
  "ROUTED",
  "PLAN_GENERATING",
  "PLAN_READY",
  "PRINTED",
  "ARCHIVED",
] as const;

export type DocumentState = (typeof DOCUMENT_STATES)[number];

export const STATE_LABEL: Record<DocumentState, string> = {
  UPLOADED: "Uploaded",
  PARSING: "Parsing…",
  PARSED: "Parsed",
  PARSE_FAILED: "Parse failed",
  EXTRACTING: "Extracting…",
  EXTRACTED: "Extracted",
  EXTRACTION_FAILED: "Extraction failed",
  IN_REVIEW: "In review",
  NEEDS_REVISION: "Needs revision",
  APPROVED: "Approved",
  ROUTED: "Routed",
  PLAN_GENERATING: "Generating plan…",
  PLAN_READY: "Plan ready",
  PRINTED: "Printed",
  ARCHIVED: "Archived",
};

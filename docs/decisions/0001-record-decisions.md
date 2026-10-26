---
id: 0001
date: 2026-10-08
title: Record thesis decisions as numbered files in the repository
status: accepted
supersedes:
superseded-by:
runs: []
---

## Context

The thesis is drafted continuously by AI agents as the work progresses. Agents have no
reliable memory across sessions, and prose generated from a model's recollection of a
conversation produces fluent claims that no experiment supports. A written record is
needed that agents read instead of remembering.

## Options considered

- **A:** Keep notes externally (notebook, Notion) and paste context into sessions.
- **B:** Numbered decision records committed alongside the code, read by both agents.

## Decision

Option B. Decisions live in `docs/decisions/NNNN-*.md`, written via `/log` after each
work session, and are the only narrative source agents may draft from.

## Evidence

Judgement, not measurement. The rationale is that provenance must survive the session
that produced it, and that a claim in the thesis must be checkable against something
written down at the time the decision was made.

## Consequences

- `/draft-section` can be restricted to decision records, run metrics, and the bib file.
- Anything not recorded cannot be written into the thesis; this is intentional friction.
- The declaration of AI assistance required by FAU can be generated from git history
  plus these records.

## Still unresolved

Whether decision records and `runs/` stay separate, or whether a run index should link
them automatically. Revisit once there are more than ~20 runs.

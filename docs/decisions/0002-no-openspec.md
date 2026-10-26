---
id: 0002
date: 2026-10-08
title: Do not adopt OpenSpec; decision records cover the same need
status: accepted
supersedes:
superseded-by:
runs: []
---

## Context

OpenSpec is an open-source spec-driven development framework that adds a specification
layer so developers and AI agents agree on what to build before code is generated, with a
propose / apply / archive workflow built around spec deltas. It is tool-agnostic and
suits brownfield codebases. Thoughtworks places it in "Assess" on its Technology Radar.

The question was whether to adopt it alongside the decision-record loop in this repository.

## Options considered

- **A:** Adopt OpenSpec and run thesis work through propose/apply/archive.
- **B:** Keep decision records as the only specification layer.
- **C:** Adopt it later, scoped to the pipeline code only, if the code side grows.

## Decision

Option B for now, with option C left open.

## Evidence

Judgement, not measurement. The reasoning:

- OpenSpec answers "what should be built, agreed before building". A thesis mostly
  answers "what did the data turn out to support". The second is a record of findings,
  not a contract agreed in advance; decision records fit it, specs do not.
- Much of this work is exploratory. Writing a spec for an experiment whose outcome
  determines the next step adds ceremony without reducing risk.
- The three records this project actually needs (decisions, runs, generated results) are
  already defined in `AGENTS.md` §4 and are lighter.
- Thoughtworks' own caveat applies: as agents improve, native capability may reduce the
  need for spec-driven tooling, so it is worth re-evaluating rather than committing to.

## Consequences

- One fewer system to learn during thesis setup.
- If the pipeline code becomes substantial and multi-component (for example a full
  raster branch plus the mapping back to vector elements plus HSCAD emission), OpenSpec
  is worth reassessing for that code only, not for the thesis narrative.

## Still unresolved

Whether the raster branch, once scoped, is large enough to justify spec-driven work on
its own. Revisit when that branch begins.

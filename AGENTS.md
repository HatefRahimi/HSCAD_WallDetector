# Project brief: Master's thesis

**This file is the single source of truth for both agents (Claude Code and Codex/GPT).**
Read it fully before doing anything in this repository.

---

## 1. The thesis

**Title:** Learning Semantic Structure from Industrial Vector CAD Floor Plans
**Author:** Hatef Rahimi
**Institution:** Pattern Recognition Lab, FAU Erlangen-Nürnberg
**Industry partner:** Siemens Healthineers AG, Enterprise Services, Facility Design and Planning Services
**Supervisors:** Matthias Zinnen, Prof. Dr. Andreas Maier, Christian Petry (Siemens Healthineers)

### Research question

Can a collection of industrial DWG floor plans, never annotated for machine learning,
be used to train a model that recognizes what each element of a drawing represents, and
which kind of method is best suited to the task?

Two sub-questions the thesis must answer:

1. Does the archive contain enough reliably labeled drawings, and enough variety of
   drafting styles, for a learned model to work? Does the geometry itself carry the
   distinction at all?
2. Layer names are available at training time but unreliable in practice. Does the
   structure of a floor plan carry enough signal to classify elements from **geometry and
   context alone**, without layer names?

### Scope

- **Primary target:** walls (most common element, most expensive to redraw by hand).
- **Secondary / stretch:** doors and windows (much rarer, harder).
- **Final practical check:** can detected geometry be turned into valid 3D HSCAD objects?

### Baselines

No prior result is cited. Every baseline is built and measured in this repository, under
the protocol in §2, and introduced by a decision record. Until one exists, the thesis
has no baseline number.

---

## 2. Evaluation protocol (FROZEN: change only via a decision record)

- **Primary metrics:** per-element precision, recall, F1 for the wall class.
- **Held-out split:** by **drawing**, and where possible by **customer / drafting office**.
  Never split by element within a drawing. Leakage here invalidates every downstream claim.
- **Comparability rule:** the raster/vision branch predicts pixels; the metric is
  per-element. Raster output MUST be mapped back to vector elements before any comparison
  with the GNN. That mapping is part of the method and must be documented.
- Doors/windows reported separately, never folded into the wall metric.

---

## 3. Data boundary (HARD RULE: no exceptions)

Siemens Healthineers does **not** permit external AI services on company data.

- Agents (Claude Code, Codex/GPT) may see: **code, schemas, aggregate metrics, public
  datasets, and explicitly permitted sample drawings only**.
- Agents must **never** read, open, summarize, or transmit company drawings, their JSON
  exports, customer names, or site identifiers.
- `data/` is git-ignored and agent-denied. Keep full archive data **off this machine**.
- Full-archive runs happen on the company machine, with agents not involved.
- Only aggregate results come back: metrics, per-style breakdowns with anonymized IDs,
  failure counts by reason, attached to a run ID and git tag.

**If a task appears to require company data, stop and say so instead of improvising.**

---

## 4. How work is recorded

Nothing is written into the thesis from an agent's memory of a session. Everything traces
to one of three records:

| Record | Where | Written by |
|---|---|---|
| Decisions (what was chosen and why) | `docs/decisions/NNNN-*.md` | `/log` after each session |
| Experiment runs (configs + metrics) | `runs/<run_id>/` | `scripts/log_run.py` |
| Numbers and figures in the thesis | `results/tables/*.tex`, `results/figures/*` | evaluation scripts |

**Rule:** every claim in a chapter must trace to a decision record, a run ID, or a
citation key that already exists in `thesis/references.bib`. Anything else goes in as
`\todo{...}`, never as invented prose.

Numbers are **never typed by hand or by an agent** into LaTeX. Chapters `\input{}` the
generated tables and `\includegraphics{}` the generated figures. Rerun an experiment and
the thesis updates on the next compile.

---

## 5. Two-machine workflow

Develop locally on sampled/public data → run a tagged snapshot on the company machine
against the full archive.

- All paths and settings come from `configs/*.yaml`. **Nothing hardcoded.**
- Environment pinned via lockfile. The company machine runs exactly what was tested.
- Pipeline must survive bad files: log the failure with a reason, skip, continue.
  Finish with a data report (processed / failed / why).
- Parsing stage is cached: DWG→JSON happens once, not per run.
- Always trial-run with `--limit 50` on the company machine before a full run.
- Tag each snapshot in git (`run-YYYY-MM-DD`); results come back labeled with that tag.

GPU: training on public data may go to an FAU cluster (TinyGPU / Alex) or a PRL lab
machine. Company data never leaves company hardware.

---

## 6. Agent roles

| Agent | Role | Invoked as |
|---|---|---|
| **Codex / GPT** | **Writer.** Drafts and extends chapters. | `$draft-section` in Codex, or `/codex:delegate` from Claude Code |
| **Claude Code** | **Engineer and reviewer.** Pipeline code, experiments, and critique of drafts. | `/review-chapter`, `/audit-eval`, `/log` |

The roles are deliberate, not fixed. Swap them occasionally: a chapter drafted by Claude
and reviewed by GPT surfaces different problems than the reverse. What must never happen
is the same agent drafting and approving its own text.

Both agents read the same files. Nothing is ever pasted between them.

Skills for Codex live in `.agents/skills/`; commands for Claude live in
`.claude/commands/`. They encode the same rules, so keep them in sync when one changes.

## 7. Writing rules

See `STYLE.md`, the language DNA, derived from measurements of the author's own prose.
It is binding for every word written into `thesis/`. The two rules broken most often:
**no first person** (§3) and **no em-dashes** (§6).

- Write into the existing chapter files under `thesis/chapters/`. Never invent new files
  or restructure the template.
- The **introduction, contributions framing, and discussion** are written by the author,
  not by agents. Agents may critique them.
- Every AI-assisted commit carries an `Assisted-by:` trailer (see §7) so the FAU
  declaration of AI assistance can be generated from the git history.

---

## 8. Conventions

- Commit trailer: `Assisted-by: Claude` or `Assisted-by: Codex` (or both lines).
- Decision records are numbered sequentially and never edited after being superseded;
  write a new one that supersedes the old.
- Reviews target uncommitted changes or the branch vs. `main`. Work in small units:
  one unit of work → review → commit.
- `graphify` (knowledge-graph layer over the repo) is planned for ~month 2-3, once the
  repo is large enough to be annoying to navigate. Not installed yet by design.

# Thesis workspace — Learning Semantic Structure from Industrial Vector CAD Floor Plans

Two agents (Claude Code and Codex/GPT) work on one repository. Nothing is copy-pasted
between them: GPT reads the same files Claude writes. The thesis is drafted continuously
from a written record, not from a model's memory of a session.

## First-time setup

```bash
cd thesis-starter
git init
git add -A
git commit -m "Initial thesis workspace"

# enable the citation / inline-number check
git config core.hooksPath .githooks

# environment
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Then, inside Claude Code (`claude`):

```
/plugin marketplace add openai/codex-plugin-cc
/plugin install codex@openai-codex
/codex:setup
```

Leave the automatic review gate **off**. Call reviews deliberately — it otherwise loops
between the two agents and burns through both subscriptions.

## Before you write anything

1. **`AGENTS.md`** — fill in anything marked as yours. This is the file both agents read.
2. **`STYLE.md`** — already built from your proposal's measured style. Set the
   spelling convention in §4 (currently blank), and add more voice samples to §1 as you
   write chapters you like.
3. **`thesis/main.tex`** — swap the placeholder for the official FAU/PRL template, keeping
   the `\input` structure.
4. **`thesis/references.bib`** — point Zotero (Better BibTeX) here with auto-export on.

## Daily loop

| Step | Command |
|---|---|
| Work on code or data | normal Claude Code session |
| Record what you decided | `/log` |
| Record an experiment | `log_run(...)` in your script, or `scripts/log_run.py` |
| Draft a section (GPT writes) | `/draft-section method/labeling` |
| Have Claude challenge a chapter | `/review-chapter method` |
| Audit the evaluation code | `/audit-eval` |
| Commit | `git commit` — the hook checks citations |

Work in small units: one unit → review → commit. Reviews target uncommitted changes or
your branch against `main`.

## Layout

```
AGENTS.md              project brief — single source of truth for both agents
CLAUDE.md              pointer to AGENTS.md + Claude-specific rules
STYLE.md               language DNA — measured from your own prose; binding
.claude/commands/      Claude: /log  /draft-section  /review-chapter  /audit-eval
.agents/skills/        Codex/GPT: draft-section, review-chapter, audit-eval
.claude/settings.json  denies agent access to data/
docs/decisions/        numbered decision records — the narrative record
runs/                  one directory per experiment: config, metrics, environment
results/tables/        generated .tex tables — chapters \input these
results/figures/       generated figures — chapters \includegraphics these
thesis/                LaTeX: main.tex, chapters/, references.bib
src/                   pipeline code
configs/               all paths and settings; nothing hardcoded
data/                  git-ignored, agent-denied — permitted samples only
scripts/               log_run.py, check_citations.py
.githooks/pre-commit   blocks unknown citation keys and inline numbers
```

## Roles

GPT drafts the prose; Claude engineers the pipeline and reviews the drafts. Both read the
same repository, so nothing is pasted between them. Swap the roles occasionally — what
must never happen is one agent drafting and approving its own text.

## The three rules that make this work

1. **No number is ever typed into LaTeX.** Evaluation scripts write
   `results/tables/*.tex`; chapters `\input` them. Rerun an experiment and the thesis
   updates on the next compile.
2. **Every claim traces to a decision record, a run ID, or an existing bib key.**
   Anything else is `\todo{}`. An honest gap beats fluent invention.
3. **Company data never reaches an agent.** Enforced in `.gitignore`,
   `.claude/settings.json`, and `AGENTS.md` §3.

## What stays yours

The introduction, the framing of contributions, and the discussion. Those carry your
thinking and are what examiners probe. Agents may critique them; they must not draft them.

## Later

`graphify` (knowledge-graph layer over the repo) around month 2–3, once there is enough
code and literature that navigating by hand is annoying. Check what it sends off-machine
before pointing it at anything.

OpenSpec (spec-driven development) is **not** included. The decision records already
cover the same need for this project; see `docs/decisions/0002-no-openspec.md`.

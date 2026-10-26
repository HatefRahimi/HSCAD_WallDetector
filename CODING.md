# Coding guide

Binding for every line of code written in this repository, by a person or an agent.
Read alongside `AGENTS.md`.

The goal is not elegance. It is that a number in the thesis can be reproduced eight
months from now, on a different machine, by someone who was not there, and that the
code reads like a person wrote it.

Languages: **C#** (DWG parsing, HSCAD emission) and **Python** (pipeline, models,
evaluation).

---

## 1. Non-negotiable

- **Determinism.** Every run seeds Python, NumPy and Torch from the config. A result
  that changes between identical runs is a bug, not noise.
- **No hardcoded paths.** Every path, hyperparameter and flag comes from
  `configs/*.yaml`. The only difference between a local run and a company-machine run
  is which config is passed.
- **No silent failure.** A drawing that fails to parse is logged with a reason,
  skipped, and counted. Every run ends with a data report: processed / failed / why.
- **No network calls in the pipeline.** Datasets are downloaded by a separate explicit
  script. A training run that reaches the internet is not reproducible.
- **Nothing under `data/` is read by an agent.** See `AGENTS.md` §3.

---

## 2. Working style

- **Iterative and targeted.** Change the few lines that need changing. Do not
  regenerate a whole file to alter one function. The diff is what gets reviewed, and a
  rewritten file hides what actually changed.
- **Explain the why before implementing.** For anything architectural, state the
  reasoning and the alternative rejected, and wait. Mechanical fixes need no preamble.
- **One concern per commit.** A refactor and a behaviour change in the same commit
  cannot be reviewed or reverted independently.
- **Do not add a dependency** without saying why and what it replaces.
- **Do not "improve" code that was not part of the task.** Note it and move on.

---

## 3. Layout

- **No compressed one-liners.** A statement goes on its own line, under the thing that
  controls it. Never `if (x < y) return;` or `if x < y: return`:

  ```csharp
  if (x < y)
      return;
  ```

  Braces are optional for a single-statement guard; the line break is not. A statement
  hidden on the same line as its condition is a statement nobody sees, and a breakpoint
  with nowhere to land.
- When the body grows past one statement, add braces. Never add a second statement to
  an unbraced body.
- **One-liners that are fine:** lambdas, LINQ clauses, comprehensions,
  expression-bodied properties and methods, ternaries, `with` and `using` lines, and
  guard-return pairs as above. These are one expression. The rule targets statements
  crammed onto a line to save vertical space, not expressions that read naturally
  inline.
- One statement per line. No comma-chained declarations.
- Blank lines separate logical blocks inside a function. A function with no blank lines
  is usually doing several things.
- Line length 100. Break at a meaningful boundary, not wherever the limit falls.
- Early return over nested `if`. Guard clauses at the top, the real work unindented
  below.
- Python follows `ruff format`. C# uses Allman braces where braces are present.

---

## 4. Naming

- **C#:** `_camelCase` for private fields, `PascalCase` for types, methods, properties
  and constants, `camelCase` for locals and parameters. Interfaces `IThing`.
- **Python:** `snake_case` for functions, variables and modules, `PascalCase` for
  classes, `UPPER_SNAKE` for constants, leading `_` for non-public members.
- Name the thing, not its type. `drawings`, not `drawingList`. `entity`, not
  `entityObj`.
- Booleans read as assertions: `isCached`, `hasWalls`, `shouldRetry`.
- Methods are verbs; properties and variables are nouns. A method named `Walls()` that
  computes something should be `FindWalls()`.
- No abbreviations beyond the domain's own. `dwg`, `cad`, `gnn` are fine; `calcWlSeg`
  is not.
- Domain terms match `STYLE.md` §5, so code and thesis use the same words: `drawing`,
  `entity`, `wall_segment`, `label_recovery`, `drafting_office`. Never `element` in code
  and `entity` in the thesis.

---

## 5. Return types

- **No tuples in a public signature.** Return a named record, class or dataclass.
  `(float, float, int)` tells the caller nothing; `WallMetrics` does, and adding a field
  later doesn't break every call site.
- Tuples are fine for a local unpack or a private helper used in one place.
- No out-parameters in C# except the `TryParse` pattern.
- A method returning a collection returns an empty one, never null.

---

## 6. Exceptions

- **Every exception has an owner.** Before throwing, know which layer catches it. An
  exception nobody handles is a crash with extra steps.
- Catch where you can actually do something: retry, substitute a default, skip the item
  and log it, or convert it to something the caller understands. Catching to write a log
  line and rethrow unchanged adds nothing.
- Never catch the base type (`catch (Exception)`, `except Exception:`) outside the
  top-level entry point. At the entry point, catch broadly, log with context, exit
  non-zero.
- Never swallow silently. `except: pass` and empty `catch {}` are defects.
- Throw the specific type, with a message naming the actual values involved: "drawing
  4812 has no entities on layer A-WALL", not "invalid input".
- Expected conditions are not exceptions. A drawing that fails to parse during a batch
  run is an outcome to record and move past, not control flow.

---

## 7. Functions

- One thing, at one level of abstraction. Loading, transforming and writing is three
  functions.
- More than about 40 lines, or more than three levels of nesting, means split it.
- Four parameters is a lot. Beyond that, group them into a config object or record.
- No boolean flag parameters that switch behaviour. `Export(data, true)` is unreadable
  at the call site; write two methods.
- No side effects in something named like a query. `GetWalls()` does not mutate.

---

## 8. State

- Immutable by default: `readonly` fields and records in C#, frozen dataclasses in
  Python. Mutate only where there is a reason.
- No module-level mutable state in Python. No static mutable state in C#.
- Narrowest scope that works. Declare variables where first used.
- Dependencies are injected, not constructed inside the class that uses them. Zenject
  already enforces this on the C# side; keep the same discipline in Python by passing
  collaborators into constructors.

---

## 9. Comments

- Comment the **why**. The code already says what.

  ```python
  # Pairs are matched within 1.5x the median wall thickness because drafting offices
  # vary wall width by roughly that factor across the archive.
  # See docs/decisions/0007-wall-pairing-tolerance.md
  ```

- A magic number without a comment pointing at the decision record that justifies it is
  a defect. These get defended in a viva.
- Delete commented-out code. Git remembers it.
- No section-divider comments (`# ---- helpers ----`). If a file needs them, split the
  file.
- C#: XML doc comments on public APIs only, and only when they say something the
  signature doesn't. Python: docstrings on public functions, one line unless the
  contract is genuinely subtle.

---

## 10. Things that make code look machine-written

Avoid all of these:

- Restating the code in a comment: `# increment the counter` above `count += 1`.
- A docstring on every three-line private helper.
- `try`/`except` around code that cannot fail, or that has no recovery.
- Defensive null checks on values that cannot be null in this codebase.
- Wrapper functions that only forward to another function.
- Abstractions with exactly one implementation, written for a second that never arrives.
- `# Step 1:` / `# Step 2:` narration through a function body.
- Ceremonial names: `DrawingProcessingServiceManager`, `data_processor_util`.
- Emoji or decorative banners in output or comments.
- Re-explaining the obvious in a log message.

Write the shortest thing that is clear. Then stop.

---

## 11. C# specifics

- `var` when the type is evident from the right-hand side; the explicit type when it
  isn't.
- Expression-bodied members only for genuine one-expression properties and accessors,
  never to compress a real method body.
- `using` declarations for anything disposable.
- `async`/`await` all the way down. No `.Result`, no `.Wait()`.
- Nullable reference types enabled. Don't silence the warning with `!` and no comment.
- LINQ where it reads better than a loop, not as a puzzle. One chain, one purpose.
- UniRx subscriptions are disposed. A subscription without a matching disposal is a
  leak.

---

## 12. Python specifics

- Type hints on every signature. `from __future__ import annotations` at the top.
- `pathlib.Path`, never string path concatenation.
- f-strings only. No `%`, no `.format()`.
- No mutable default arguments. No wildcard imports. No bare `except:`.
- `logging`, not `print()`, outside script entry points.
- Comprehensions one level deep. Two nested levels is a loop.
- Dataclasses for structured records; plain dicts only for JSON at the boundary.
- `ruff format` and `ruff check` are the arbiters. Don't argue with the formatter.

---

## 13. Project layout

```
src/
  parsing/        DWG/JSON ingestion, caching
  labels/         label recovery heuristics, each independently testable
  graph/          graph construction, features, GraphSAGE model
  raster/         rasterization, segmentation, mapping back to entities
  evaluate/       splits, metrics  <- FROZEN, see section 15
  emit/           AutoLISP / HSCAD output
  thesis_utils/   table and figure generation for results/
scripts/          entry points, argparse, thin wrappers over src/
tests/            pytest
```

An entry point in `scripts/` parses arguments and calls into `src/`. It holds no logic
worth testing. Logic lives in `src/` where it can be imported and tested.

---

## 14. Experiments

Every experiment producing a number in the thesis must:

1. Read its settings from a config file, not from edited constants.
2. Seed from that config.
3. Call `log_run()` from `scripts/log_run.py` with config, metrics and notes.
4. Run from a **clean working tree**. `log_run` warns when it is dirty; treat that
   warning as an error for anything headed into a chapter.

The run ID is what decision records and LaTeX comments cite. A number without a run ID
cannot enter the thesis.

**Caching.** Parsing is cached by content hash, not filename. A changed drawing must
invalidate its cache entry. The cache lives under `data/cache/` and is never committed.

**Long runs.** Anything over a few minutes writes progress to a log file and can resume.
The failure mode to design against is a crash on drawing 1,800 after three hours.

---

## 15. The evaluation module is frozen

`src/evaluate/` implements the protocol in `AGENTS.md` §2. Treat it as read-only:

- Changing a split rule, a metric definition, or the positive-class definition requires
  a decision record **before** the change.
- It needs the heaviest test coverage in the repository. At minimum: the same seed
  yields the same folds; no drawing ID appears in two folds; no `customer_id` spans
  folds when splitting by customer; metrics match a hand-computed example.
- No dataset-wide statistic may be computed before the split. Normalization parameters
  are fitted on train and applied to test.

If a change here looks necessary, stop and ask.

---

## 16. Testing

- `pytest`, tests mirroring the `src/` layout.
- Every label-recovery heuristic has a test with a small hand-built fixture whose
  correct answer is obvious by inspection.
- Every metric has a test against a hand-computed value.
- Fixtures are synthetic or drawn from permitted samples. **Never commit a real customer
  drawing as a fixture.**
- A bug fix starts with the failing test.

Tests are not for coverage targets. They exist so a refactor eight months in does not
silently change a number already written into a chapter.

---

## 17. Generating tables and figures

`src/thesis_utils/` writes into `results/tables/` and `results/figures/`. These are
build artifacts: regenerated, never hand-edited.

- Tables emit **booktabs** bodies (`\toprule`, `\midrule`, `\bottomrule`). No `\hline`,
  no vertical rules; the LME template requires this.
- A table file contains the tabular body only. The caption and `\label` live in the
  chapter, so the thesis controls presentation and the script controls numbers.
- Figures: PDF for vector plots, PNG at 300 dpi for rasters. Readable at print size,
  with axis labels.
- Every generated file carries the run ID it came from, as a LaTeX comment or in the
  filename.

---

## 18. Git

- Small commits, imperative subject: `Add parallel-line pairing to label recovery`.
- Trailer `Assisted-by: Claude` or `Assisted-by: Codex` on AI-assisted commits, so the
  FAU declaration of AI assistance can be generated from history.
- Tag each snapshot carried to the company machine: `run-YYYY-MM-DD`.
- Never commit: anything under `data/`, model checkpoints, `.env`, credentials, or
  customer names and site identifiers in code, comments, fixtures or commit messages.

#!/usr/bin/env python3
"""Record one experiment run so every number in the thesis traces back to it.

Usage, from inside your training/eval script:

    from scripts.log_run import log_run
    log_run(
        name="gnn-baseline",
        config={"model": "graphsage", "layers": 3, "k": 30},
        metrics={"wall_precision": 0.48, "wall_recall": 0.75, "wall_f1": 0.587},
        notes="Baseline reproduction on the hand-verified set.",
    )

Or from the command line, to record a run you did elsewhere (e.g. on the company
machine, pasting back only aggregate numbers):

    python scripts/log_run.py --name full-archive-eval \\
        --metrics wall_f1=0.61 wall_precision=0.52 wall_recall=0.74 \\
        --config split=by_customer limit=none \\
        --notes "Full archive, company machine, tag run-2026-11-03"

Writes runs/<YYYY-MM-DD>-<name>/{config.json,metrics.json,env.json}.
Run IDs are what decision records and LaTeX comments cite.
"""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
RUNS_DIR = REPO_ROOT / "runs"


def _git(*args: str) -> str | None:
    try:
        out = subprocess.run(
            ["git", *args],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=10,
        )
        return out.stdout.strip() if out.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None


def _git_state() -> dict[str, Any]:
    return {
        "commit": _git("rev-parse", "HEAD"),
        "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
        "tag": _git("describe", "--tags", "--exact-match") or None,
        "dirty": bool(_git("status", "--porcelain")),
    }


def _packages() -> dict[str, str]:
    """Versions of the packages whose behaviour could change a result."""
    wanted = ("torch", "torch_geometric", "numpy", "scikit-learn", "shapely")
    found: dict[str, str] = {}
    for name in wanted:
        try:
            module = __import__(name)
        except ImportError:
            continue
        version = getattr(module, "__version__", None)
        if version:
            found[name] = str(version)
    return found


def _unique_dir(base: Path) -> Path:
    if not base.exists():
        return base
    for n in range(2, 1000):
        candidate = base.with_name(f"{base.name}-{n}")
        if not candidate.exists():
            return candidate
    raise RuntimeError(f"too many runs named {base.name}")


def log_run(
    name: str,
    config: dict[str, Any] | None = None,
    metrics: dict[str, Any] | None = None,
    notes: str = "",
    run_date: date | None = None,
) -> Path:
    """Write one run record and return its directory."""
    stamp = (run_date or date.today()).isoformat()
    run_dir = _unique_dir(RUNS_DIR / f"{stamp}-{name}")
    run_dir.mkdir(parents=True)

    git_state = _git_state()
    (run_dir / "config.json").write_text(
        json.dumps(config or {}, indent=2, sort_keys=True, default=str) + "\n"
    )
    (run_dir / "metrics.json").write_text(
        json.dumps(metrics or {}, indent=2, sort_keys=True, default=str) + "\n"
    )
    (run_dir / "env.json").write_text(
        json.dumps(
            {
                "run_id": run_dir.name,
                "notes": notes,
                "git": git_state,
                "python": sys.version.split()[0],
                "platform": platform.platform(),
                "packages": _packages(),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )

    if git_state["dirty"]:
        print(
            f"warning: working tree was dirty for {run_dir.name} — "
            "this run is not reproducible from a commit",
            file=sys.stderr,
        )
    print(f"run logged: {run_dir.name}")
    return run_dir


def _parse_pairs(pairs: list[str]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for pair in pairs:
        if "=" not in pair:
            raise SystemExit(f"expected key=value, got: {pair}")
        key, _, raw = pair.partition("=")
        try:
            out[key] = json.loads(raw)
        except json.JSONDecodeError:
            out[key] = raw
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True, help="short slug, e.g. gnn-baseline")
    parser.add_argument("--config", nargs="*", default=[], metavar="K=V")
    parser.add_argument("--metrics", nargs="*", default=[], metavar="K=V")
    parser.add_argument("--notes", default="")
    args = parser.parse_args()

    log_run(
        name=args.name,
        config=_parse_pairs(args.config),
        metrics=_parse_pairs(args.metrics),
        notes=args.notes,
    )


if __name__ == "__main__":
    main()

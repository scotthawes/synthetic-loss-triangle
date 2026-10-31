#!/usr/bin/env python3
"""Check that the committed data is reproducible, and that the factors are recoverable.

Two properties matter to anyone who relies on this file:

1. The CSVs match their recorded digests, and regenerating produces the same bytes.
2. The declared age-to-age factors can be recovered from the published triangle.

The second is also where people go wrong: factors must be weighted over origins observed at
**both** ages. Pooling unmatched origin sets gives factors below 1 and is the wrong estimator,
so this script demonstrates the right one.
"""

from __future__ import annotations

import csv
import hashlib
import json
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: pathlib.Path) -> dict[tuple[int, int], float]:
    with path.open(newline="") as handle:
        return {
            (int(row["origin"]), int(row["development"])): float(row["cumulative_paid"])
            for row in csv.DictReader(handle)
        }


def main() -> int:
    params = json.loads((ROOT / "data/synthetic_triangle_params.json").read_text())
    failures = []

    for name, key in (
        ("synthetic_triangle_observed.csv", "observed_sha256"),
        ("synthetic_triangle_full.csv", "full_sha256"),
    ):
        actual = sha256(ROOT / "data" / name)
        ok = actual == params[key]
        print(f"{'PASS' if ok else 'FAIL'}  digest  {name}  {actual[:16]}...")
        if not ok:
            failures.append(name)

    before = {n: sha256(ROOT / "data" / n) for n in (
        "synthetic_triangle_observed.csv", "synthetic_triangle_full.csv")}
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/make_triangle.py")],
        check=True, capture_output=True,
    )
    after = {n: sha256(ROOT / "data" / n) for n in before}
    ok = before == after
    print(f"{'PASS' if ok else 'FAIL'}  regenerating produces identical bytes")
    if not ok:
        failures.append("regeneration")

    cells = load(ROOT / "data/synthetic_triangle_observed.csv")
    declared = params["development_factors"]
    print("\nrecovered age-to-age factors (origins observed at both ages):")
    print(f"  {'step':<8} {'recovered':>10} {'declared':>10} {'rel err':>9}")
    worst = 0.0
    for j in range(len(declared)):
        origins = [a for a in range(10) if (a, j) in cells and (a, j + 1) in cells]
        if not origins:
            continue
        recovered = sum(cells[(a, j + 1)] for a in origins) / sum(cells[(a, j)] for a in origins)
        rel = abs(recovered - declared[j]) / declared[j]
        worst = max(worst, rel)
        print(f"  {j}->{j+1:<5} {recovered:>10.3f} {declared[j]:>10.3f} {rel:>8.1%}")
    ok = worst < 0.05
    print(f"\n{'PASS' if ok else 'FAIL'}  all factors recover within 5 % (worst {worst:.1%})")
    if not ok:
        failures.append("factor recovery")

    print(f"\n{'all checks passed' if not failures else 'FAILURES: ' + ', '.join(failures)}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())

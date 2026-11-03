#!/usr/bin/env python3
"""Generate the synthetic population the pooled arm is fitted on.

Fifty triangles from the parameter set in `make_triangle.py`, **identical exposure
parameters and only the seed varying**, as decided in issue #10. Same exposure keeps
`latest_cum` and `log_latest_cum` on one scale, so pooling cannot teach the model a level
effect that would later look like a depth effect.

Deterministic: the seed list is derived from a base seed, so a re-run reproduces both CSVs
byte-for-byte. `synthetic_population_params.json` records the seeds and the digests to check
against.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import pathlib

from make_triangle import DEFAULT_SEED, build

DEFAULT_COUNT = 50


def write_csv(path: pathlib.Path, rows: list[dict]) -> str:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows_per_anchor(developments: int) -> dict[int, int]:
    """Fit rows available at anchor k: k(k+1)/2 — triangle.Triangle.known, one triangle."""
    return {k: k * (k + 1) // 2 for k in range(1, developments - 1)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=DEFAULT_COUNT)
    parser.add_argument("--base-seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--origins", type=int, default=10)
    parser.add_argument("--developments", type=int, default=10)
    parser.add_argument("--out-dir", type=pathlib.Path, default=pathlib.Path("data"))
    args = parser.parse_args()

    if args.origins != args.developments:
        raise SystemExit("a square triangle is required")

    seeds = [args.base_seed + index for index in range(args.count)]

    observed: list[dict] = []
    full: list[dict] = []
    for triangle_id, seed in enumerate(seeds):
        rows = build(seed, args.origins, args.developments)
        for row in rows:
            record = {"triangle_id": triangle_id, **row}
            full.append(record)
            if row["observed"]:
                observed.append(record)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    observed_path = args.out_dir / "synthetic_population_observed.csv"
    full_path = args.out_dir / "synthetic_population_full.csv"
    params_path = args.out_dir / "synthetic_population_params.json"

    observed_sha = write_csv(observed_path, observed)
    full_sha = write_csv(full_path, full)

    per_anchor = rows_per_anchor(args.developments)
    params = {
        "count": args.count,
        "base_seed": args.base_seed,
        "seeds": seeds,
        "origins": args.origins,
        "developments": args.developments,
        "exposure_varied": False,
        "observed_rows": len(observed),
        "unobserved_rows": len(full) - len(observed),
        "rows_per_anchor_per_triangle": {str(k): v for k, v in per_anchor.items()},
        "pooled_rows_per_anchor": {str(k): v * args.count for k, v in per_anchor.items()},
        "observed_sha256": observed_sha,
        "full_sha256": full_sha,
    }
    params_path.write_text(json.dumps(params, indent=2) + "\n")

    print(f"triangles: {args.count}   seeds: {seeds[0]}..{seeds[-1]}")
    print(f"observed rows: {len(observed)}   unobserved rows: {len(full) - len(observed)}")
    print("pooled rows per anchor:", params["pooled_rows_per_anchor"])
    print(f"{observed_path}  sha256={observed_sha[:16]}...")
    print(f"{full_path}  sha256={full_sha[:16]}...")


if __name__ == "__main__":
    main()

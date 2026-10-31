#!/usr/bin/env python3
"""Generate a deterministic synthetic loss triangle.

Committed with the data it produces: run it again and the CSVs are byte-identical, so a
result measured on this triangle can always be rebuilt.

Why this exists: the CAS corpus cannot be uploaded to a third party (see
`docs/alpha-findings.md` and issue #2), and a capability probe needs triangle-shaped data
with clean provenance. This makes its own.

Shape mirrors the real triangles: 10 origins by 10 development periods, observed in the
upper triangle only (origin + development <= 9). The bottom-right corner never happened,
which is the reserve. `*_full.csv` contains that corner and is for **scoring only** — never
feed it to training.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import pathlib
import random

# Age-to-age development factors for 9 transitions. Start large, decay toward 1.
DEVELOPMENT_FACTORS = (2.60, 1.65, 1.32, 1.16, 1.09, 1.05, 1.03, 1.02, 1.01)

EXPOSURE_BASE = 1_000_000.0
EXPOSURE_TREND = 0.03
EXPOSURE_SIGMA = 0.05
LOSS_RATIO = 0.68
ULTIMATE_SIGMA = 0.10
INCREMENTAL_SIGMA = 0.15

DEFAULT_SEED = 20261030


def cumulative_proportions(factors: tuple[float, ...]) -> list[float]:
    """Cumulative paid proportion at each development age, fully developed = 1.0."""
    proportions = [1.0] * (len(factors) + 1)
    for j in range(len(factors) - 1, -1, -1):
        proportions[j] = proportions[j + 1] / factors[j]
    return proportions


def incremental_shares(proportions: list[float]) -> list[float]:
    shares = []
    for j, proportion in enumerate(proportions):
        previous = proportions[j - 1] if j else 0.0
        shares.append(proportion - previous)
    return shares


def build(seed: int, origins: int, developments: int) -> list[dict]:
    if len(DEVELOPMENT_FACTORS) != developments - 1:
        raise SystemExit(
            f"DEVELOPMENT_FACTORS has {len(DEVELOPMENT_FACTORS)} entries; "
            f"{developments} developments need {developments - 1}"
        )

    rng = random.Random(seed)
    shares = incremental_shares(cumulative_proportions(DEVELOPMENT_FACTORS))

    rows: list[dict] = []
    for origin in range(origins):
        exposure = EXPOSURE_BASE * (1 + EXPOSURE_TREND) ** origin
        exposure *= rng.lognormvariate(0.0, EXPOSURE_SIGMA)
        ultimate = exposure * LOSS_RATIO * rng.lognormvariate(0.0, ULTIMATE_SIGMA)

        cumulative = 0.0
        for development in range(developments):
            # Incrementals are drawn non-negative, so cumulative paid can never decrease.
            incremental = ultimate * shares[development] * rng.lognormvariate(
                0.0, INCREMENTAL_SIGMA
            )
            cumulative += incremental
            rows.append(
                {
                    "origin": origin,
                    "development": development,
                    "incremental_paid": round(incremental, 2),
                    "cumulative_paid": round(cumulative, 2),
                    "observed": origin + development <= origins - 1,
                }
            )
    return rows


def write_csv(path: pathlib.Path, rows: list[dict]) -> str:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--origins", type=int, default=10)
    parser.add_argument("--developments", type=int, default=10)
    parser.add_argument("--out-dir", type=pathlib.Path, default=pathlib.Path("data"))
    args = parser.parse_args()

    if args.origins != args.developments:
        raise SystemExit("a square triangle is required: --origins must equal --developments")

    rows = build(args.seed, args.origins, args.developments)
    observed = [row for row in rows if row["observed"]]
    unobserved = [row for row in rows if not row["observed"]]

    args.out_dir.mkdir(parents=True, exist_ok=True)
    observed_path = args.out_dir / "synthetic_triangle_observed.csv"
    full_path = args.out_dir / "synthetic_triangle_full.csv"
    params_path = args.out_dir / "synthetic_triangle_params.json"

    observed_sha = write_csv(observed_path, observed)
    full_sha = write_csv(full_path, rows)

    params = {
        "seed": args.seed,
        "origins": args.origins,
        "developments": args.developments,
        "development_factors": list(DEVELOPMENT_FACTORS),
        "cumulative_proportions": [round(p, 6) for p in cumulative_proportions(DEVELOPMENT_FACTORS)],
        "exposure_base": EXPOSURE_BASE,
        "exposure_trend": EXPOSURE_TREND,
        "exposure_sigma": EXPOSURE_SIGMA,
        "loss_ratio": LOSS_RATIO,
        "ultimate_sigma": ULTIMATE_SIGMA,
        "incremental_sigma": INCREMENTAL_SIGMA,
        "observed_rows": len(observed),
        "unobserved_rows": len(unobserved),
        "observed_sha256": observed_sha,
        "full_sha256": full_sha,
    }
    params_path.write_text(json.dumps(params, indent=2) + "\n")

    ultimate_total = sum(row["cumulative_paid"] for row in rows if row["development"] == args.developments - 1)
    paid_total = sum(row["incremental_paid"] for row in observed)
    print(f"seed: {args.seed}  shape: {args.origins}x{args.developments}")
    print(f"observed rows: {len(observed)}   unobserved rows: {len(unobserved)}")
    print(f"paid to date (observed): {paid_total:,.0f}   ultimate (all origins): {ultimate_total:,.0f}")
    print(f"{observed_path}  sha256={observed_sha[:16]}...")
    print(f"{full_path}      sha256={full_sha[:16]}...")
    print(f"{params_path}")


if __name__ == "__main__":
    main()

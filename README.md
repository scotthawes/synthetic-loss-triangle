# A synthetic loss triangle

> **This is a shape demo, not a benchmark.** It demonstrates the *structure* of a loss triangle so a tool can be
> exercised on one. It says nothing about how any method performs on real claim data. See
> [What this is not](#what-this-is-not) before using it for anything.

A deterministic, reproducible 10 × 10 loss triangle — accident years down, development periods across, cumulative
paid losses in the cells. The upper triangle is observed; the lower-right corner is unknown, which is the reserve.

Built because every public triangle corpus carries licence terms that usually prohibit uploading the data to a
hosted service, and because "here is a table with the right shape" is genuinely useful when you are testing
plumbing rather than actuarial accuracy.

## Quick start

```sh
python3 scripts/make_triangle.py             # regenerates data/ byte-identically
python3 scripts/make_triangle_population.py  # the 50-triangle population, byte-identically
python3 scripts/verify.py                    # checks the digests and recovers the factors
```

For the framing that turns this into a reserving demo — predict the link ratio over Chain Ladder's factor, pool by
anchor, and the depth caveat — see [docs/using-this-as-a-demo.md](docs/using-this-as-a-demo.md).

No dependencies. Python 3.10 or newer, standard library only.

## What the data is

| File | Contents |
| --- | --- |
| `data/synthetic_triangle_observed.csv` | 55 rows — the upper triangle only, `origin + development <= 9` |
| `data/synthetic_triangle_full.csv` | 100 rows — includes the unknown corner. **Scoring only, never training** |
| `data/synthetic_triangle_params.json` | seed, factors, exposure curve, and the SHA-256 of both CSVs |

Generation: exposure grows 3 % per origin with lognormal noise; ultimate loss ratio 0.68; age-to-age development
factors decaying from 2.60 to 1.01 over nine transitions; non-negative lognormal incrementals, so cumulative paid
can never decrease. Round-tripped through 2 decimal places.

Seed is `20261030`. Run the generator again and both CSVs are byte-identical.

## What this is not

**It is not a benchmark.** Do not use it to compare reserving methods, to claim a model "works" on triangles, or to
estimate real-world performance. Three reasons, all deliberate consequences of how it is built:

- **No real structure.** Real triangles contain negative incrementals, case-outstanding recoveries, diagonal shocks
  and calendar-year effects. This one has none of them, and those are exactly where methods differ.
- **Too separable.** The development factors are recoverable from the data to within about 1 % — good for a
  demonstration, useless for discriminating between methods.
- **The answer differs from real data.** Measured on this generator's 50-triangle population
  (`scripts/make_triangle_population.py`), a depth-dependent error slope came out at **+0.0493**; the same method on
  real casualty triangles gives **+0.0317**. A 1.5× difference from corpus alone. Treat any absolute number measured
  here as a property of *this file*.

What it *is* for: exercising a CSV-to-model pipeline, demonstrating a workflow, checking that depth and anchors
mean what you think they mean, and teaching the shape.

## Provenance

Generated entirely by `scripts/make_triangle.py` from the parameters in this repository.

The development factors were chosen a priori as plausible industry-typical values. They are **not** fitted to,
sampled from, or otherwise derived from the CAS Loss Reserve Database or any other real portfolio. No real claim
data was consulted at any point.

The generator does not use any external data, and the only dependency is the Python standard library.

## What the triangle is for, in actuarial terms

Rows are **origins** (accident years), columns are **development periods**, cells are **cumulative paid losses**.
The observed region is `origin + development <= 9`. The empty corner is what a reserving method must estimate.

Two definitions that are easy to get wrong, and that this data is convenient for checking:

- **Depth** — how far past its last observed cell an origin has been projected: `depth = (d - 1) - (k - a)` for
  anchor `k`, origin `a` and development `d`. Training rows sit at depth ≤ −1; the first predicted cell is depth 0.
  On a ten-origin triangle the maximum reachable depth is `8 - k`, so only `k = 3` reaches depth 5.
- **Anchor** — the diagonal of the triangle a model is allowed to see, `k = a + d` for the last observed diagonal.

If you are fitting age-to-age factors from this data, weight over **origins observed at both ages**. Pooling
unmatched origin sets produces factors below 1 and is simply the wrong estimator.

## Licence

Copyright 2026 Scott Hawes. Apache-2.0 — see [LICENSE](LICENSE).

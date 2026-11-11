# Synthetic loss triangle glossary

The vocabulary this repository uses for the triangle it generates, the way that triangle is scored, and the
50-triangle population built from it. The terms overlap with general reserving language but are pinned here
to the quantities the scripts actually compute — `origin` and `development` are column indices, `anchor` and
`depth` are derived from them, and a link ratio is not the same object as a development factor.

## Language

### The table

**Loss triangle**:
A table of cumulative paid losses with origins down and development periods across, observed only where
`origin + development <= 9`; the empty lower-right corner is the reserve.

**Origin**:
The row of the triangle — the year a group of claims arose, indexed 0 to 9.

**Development period**:
The column of the triangle — how many periods a group of claims has developed, indexed 0 to 9.

**Cumulative paid**:
The cell value: total paid to date for one origin at one development period.

**Reserve**:
The unknown lower-right corner that a reserving method has to estimate.

### Reading the triangle

**Anchor (k)**:
The diagonal a model is allowed to see, `k = a + d` for the last observed diagonal; the valuation date a
prediction is made from.

**Depth**:
How far past its last observed cell an origin has been projected, `depth = (d - 1) - (k - a)`; training rows
sit at depth ≤ −1 and the first predicted cell is depth 0.

**Link ratio**:
One development period's cumulative paid over the period before, for the same origin.

**Development factor**:
An age-to-age multiplier: declared in the params file as the generator's truth (2.60 down to 1.01), and
recoverable from the triangle as the volume-weighted average of link ratios over origins observed at both
ages.

**Unobserved corner**:
The cells where `origin + development > 9`; they exist only in the `_full` CSV, for scoring and never for
fitting.

### The artefact

**Shape demo**:
The repository's own description of what the triangle is — data with the structure of a loss triangle, for
exercising a pipeline.
_Avoid_: benchmark — the README says explicitly that it is not one.

**Population**:
The 50 triangles generated from the same exposure parameters with only the seed varying, built so a fit at
one anchor has hundreds of rows instead of 36.
_Avoid_: corpus — the corpus is the public real-triangle collections this data deliberately does not copy.

**Pooling by anchor**:
Building one table per anchor across the population, so rows from many triangles at the same valuation date
are fitted together rather than one triangle at a time.

**Unseen bucket**:
What a categorical runtime routes an unknown depth category to, which means deep cells are predicted from the
model's response to "unknown" rather than from a learned depth effect.

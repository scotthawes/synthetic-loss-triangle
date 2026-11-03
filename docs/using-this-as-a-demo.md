# Using this as a reserving demo

The triangle exists to exercise a pipeline. If you want to demo it end to end — fit something, then score the
unknown corner — this is the framing that worked.

## Predict a ratio, not a loss

The object classical reserving is built from is the **link ratio**: one development period's cumulative paid
losses over the period before. Chain Ladder is just a volume-weighted average of those ratios.

So do not ask a model to predict losses. Ask it to predict the ratio **divided by Chain Ladder's own
volume-weighted factor for that step**. Then:

- **1.0 reproduces Chain Ladder exactly** — the model starts from a number an actuary already trusts;
- the model learns a **correction** to that number, not the level itself;
- every prediction is readable against a known baseline, so a bad fit is obvious immediately.

This is a much better entry point than predicting cumulative losses directly, where a model can be badly wrong in a
way that still looks plausible.

## Pool by anchor

An **anchor** `k` is the diagonal of the triangle the model is allowed to see (`k = a + d` for the last observed
diagonal). A single triangle at anchor 8 gives you 36 training rows — too few to say anything.

Pooling across the 50 triangles in the population at a given anchor gives:

| Anchor | Pooled rows |
| --- | --- |
| 3 | 300 |
| 5 | 750 |
| 8 | 1,800 |

Build one table per anchor: rows are cells, the target is the link ratio over Chain Ladder's factor, and the
features are the things an actuary would actually have — origin index, development index, calendar index, latest
cumulative, log latest cumulative, the origin's own last ratio, and the previous step's global factor.

## The caveat worth stating up front

**Depth is not a number the model can see unless you give it one.** Depth is how far past its last observed cell an
origin is being projected: `depth = (d - 1) - (k - a)`.

If you encode depth as a categorical column, every row at an anchor deeper than the training rows carries a category
the model never saw. Most runtimes route unknown categories to a dedicated **unseen bucket**, which means depth
extrapolation is happening through the model's response to *unknown*, not through any learned depth effect. That is
worth knowing before you read anything into a depth-based metric.

Two ways out, neither free: give the model depth as a continuous feature and accept it will extrapolate linearly at
best, or keep depth categorical and accept that the deepest cells are all being predicted from one bucket.

## What to expect

On this population the development factors are recoverable to about 1%, which is what makes it a good shape demo and
a poor discriminator. Methods that should differ barely do. Treat any absolute number measured here as a property of
*this file*, not of reserving.

For the same reason, do not use it to compare methods. The [README](../README.md#what-this-is-not) says what it is
not, and that applies here too.

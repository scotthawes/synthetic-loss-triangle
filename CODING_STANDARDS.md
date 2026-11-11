# Coding Standards

Judgement calls only. There is no linter, formatter or test framework configured, so nothing here restates
mechanical style — these are the calls that decide whether a committed number stays trustworthy: paths resolve
from the script, the params file is written by the generator, factors are weighted over matched origins, and
every document says what the data is not.

## Verification

- `python3 scripts/verify.py` — checks both artefacts' SHA-256 digests, re-runs both generators and confirms
  byte-identical output, and confirms the declared age-to-age factors are recoverable within 5%

That is the only check command in the repository: there is no CI workflow, no test suite and no lint config.
The generators themselves are `python3 scripts/make_triangle.py` and
`python3 scripts/make_triangle_population.py`.

## Determinism and provenance

### Generated data ships with the script that made it

The CSVs and the params file exist only because a committed script writes them from constants in this repo.
A new data file without its generator and its params entry is not admissible, because neither the reviewer nor
a downstream user can reproduce it.

### Regeneration checks resolve paths from the script, never from the caller's cwd

`verify.py` runs the generators with `cwd=ROOT` and says why: both default `--out-dir` to the relative path
`data`, so a check invoked from elsewhere writes somewhere else and "the comparison passes without ever
touching the committed files". Paths are derived from `pathlib.Path(__file__).resolve().parent`, which is also
what makes the check safe to run from any directory.

### The params file is written by the generator

`synthetic_triangle_params.json` and `synthetic_population_params.json` are regenerated as part of the same
run that writes the CSVs, "so it cannot drift from the seeds and row counts it claims". Hand-editing a digest,
a row count or a seed breaks the chain that the verifier depends on.

## Estimators

### Weight factors over origins observed at both ages

An age-to-age factor is `sum(C[a, j+1]) / sum(C[a, j])` over the origins present at both ages — never a mean
of per-origin ratios, and never pooled over unmatched origin sets. Both the README and `verify.py` state the
reason: unmatched sets produce factors below 1 and are simply the wrong estimator.

## Claims

### Say what the data is not, beside what it is

The README's "What this is not" and `docs/using-this-as-a-demo.md` both carry the caveat, and any document
quoting a measurement from this generator repeats it: a number measured here is a property of this file, not
of reserving. The concrete case is the depth slope (+0.0493 here against +0.0317 on real casualty triangles),
which is a corpus artefact rather than a method result.

### Name the depth encoding

Depth is not a number a model can see unless it is given one. If depth is encoded as a categorical column, the
deepest rows carry a category the model never met and are predicted through the unseen bucket; if it is
continuous, the model extrapolates at best linearly. Either choice is defensible, but a depth-based metric is
unreadable without it, so the document says which one was used.

## Working on the repo

### `_full` is never training input

`synthetic_triangle_full.csv` and `synthetic_population_full.csv` contain the unknown corner. The README marks
them "Scoring only, never training", and a pipeline trained on that file scores itself on data it was shown.

### Keep the generators standard-library only

The README promises "No dependencies. Python 3.10 or newer, standard library only", which is what lets the
triangle be regenerated anywhere without an environment. pandas or numpy would make the generator easier and
the artefact harder to trust.

### Issues live in `scotthawes/synthetic-loss-triangle`

`AGENTS.md` points at `docs/agents/issue-tracker.md` for the `gh` operations and `docs/agents/triage-labels.md`
for the label strings. The repo has one remote, so a bare `#N` resolves without a `-R` flag.

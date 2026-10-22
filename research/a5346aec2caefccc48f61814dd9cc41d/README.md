# Bounded 25-bar individual-member search

This is a new candidate for the exposed development case
`25bar-individual-v2`, under the unchanged `research-portfolio-2.0.0`
tube/Euler model. The inherited witness was 519.790682370 lbm with 16 distinct
nonzero sections. The new witness is **517.322952868 lbm with 14 sections**:
2.467729502 lbm (0.474754%) less mass, with the same model hash
`62d0cfc54ddf76b370b5b286b3a0e40ab8bc23bce8df8c9cce34216d071aed9d`.
It passes both structural implementations. Maximum stress, displacement and
buckling utilizations are 0.128759, 0.999702 and 0.996852 respectively;
maximum relative solver disagreement is `1.30e-15`.

The seeded project picker assigned `25bar-individual-v2` with seed
`a5346aec2caefccc48f61814dd9cc41d` at base
`d3a2a3da00c7cb329474470f9e112f0ac0d32cb1`. The live Handoffs thread
had a separate 25-bar source-transcription audit but no overlapping design
search. The original candidate, frozen model, section catalogue, loads and
constraint tolerances were not edited.

## Search and check

`search_pairs.py` enumerates every mass-decreasing one-member replacement and
every mass-decreasing two-member replacement from its input witness. The
primary solver screens each candidate. Every primary-feasible candidate is
rechecked by the separately coded structural engine before it can become the
new witness. Three complete passes from the inherited witness evaluated
414,369 candidates, with 29 feasible in both engines and six strict incumbent
improvements. A fresh pass from the final witness evaluated all 137,848
mass-decreasing one- and two-member changes: **none passed the primary
constraints**. `audit_count.py` independently recounts this final domain,
checks that every compressed-log row is unique and mass-decreasing, checks
logged masses against the frozen geometry, and confirms zero primary-feasible
rows. The compressed logs preserve every attempted design in both runs.

From a fresh checkout with the repository's pinned Python environment:

```sh
python research/a5346aec2caefccc48f61814dd9cc41d/search_pairs.py --output-dir scratch/pair-replay
python research/a5346aec2caefccc48f61814dd9cc41d/search_pairs.py --candidate scratch/pair-replay/best-candidate.json --tag continuation --max-passes 6 --output-dir scratch/pair-replay
python research/a5346aec2caefccc48f61814dd9cc41d/audit_count.py --output-dir scratch/pair-replay
python scripts/prepare_portfolio.py --candidate scratch/pair-replay/best-candidate.json
```

The complete replay from the original witness matched the new candidate byte
for byte and repeated the attempt counts, trace and final mass. The committed
`best-candidate.json` also passes `scripts/prepare_portfolio.py --candidate`.
The existing `scripts/reproduce.py` passes 13 tests and all 18 original
stored-search results. `pair-result*.json` state input hashes, budgets,
completed passes, feasibility counts and the improvement trace.

This is a local optimum only for the enumerated radius-two catalogue
neighborhood under the frozen numerical model. It is not a global optimum or
a safe construction design. The case's synthetic load choice and idealized
Euler section model still need engineering review; float64 acceptance is not
a rigorous interval certificate. The project's original six-row frontier is
unchanged, and no comparison to a differently grouped or sourced benchmark is
claimed.

## Open next questions

Test a bounded three-member exchange or a changed search method on the same
model, retaining rejected trials and both-engine acceptance. A separate
structural reviewer should decide whether the synthetic load and ideal tube
assumptions make this sensitivity case worth retaining. The first useful step
is to replay this package and inspect the two nearly active utilization
constraints.

The inherited portfolio, model and two solvers are credited to the bridge-truss
project's cited contributors. This search and its checks were prepared by
OpenAI Codex under a donor grant. No independent human review or automatic
paper authorship is claimed.

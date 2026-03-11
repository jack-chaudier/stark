# Selective Memory, Causal Memory, and the Boundary of Runtime Hypergraph State

## Prerequisites

This document assumes familiarity with:
- Basic causal inference (DAGs, adjustment sets, confounders)
- Algebraic notions of quotients and congruences
- The distinction between "getting the right answer" and "knowing which variables justify it"

For a shorter introduction, start with the [short overview](selective-memory-master-synthesis-short.md).

## Abstract

This document consolidates the current selective-memory / causal-memory program into one narrative.
The program began with tropical threshold memory — a max-plus algebraic framework where the exact question was how much compositional state is needed to preserve bare predecessor feasibility.
It then moved through a negative causal correction, a positive witness-refined repair, a unique-minimal causal factorization theorem, a phase-transition program for answer-versus-justification failure, a finite-probe quotient tower, exact separator closure, exact Pareto frontiers, overlapping-family contract memory, a binary-completion runtime boundary, and finally the semantic boundary atlas.

The strongest clean statement now supported is this:

> On the fixed witness carrier, hypergraph complexity is already exact at the contract layer, can become visible at the teaching/probe layer, and readout-only semantic enrichment can break the old runtime quotient and even require overlap for the first break. But no scanned readout-only enrichment forces genuinely non-coordinate runtime state. Therefore the next true runtime-hypergraph theorem must change the carrier or the composition law, not just the readout.

That is the boundary result of the current phase.

## Executive Thesis

The original hope was that a bare tropical summary might recover causal justification directly.
The work in this repository shows that this was the wrong target.
Bare tropical memory is canonical for a bare threshold contract, not for causal identity.
The correct repair is a witness-preserving quotient, and on the unique-minimal causal class that repair is exact.
Once that layer is in place, the experiments reveal a sharper phenomenon: under finite memory, answerability can survive before justification does.
The finite-probe tower, separator closure, exact Pareto frontiers, and family-memory search then show that there is not one memory problem here but several: contract memory, probe memory, and runtime memory.
The semantic atlas closes the current phase by locating the present boundary precisely: hypergraph structure matters already for contracts and probes, but runtime hypergraph state has not yet appeared on the fixed witness carrier.

## What We Unlocked

1. Bare threshold memory and witness-preserving memory are now cleanly separated by contract.
2. The right causal repair is a protected-witness quotient with exact state count `|Q_(k,p)| = sum_(d=0)^k (d + 2)^p`.
3. The unique-minimal causal class factors through that witness quotient, and the ordered-DAG referee supports the theorem exhaustively on the scanned world.
4. Finite-memory failure is phased: exact answerability can survive before exact justification does.
5. The current experiments now measure a quotient tower, not a single quotient.
6. Overlapping minimal adjustment families force a hypergraph-valued contract object, but not yet a hypergraph-valued runtime automaton.
7. Under binary completion, arbitrary antichains still collapse to a universal runtime quotient.
8. Under readout-only semantic enrichment, runtime collapse can fail in coordinate-level, family-specific, and overlap-required ways, but full coordinate state remains exact.

## Roadmap Of The Program

The program now has ten layers.

1. Bare threshold quotient and bounded separators.
2. Protected-witness quotient and provenance tax.
3. Witness-faithful factorization on the unique-minimal causal class.
4. Mirage shelf and breach-versus-forced phase laws.
5. Finite-probe quotient tower.
6. Separator closure and closure-rank observations.
7. Exact Pareto frontiers and the intrinsic shelf.
8. Family-memory contract/runtime split.
9. Runtime-collapse boundary under binary completion.
10. Semantic boundary atlas.

Each layer did two things:

- it solved or sharpened the current target,
- and it exposed the next place where the original target was still too coarse.

## Definitions And Notation

This section defines the mathematical objects used throughout. If you're reading for the first time, the key intuition is: each "quotient" is a compressed view of memory that keeps only what matters for a specific task. Coarser quotients use less memory but lose more information.

### Raw compositional world

The background selective-memory work starts from a raw associative memory object `L2 = (W[0..k], d_total)` with tropical (max-plus) composition. Here `W[0..k]` is a frontier vector tracking predecessor capacity at each depth level, and `d_total` counts total predecessors seen.
The earlier quotient ladder is:

`raw L2 -> L2' -> M_k -> R_k`.

Here:

- `L2'` caps total depth at `k`,
- `M_k = (d_hat, m)` is the exact two-sided bare threshold quotient,
- `R_k` is the one-sided residual-demand quotient.

The exact bare state count is:

`|M_k| = ((k + 1)(k + 4)) / 2`.

This matches the computed family table:

- `|M_1| = 5`,
- `|M_2| = 9`,
- `|M_3| = 14`,
- `|M_4| = 20`,
- `|M_5| = 27`.

### Protected-witness quotient

For a threshold `k` and `p` named protected witnesses, the exact witness quotient has class count:

`|Q_(k,p)| = sum_(d=0)^k (d + 2)^p`.

When witness labels are semantically interchangeable, the symmetric quotient count is:

`|Q_(k,p)^sym| = binom(k + p + 2, p + 1) - 1`.

### Contract, support, and probe quotients

The current program now uses four distinct quotient notions.

- Canonical contract quotient: `Q_C`.
- Empirical support quotient: `Q_C|_(support(mu))`.
- Finite-probe joint quotient: `Q_(C,P)^joint`.
- Finite-probe answer quotient: `Q_(C,P)^answer`.

The measured probe statistics are:

- probe deficiency:

  `delta(C, P) = log_2 |Q_C| - log_2 |Q_(C,P)^joint|`

- shelf width:

  `omega(C, P) = log_2 |Q_(C,P)^joint| - log_2 |Q_(C,P)^answer|`.

### Family memory

For overlapping minimal adjustment families, let `A` denote the antichain of admissible minimal families.
The current distinction is:

- contract layer: compare different `A`,
- runtime layer: fix one `A` and ask what dynamic state is needed under composition.

That split became decisive.

## How We Got Here

### The original hope

The early ambition was stronger than the current theory supports.
The dream was that a bare tropical summary might preserve enough structure to recover causal justification directly.
In that version of the program, there would have been a direct bridge:

- tropical predecessor memory on one side,
- minimal adjustment-set identity on the other.

### What failed

The causal refinement note closed that door.
Bare `L2` is invariant under predecessor relabeling inside non-focal intervals.
So it preserves predecessor capacity, not named predecessor identity.
The result is structural:

- bare threshold feasibility can survive,
- but exact adjustment identity can be lost.

This is the causal version of the earlier validity-mirage lesson.

### What replaced it

The repair was not to abandon the compositional program.
It was to lift the contract.

Once the contract is changed from:

- bare feasibility

to:

- witness-preserving feasibility,

the right exact object becomes `Q_(k,p)`.
That repaired object then becomes the bridge into causality on the unique-minimal class.

### What forced the next layer

After the positive factorization theorem, the most important question changed again.
The issue was no longer only whether the right quotient exists.
It became:

- how finite memory fails around that quotient,
- how observation coarsens the quotient,
- and where overlapping causal families enter.

That is what produced the current stack of experiments and boundary results.

## Core Results In Order

## 1. Bare Threshold Quotients And Contract-Relative Canonicality

**Status:** THEOREM (imported background into this repository; used as established input here)

**Supporting artifacts:** [causal-contract-refinement.md](../foundations/causal-contract-refinement.md), [contract-representation-theorem.md](../foundations/contract-representation-theorem.md)

The bare threshold memory problem is already solved at the quotient level.
For the threshold contract, the canonical two-sided object is `M_k` and the one-sided object is `R_k`.
This gives the first conceptual lesson that survives every later refinement:

> canonicality is always relative to a contract.

The contract-representation note abstracts this into a meta-theorem template:

- finite-index two-sided congruence,
- bounded separators,
- canonical quotient `Q_C`,
- universal factorization for every contract-sound associative summary.

This is not yet a full causal theorem.
It is the structural template that organizes the layers already proved.

## 2. Protected-Witness Quotient And The Provenance Tax

**Status:** THEOREM (imported background into this repository; used as established input here)

**Supporting artifacts:** [causal-contract-refinement.md](../foundations/causal-contract-refinement.md), [witness-faithful-factorization.md](../foundations/witness-faithful-factorization.md), [contract-representation-theorem.md](../foundations/contract-representation-theorem.md)

The causal correction note proves the negative step:

- bare `L2` cannot universally recover minimal adjustment-set identity.

It also identifies the positive repair:

- move from a bare threshold contract to a witness-preserving contract.

The exact protected-witness state count is:

`|Q_(k,p)| = sum_(d=0)^k (d + 2)^p`.

This is the first exact provenance budget in the program.
It also yields the provenance tax:

- bare threshold memory is cheaper,
- witness identity raises the degree of the state count,
- symmetry can lower the coefficient but not remove the need for witness structure.

This is the key replacement object behind every later causal result.

## 3. Witness-Faithful Factorization On The Unique-Minimal Causal Class

**Status:** THEOREM

**Supporting artifacts:** [witness-faithful-factorization.md](../foundations/witness-faithful-factorization.md), [unique_minimal_referee.md](../../../results/referee/unique-minimal-referee/unique_minimal_referee.md)

The first positive causal theorem that survives contact with exact checks is deliberately narrow.

For causal queries with:

- a directed treatment-outcome path,
- a unique non-empty minimal adjustment set,
- and a witness-faithful prefix linearization,

the causal contract factors through the protected-witness quotient `Q_(k,p)` with `k = p = |A*|`.

The exhaustive ordered-DAG referee supports that theorem on the scanned world:

- treatment-outcome queries with directed path: `325404`,
- unique non-empty minimal queries: `89291`,
- admitted prefix-witness queries: `89291`,
- exact `Q_(k,p)` recovery rate: `1.000`,
- exact orbit recovery rate: `1.000`,
- residual `Q_(k,p)` failures: `0`,
- bare collision groups with distinct witness signatures: `6`.

This is a clean split result:

- bare `L2` stays too coarse,
- witness memory is sufficient on the unique-minimal witness-faithful class.

## 4. Phase Laws: Breach, Mirage, And The First Dynamic Failure Theory

**Status:** EXACT COMPUTATIONAL RESULT for the listed families; OBSERVED LAW for the general shelf story on the scanned grid

**Supporting artifacts:** [phase_transition_sweep.md](../../../results/quotient-thresholds/phase-transition-sweep/phase_transition_sweep.md), [phase_transition_breach.svg](../../../results/quotient-thresholds/phase-transition-sweep/phase_transition_breach.svg), [phase_transition_forced.svg](../../../results/quotient-thresholds/phase-transition-sweep/phase_transition_forced.svg)

The phase sweep adds a dynamic law that the quotient theorems alone cannot provide.

On the exact compositional families, exact turn-on occurs at the quotient bit ceiling.
For example:

- `M_3`: `14` states, exact at `4` bits,
- `Q_(3,2)`: `54` states, exact at `6` bits,
- `Q_(5,3)`: `783` states, exact at `10` bits.

Under breach decoding:

- subthreshold budgets abstain,
- exactness returns sharply at the threshold.

Under forced decoding:

- answer fidelity can remain high before witness fidelity does,
- the underbudget regime becomes a mirage regime instead of a breach regime.

The causal slice makes the point sharply:

- `causal_referee` has `15` empirical support states, `3.907` bits,
- but its answer channel already collapses to `4` probe-answer states,
- and at `3` bits the forced shelf preserves perfect answer while witness fidelity is still below exact.

The bit geometry sweeps and clustering controls then add a second lesson:

- the existence of the shelf is robust,
- the height and shape of the shelf depend on the observational regime.

## 5. The Finite-Probe Quotient Tower

**Status:** EXACT COMPUTATIONAL RESULT for the measured tower counts; PROPOSITION/TEMPLATE for the finite-probe quotient language

**Supporting artifacts:** [finite-probe-quotient-tower.md](../experiments/quotient-thresholds/finite-probe-quotient-tower.md), [phase_transition_sweep.md](../../../results/quotient-thresholds/phase-transition-sweep/phase_transition_sweep.md), [memory_stratigraphy.svg](../../../results/quotient-thresholds/separator-closure-experiment/memory_stratigraphy.svg)

The clustering controls showed that the experiments were no longer measuring only one quotient.
They were measuring a tower.

The strongest examples are:

- `Q_(5,3)`: algebraic `783` -> probe-joint `13` -> probe-answer `7`,
- `causal_referee`: algebraic upper bound `2532` -> empirical support `15` -> probe-joint `15` -> probe-answer `4`.

This yields:

- `delta(Q_(5,3), P) = 5.912` bits,
- `omega(Q_(5,3), P) = 0.893` bits,
- `delta(causal_referee, P) = 7.399` bits,
- `omega(causal_referee, P) = 1.907` bits.

The main synthesis lesson is:

> a shelf appears whenever the quotient for being right is smaller than the quotient for knowing why.

This is not yet a full theorem for arbitrary probe banks.
It is an exact measured tower on the current probe regimes, together with the right formal language for the next theorem.

**Selected figure:** [Memory stratigraphy](../../../results/quotient-thresholds/separator-closure-experiment/memory_stratigraphy.svg)
Why it matters: it is the clearest one-picture view of how algebraic, empirical, and observational complexity separate.

## 6. Separator Closure And Exact Pareto Frontiers

**Status:** EXACT COMPUTATIONAL RESULT on the listed synthetic families; OBSERVED LAW for closure-rank scaling

**Supporting artifacts:** [separator_closure_experiment.md](../../../results/quotient-thresholds/separator-closure-experiment/separator_closure_experiment.md), [exact_pareto_frontier.md](../../../results/quotient-thresholds/exact-pareto-frontier/exact_pareto_frontier.md), [separator_closure_deficiency.svg](../../../results/quotient-thresholds/separator-closure-experiment/separator_closure_deficiency.svg), [exact_pareto_frontier.svg](../../../results/quotient-thresholds/exact-pareto-frontier/exact_pareto_frontier.svg)

Separator closure asks how far the current finite probe bank is from the full two-sided quotient.
On the tested synthetic families, closure is exact:

- `Q_(3,2)` closes from probe-joint `7` to canonical `54` after `3` left actions,
- `Q_(4,2)` closes from `8` to `90` after `4`,
- `Q_(5,3)` closes from `13` to `783` after `5`.

The exact minimal basis is the depth ladder:

- `[(1, BOT^p), ..., (k, BOT^p)]`

on each listed family.

This gives two distinct outputs.

First, probe deficiency falls to zero.

Second, shelf width widens rather than shrinks:

- `Q_(5,3)`: `omega` grows from `0.893` to `4.858` bits along exact closure.

The exact Pareto frontier then shows that the shelf is intrinsic on the measured atomic state spaces.
The strongest two examples are:

- `Q_(5,3)` on the probe-joint space: at `3` bits, perfect answer is already achievable, but witness-at-perfect-answer is only `0.982`.
- `causal_referee` on empirical support: at `2` bits, perfect answer is already achievable, but witness-at-perfect-answer is only `0.641`.

So underbudget tradeoff is not merely an artifact of the tested compressors.
It is built into the measured quotient tower itself.

**Selected figure:** [Separator closure deficiency](../../../results/quotient-thresholds/separator-closure-experiment/separator_closure_deficiency.svg)
Why it matters: it is the cleanest direct picture of probe deficiency going to zero while the potential mirage interval widens.

**Selected figure:** [Exact Pareto frontier](../../../results/quotient-thresholds/exact-pareto-frontier/exact_pareto_frontier.svg)
Why it matters: it turns “the shelf exists” into an exact underbudget frontier statement.

## 7. Overlapping Adjustment Families And The Contract/Runtime Split

**Status:** EXACT COMPUTATIONAL RESULT on the enumerated overlapping-family worlds; OBSERVED LAW for the fixed-family runtime count formula

**Supporting artifacts:** [overlapping_adjustment_families.md](../../../results/family-runtime/overlapping-adjustment-families/overlapping_adjustment_families.md), [separator-closure-and-family-memory.md](../experiments/quotient-thresholds/separator-closure-and-family-memory.md), [family-memory-contract-and-runtime.md](../experiments/family-runtime/family-memory-contract-and-runtime.md), [family_memory_exact_search.md](../../../results/family-runtime/family-memory-exact-search/family_memory_exact_search.md), [family_memory_thresholds.svg](../../../results/family-runtime/family-memory-exact-search/family_memory_thresholds.svg)

This layer changed the shape of the research question.
The first explicit overlapping-family examples already show that variable-wise survivor memory is too coarse at the contract layer.

The canonical pair is:

- `n5_m732`: family `{{0,1}, {0,2}}`,
- `n5_m746`: family `{{0,1}, {1,2}}`.

They live on the same witness universe, but family survival under survivor subsets differs.
So the exact contract object must remember families, not only variables.

The exact search then separates two layers.

### Contract layer

Across `52` normalized overlapping-family worlds:

- `union/core/size` fails,
- degree and intersection signatures fail,
- orbit summaries fail,
- the full antichain is exact.

### Runtime layer

For every fixed normalized family `A` realized by the scan:

- the exact runtime quotient matches `(depth, completed-variable set)`,
- variable-runtime and family-runtime thresholds coincide,
- the observed family-runtime count law is `k + 2^p`.

Representative worlds are:

- `A_path_k2_p3`: answer `6`, variable `10`, family `10`,
- `A_star_k2_p4`: answer `6`, variable `18`, family `18`,
- `A_mixed_k3_p4`: answer `11`, variable `19`, family `19`.

This is the first exact contract/runtime split in the repository:

> the contract is hypergraph-valued, but the fixed-contract runtime automaton is still variable-based on the scanned worlds.

**Selected figure:** [Family-memory thresholds](../../../results/family-runtime/family-memory-exact-search/family_memory_thresholds.svg)
Why it matters: it is the clearest summary of the answer/variable/family threshold relation on the representative fixed-family worlds.

## 8. Runtime-Collapse Boundary Under Binary Completion

**Status:** EXACT COMPUTATIONAL RESULT on the enumerated arbitrary antichains; THEOREM TEMPLATE / PROOF SKETCH for the binary-completion factorization

**Supporting artifacts:** [runtime-collapse-boundary.md](../experiments/family-runtime/runtime-collapse-boundary.md), [runtime_collapse_boundary.md](../../../results/family-runtime/runtime-collapse-boundary/runtime_collapse_boundary.md), [runtime_collapse_boundary.svg](../../../results/family-runtime/runtime-collapse-boundary/runtime_collapse_boundary.svg), [teaching_complexity_boundary.svg](../../../results/family-runtime/runtime-collapse-boundary/teaching_complexity_boundary.svg)

The next question was whether the fixed-family runtime collapse only held because the overlapping families came from DAGs.
The antichain boundary scan says no.

On exact arbitrary full-union antichains with `p <= 5`, `k <= 3`:

- exact `(p,k)` classes scanned: `11`,
- exact antichains scanned: `6336`,
- runtime-collapse failures under current semantics: `0`.

The observed exact runtime family counts are:

- `(2,1) -> 5`,
- `(2,2) -> 6`,
- `(3,2) -> 10`,
- `(4,2) -> 18`,
- `(4,3) -> 19`,
- `(5,2) -> 34`,
- `(5,3) -> 35`,

matching the law:

`runtime_family_count = k + 2^p`

on the scanned grid.

The exact teaching laws on those classes are:

- answer basis: `sum_(r=1)^k C(p,r)` on every nontrivial class,
- variable basis: `sum_(r=2)^k C(p,r)` except the exact small exception `(p=4, k=3) = 7`,
- family basis: `1` on every nontrivial class.

So by the end of this layer the boundary had become sharp:

- arbitrary antichains do not break the current runtime collapse,
- the first break must be semantic, not combinatorial.

**Selected figure:** [Runtime-collapse boundary](../../../results/family-runtime/runtime-collapse-boundary/runtime_collapse_boundary.svg)
Why it matters: it is the cleanest picture of the semantic, rather than combinatorial, location of the boundary.

## 9. The Semantic Boundary Atlas

**Status:** EXACT COMPUTATIONAL RESULT on the scanned semantic library; THEOREM / PROPOSITION for the fixed-carrier coordinate bound

**Supporting artifacts:** [semantic-boundary-atlas.md](../experiments/runtime-semantics/semantic-boundary-atlas.md), [semantic_boundary_atlas.md](../../../results/runtime-semantics/semantic-boundary-atlas/semantic_boundary_atlas.md), [semantic_boundary_atlas.svg](../../../results/runtime-semantics/semantic-boundary-atlas/semantic_boundary_atlas.svg), [semantic_runtime_thresholds.svg](../../../results/runtime-semantics/semantic-boundary-atlas/semantic_runtime_thresholds.svg), [semantic_teaching_atlas.svg](../../../results/runtime-semantics/semantic-boundary-atlas/semantic_teaching_atlas.svg)

The semantic atlas keeps the witness carrier and composition law fixed and varies only the family readout.
That exact design decision makes the current boundary visible.

The atlas scans eight enrichments plus the binary baseline.

### Break taxonomy

The first breaks separate into three types.

1. Coordinate-level:

   - `additive_partial_activation`,
   - `capped_additive_activation`,
   - `heterogeneous_variable_weights`,
   - `order_sensitive_completion`,
   - `multilevel_local_progress`,

   all first break at `(p=2, k=2, A={{1,2}})`.

2. Family-specific but not overlap-specific:

   - `heterogeneous_family_thresholds`

   first breaks at `(p=3, k=2, A={{1,2},{3}})`.

3. Genuinely hypergraph-specific:

   - `overlap_bonus`,
   - `overlap_exclusion`

   first break at `(p=3, k=2, A={{1,2},{1,3}})`.

### Runtime consequences

The atlas shows several different runtime patterns.

- Some enrichments break the old summary before family bits exceed old variable bits.
- Some open an immediate family-runtime tax.
- Several produce strict `answer < variable < family` worlds.
- `overlap_bonus` and `overlap_exclusion` give the first overlap-required breaks.

### Teaching consequences

The old subset-probe bank now separates into three regimes.

- Family teaching remains trivial for many enrichments.
- `overlap_exclusion` is the first exact family-teaching nontriviality: family basis `3` at `(p=3, k=2)`.
- `order_sensitive_completion` is the first family-teaching failure of the old probe bank: answer, variable, and family teaching are all inexact on the scanned nontrivial groups.

### The fixed-carrier theorem-shaped boundary

Because every enriched output is still a deterministic readout of the composed witness state, full coordinate state remains exact.
So the strongest exact proposition now in hand is:

> no readout-only enrichment on the fixed witness carrier can force genuinely non-coordinate runtime state.

This is the culminating boundary statement of the current phase.

**Selected figure:** [Semantic boundary atlas](../../../results/runtime-semantics/semantic-boundary-atlas/semantic_boundary_atlas.svg)
Why it matters: it is the cleanest compact view of where the first breaks occur and how teaching changes with semantics.

**Selected figure:** [Semantic runtime thresholds](../../../results/runtime-semantics/semantic-boundary-atlas/semantic_runtime_thresholds.svg)
Why it matters: it shows which enrichments merely break the old summary and which actually open a positive family-runtime tax over the old variable channel.

**Selected figure:** [Semantic teaching atlas](../../../results/runtime-semantics/semantic-boundary-atlas/semantic_teaching_atlas.svg)
Why it matters: it shows that observation can separate from runtime, especially in the order-sensitive and overlap-exclusion regimes.

## The Central Boundary Result Of The Current Phase

The strongest clean synthesis now supported is:

**Main Boundary Result.**

On the fixed witness carrier:

1. hypergraph complexity is exact at the contract layer,
2. can become visible at the teaching/probe layer,
3. readout-only semantic enrichment can break the old runtime quotient and can even require overlap for the first break,
4. but no scanned readout-only enrichment forces genuinely non-coordinate runtime state.

Therefore:

> the next true runtime-hypergraph theorem must change the carrier or the composition law, not just the readout.

This is stronger than the earlier question “do hypergraphs matter?”
They already matter.
The real question is now:

> what is the smallest carrier/composition enrichment that makes hypergraph state computationally necessary at runtime?

## What Is Now Proved, Exact, Observed, And Conjectured

### Proved or treated as proved background in the repository

- Bare threshold quotient ladder `raw L2 -> L2' -> M_k -> R_k`.
- Protected-witness quotient with exact state count `|Q_(k,p)| = sum_(d=0)^k (d + 2)^p`.
- Symmetry quotient `|Q_(k,p)^sym| = binom(k + p + 2, p + 1) - 1`.
- Contract-representation theorem template for admissible finite-index two-sided contracts with bounded separators.
- Witness-faithful factorization theorem on the unique-minimal causal class.
- Fixed-carrier proposition that readout-only enrichments still factor through full coordinate state.

### Exact computational results

- Ordered-DAG unique-minimal referee on `89291` admissible queries with zero `Q_(k,p)` failures.
- Phase sweeps, geometry sweeps, and clustering controls on the listed synthetic families and `causal_referee`.
- Measured quotient-tower counts for synthetic families and `causal_referee`.
- Exact separator closure on the listed synthetic families.
- Exact Pareto frontiers on the listed atomic state spaces.
- Overlapping-family contract collisions and exact family-memory search on `52` normalized family worlds.
- Runtime-collapse boundary on `6336` arbitrary antichains.
- Semantic boundary atlas on eight exact readout enrichments.

### Observed laws on scanned grids

- Closure rank appears to equal `k` on the tested synthetic witness families.
- The minimal exact closure basis appears to be the clean depth ladder.
- On the scanned fixed-family worlds, runtime family count follows `k + 2^p`.
- On the binary-completion antichain scan, runtime family count also follows `k + 2^p`.
- Family-runtime and variable-runtime thresholds coincide on the scanned fixed-family worlds and the binary-completion antichain scan.

### Conjectural or open

- A general proof of the closure-rank law.
- A general proof of the runtime family count law beyond the scanned worlds.
- A canonical minimal normal form for overlapping-family contracts smaller than the raw antichain, if such a form exists.
- A separator-complete theorem for finite probe banks.
- The first carrier/composition enrichment that forces genuinely non-coordinate runtime state.

## Theorem / Status Ledger

The full ledger is collected separately in [selective-memory-theorem-ledger.md](selective-memory-theorem-ledger.md).
The short version is:

| Layer | Main statement | Status |
| --- | --- | --- |
| Bare threshold quotient | `M_k` and `R_k` are the canonical bare contract quotients | THEOREM (background) |
| Protected-witness quotient | witness identity requires `Q_(k,p)` with exact count `sum_(d=0)^k (d + 2)^p` | THEOREM (background) |
| Unique-minimal causal factorization | witness-faithful unique-minimal causal queries factor through `Q_(k,p)` | THEOREM |
| Unique-minimal referee | zero `Q_(k,p)` failures on `89291` admitted ordered-DAG queries | EXACT COMPUTATIONAL RESULT |
| Phase law | exact turn-on at quotient ceilings on listed families; mirage shelf under forcing | EXACT COMPUTATIONAL RESULT / OBSERVED LAW |
| Finite-probe tower | canonical, empirical, and probe quotients separate | EXACT COMPUTATIONAL RESULT |
| Separator closure | deficiency closes to zero on listed synthetic families | EXACT COMPUTATIONAL RESULT |
| Closure rank `= k` | depth ladder appears minimal on tested synthetic families | OBSERVED LAW |
| Exact Pareto frontier | answer/witness shelf is intrinsic on listed atomic spaces | EXACT COMPUTATIONAL RESULT |
| Family-memory split | contract hypergraph exact, runtime fixed-family collapse on scanned worlds | EXACT COMPUTATIONAL RESULT / OBSERVED LAW |
| Runtime-collapse boundary | binary completion still collapses on `6336` arbitrary antichains | EXACT COMPUTATIONAL RESULT |
| Semantic atlas | readout-only enrichment breaks old quotient but not full coordinate exactness | EXACT COMPUTATIONAL RESULT plus fixed-carrier proposition |

## Open Problems And The Next Seam

The next seam is now disciplined.
It is not:

- do hypergraphs matter?

That is already settled at the contract layer and visible in the probe layer.

It is:

- what carrier/composition enrichment is the first to force genuinely non-coordinate runtime memory?

The most disciplined next exact targets are:

1. A carrier-extension theorem.
   Search for the smallest carrier augmentation or composition change that creates a runtime family quotient strictly larger than any coordinate-only summary.

2. A hypergraph-runtime counterexample family.
   Find the smallest exact world where full coordinate progress is no longer sufficient but a family- or edge-valued runtime state is.

3. A separator-complete probe theorem.
   Identify exact conditions under which finite probe banks recover the full two-sided quotient.

4. A canonical family-contract normal form.
   Determine whether the raw family antichain is minimal, or whether a smaller exact contract object exists.

5. The enriched `Q_(k,𝒜)` theorem.
   Replace unique minimal witness coordinates with overlapping admissible-family memory once the carrier is genuinely enriched.

## Artifact Index And Figure Guide

### Core notes

- [Causal contract refinement](../foundations/causal-contract-refinement.md)
- [Witness-faithful factorization](../foundations/witness-faithful-factorization.md)
- [Contract representation theorem](../foundations/contract-representation-theorem.md)
- [Finite-probe quotient tower](../experiments/quotient-thresholds/finite-probe-quotient-tower.md)
- [Separator-closure and family-memory](../experiments/quotient-thresholds/separator-closure-and-family-memory.md)
- [Family-memory contract/runtime](../experiments/family-runtime/family-memory-contract-and-runtime.md)
- [Runtime-collapse boundary](../experiments/family-runtime/runtime-collapse-boundary.md)
- [Semantic boundary atlas](../experiments/runtime-semantics/semantic-boundary-atlas.md)

### Core reports

- [Unique-minimal referee](../../../results/referee/unique-minimal-referee/unique_minimal_referee.md)
- [Phase-transition sweep](../../../results/quotient-thresholds/phase-transition-sweep/phase_transition_sweep.md)
- [Separator closure experiment](../../../results/quotient-thresholds/separator-closure-experiment/separator_closure_experiment.md)
- [Exact Pareto frontier](../../../results/quotient-thresholds/exact-pareto-frontier/exact_pareto_frontier.md)
- [Overlapping adjustment families](../../../results/family-runtime/overlapping-adjustment-families/overlapping_adjustment_families.md)
- [Family-memory exact search](../../../results/family-runtime/family-memory-exact-search/family_memory_exact_search.md)
- [Runtime-collapse boundary report](../../../results/family-runtime/runtime-collapse-boundary/runtime_collapse_boundary.md)
- [Semantic boundary atlas report](../../../results/runtime-semantics/semantic-boundary-atlas/semantic_boundary_atlas.md)

### Selected figures

- [Memory stratigraphy](../../../results/quotient-thresholds/separator-closure-experiment/memory_stratigraphy.svg)
- [Separator closure deficiency](../../../results/quotient-thresholds/separator-closure-experiment/separator_closure_deficiency.svg)
- [Exact Pareto frontier](../../../results/quotient-thresholds/exact-pareto-frontier/exact_pareto_frontier.svg)
- [Family-memory thresholds](../../../results/family-runtime/family-memory-exact-search/family_memory_thresholds.svg)
- [Runtime-collapse boundary](../../../results/family-runtime/runtime-collapse-boundary/runtime_collapse_boundary.svg)
- [Semantic boundary atlas](../../../results/runtime-semantics/semantic-boundary-atlas/semantic_boundary_atlas.svg)
- [Semantic runtime thresholds](../../../results/runtime-semantics/semantic-boundary-atlas/semantic_runtime_thresholds.svg)
- [Semantic teaching atlas](../../../results/runtime-semantics/semantic-boundary-atlas/semantic_teaching_atlas.svg)

## Takeaways

1. The original bare-causal target failed for the right reason: contract mismatch.
2. The witness quotient repaired that failure exactly on the unique-minimal causal class.
3. The phase program then showed that finite memory can preserve answers after it stops preserving reasons.
4. The probe tower, separator closure, and exact Pareto frontiers turned that intuition into a measured geometry.
5. Overlapping families force a hypergraph-valued contract object but not yet a hypergraph-valued runtime automaton.
6. Binary completion still collapses on arbitrary antichains.
7. Semantic enrichment can require overlap for the first runtime break without escaping the coordinate carrier.
8. The next true abyss is no longer contract hypergraph memory. It is runtime hypergraph memory under an enriched carrier or composition law.

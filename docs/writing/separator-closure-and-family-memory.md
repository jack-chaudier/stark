# Separator Closure And Family Memory

## Thesis

The new experiments separate three questions that had previously been tangled together:

1. how incomplete the current probe bank is,
2. whether the mirage shelf is intrinsic or merely a compressor artifact,
3. what the next exact causal memory object must remember once minimal adjustment families overlap.

The current answer is sharper than before:

> the present right-bank probe deficiency can be closed by a small depth-indexed separator basis, the observed answer/witness shelf survives exact compressor optimization on the measured tower, and the first overlapping causal families already force a hypergraph-valued state object.

This note records exactly what is now measured, what is still only observed, and what the overlapping-family scan suggests about `Q_(k, A)`.

## Source Basis

This note uses only local artifacts generated in the workspace:

- [finite-probe-quotient-tower.md](finite-probe-quotient-tower.md)
- [phase_transition_sweep.md](../../results/phase_transition_sweep.md)
- [separator_closure_experiment.md](../../results/separator_closure_experiment.md)
- [separator_closure_experiment.json](../../results/separator_closure_experiment.json)
- [exact_pareto_frontier.md](../../results/exact_pareto_frontier.md)
- [exact_pareto_frontier.json](../../results/exact_pareto_frontier.json)
- [overlapping_adjustment_families.md](../../results/overlapping_adjustment_families.md)
- [overlapping_adjustment_families.json](../../results/overlapping_adjustment_families.json)

## 1. Separator-Complete Closure Is Now Measurable

The current synthetic probe deficiency is no longer a metaphor.

It is now an exact observable closure problem:

- start from the current right-bank probe-joint quotient,
- collapse left contexts into their induced action types on that quotient,
- search over action subsets exactly,
- ask how many added left actions are needed to recover the canonical quotient.

On the target synthetic families, the result is unexpectedly clean:

- `Q_(3,2)` starts at `7` probe-joint states and reaches the canonical `54` after `3` added left actions,
- `Q_(4,2)` starts at `8` and reaches `90` after `4`,
- `Q_(5,3)` starts at `13` and reaches `783` after `5`.

The exact minimal basis is unique on all three targets:

- `Q_(3,2)`: `[(1, BOT^2), (2, BOT^2), (3, BOT^2)]`,
- `Q_(4,2)`: `[(1, BOT^2), (2, BOT^2), (3, BOT^2), (4, BOT^2)]`,
- `Q_(5,3)`: `[(1, BOT^3), (2, BOT^3), (3, BOT^3), (4, BOT^3), (5, BOT^3)]`.

Here `BOT^p` means that every witness coordinate is absent in the added left context.

So the cleanest new invariant is:

`closure_rank(Q_(k,p), P_right) = k`

on every tested family with `k <= 5`, `p <= 3`.

This is not yet proved in general.
It is an exact observed law on the current grid.

## 2. Better Probes Shrink Deficiency But Widen The Potential Shelf

The closure sweep revealed a second, less obvious law.

As the exact left basis is added:

- probe deficiency falls monotonically,
- unresolved canonical pairs fall monotonically,
- but shelf width increases rather than decreases.

The cleanest target is `Q_(5,3)`:

- at `0` added left actions: deficiency `5.912` bits, shelf width `0.893` bits,
- at `1` action: deficiency `3.547`, shelf `2.366`,
- at `2` actions: deficiency `2.121`, shelf `3.322`,
- at `3` actions: deficiency `1.153`, shelf `4.000`,
- at `4` actions: deficiency `0.471`, shelf `4.498`,
- at exact closure: deficiency `0.000`, shelf `4.858`.

So separator-complete closure is doing two opposing things at once:

- it repairs the missing two-sided distinctions,
- it exposes a larger possible answer-vs-justification gap inside the observational tower before exact recovery is reached.

That is the opposite of the naive expectation that “better probes just make the shelf disappear.”

## 3. The Shelf Is Intrinsic On The Measured Tower

The exact partition frontiers answer the next natural objection.

The question is not only whether the tested schemes show a shelf.
It is whether *any* compressor on the measured atomic state space can avoid it.

The exact frontier says no on the strongest observational cases.

### `Q_(5,3)` on the current probe-joint quotient

The measured observational state space has:

- `13` joint states,
- `7` answer states.

So there is a real observational gap.

At `8` buckets (`3` observational bits):

- the exact forced frontier reaches answer accuracy `1.000`,
- but the best witness fidelity on the frontier is only `0.993`,
- and the best witness fidelity among partitions with perfect answer is only `0.982`.

Exact joint recovery appears only at `13` buckets (`4` observational bits).

### `causal_referee` on empirical support

The measured empirical support has:

- `15` joint states,
- `4` answer states.

At `4` buckets (`2` bits):

- the exact forced frontier already reaches answer accuracy `1.000`,
- but the best witness fidelity on the frontier is only `0.894`,
- and the best witness fidelity while keeping answer perfect is only `0.641`.

At `8` buckets (`3` bits):

- answer remains `1.000`,
- best witness fidelity rises to `0.976`,
- witness fidelity under perfect answer rises to `0.964`.

Exact witness recovery appears only at `15` buckets (`4` bits).

So on the measured tower, the shelf is not merely a quirk of one deterministic compressor.
It is an exact underbudget frontier phenomenon.

The breach frontiers tell the complementary story:

- below the joint threshold, breach never attains perfect answer,
- exactness returns only when the joint atomic states are fully separated.

This is exactly the breach-versus-mirage dichotomy the larger program wanted.

## 4. Memory Stratigraphy Is Now A First-Class Figure

The new stratigraphy figure puts the tower on one line for each family:

- `M_3`: algebraic `3.807`, empirical `3.807`, joint `2.322`, answer `2.322`,
- `Q_(3,2)`: algebraic `5.755`, empirical `5.755`, joint `2.807`, answer `2.322`,
- `Q_(4,2)`: algebraic `6.492`, empirical `6.492`, joint `3.000`, answer `2.585`,
- `Q_(5,3)`: algebraic `9.613`, empirical `9.613`, joint `3.700`, answer `2.807`,
- `causal_referee`: algebraic `11.306`, empirical `3.907`, joint `3.907`, answer `2.000`.

That figure already separates regimes:

- bare threshold families, where answer and joint coincide,
- protected-witness families, where answer is strictly cheaper than joint,
- realistic causal support, where empirical support is tiny relative to the worst-case algebraic ceiling but the answer/joint gap remains large.

So the tower is no longer just a definition.
It is a measured stratigraphy of reasoning.

## 5. The First Explicit `Q_(k, A)` Counterexamples

The overlapping-family search gives the first exact small-world cases where variable-wise witness summaries are already too coarse.

No overlaps appear for `n <= 4`.
The first explicit overlaps appear at `n = 5`.

Two smallest counterexamples live on the same witness universe `{0,1,2}`:

- `n5_m732`, query `(3,4)`, family `{ {0,1}, {0,2} }`,
- `n5_m746`, query `(3,4)`, family `{ {0,1}, {1,2} }`.

In both cases every variable in the universe matters individually.
So a flat survivor vector cannot tell the states apart.

But under survivor set `{0,2}`:

- the first family still leaves `{ {0,2} }`,
- the second leaves nothing.

So the exact object must preserve admissible family structure, not only per-variable availability.

The safest exploratory state here is the minimal-adjustment antichain itself, or equivalently the family-survival function on survivor subsets.

This does **not** prove that the antichain is the minimal exact representation.
It does prove that coordinate-wise witness memory is already too coarse on the smallest overlapping cases.

That is the first concrete foothold for `Q_(k, A)`.

## 6. What Is Proved, Observed, And Open

### Proved or exact inside the current artifacts

1. The target synthetic closure runs are exact relative to the full current right-bank probe set.
2. The minimal basis sizes reported in the closure experiment are exact on the tested families.
3. The partition frontiers are exact on the listed atomic state spaces.
4. The overlapping-family examples are explicit exhaustive small-world witnesses.

### Observed but not yet proved in general

1. Closure rank appears to equal `k` on every tested `Q_(k,p)` family.
2. The minimal exact closure basis appears to be the clean depth ladder `[(1, BOT^p), ..., (k, BOT^p)]`.
3. Shelf width widens monotonically along exact closure on the tested grid.

### Still open

1. A general proof of the closure-rank law.
2. A separator-complete theorem identifying which finite probe banks suffice for full two-sided recovery.
3. The exact causal quotient once adjustment families overlap.
4. Whether the hypergraph antichain itself is minimal, or whether a smaller family-valued state object exists.

## Takeaways

1. Probe deficiency is now measurable and exactly closable on the tested synthetic families.
2. The shelf is intrinsic on the measured observational tower, not merely an artifact of one compressor.
3. Better probes can widen the possible answer-vs-justification gap even while reducing probe deficiency.
4. The first overlapping causal examples already force a family-level, hypergraph-valued next object.

So the project has crossed another threshold.

It is no longer only about whether finite memory fails.
It is about how missing probes, limited support, and the contract itself jointly determine the gap between being right and knowing why.

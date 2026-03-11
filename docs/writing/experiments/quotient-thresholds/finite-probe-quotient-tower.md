# Finite-Probe Quotient Tower

## Thesis

The current sweep no longer supports a one-object story.

The data is forcing a quotient tower:

`canonical quotient -> empirical support quotient -> probe-joint quotient -> probe-answer quotient`.

That tower separates three distinct notions of memory complexity:

1. the worst-case algebraic complexity of the full contract,
2. the complexity actually visited by a distribution,
3. the complexity visible to a finite observational regime.

The mirage shelf lives in the gap between the last two observable layers:

> a shelf appears whenever the quotient for being right is smaller than the quotient for knowing why.

This note names that tower precisely, records what is already measured by the current artifacts, and states the next theorem template suggested by the data.

## Source Basis

This note uses only local artifacts already in the workspace:

- [contract-representation-theorem.md](../../foundations/contract-representation-theorem.md)
- [witness-faithful-factorization.md](../../foundations/witness-faithful-factorization.md)
- [unique_minimal_referee.md](../../../../results/referee/unique-minimal-referee/unique_minimal_referee.md)
- [phase_transition_sweep.md](../../../../results/quotient-thresholds/phase-transition-sweep/phase_transition_sweep.md)
- [phase_transition_sweep.json](../../../../results/quotient-thresholds/phase-transition-sweep/phase_transition_sweep.json)

## 1. Why One Quotient Is No Longer Enough

The canonical contract quotient `Q_C` is still the top object.

For the synthetic families already on disk, it gives the exact worst-case state counts:

- `|M_3| = 14`, so the exact ceiling is `4` bits,
- `|Q_(3,2)| = 54`, so the exact ceiling is `6` bits,
- `|Q_(5,3)| = 783`, so the exact ceiling is `10` bits.

The geometry sweeps show that the pre-threshold answer/witness split is not a prefix artifact:

- `Q_(5,3)` at `9` bits stays in mirage under `prefix`, `suffix`, and `interleaved`,
- `causal_referee` at `3` bits keeps the same qualitative split under the same three geometries.

But the clustering controls add a new fact:

- on synthetic `Q_(5,3)`, `cluster_joint` becomes exact far below the canonical `10`-bit ceiling,
- on the realistic `causal_referee` slice, the same pre-threshold point remains visibly subexact.

That can only happen if the current probe bank is strictly coarser than the full two-sided contract separators.

So the experiments are no longer measuring only `Q_C`.
They are measuring a tower of quotients indexed by support and observation.

## 2. Definitions

Fix a contract `C` on raw state space `X`.

### 2.1 Canonical quotient

Let

`Q_C = X / ~_C`

be the full contract quotient from the contract-representation note.

This is the worst-case algebraic object.

### 2.2 Empirical support quotient

Let `mu` be the distribution actually used by an experiment.

Restrict the canonical quotient to the support visited by `mu`:

`Q_C|_(support(mu))`.

This is the empirical state space actually touched by the dataset.

For the current synthetic sweeps, the support is uniform over all exact states, so the empirical quotient equals the algebraic quotient.

For the realistic causal slice, this is not true:

- canonical upper bound across the observed `k` values: `2532` states,
- empirical support on `causal_referee`: `15` states.

### 2.3 Finite-probe observational quotient

Let `P` be a finite probe bank and let `O` be the observable family we care about.

Define observational equivalence by

`x ~_(C,P)^O y`

iff `x` and `y` induce the same `O`-trace on every probe in `P`.

This yields a finite observational quotient

`Q_(C,P)^O`.

The current sweep already measures three observable families:

- `O = answer`,
- `O = witness`,
- `O = joint = (answer, witness)`.

So the current artifacts are already computing:

- `Q_(C,P)^answer`,
- `Q_(C,P)^witness`,
- `Q_(C,P)^joint`.

## 3. The Tower Measured by the Current Sweep

The tower table in [phase_transition_sweep.md](../../../../results/quotient-thresholds/phase-transition-sweep/phase_transition_sweep.md) now records the following counts.

### `Q_(5,3)`

- algebraic quotient: `783` states, `9.613` bits,
- empirical support: `783` states, `9.613` bits,
- probe-joint quotient: `13` states, `3.700` bits,
- probe-answer quotient: `7` states, `2.807` bits,
- probe deficiency: `5.912` bits,
- shelf width: `0.893` bits.

This is the cleanest synthetic evidence that the current right-context probe bank is not separator-complete for the full two-sided quotient.

### `causal_referee`

- algebraic upper bound: `2532` states, `11.306` bits,
- empirical support: `15` states, `3.907` bits,
- probe-joint quotient: `15` states, `3.907` bits,
- probe-answer quotient: `4` states, `2.000` bits,
- probe deficiency: `7.399` bits,
- shelf width: `1.907` bits.

So the realistic corpus sits on a thin empirical manifold inside the worst-case witness quotient, but still retains a substantial gap between answer-only and full joint identity.

### Lower rungs

The same tower already appears on the smaller synthetic families:

- `Q_(3,2)`: algebraic `54`, probe-joint `7`, probe-answer `5`,
- `M_3`: algebraic `14`, probe-joint `5`, probe-answer `5`.

So the answer shelf is not universal across all contracts:

- for bare threshold families, the observed answer quotient and joint quotient coincide,
- for protected-witness families, the answer quotient is strictly smaller.

That is exactly the semantic distinction the repaired theory wanted.

## 4. Finite-Probe Quotient Theorem Template

The next theorem should be stated at the observational level first.

### Definition

For fixed contract `C`, finite probe bank `P`, and observable family `O`, define the finite-probe quotient

`Q_(C,P)^O = X / ~_(C,P)^O`.

### Proposition 1. Finite-probe quotient exists

Because `P` is finite and each probe produces a finite `O`-trace in the current experimental regime, `~_(C,P)^O` has finite index.

So `Q_(C,P)^O` exists as a finite observational quotient.

This is not the full contract theorem.
It is the observational shadow of that theorem under a chosen probe bank.

### Proposition 2. Observational turn-on

If a summary is required to preserve exactly the `O`-traces induced by `P`, then exact recovery turns on at

`ceil(log_2 |Q_(C,P)^O|)`.

This is the observational counterpart of the exact quotient threshold.

### Definition. Probe deficiency

Define

`delta(C, P) = log_2 |Q_C| - log_2 |Q_(C,P)^joint|`.

This measures how far a probe bank is from the full two-sided theorem.

### Definition. Shelf width

Define

`omega(C, P) = log_2 |Q_(C,P)^joint| - log_2 |Q_(C,P)^answer|`.

This is the width of the potential mirage interval under the chosen observational regime.

If `omega(C, P) > 0`, then the probe bank can in principle distinguish more about justification than about bare correctness.

## 5. What Is Proved, and What Is Not

What is already supported by the current artifacts:

1. the canonical quotient still sets the worst-case algebraic ceiling,
2. the deterministic geometry sweeps show a robust pre-threshold mirage shelf,
3. the clustering controls reveal that the probe bank itself has a quotient tower,
4. the realistic causal corpus has a large answer/joint gap even when the synthetic joint trace bank collapses early.

What is **not** yet proved:

1. that the current probe bank is separator-complete,
2. that the current shelf widths are optimal over all compressors,
3. that `Q_(C,P)^joint` equals the full canonical quotient on the synthetic families,
4. that the same tower extends unchanged beyond the unique-minimal witness class.

So the correct sentence is:

> the current experiments measure an observational quotient tower, not yet the full two-sided contract quotient.

That sentence is a strength, not a weakness.
It tells us exactly what the next experiment must close.

## 6. The Next Closure Step

The current right-context trace bank leaves a large synthetic probe deficiency:

- `delta(Q_(5,3), P) = 5.912` bits.

So the natural next move is separator-complete closure:

1. find a pair of synthetic states merged by the current `cluster_joint` baseline,
2. search for a missing left/right separator,
3. add that separator to `P`,
4. recompute `Q_(C,P)^joint`,
5. repeat until the joint observational quotient reaches the canonical quotient.

That procedure would make probe deficiency measurable rather than rhetorical.

## 7. Why This Matters for `Q_(k,𝒜)`

The tower language also clarifies the next causal theorem.

`Q_(k,p)` is the right exact object on the unique-minimal class because the witness coordinates are enough there.

Once minimal adjustment families overlap, a variable-level witness vector is unlikely to remain exact.

The next quotient should therefore preserve family survival rather than only named coordinates:

`Q_(k,𝒜)`.

The tower perspective suggests what that object must do:

- algebraically, it must refine the unique-minimal witness quotient,
- empirically, it may still collapse sharply on realistic supports,
- observationally, it will depend on which family-level probes can be applied.

So the tower does not replace the `Q_(k,𝒜)` program.
It gives it the right language.

## Takeaways

1. The experiments are now measuring more than one threshold.
2. The correct object is a quotient tower indexed by contract, support, and probe bank.
3. The mirage shelf is the gap between the probe-joint quotient and the probe-answer quotient.
4. Probe deficiency is the gap between the full canonical quotient and the current observational quotient.
5. The next serious experiment is separator-complete closure of the joint probe bank.

## References

- [contract-representation-theorem.md](../../foundations/contract-representation-theorem.md)
- [witness-faithful-factorization.md](../../foundations/witness-faithful-factorization.md)
- [unique_minimal_referee.md](../../../../results/referee/unique-minimal-referee/unique_minimal_referee.md)
- [phase_transition_sweep.md](../../../../results/quotient-thresholds/phase-transition-sweep/phase_transition_sweep.md)

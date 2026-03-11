# Witness-Faithful Factorization on the Unique-Minimal Causal Class

## Thesis

The first positive theorem that survives contact with reality is not that bare `L2` recovers adjustment sets. That door is already closed. The right theorem is narrower and stronger:

> For causal queries with a unique minimal adjustment set, a witness-faithful linearization translates the query into the already-proved protected-witness contract. Therefore the minimal contract-sound compositional summary factors through `Q_(k,p)`.

This note writes that theorem down cleanly, states exactly what is proved versus inherited, and records the first exhaustive referee results on the small ordered-DAG world.

The deepest sentence justified by this note is deliberately scoped:

> In the unique-minimal witness-faithful regime, causality does not live in the answer. It lives in the smallest state that keeps the answer identifiable.

## Sources

This note uses the in-repo sources below plus a few local working notes that are
not part of the repository snapshot:

- [causal-contract-refinement.md](causal-contract-refinement.md)
- [unique_minimal_referee.json](../../../results/referee/unique-minimal-referee/unique_minimal_referee.json)

## Outline

1. State the narrow causal class.
2. Define the witness-faithful translation.
3. Prove factorization through the protected-witness contract.
4. Record the symmetry corollary.
5. Check the class exhaustively on small DAGs.
6. Mark the next rung: the adjustment-family quotient `Q_(k,𝒜)`.

## 1. The Narrow Causal Class

Fix a causal query `q = (G, T, Y)` in a DAG.

Assume:

1. there is a directed path `T -> ... -> Y`,
2. the backdoor effect is identifiable by adjustment,
3. the minimal adjustment family is unique and non-empty,
4. write that unique minimal set as `A* = {lambda_1, ..., lambda_p}`.

This is the smallest honest class because it removes two sources of ambiguity:

- no empty-set triviality,
- no overlap among several minimal adjustment families.

It does **not** trivialize the problem. Bare `L2` still fails here.

## 2. Prefix-Witness Linearizations

We now define the causal-to-contract translation.

### Definition 1. Prefix-witness linearization

A prefix-witness linearization of `q` is a topological linearization together with a symbol map into the alphabet

`Sigma_q = {N, T} union {W_lambda : lambda in A*}`

satisfying:

1. every `lambda in A*` appears before `T`,
2. each member of `A*` is mapped to its own protected symbol `W_lambda`,
3. every other pre-treatment node is mapped to anonymous predecessor symbol `N`,
4. the treatment node is mapped to the focal symbol `T`,
5. post-treatment nodes are quotient-irrelevant for the contract and are discarded.

So the retained word has the form

`u T`

where `u` is a word over `{N} union {W_lambda}`.

### Definition 2. The unique-minimal causal contract

Fix `k = |A*| = p`.

The contract asks the summary to preserve, under admissible concatenations, which protected witnesses remain available as named justification for a feasible treatment pivot at threshold `k`.

In plain language:

- anonymous predecessor mass may matter for capacity,
- but witness identity matters for causal soundness,
- and the output obligation is exactly the unique minimal set `A*`.

## 3. The Positive Theorem

### Theorem 1. Witness-faithful factorization theorem

Let `q = (G, T, Y)` have unique minimal adjustment set `A* = {lambda_1, ..., lambda_p}` and let `PW(q)` be the class of prefix-witness linearizations of `q`.

Then the unique-minimal causal contract on `PW(q)` factors through the protected-witness contract with quotient state

`Q_(k,p)`, where `k = p`,

and therefore every contract-sound associative summary for this class factors through `Q_(k,p)`.

Equivalently: once the linearization preserves the unique minimal witnesses as named protected predecessors, the causal memory problem is no longer a new object. It is an instance of the already-solved protected-witness memory problem.

### Proof

The proof is a translation argument.

#### Step 1. Translate the causal instance into the protected-witness alphabet

By Definition 1, every admissible linearization of `q` is mapped to a word over

`Sigma_q = {N, T} union {W_lambda : lambda in A*}`.

This translation keeps exactly the information the contract promises to preserve:

- predecessor capacity before treatment,
- the named witnesses in `A*`,
- the treatment pivot itself.

It discards only post-treatment structure and non-witness identity, which are outside the contract by construction.

#### Step 2. Identify the inherited contract

After translation, the causal question becomes:

> under concatenation, which protected witnesses still survive as named support for a feasible treatment pivot?

That is precisely the protected-witness contract already analyzed in the selective-memory note. Its exact quotient is `Q_(k,p)` with class count

`|Q_(k,p)| = sum_(d=0)^k (d + 2)^p`.

So the translated causal problem is not merely analogous to the witness problem. It **is** the witness problem.

#### Step 3. Factorization

Let `L_q` be the prefix-witness translation from admissible causal linearizations into the protected-witness language, and let `rho_(k,p)` be the exact protected-witness quotient map.

Then the causal contract observable is obtained by composition:

`causal observable = protected-witness observable o L_q`.

Hence the causal contract factors through

`rho_(k,p) o L_q`.

Therefore any associative summary that is sound for the unique-minimal causal contract must factor through `Q_(k,p)`.

QED.

## 4. What Is Proved, and What Is Inherited

The theorem above proves a **causal factorization** result.

It does **not** re-prove the full finite-state exactness of `Q_(k,p)` from scratch in DAG language. That exactness is inherited from the protected-witness theorem already developed in the selective-memory note.

This distinction matters, and it is a strength rather than a weakness:

- the hard finite-state theorem is already on the table,
- the new work shows the first honest causal class embeds into it cleanly.

That is exactly the right kind of progress.

## 5. Consequences

### Corollary 1. Exact class count on the unique-minimal translated class

Because the causal contract factors through the exact protected-witness quotient, the relevant state budget is bounded by

`|Q_(k,p)| = sum_(d=0)^k (d + 2)^p`.

For `k = p`, this is the first exact causal provenance budget on the unique-minimal class.

### Corollary 2. Symmetry reduction

If witness names are semantically interchangeable and only the orbit of the witness family matters, then the state space further quotients to

`|Q_(k,p)^sym| = binom(k + p + 2, p + 1) - 1`.

This is the unique-minimal precursor to the multi-family case. It says:

> if causal semantics permits substitution among witnesses, memory drops by quotienting under that symmetry.

### Corollary 3. Bare `L2` remains too coarse even here

The factorization theorem is positive about `Q_(k,p)`, not a reprieve for bare `L2`.

The negative theorem from the earlier note still applies: bare `L2` preserves predecessor capacity but not witness identity.

So the repaired theory is genuinely stronger than the original dream:

- it explains failure,
- it gives the right replacement,
- it gives the replacement's exact cost.

## 6. Exhaustive Ordered-DAG Referee

The companion referee script

`scripts/referee/unique_minimal_referee.py`

checks the narrow theorem regime exhaustively on ordered DAGs up to six nodes.

### Scope

- all ordered DAGs on `n = 3..6`,
- all queries `(T, Y)` with a directed path `T -> ... -> Y`,
- unique, non-empty minimal adjustment sets,
- witness-faithful topological linearizations,
- contract instantiated at `k = |A*|`.

### Results

From `results/referee/unique-minimal-referee/unique_minimal_referee.json`:

- queries with directed treatment-outcome path: `325,404`
- unique non-empty minimal queries: `89,291`
- prefix-witness queries admitted by the theorem class: `89,291`
- exact `Q_(k,p)` recovery rate: `1.000`
- exact orbit recovery rate: `1.000`
- residual `Q_(k,p)` failures: `0`
- bare collision groups across distinct query instances: `10`
- bare collision groups with distinct witness signatures: `6`

The saved report is [unique_minimal_referee.md](../../../results/referee/unique-minimal-referee/unique_minimal_referee.md).

### Meaning of the referee

This does **not** prove the theorem. The proof is the translation argument above.

What it does prove empirically is that, on the small exhaustive world we can currently enumerate, the theorem class behaves exactly as the repaired theory predicts:

- bare summaries collide,
- witness-refined summaries recover the unique target,
- symmetry quotienting behaves cleanly,
- no counterexample appears inside the class.

That is the right relationship between proof and computation.

## 7. Why the Next Object Is Probably `Q_(k,𝒜)`

The unique-minimal class is only the first rung.

Once the minimal adjustment family is no longer unique, variable-level witness coordinates may be too fine in one direction and too coarse in another:

- too fine, because several witness names may be semantically interchangeable,
- too coarse, because overlapping admissible families are not just independent coordinates.

That is where the adjustment-family quotient appears naturally.

Let `𝒜` be the hypergraph of admissible minimal adjustment sets. Then the next likely object is a contract state that tracks survival of admissible witness **families**, not merely witness variables:

`Q_(k,𝒜)`.

If `Q_(k,p)` is exact on the unique-minimal class and `Q_(k,𝒜)` is needed beyond it, that is not a failure. It is the quotient ladder inside causal memory itself.

## 8. Limits

This note is intentionally narrow.

It does not yet prove:

1. a full Pearl-level bridge for arbitrary identifiable queries,
2. exact causal minimality beyond the translated protected-witness class,
3. the final quotient for overlapping minimal adjustment families.

What it **does** prove is the first exact positive theorem on a real causal class.

That is the correct next step.

## 9. Takeaways

1. The first positive causal theorem is a factorization theorem, not a bare-recovery theorem.
2. The correct state object on the unique-minimal class is inherited from the protected-witness quotient `Q_(k,p)`.
3. On exhaustive ordered DAGs up to six nodes, the theorem class shows zero `Q_(k,p)` failures and persistent bare collisions.
4. The next rung is almost certainly the adjustment-family quotient `Q_(k,𝒜)`.

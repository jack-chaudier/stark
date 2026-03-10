# Family Memory: Contract And Runtime

## Thesis

The next exact object was not the one we expected.

The overlapping-family search does show that causal memory becomes hypergraph-valued, but only at one layer of the problem.

The clean result from the new exact search is:

> overlapping minimal adjustment families force a hypergraph-valued contract parameter, but on every fixed family `A` realized by the current small-world scan the exact runtime quotient still collapses to `depth + completed-variable set`.

So `Q_(k, A)` now looks two-layered rather than uniformly hypergraph-valued.

## Source Basis

This note uses only the local artifacts generated in the workspace:

- [witness-faithful-factorization.md](witness-faithful-factorization.md)
- [finite-probe-quotient-tower.md](finite-probe-quotient-tower.md)
- [separator-closure-and-family-memory.md](separator-closure-and-family-memory.md)
- [overlapping_adjustment_families.md](../../results/overlapping_adjustment_families.md)
- [overlapping_adjustment_families.json](../../results/overlapping_adjustment_families.json)
- [family_memory_exact_search.md](../../results/family_memory_exact_search.md)
- [family_memory_exact_search.json](../../results/family_memory_exact_search.json)

## 1. What The New Search Actually Tested

The experiment separated two questions that had been bundled together.

### Contract layer

Different overlapping families `A` were extracted from the exhaustive small-DAG scan and normalized up to relabeling of the witness universe.

Here the question is:

- which family-level summaries distinguish different overlapping contracts,
- whether the raw antichain is really needed,
- and how many survivor-subset probes are needed before the contract becomes exact.

### Runtime layer

For each fixed normalized family `A`, the existing witness semigroup was reused with:

- `k = max |F|`,
- `p = |union(A)|`,
- runtime outputs given by the surviving adjustment family after composition.

Here the question is different:

- once `A` is fixed, what dynamic state is needed to preserve answer behavior,
- what is needed to preserve completed-variable identity,
- and what is needed to preserve exact surviving-family behavior.

That split turned out to matter.

## 2. The Contract Layer Really Is Hypergraph-Valued

Across the small-world scan there are `52` normalized overlapping family worlds:

- `(k=2, p=3)`: `3`,
- `(k=2, p=4)`: `31`,
- `(k=3, p=4)`: `18`.

The exact contract-level result is negative for every coarse summary tested:

- `union_core_size`: `20` summaries, `7` mixed classes,
- `degree_signature`: `7` summaries, `7` mixed classes,
- `intersection_signature`: `7` summaries, `7` mixed classes,
- `orbit`: `7` summaries, `7` mixed classes,
- `full_antichain`: `52` summaries, `0` mixed classes.

So across different overlapping contracts, the antichain really is doing essential work.

This confirms the earlier intuition from the explicit counterexamples:

- `n5_m732` with family `{ {0,1}, {0,2} }`,
- `n5_m746` with family `{ {0,1}, {1,2} }`.

They live on the same witness universe, but under survivor set `{0,2}` one family survives and the other does not.
Coordinate-wise witness identity is therefore too coarse at the contract layer.

## 3. Full Contract Profiles Collapse, But Teaching Complexity Does Not

There is a second exact fact that is easy to miss.

With the **full** survivor-subset probe bank, the contract profiles all become exact:

- family profiles: `52`,
- variable profiles: `52`,
- answer profiles: `52`.

So the contract-level difference is not a quotient-size gap once every subset probe is available.
It is a **teaching-complexity** gap.

Exact minimal probe bases on the normalized family worlds are:

- `(k=2, p=3)`: answer basis `2`, variable basis `2`, family basis `1`,
- `(k=2, p=4)`: answer basis `9`, variable basis `5`, family basis `1`,
- `(k=3, p=4)`: answer basis `8`, variable basis `3`, family basis `1`.

In every tested group, a single full-union family probe already identifies the contract, while answer-only and variable-only teaching sets are much larger.

So overlap raises a new exact question:

> not only what the contract is, but how many probes are needed to teach it through a chosen observational channel.

## 4. The Runtime Layer Did Not Become Hypergraph-Valued

This is the strongest surprise in the new pass.

For every normalized overlapping family realized by the small-world scan, the exact runtime family quotient matched the candidate state:

`(depth, completed-variable set)`

with no residual failures on the tested worlds.

Observed exact runtime counts by `(k,p)` are:

- `(2,3) -> 10`,
- `(2,4) -> 18`,
- `(3,4) -> 19`.

These match the simple law:

`runtime_family_count = k + 2^p`

on the tested grid.

The representative worlds show the same pattern:

- `A_path_k2_p3`: answer `6`, variable `10`, family `10`,
- `A_star_k2_p4`: answer `6`, variable `18`, family `18`,
- `A_mixed_k3_p4`: answer `11`, variable `19`, family `19`.

Candidate summaries fail in a structured way:

- `completed_only`: not exact,
- `current_family`: not exact,
- `depth_family`: not exact,
- `depth_saturation_profile`: exact,
- `depth_completed`: exact.

So on the scanned fixed-`A` worlds, the hypergraph lives in the contract parameter, not in a larger runtime state.

## 5. The Family Tower Exists, But It Collapses One Rung

The runtime tower is now measured directly.

For the representative worlds:

- `A_path_k2_p3`: answer `2.585` bits, variable `3.322`, family `3.322`,
- `A_star_k2_p4`: answer `2.585` bits, variable `4.170`, family `4.170`,
- `A_mixed_k3_p4`: answer `3.459` bits, variable `4.248`, family `4.248`.

So there is a real **answer-to-family shelf**:

- `(2,3)`: `0.737` bits,
- `(2,4)`: `1.000` to `1.585` bits,
- `(3,4)`: `0.788` bits.

But there is **no extra variable-to-family threshold gap** on the tested worlds:

- variable bits = family bits everywhere in the scan.

That is the cleanest tower statement we currently have:

1. answerability is cheaper than preserving the surviving family,
2. preserving the surviving family is not more expensive than preserving completed-variable identity once the contract is fixed.

## 6. The Smallest Exact Family Frontier

The exact frontier on `A_path_k2_p3` shows the same layered story dynamically.

Under forced decoding:

- at `3` bits, answer accuracy is already `1.000`,
- variable fidelity is `0.988`,
- family fidelity is `0.991`,
- exact recovery appears only at `4` bits.

Under breach decoding:

- all three channels move together below threshold,
- and exactness returns only at `4` bits.

So the family shelf is real against the answer channel.
But in the smallest exact world, family fidelity is not harder than variable fidelity at the pointwise frontier; if anything, it is slightly easier.

That is consistent with the quotient result:

- family and variable need the same exact threshold,
- but they are different output channels and can degrade differently before that threshold.

## 7. What Is Exact, Observed, And Still Open

### Exact in the current artifacts

1. The `52` normalized overlapping family worlds and their contract collisions.
2. Failure of all tested coarse contract summaries except the full antichain.
3. Exact contract teaching-set sizes on the scanned `(k,p)` groups.
4. Exact runtime family quotients on every normalized family realized by the scan.
5. The smallest fixed-`A` exact frontier on `A_path_k2_p3`.

### Observed but not yet proved in general

1. `runtime_family_count = k + 2^p` on the tested overlapping worlds.
2. `Q_runtime(A) = (depth, completed-variable set)` for every normalized family in the scan.
3. Variable-runtime threshold equals family-runtime threshold on the tested grid.

### Still open

1. A general proof of the runtime collapse law.
2. Whether larger overlapping families outside the current scan force a genuinely hypergraph-valued runtime state.
3. A smaller exact contract normal form than the raw antichain, if one exists.
4. A compositional theorem that integrates contract teaching complexity with runtime memory.

## Takeaway

The cleanest sentence after this pass is:

> overlap forces hypergraph memory at the level of the contract, but not yet at the level of fixed-contract runtime state.

That is not weaker than the earlier expectation.
It is sharper.

It says the next exact causal memory object is probably not a single monolithic `Q_(k, A)`.
It is more likely a two-layer object:

- a hypergraph-valued contract parameter that specifies which families count as admissible witnesses,
- and a universal runtime quotient that tracks depth plus completed-variable identity once that contract is fixed.

If that survives the next worlds, then the real new causal complexity is not “runtime hypergraph state everywhere.”
It is the split between:

- what must be remembered to know the contract,
- and what must be remembered to execute it exactly.

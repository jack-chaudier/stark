# Runtime Collapse Boundary

## Thesis

The new antichain sweep moves the boundary question from combinatorics to semantics.

The exact search no longer supports the idea that runtime collapse might fail merely because we left the DAG-realizable world.
It says something sharper:

> under the current binary-completion semantics, arbitrary full-union antichains still collapse to a universal runtime quotient, while contract complexity and teaching complexity remain genuinely larger; the first runtime break appears only after the family readout is semantically enriched.

So the present boundary is not:

- DAG-realizable versus arbitrary antichain,
- or contract hypergraph versus runtime hypergraph.

It is:

- binary completion versus enriched completion.

## Source Basis

This note uses only local artifacts already generated in the workspace:

- [family-memory-contract-and-runtime.md](family-memory-contract-and-runtime.md)
- [finite-probe-quotient-tower.md](finite-probe-quotient-tower.md)
- [separator-closure-and-family-memory.md](separator-closure-and-family-memory.md)
- [overlapping_adjustment_families.md](../../results/overlapping_adjustment_families.md)
- [family_memory_exact_search.md](../../results/family_memory_exact_search.md)
- [runtime_collapse_boundary.md](../../results/runtime_collapse_boundary.md)
- [runtime_collapse_boundary.json](../../results/runtime_collapse_boundary.json)

## 1. The Search Expanded Far Beyond The DAG-Realized Class

The previous family-memory pass only touched `52` normalized overlapping families extracted from the DAG scan.

The new boundary scan replaces that restricted source class with exact full-union antichain classes on `[p]`, grouped by exact maximal edge size `k`, over:

- `p <= 5`,
- `k <= 3`.

That yields `11` exact `(p,k)` classes and `6336` exact antichains in total.

The largest classes are already far beyond the DAG-realized sample:

- `(p=5, k=2)`: `1023` exact antichains,
- `(p=5, k=3)`: `5188` exact antichains.

So the runtime test is no longer a small perturbation of the old scan.
It is a real combinatorial expansion.

## 2. Arbitrary Antichains Still Do Not Break The Current Runtime Quotient

The exact runtime result is now uniform across the scanned classes.

For every exact `(p,k)` class:

- factorization through `(depth, completed-variable set)` holds,
- runtime collapse failures are `0`,
- family-runtime and variable-runtime counts still agree,
- the exact family-runtime count is `k + 2^p`.

The clean group table is:

- `(2,1)`: `5` family states,
- `(2,2)`: `6`,
- `(3,2)`: `10`,
- `(4,2)`: `18`,
- `(4,3)`: `19`,
- `(5,2)`: `34`,
- `(5,3)`: `35`,

with the trivial `k=1` ladders fitting the same law.

So the earlier collapse was not an accident of DAG realizability.
It survives exhaustive passage to arbitrary antichains on the tested grid.

## 3. Why The Collapse Survives

The key point is family-independent.

Fix a left state `(d,c)` and a right continuation `(e,r)`.
Under the current witness semigroup:

- a coordinate that is already maximal stays maximal,
- a coordinate that is not yet maximal becomes maximal exactly when the right coordinate crosses the depth-controlled threshold `k - d`.

So for future behavior, every non-maximal coordinate is interchangeable.
The continuation only sees:

- the current depth `d`,
- and which coordinates are already at `k`.

That gives the factorization:

`left state -> (depth, completed-variable set) -> future completed sets -> future family outputs`.

On the exact full-union antichain classes, that summary is not only sufficient.
It is exact.

The separation proof is also simple in spirit:

- different depths are separated by continuations that complete one whole edge at one depth but not the other,
- different completed-variable sets are separated by continuations that finish an edge using one already-complete coordinate as the missing witness.

That is why the current semantics produce a universal runtime quotient even when the contract itself is hypergraph-valued.

## 4. The Runtime Shelf Remains Real

The collapse does **not** mean the answer channel and family channel coincide.

The arbitrary-antichain scan still shows answer-to-family shelves on the exact classes:

- `(p=5, k=2)`: answer counts range from `6` to `15` against `34` family states,
- `(p=5, k=3)`: answer counts range from `11` to `26` against `35` family states,
- `(p=4, k=2)`: answer counts range from `6` to `12` against `18` family states.

So the runtime tower under the current semantics is now:

- family = variable,
- answer < family in general.

The new fact is not that the shelf disappears.
It is that the variable-to-family rung collapses even on arbitrary antichains.

## 5. Teaching Complexity Is Exact And Smaller Than Contract Complexity

The contract layer still does not collapse.
But the expanded exact classes now expose a clean teaching-complexity structure.

### Answer bases

On every nontrivial scanned exact `(p,k)` class, the exact minimal answer basis has size

`sum_{r=1}^k C(p,r)`.

Examples:

- `(3,2) -> 6`,
- `(4,2) -> 10`,
- `(4,3) -> 14`,
- `(5,2) -> 15`,
- `(5,3) -> 25`.

These answer bases are exact and globally essential on every nontrivial scanned class.

### Variable bases

The variable channel is cheaper than the answer channel, but it is not completely uniform.

The exact minima are:

- `(3,2) -> 3`,
- `(4,2) -> 6`,
- `(5,2) -> 10`,
- `(5,3) -> 20`,
- `(4,3) -> 7`.

So the clean law

`sum_{r=2}^k C(p,r)`

is exact on every nontrivial scanned class except the small exceptional case `(4,3)`, where exhaustive exact search compresses the minimum from `10` to `7`.

That exception is important.
It shows that teaching complexity is not just a smooth closed form.
Small symmetry effects can still lower the true minimum.

### Family bases

On every nontrivial scanned class, the family channel is teachable with a single full-union family probe.

So the contract/probe hierarchy now looks like:

- raw antichain for intrinsic contract identity,
- exact answer and variable teaching signatures for observational identity,
- universal fixed-contract runtime quotient under current semantics.

## 6. The First Runtime Break Is Semantic, Not Combinatorial

Since arbitrary antichains do not break runtime collapse, the next question is forced:

what semantic perturbation breaks it first?

The smallest exact hit found in the current scan is additive partial activation.

Keep:

- the same witness carrier,
- the same composition law.

Change only the family readout to:

`Out_H(d,c) = { F in A : sum_{i in F} u_i >= H_F }`

with `u_i = c_i + 1` for non-`BOT` coordinates and `0` for `BOT`.

The smallest same-now / future-separate counterexample is:

- class `(p=2, k=2)`,
- family `{ {1,2} }`,
- threshold `H_{12} = 2`,
- states `s = (0,(-1,-1))`, `t = (0,(-1,0))`,
- continuation `r = (0,(0,-1))`.

Here:

- `s` and `t` have the same old summary `(depth, completed-variable set) = (0, emptyset)`,
- `Out_H(s) = Out_H(t) = emptyset`,
- but `Out_H(s ∘ r) = emptyset` while `Out_H(t ∘ r) = { {1,2} }`.

So the first runtime break is not an overlap-specific hypergraph effect.
It is a coordinate-level partial-progress effect.

That matters.
It means the current universal collapse is a theorem of the binary-completion semantics, not a theorem of family structure alone.

## 7. What Is Exact, Observed, And Open

### Exact in the current artifacts

1. The arbitrary-antichain scan on the `11` exact `(p,k)` classes.
2. Zero runtime-collapse failures on those classes under the current semantics.
3. Exact answer-basis minima on all nontrivial scanned classes.
4. Exact variable-basis minima on the scanned classes, including the `(4,3)` exceptional collapse to `7`.
5. The first same-now / future-separate additive counterexample.

### Honest theorem templates suggested by the data

1. Under current binary completion, any family output depending only on the post-composition completed-variable set factors through `(depth, completed-variable set)`.
2. On the exact full-union antichain classes scanned here, that factorization is exact.

These statements now have both a proof sketch and exhaustive support on the tested grid.

### Still open

1. A clean general proof that the runtime count is always `k + 2^p` for every full-union antichain under the current semantics.
2. A conceptual explanation of the `(p=4, k=3)` variable-teaching exception.
3. The first semantic enrichment that forces genuinely overlap-specific or hypergraph-specific runtime memory, rather than merely coordinate-level partial-progress memory.
4. Whether there is an intrinsic contract normal form smaller than the raw antichain.

## Takeaway

The new boundary result is:

> hypergraph complexity enters the present system in the contract and in the probes before it enters the runtime automaton.

Under the current binary-completion semantics:

- arbitrary antichains still collapse,
- answerability is still cheaper than full family preservation,
- and the family channel still does not outrun the variable channel at runtime.

Only after the readout is semantically enriched does the old runtime quotient break.

So the right next theorem is no longer “do arbitrary antichains break collapse?”
That question is now answered on the tested grid.

The right next theorem is:

- why binary completion forces universal runtime collapse,
- and what the smallest genuinely hypergraph-specific semantic enrichment must remember once that theorem stops applying.

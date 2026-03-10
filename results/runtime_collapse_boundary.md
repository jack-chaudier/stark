# Runtime Collapse Boundary

This report separates three boundary questions:

1. whether arbitrary antichains break the current runtime collapse,
2. what the exact teaching laws are on the same exact `(p,k)` contract classes,
3. which minimal semantic enrichment breaks the collapse first.

## Aggregate result

- exact antichain classes scanned: `11`
- total exact antichains scanned: `6336`
- runtime collapse failures under current semantics: `0`
- current factorization lemma verified on every scanned `(p,k)`: `True`
- first semantic break found: `additive_partial_activation`

## Current Semantics: Arbitrary Antichains

The current family readout depends only on the completed-variable set after composition. On the exact antichain classes scanned here, that induces a universal runtime collapse.

### Group table

| group | families | family states | family bits | answer count range | answer bit range | shelf width range | collapse failures |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `(p=2, k=1)` | `1` | `5` | `2.322` | `[3, 3]` | `(1.585, 1.585)` | `(0.737, 0.737)` | `0` |
| `(p=2, k=2)` | `1` | `6` | `2.585` | `[6, 6]` | `(2.585, 2.585)` | `(0.000, 0.000)` | `0` |
| `(p=3, k=1)` | `1` | `9` | `3.170` | `[3, 3]` | `(1.585, 1.585)` | `(1.585, 1.585)` | `0` |
| `(p=3, k=2)` | `7` | `10` | `3.322` | `[6, 7]` | `(2.585, 2.807)` | `(0.515, 0.737)` | `0` |
| `(p=3, k=3)` | `1` | `11` | `3.459` | `[11, 11]` | `(3.459, 3.459)` | `(0.000, 0.000)` | `0` |
| `(p=4, k=1)` | `1` | `17` | `4.087` | `[3, 3]` | `(1.585, 1.585)` | `(2.503, 2.503)` | `0` |
| `(p=4, k=2)` | `63` | `18` | `4.170` | `[6, 12]` | `(2.585, 3.585)` | `(0.585, 1.585)` | `0` |
| `(p=4, k=3)` | `49` | `19` | `4.248` | `[11, 15]` | `(3.459, 3.907)` | `(0.341, 0.788)` | `0` |
| `(p=5, k=1)` | `1` | `33` | `5.044` | `[3, 3]` | `(1.585, 1.585)` | `(3.459, 3.459)` | `0` |
| `(p=5, k=2)` | `1023` | `34` | `5.087` | `[6, 15]` | `(2.585, 3.907)` | `(1.181, 2.503)` | `0` |
| `(p=5, k=3)` | `5188` | `35` | `5.129` | `[11, 26]` | `(3.459, 4.700)` | `(0.429, 1.670)` | `0` |

### Boundary statement

No arbitrary-antichain counterexample appeared on the scanned exact classes.

The strongest honest theorem template suggested by the computation is:

> under the current binary-completion semantics, any family output that depends only on the surviving completed-variable set factors through `(depth, completed-variable set)`, and on the exact full-union antichain classes that summary is itself exact.

So the current boundary is not DAG-realizability versus arbitrary antichain. It is the semantics of completion itself.

## Contract Complexity And Teaching Complexity

The contract layer behaves differently from the runtime layer. The antichain is still the exact contract object, but the exact teaching bases on the exact `(p,k)` antichain classes follow much smaller laws.

| group | families | answer basis | variable basis | family basis | answer exact/essential | variable exact/essential |
| --- | --- | --- | --- | --- | --- | --- |
| `(p=2, k=1)` | `1` | `0` | `0` | `0` | `True/False` | `True/False` |
| `(p=2, k=2)` | `1` | `0` | `0` | `0` | `True/False` | `True/False` |
| `(p=3, k=1)` | `1` | `0` | `0` | `0` | `True/False` | `True/False` |
| `(p=3, k=2)` | `7` | `6` | `3` | `1` | `True/True` | `True/True` |
| `(p=3, k=3)` | `1` | `0` | `0` | `0` | `True/False` | `True/False` |
| `(p=4, k=1)` | `1` | `0` | `0` | `0` | `True/False` | `True/False` |
| `(p=4, k=2)` | `63` | `10` | `6` | `1` | `True/True` | `True/True` |
| `(p=4, k=3)` | `49` | `14` | `7` | `1` | `True/True` | `True/True` |
| `(p=5, k=1)` | `1` | `0` | `0` | `0` | `True/False` | `True/False` |
| `(p=5, k=2)` | `1023` | `15` | `10` | `1` | `True/True` | `True/True` |
| `(p=5, k=3)` | `5188` | `25` | `20` | `1` | `True/True` | `True/True` |

### Teaching laws on exact `(p,k)` classes

- answer basis size: `sum_{r=1}^k C(p,r)` on every nontrivial scanned group, and `0` on the trivial single-family classes
- variable basis size: `sum_{r=2}^k C(p,r)` on every scanned nontrivial group except `(p=4, k=3)`, where exhaustive exact search drops the minimum to `7`
- family basis size: `1` on every nontrivial scanned group, and `0` on the trivial single-family classes

The listed answer bases are exact and globally essential on every nontrivial scanned group. The listed variable bases are exact everywhere in the scan, and minimal after an exhaustive correction on the small exceptional `(p=4, k=3)` class.

## Contract Normal Forms

Raw antichains remain exact, but the expanded scan now separates intrinsic contract summaries from observational normal forms.

- coarse summaries such as `union/core/size`, degree signatures, intersection signatures, and orbit summaries still fail in the nontrivial groups,
- full antichains stay exact,
- answer-basis signatures and variable-basis signatures give exact observational normal forms on the exact `(p,k)` classes.

So the antichain still looks like the right intrinsic contract object, while the teaching signatures look like the right observational normal forms.

## First Semantic Break

The first tested enrichment that breaks runtime collapse is additive partial activation:

`Out_H(d,c) = { F in A : sum_{i in F} (c_i + 1 if c_i != BOT else 0) >= H_F }`

This keeps the same witness carrier and the same composition law. It only changes the family readout.

- smallest counterexample: `(p=2, k=2)`
- family: `[[1, 2]]`
- thresholds: `{'1,2': 2}`
- shared old summary: `{'depth': 0, 'completed_variables': []}`

This break is coordinate-level rather than genuinely hypergraph-specific: a single-edge family already suffices. So the first semantic perturbation that breaks the old runtime quotient does not yet force overlapping-family hypergraph memory.

## Interpretation

The cleanest boundary result in this pass is:

1. Contract complexity is genuinely hypergraph-valued.
2. Teaching complexity is smaller and follows exact probe-basis laws on the exact antichain classes.
3. Runtime complexity under the current semantics is universal and variable-based even on arbitrary antichains.
4. The first break is semantic, not combinatorial: additive partial progress destroys the old runtime collapse before overlap itself does.

So hypergraph complexity enters the present system first in the contract, then in the probes, and only later in runtime once the completion semantics are enriched.

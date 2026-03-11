# Committed Resource Carrier Boundary

## Question

This quick experiment changes the witness carrier itself rather than only the readout.
Each variable can be committed to at most one incident family edge, and segments compose only when their domains are disjoint.
The question is whether overlap becomes computationally necessary at runtime the moment witness commitment moves into the carrier.

## Setup

- World: exact arbitrary full-union antichains on `[p]` with `p <= 4` and `k <= 3`.
- Carrier state: a partial assignment `variable -> incident family edge`, with `-1` meaning uncommitted.
- Composition: disjoint-domain union; incompatible overlaps are recorded as `NA` in continuation rows.
- Variable channel: committed-variable domain.
- Family channel: residual family profile, i.e. the live edges together with the variables they still need.
- Answer channel: whether some edge is already complete after composition.

## Main Exact Findings

1. The scan covers `124` exact full-union antichains on `[p]` with `p <= 4` and `k <= 3`.
   Raw carrier size is exact by construction: `|S_A| = product_v (deg_A(v) + 1)`.
2. The smallest runtime family gap appears immediately at `{{1,2}, {1,3}}` with `(p=3, k=2)`.
   Counts: raw `12`, variable `8`, family `11`.
   Bits: raw `3.585`, variable `3.000`, family `3.459`.
3. On the full scanned grid, the variable quotient still collapses exactly to `2^p`.
4. On the full scanned grid, `family_row_count > variable_row_count` if and only if the family overlaps.
5. The tested coarser summaries all fail on the smallest overlap example: `domain_only`, `edge_load_vector`, `edge_load_multiset`, and `residual_profile`.
6. `full_assignment` is exact on the scan, so this carrier change breaks the old binary-completion coordinate law but does not yet force a genuinely global non-coordinate runtime state.

## Smallest Counterexample

- Family: `{{1,2}, {1,3}}`
- Shared domain: `[1]`
- Left state: `{1->(1, 2)}`
- Alternate state: `{1->(1, 3)}`
- Future segment: `{3->(1, 3)}`
- Left future family: `((2,),)`
- Alternate future family: `((),)`

This is the first place where the old domain-only coordinate summary fails because a shared witness has already been committed to different overlapping families.

## Representative Families

| Label | Family | Overlap | Raw states | Variable rows | Family rows | Bits (raw / variable / family) |
| --- | --- | --- | --- | --- | --- | --- |
| `disjoint_pair` | `{{1,2}, {3}}` | `False` | `8` | `8` | `8` | `3.000 / 3.000 / 3.000` |
| `overlap_path` | `{{1,2}, {1,3}}` | `True` | `12` | `8` | `11` | `3.585 / 3.000 / 3.459` |
| `triangle` | `{{1,2}, {1,3}, {2,3}}` | `True` | `27` | `8` | `21` | `4.755 / 3.000 / 4.392` |
| `overlap_star` | `{{1,2}, {1,3}, {1,4}}` | `True` | `32` | `16` | `27` | `5.000 / 4.000 / 4.755` |

## Group Scan Summary

| Group | Families | Overlap families | Family > variable | Variable rows = 2^p | Gap iff overlap | Max family gap (bits) |
| --- | --- | --- | --- | --- | --- | --- |
| `(p=2, k=1)` | `1` | `0` | `0` | `True` | `True` | `0.000` |
| `(p=2, k=2)` | `1` | `0` | `0` | `True` | `True` | `0.000` |
| `(p=3, k=1)` | `1` | `0` | `0` | `True` | `True` | `0.000` |
| `(p=3, k=2)` | `7` | `4` | `4` | `True` | `True` | `1.392` |
| `(p=3, k=3)` | `1` | `0` | `0` | `True` | `True` | `0.000` |
| `(p=4, k=1)` | `1` | `0` | `0` | `True` | `True` | `0.000` |
| `(p=4, k=2)` | `63` | `54` | `54` | `True` | `True` | `2.883` |
| `(p=4, k=3)` | `49` | `45` | `45` | `True` | `True` | `2.150` |

## Candidate Exactness On The Smallest Overlap Example

| Candidate summary | Summary count | Mixed classes | Exact |
| --- | --- | --- | --- |
| `domain_only` | `8` | `3` | `False` |
| `domain_size` | `4` | `2` | `False` |
| `edge_load_vector` | `8` | `3` | `False` |
| `edge_load_multiset` | `5` | `3` | `False` |
| `residual_profile` | `7` | `3` | `False` |
| `full_assignment` | `12` | `0` | `True` |

## Interpretation

This experiment is a real boundary push.
Under binary completion, overlap changed the contract but not the fixed-carrier runtime quotient.
Under committed allocation, overlap becomes visible in the runtime family quotient itself.
The old `2^p` variable collapse survives, but it is no longer sufficient whenever the family overlaps.

The boundary is still honest:

- overlap is now computationally active at runtime,
- the old coordinate law is broken,
- but the tested exact runtime state is still captured by the full assignment carrier rather than by a genuinely global hypergraph-only state.

So this quick push does not yet prove the final runtime-hypergraph theorem.
It does show that changing the carrier is enough to make overlap matter at runtime immediately.

## Artifacts

- JSON: [resource_carrier_boundary.json](resource_carrier_boundary.json)
- Figure: [resource_carrier_boundary.svg](resource_carrier_boundary.svg)

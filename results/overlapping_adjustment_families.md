# Overlapping Adjustment Families

This report is the first explicit search step toward a family-level causal memory object `Q_(k, A)`.

## Aggregate signal

- first overlaps appear at `n = 5`
- overlap counts by `n`: `{5: 34, 6: 6384}`

## Why variable-wise summaries are too coarse

The current witness-coordinate quotient only remembers which named variables survive.
That is enough on the unique-minimal class, but it is not enough once multiple overlapping minimal adjustment sets are admissible.

- `n5_m732` has family `[[0, 1], [0, 2]]` on universe `[0, 1, 2]`.
- `n5_m746` has family `[[0, 1], [1, 2]]` on the same universe.
- In both cases every variable in the universe matters individually, so a flat survivor vector cannot tell the two apart.
- But under the survivor set `[0, 2]`, the first family leaves `[[0, 2]]` while the second leaves `[]`.

So family survival is genuinely hypergraph-valued: the exact object must remember admissible witness families, not only which variables are available one by one.

## Small explicit examples

- `n5_m732` query `(3, 4)` -> family `[[0, 1], [0, 2]]`, union `[0, 1, 2]`, core `[0]`
- `n5_m733` query `(3, 4)` -> family `[[0, 1], [0, 2]]`, union `[0, 1, 2]`, core `[0]`
- `n5_m734` query `(3, 4)` -> family `[[0, 1], [0, 2]]`, union `[0, 1, 2]`, core `[0]`
- `n5_m735` query `(3, 4)` -> family `[[0, 1], [0, 2]]`, union `[0, 1, 2]`, core `[0]`
- `n5_m746` query `(3, 4)` -> family `[[0, 1], [1, 2]]`, union `[0, 1, 2]`, core `[1]`
- `n5_m747` query `(3, 4)` -> family `[[0, 1], [1, 2]]`, union `[0, 1, 2]`, core `[1]`
- `n5_m762` query `(3, 4)` -> family `[[0, 1], [1, 2]]`, union `[0, 1, 2]`, core `[1]`
- `n5_m763` query `(3, 4)` -> family `[[0, 1], [1, 2]]`, union `[0, 1, 2]`, core `[1]`

## Experimental implication

A compact exploratory state representation for this regime is the antichain hypergraph of minimal adjustment families itself, or an equivalent family-survival function on survivor subsets.

The current search does not prove that the hypergraph antichain is minimal.
It does show that coordinate-wise witness availability is already too coarse on the smallest overlapping cases.

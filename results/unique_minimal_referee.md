# Unique-Minimal Referee

This report exhaustively checks the narrow theorem regime implemented by
`scripts/unique_minimal_referee.py`.

## Scope

- Ordered DAGs up to `n = 6`
- Queries `(T, Y)` with a directed path `T -> ... -> Y`
- Unique, non-empty minimal adjustment sets
- Witness-faithful topological linearizations
- Causal contract instantiated at `k = |A*|`

## Aggregate counts

- Queries with directed treatment-outcome path: `325404`
- Unique non-empty minimal queries: `89291`
- Prefix-witness queries admitted by the theorem class: `89291`
- Exact `Q_(k,p)` recovery rate: `1.000`
- Exact orbit recovery rate: `1.000`
- Residual `Q_(k,p)` failures: `0`
- Bare collision groups across distinct query instances: `10`
- Bare collision groups with distinct witness signatures: `6`

## By k

- `k = 1`: `72389` records, prefix length range `1` to `4`
- `k = 2`: `15182` records, prefix length range `2` to `4`
- `k = 3`: `1656` records, prefix length range `3` to `4`
- `k = 4`: `64` records, prefix length range `4` to `4`

## Collision examples

- `k = 1`, bare state `{'weights': [1, 1], 'd_total': 2}`
  query `n4_m11 : (1, 2)` -> witnesses `(0,)`, word `('W0', 'N', 'T')`
  query `n4_m56 : (2, 3)` -> witnesses `(1,)`, word `('W1', 'N', 'T')`
- `k = 1`, bare state `{'weights': [1, 1], 'd_total': 3}`
  query `n5_m19 : (1, 2)` -> witnesses `(0,)`, word `('W0', 'N', 'N', 'T')`
  query `n5_m176 : (2, 3)` -> witnesses `(1,)`, word `('W1', 'N', 'N', 'T')`
  query `n5_m896 : (3, 4)` -> witnesses `(2,)`, word `('W2', 'N', 'N', 'T')`
- `k = 2`, bare state `{'weights': [1, 1, 1], 'd_total': 3}`
  query `n5_m182 : (2, 3)` -> witnesses `(0, 1)`, word `('W0', 'W1', 'N', 'T')`
  query `n5_m908 : (3, 4)` -> witnesses `(0, 2)`, word `('W0', 'W2', 'N', 'T')`
  query `n5_m992 : (3, 4)` -> witnesses `(1, 2)`, word `('W1', 'W2', 'N', 'T')`
- `k = 1`, bare state `{'weights': [1, 1], 'd_total': 4}`
  query `n6_m35 : (1, 2)` -> witnesses `(0,)`, word `('W0', 'N', 'N', 'N', 'T')`
  query `n6_m608 : (2, 3)` -> witnesses `(1,)`, word `('W1', 'N', 'N', 'N', 'T')`
  query `n6_m5632 : (3, 4)` -> witnesses `(2,)`, word `('W2', 'N', 'N', 'N', 'T')`
  query `n6_m28672 : (4, 5)` -> witnesses `(3,)`, word `('W3', 'N', 'N', 'N', 'T')`
- `k = 2`, bare state `{'weights': [1, 1, 1], 'd_total': 4}`
  query `n6_m614 : (2, 3)` -> witnesses `(0, 1)`, word `('W0', 'W1', 'N', 'N', 'T')`
  query `n6_m5644 : (3, 4)` -> witnesses `(0, 2)`, word `('W0', 'W2', 'N', 'N', 'T')`
  query `n6_m5824 : (3, 4)` -> witnesses `(1, 2)`, word `('W1', 'W2', 'N', 'N', 'T')`
  query `n6_m28696 : (4, 5)` -> witnesses `(0, 3)`, word `('W0', 'W3', 'N', 'N', 'T')`
- `k = 3`, bare state `{'weights': [1, 1, 1, 1], 'd_total': 4}`
  query `n6_m5836 : (3, 4)` -> witnesses `(0, 1, 2)`, word `('W0', 'W1', 'W2', 'N', 'T')`
  query `n6_m29080 : (4, 5)` -> witnesses `(0, 1, 3)`, word `('W0', 'W1', 'W3', 'N', 'T')`
  query `n6_m31768 : (4, 5)` -> witnesses `(0, 2, 3)`, word `('W0', 'W2', 'W3', 'N', 'T')`
  query `n6_m32128 : (4, 5)` -> witnesses `(1, 2, 3)`, word `('W1', 'W2', 'W3', 'N', 'T')`

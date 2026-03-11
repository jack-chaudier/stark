# Separator Closure Experiment

This report measures how quickly the current right-bank observational quotient closes back up to the exact two-sided quotient once left separators are added explicitly.

## Takeaways

- `Q_(3,2)` starts at probe-joint `7` and reaches the canonical `54` after `3` added left actions.
- Its exact minimal basis is `[(1, (-1, -1)), (2, (-1, -1)), (3, (-1, -1))]`.
- Probe deficiency falls from `2.948` bits to `0.000` bits, while shelf width changes from `0.485` to `1.948` bits.
- `Q_(4,2)` starts at probe-joint `8` and reaches the canonical `90` after `4` added left actions.
- Its exact minimal basis is `[(1, (-1, -1)), (2, (-1, -1)), (3, (-1, -1)), (4, (-1, -1))]`.
- Probe deficiency falls from `3.492` bits to `0.000` bits, while shelf width changes from `0.415` to `2.170` bits.
- `Q_(5,3)` starts at probe-joint `13` and reaches the canonical `783` after `5` added left actions.
- Its exact minimal basis is `[(1, (-1, -1, -1)), (2, (-1, -1, -1)), (3, (-1, -1, -1)), (4, (-1, -1, -1)), (5, (-1, -1, -1))]`.
- Probe deficiency falls from `5.912` bits to `0.000` bits, while shelf width changes from `0.893` to `4.858` bits.

## Strategy Comparison

All three greedy policies were evaluated:

- `greedy_joint_gain`: maximize new probe-joint classes at each step.
- `greedy_pair_gain`: maximize resolved canonical-state pairs at each step.
- `greedy_info_gain`: maximize joint partition entropy at each step.

- `Q_(3,2)`: `greedy_info_gain` -> `[(2, (-1, -1)), (3, (-1, -1)), (1, (-1, -1))]`, `greedy_joint_gain` -> `[(3, (-1, -1)), (2, (-1, -1)), (1, (-1, -1))]`, `greedy_pair_gain` -> `[(2, (-1, -1)), (3, (-1, -1)), (1, (-1, -1))]`
- `Q_(3,2)` greedy path count: `2` distinct paths; exact minimal basis count: `1`.
- `Q_(4,2)`: `greedy_info_gain` -> `[(3, (-1, -1)), (4, (-1, -1)), (2, (-1, -1)), (1, (-1, -1))]`, `greedy_joint_gain` -> `[(4, (-1, -1)), (3, (-1, -1)), (2, (-1, -1)), (1, (-1, -1))]`, `greedy_pair_gain` -> `[(3, (-1, -1)), (2, (-1, -1)), (4, (-1, -1)), (1, (-1, -1))]`
- `Q_(4,2)` greedy path count: `3` distinct paths; exact minimal basis count: `1`.
- `Q_(5,3)`: `greedy_info_gain` -> `[(3, (-1, -1, -1)), (5, (-1, -1, -1)), (2, (-1, -1, -1)), (4, (-1, -1, -1)), (1, (-1, -1, -1))]`, `greedy_joint_gain` -> `[(5, (-1, -1, -1)), (4, (-1, -1, -1)), (3, (-1, -1, -1)), (2, (-1, -1, -1)), (1, (-1, -1, -1))]`, `greedy_pair_gain` -> `[(3, (-1, -1, -1)), (5, (-1, -1, -1)), (2, (-1, -1, -1)), (4, (-1, -1, -1)), (1, (-1, -1, -1))]`
- `Q_(5,3)` greedy path count: `2` distinct paths; exact minimal basis count: `1`.

## Exact Closure Frontiers

### `Q_(3,2)`

| separators | joint | answer | witness | unresolved pairs | deficiency bits | shelf width bits |
| --- | --- | --- | --- | --- | --- | --- |
| `0` | `7` | `5` | `7` | `294` | `2.948` | `0.485` |
| `1` | `21` | `9` | `21` | `98` | `1.363` | `1.222` |
| `2` | `38` | `12` | `38` | `22` | `0.507` | `1.663` |
| `3` | `54` | `14` | `54` | `0` | `0.000` | `1.948` |
| `4` | `54` | `14` | `54` | `0` | `0.000` | `1.948` |
| `5` | `54` | `14` | `54` | `0` | `0.000` | `1.948` |
| `6` | `54` | `14` | `54` | `0` | `0.000` | `1.948` |

### `Q_(4,2)`

| separators | joint | answer | witness | unresolved pairs | deficiency bits | shelf width bits |
| --- | --- | --- | --- | --- | --- | --- |
| `0` | `8` | `6` | `8` | `782` | `3.492` | `0.415` |
| `1` | `25` | `11` | `25` | `326` | `1.848` | `1.184` |
| `2` | `47` | `15` | `47` | `112` | `0.937` | `1.648` |
| `3` | `70` | `18` | `70` | `26` | `0.363` | `1.959` |
| `4` | `90` | `20` | `90` | `0` | `0.000` | `2.170` |
| `5` | `90` | `20` | `90` | `0` | `0.000` | `2.170` |
| `6` | `90` | `20` | `90` | `0` | `0.000` | `2.170` |
| `7` | `90` | `20` | `90` | `0` | `0.000` | `2.170` |

### `Q_(5,3)`

| separators | joint | answer | witness | unresolved pairs | deficiency bits | shelf width bits |
| --- | --- | --- | --- | --- | --- | --- |
| `0` | `13` | `7` | `13` | `58520` | `5.912` | `0.893` |
| `1` | `67` | `13` | `67` | `21261` | `3.547` | `2.366` |
| `2` | `180` | `18` | `180` | `6745` | `2.121` | `3.322` |
| `3` | `352` | `22` | `352` | `1792` | `1.153` | `4.000` |
| `4` | `565` | `25` | `565` | `341` | `0.471` | `4.498` |
| `5` | `783` | `27` | `783` | `0` | `0.000` | `4.858` |
| `6` | `783` | `27` | `783` | `0` | `0.000` | `4.858` |
| `7` | `783` | `27` | `783` | `0` | `0.000` | `4.858` |
| `8` | `783` | `27` | `783` | `0` | `0.000` | `4.858` |
| `9` | `783` | `27` | `783` | `0` | `0.000` | `4.858` |
| `10` | `783` | `27` | `783` | `0` | `0.000` | `4.858` |
| `11` | `783` | `27` | `783` | `0` | `0.000` | `4.858` |
| `12` | `783` | `27` | `783` | `0` | `0.000` | `4.858` |

## Observed Scaling Law

Across the full grid `k <= 5`, `p <= 3`, the minimal exact observational separator basis size matches `k` on every tested `Q_(k,p)` family.

| family | base joint | candidate actions | minimal basis size | minimal basis |
| --- | --- | --- | --- | --- |
| `Q_(1,1)` | `3` | `2` | `1` | `[[1, [-1]]]` |
| `Q_(2,1)` | `4` | `3` | `2` | `[[1, [-1]], [2, [-1]]]` |
| `Q_(3,1)` | `5` | `4` | `3` | `[[1, [-1]], [2, [-1]], [3, [-1]]]` |
| `Q_(4,1)` | `6` | `5` | `4` | `[[1, [-1]], [2, [-1]], [3, [-1]], [4, [-1]]]` |
| `Q_(5,1)` | `7` | `6` | `5` | `[[1, [-1]], [2, [-1]], [3, [-1]], [4, [-1]], [5, [-1]]]` |
| `Q_(1,2)` | `5` | `4` | `1` | `[[1, [-1, -1]]]` |
| `Q_(2,2)` | `6` | `5` | `2` | `[[1, [-1, -1]], [2, [-1, -1]]]` |
| `Q_(3,2)` | `7` | `6` | `3` | `[[1, [-1, -1]], [2, [-1, -1]], [3, [-1, -1]]]` |
| `Q_(4,2)` | `8` | `7` | `4` | `[[1, [-1, -1]], [2, [-1, -1]], [3, [-1, -1]], [4, [-1, -1]]]` |
| `Q_(5,2)` | `9` | `8` | `5` | `[[1, [-1, -1]], [2, [-1, -1]], [3, [-1, -1]], [4, [-1, -1]], [5, [-1, -1]]]` |
| `Q_(1,3)` | `9` | `8` | `1` | `[[1, [-1, -1, -1]]]` |
| `Q_(2,3)` | `10` | `9` | `2` | `[[1, [-1, -1, -1]], [2, [-1, -1, -1]]]` |
| `Q_(3,3)` | `11` | `10` | `3` | `[[1, [-1, -1, -1]], [2, [-1, -1, -1]], [3, [-1, -1, -1]]]` |
| `Q_(4,3)` | `12` | `11` | `4` | `[[1, [-1, -1, -1]], [2, [-1, -1, -1]], [3, [-1, -1, -1]], [4, [-1, -1, -1]]]` |
| `Q_(5,3)` | `13` | `12` | `5` | `[[1, [-1, -1, -1]], [2, [-1, -1, -1]], [3, [-1, -1, -1]], [4, [-1, -1, -1]], [5, [-1, -1, -1]]]` |

## Memory Stratigraphy Snapshot

| family | algebraic bits | empirical bits | probe-joint bits | probe-witness bits | probe-answer bits | deficiency | shelf width |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `M_3` | `3.807` | `3.807` | `2.322` | `0.000` | `2.322` | `1.485` | `0.000` |
| `Q_(3,2)` | `5.755` | `5.755` | `2.807` | `2.807` | `2.322` | `2.948` | `0.485` |
| `Q_(4,2)` | `6.492` | `6.492` | `3.000` | `3.000` | `2.585` | `3.492` | `0.415` |
| `Q_(5,3)` | `9.613` | `9.613` | `3.700` | `3.700` | `2.807` | `5.912` | `0.893` |
| `causal_referee` | `11.306` | `3.907` | `3.907` | `3.907` | `2.000` | `7.399` | `1.907` |

## Interpretation

The cleanest new invariant is not raw separator count. It is **closure rank**: the minimal number of observational left actions needed to close the current right-bank quotient back to the canonical quotient.

On the tested synthetic families, closure rank behaves like `k`, not like `p`. The canonical witness dimension still controls the size of the full quotient, but the number of missing left actions needed to close the current probe bank appears depth-indexed.

The second surprise is that better probes do not necessarily shrink the potential mirage interval. Along the exact closure frontier, probe deficiency falls monotonically, but shelf width grows because joint distinguishability opens faster than answer-only distinguishability.

That means separator-complete closure is doing two things at once:

- it repairs probe deficiency by restoring the missing two-sided distinctions,
- it reveals a larger answer-vs-justification gap inside the observational tower before exact closure arrives.

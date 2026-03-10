# Exact Pareto Frontiers

This report computes exact partition frontiers for the atomic state spaces listed below.

Scope matters:

- `M_3` is solved exactly after lossless aggregation of identical output rows for the frontier objective.
- `Q_(3,2)`, `Q_(4,2)`, and `Q_(5,3)` are solved exactly on the current probe-joint observational quotient.
- `causal_referee` is solved exactly on empirical support.

## `M_3` (canonical_row_aggregated)

- atomic states: `5`
- answer threshold: `2.322` bits
- joint threshold: `3.807` bits

### `forced`

| bits | bucket limit | frontier size | best answer | best witness | witness at perfect answer | answer at perfect witness |
| --- | --- | --- | --- | --- | --- | --- |
| `0` | `1` | `1` | `0.781` | `0.781` | `-` | `-` |
| `1` | `2` | `1` | `0.898` | `0.898` | `-` | `-` |
| `2` | `4` | `1` | `0.980` | `0.980` | `-` | `-` |
| `3` | `5` | `1` | `1.000` | `1.000` | `1.000` | `1.000` |

### `breach`

| bits | bucket limit | frontier size | best answer | best witness | witness at perfect answer | answer at perfect witness |
| --- | --- | --- | --- | --- | --- | --- |
| `0` | `1` | `1` | `0.071` | `0.071` | `-` | `-` |
| `1` | `2` | `1` | `0.668` | `0.668` | `-` | `-` |
| `2` | `4` | `1` | `0.949` | `0.949` | `-` | `-` |
| `3` | `5` | `1` | `1.000` | `1.000` | `1.000` | `1.000` |

## `Q_(3,2)` (probe_joint)

- atomic states: `7`
- answer threshold: `2.322` bits
- joint threshold: `2.807` bits

### `forced`

| bits | bucket limit | frontier size | best answer | best witness | witness at perfect answer | answer at perfect witness |
| --- | --- | --- | --- | --- | --- | --- |
| `0` | `1` | `1` | `0.799` | `0.670` | `-` | `-` |
| `1` | `2` | `2` | `0.903` | `0.843` | `-` | `-` |
| `2` | `4` | `2` | `0.988` | `0.954` | `-` | `-` |
| `3` | `7` | `1` | `1.000` | `1.000` | `1.000` | `1.000` |

### `breach`

| bits | bucket limit | frontier size | best answer | best witness | witness at perfect answer | answer at perfect witness |
| --- | --- | --- | --- | --- | --- | --- |
| `0` | `1` | `1` | `0.019` | `0.019` | `-` | `-` |
| `1` | `2` | `1` | `0.466` | `0.466` | `-` | `-` |
| `2` | `4` | `1` | `0.855` | `0.855` | `-` | `-` |
| `3` | `7` | `1` | `1.000` | `1.000` | `1.000` | `1.000` |

## `Q_(4,2)` (probe_joint)

- atomic states: `8`
- answer threshold: `2.585` bits
- joint threshold: `3.000` bits

### `forced`

| bits | bucket limit | frontier size | best answer | best witness | witness at perfect answer | answer at perfect witness |
| --- | --- | --- | --- | --- | --- | --- |
| `0` | `1` | `1` | `0.812` | `0.680` | `-` | `-` |
| `1` | `2` | `2` | `0.904` | `0.828` | `-` | `-` |
| `2` | `4` | `1` | `0.984` | `0.961` | `-` | `-` |
| `3` | `8` | `1` | `1.000` | `1.000` | `1.000` | `1.000` |

### `breach`

| bits | bucket limit | frontier size | best answer | best witness | witness at perfect answer | answer at perfect witness |
| --- | --- | --- | --- | --- | --- | --- |
| `0` | `1` | `1` | `0.011` | `0.011` | `-` | `-` |
| `1` | `2` | `1` | `0.411` | `0.411` | `-` | `-` |
| `2` | `4` | `1` | `0.812` | `0.812` | `-` | `-` |
| `3` | `8` | `1` | `1.000` | `1.000` | `1.000` | `1.000` |

## `Q_(5,3)` (probe_joint)

- atomic states: `13`
- answer threshold: `2.807` bits
- joint threshold: `3.700` bits

### `forced`

| bits | bucket limit | frontier size | best answer | best witness | witness at perfect answer | answer at perfect witness |
| --- | --- | --- | --- | --- | --- | --- |
| `0` | `1` | `1` | `0.904` | `0.647` | `-` | `-` |
| `1` | `2` | `2` | `0.947` | `0.806` | `-` | `-` |
| `2` | `4` | `1` | `0.986` | `0.950` | `-` | `-` |
| `3` | `8` | `3` | `1.000` | `0.993` | `0.982` | `-` |
| `4` | `13` | `1` | `1.000` | `1.000` | `1.000` | `1.000` |

### `breach`

| bits | bucket limit | frontier size | best answer | best witness | witness at perfect answer | answer at perfect witness |
| --- | --- | --- | --- | --- | --- | --- |
| `0` | `1` | `1` | `0.001` | `0.001` | `-` | `-` |
| `1` | `2` | `1` | `0.311` | `0.311` | `-` | `-` |
| `2` | `4` | `1` | `0.739` | `0.739` | `-` | `-` |
| `3` | `8` | `1` | `0.958` | `0.958` | `-` | `-` |
| `4` | `13` | `1` | `1.000` | `1.000` | `1.000` | `1.000` |

## `causal_referee` (empirical_support)

- atomic states: `15`
- answer threshold: `2.000` bits
- joint threshold: `3.907` bits

### `forced`

| bits | bucket limit | frontier size | best answer | best witness | witness at perfect answer | answer at perfect witness |
| --- | --- | --- | --- | --- | --- | --- |
| `0` | `1` | `1` | `0.811` | `0.532` | `-` | `-` |
| `1` | `2` | `2` | `0.981` | `0.736` | `-` | `-` |
| `2` | `4` | `3` | `1.000` | `0.894` | `0.641` | `-` |
| `3` | `8` | `2` | `1.000` | `0.976` | `0.964` | `-` |
| `4` | `15` | `1` | `1.000` | `1.000` | `1.000` | `1.000` |

### `breach`

| bits | bucket limit | frontier size | best answer | best witness | witness at perfect answer | answer at perfect witness |
| --- | --- | --- | --- | --- | --- | --- |
| `0` | `1` | `1` | `0.000` | `0.000` | `-` | `-` |
| `1` | `2` | `1` | `0.532` | `0.532` | `-` | `-` |
| `2` | `4` | `1` | `0.832` | `0.832` | `-` | `-` |
| `3` | `8` | `1` | `0.964` | `0.964` | `-` | `-` |
| `4` | `15` | `1` | `1.000` | `1.000` | `1.000` | `1.000` |

## Interpretation

The exact frontier tells us whether the shelf is a compressor artifact or an intrinsic underbudget tradeoff on the chosen atomic state space.

The strongest observational cases are the families where `answer_threshold_bits < joint_threshold_bits`. There, the exact frontier should admit budgets where perfect answerability is possible but perfect witness recovery is not. That is the intrinsic shelf for the measured quotient tower.

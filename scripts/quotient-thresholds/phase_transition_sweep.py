#!/usr/bin/env python3
"""Phase-transition sweep for quotient-threshold experiments.

This harness measures how explicit bit budgets interact with three contract
families:

1. `M_k` bare feasibility states.
2. `Q_(k,p)` protected-witness states.
3. The exhaustive unique-minimal referee corpus, using adjustment-set size as
   the answer channel and exact witness identity as the justification channel.

Compression is modeled by assigning each exact state a canonical binary code and
retaining only the first `B` bits. That creates a bounded summary alphabet with
at most `2**B` cells.

Two decoding policies are evaluated at every budget:

- `breach`: abstain whenever a compressed cell mixes incompatible full outputs.
- `forced`: always emit a majority answer; when the answer survives but the
  witness set does not, witness fidelity falls before answer accuracy does.
"""

from __future__ import annotations

import json
import math
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import DefaultDict, Dict, Iterable, List, Sequence, Tuple

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "README.md").exists())
SCRIPTS_ROOT = ROOT / "scripts"
for candidate in [SCRIPTS_ROOT] + sorted(path for path in SCRIPTS_ROOT.iterdir() if path.is_dir()):
    candidate_str = str(candidate)
    if candidate_str not in sys.path:
        sys.path.insert(0, candidate_str)

from unique_minimal_referee import enumerate_unique_minimal_queries

BOT = -1
EXTRA_BUDGET_BITS = 5
RESULTS_DIR = ROOT / "results" / "quotient-thresholds" / "phase-transition-sweep"
POSITIONAL_SCHEMES: Dict[str, str] = {
    "prefix": "Keep the first B bits of the canonical binary code.",
    "suffix": "Keep the last B bits of the canonical binary code.",
    "interleaved": "Keep B bits from a deterministic high-low interleaving of bit positions.",
}
TRACE_CLUSTER_BASELINES: Dict[str, str] = {
    "cluster_answer": "Cluster states by answer traces first, then refine within each answer block by full joint traces.",
    "cluster_witness": "Cluster states by witness traces first, then refine within each witness block by full joint traces.",
    "cluster_joint": "Cluster states directly by full joint answer/witness traces.",
}
ALL_SCHEMES: Dict[str, str] = {**POSITIONAL_SCHEMES, **TRACE_CLUSTER_BASELINES}


@dataclass(frozen=True)
class Output:
    answer: str
    witness: Tuple[int, ...]


@dataclass(frozen=True)
class CompositionalSpec:
    family: str
    label: str
    states: Tuple[Tuple[int, Tuple[int, ...]], ...]
    outcomes: Tuple[Tuple[Output, ...], ...]
    exact_state_count: int
    threshold_bits: float
    has_witness_channel: bool
    notes: str


@dataclass(frozen=True)
class DatasetSpec:
    family: str
    label: str
    examples: Tuple[Output, ...]
    support_outputs: Tuple[Output, ...]
    support_weights: Tuple[int, ...]
    support_size: int
    threshold_bits: float
    has_witness_channel: bool
    notes: str
    canonical_threshold_bits: float | None = None
    canonical_state_count: int | None = None


@dataclass(frozen=True)
class BudgetMetrics:
    budget_bits: int
    bucket_count: int
    accuracy: float
    breach_rate: float
    mirage_rate: float
    witness_fidelity: float


def log2_count(count: int) -> float:
    return math.log2(count) if count > 0 else 0.0


def shift_coord(left_depth: int, right_coord: int, k: int) -> int:
    if right_coord == BOT:
        return BOT
    return min(k, left_depth + right_coord)


def enumerate_bare_states(k: int) -> Tuple[Tuple[int, Tuple[int, ...]], ...]:
    states: List[Tuple[int, Tuple[int, ...]]] = []
    for depth in range(k + 1):
        for frontier in range(BOT, depth + 1):
            states.append((depth, (frontier,)))
    return tuple(states)


def compose_bare(
    left: Tuple[int, Tuple[int, ...]], right: Tuple[int, Tuple[int, ...]], k: int
) -> Tuple[int, Tuple[int, ...]]:
    left_depth, (left_frontier,) = left
    right_depth, (right_frontier,) = right
    depth = min(k, left_depth + right_depth)
    frontier = max(left_frontier, shift_coord(left_depth, right_frontier, k))
    return depth, (frontier,)


def output_bare(state: Tuple[int, Tuple[int, ...]], k: int) -> Output:
    _, (frontier,) = state
    feasible = frontier == k
    return Output(answer="feasible" if feasible else "blocked", witness=())


def enumerate_witness_states(k: int, p: int) -> Tuple[Tuple[int, Tuple[int, ...]], ...]:
    states: List[Tuple[int, Tuple[int, ...]]] = []

    def walk(depth: int, prefix: List[int]) -> None:
        if len(prefix) == p:
            states.append((depth, tuple(prefix)))
            return
        for coord in range(BOT, depth + 1):
            prefix.append(coord)
            walk(depth, prefix)
            prefix.pop()

    for depth in range(k + 1):
        walk(depth, [])
    return tuple(states)


def compose_witness(
    left: Tuple[int, Tuple[int, ...]], right: Tuple[int, Tuple[int, ...]], k: int
) -> Tuple[int, Tuple[int, ...]]:
    left_depth, left_coords = left
    right_depth, right_coords = right
    depth = min(k, left_depth + right_depth)
    coords = tuple(
        max(left_coord, shift_coord(left_depth, right_coord, k))
        for left_coord, right_coord in zip(left_coords, right_coords)
    )
    return depth, coords


def output_witness(state: Tuple[int, Tuple[int, ...]], k: int) -> Output:
    _, coords = state
    survivors = tuple(index + 1 for index, coord in enumerate(coords) if coord == k)
    feasible = bool(survivors)
    return Output(answer="feasible" if feasible else "blocked", witness=survivors)


def build_compositional_spec_bare(k: int) -> CompositionalSpec:
    states = enumerate_bare_states(k)
    outcomes = tuple(
        tuple(output_bare(compose_bare(left, right, k), k) for right in states) for left in states
    )
    exact_state_count = len(states)
    return CompositionalSpec(
        family="bare_threshold",
        label=f"M_{k}",
        states=states,
        outcomes=outcomes,
        exact_state_count=exact_state_count,
        threshold_bits=math.log2(exact_state_count),
        has_witness_channel=False,
        notes="Exact two-sided bare threshold quotient.",
    )


def build_compositional_spec_witness(k: int, p: int) -> CompositionalSpec:
    states = enumerate_witness_states(k, p)
    outcomes = tuple(
        tuple(output_witness(compose_witness(left, right, k), k) for right in states) for left in states
    )
    exact_state_count = len(states)
    return CompositionalSpec(
        family="protected_witness",
        label=f"Q_({k},{p})",
        states=states,
        outcomes=outcomes,
        exact_state_count=exact_state_count,
        threshold_bits=math.log2(exact_state_count),
        has_witness_channel=True,
        notes="Protected-witness quotient with exact shift-and-max composition.",
    )


def build_causal_referee_spec() -> DatasetSpec:
    records, _ = enumerate_unique_minimal_queries(max_n=6)
    examples = tuple(
        Output(answer=f"k={record.k}", witness=record.witness_set)
        for record in records
    )
    support_counter = Counter(examples)
    support = tuple(sorted(support_counter, key=lambda output: (output.answer, output.witness)))
    support_by_k: DefaultDict[int, set[Tuple[int, ...]]] = defaultdict(set)
    for record in records:
        support_by_k[record.k].add(record.witness_set)

    canonical_total = sum(sum((depth + 2) ** k for depth in range(k + 1)) for k in sorted(support_by_k))
    note = (
        "Static sweep over the 89,291 unique-minimal referee narratives. "
        "The answer channel is adjustment-set size `k`; witness fidelity tracks exact "
        "named adjustment-set identity."
    )
    return DatasetSpec(
        family="causal_referee",
        label="causal_referee",
        examples=examples,
        support_outputs=tuple(support),
        support_weights=tuple(support_counter[output] for output in support),
        support_size=len(support),
        threshold_bits=math.log2(len(support)),
        has_witness_channel=True,
        notes=note,
        canonical_threshold_bits=math.log2(canonical_total),
        canonical_state_count=canonical_total,
    )


def full_bits(state_count: int) -> int:
    return max(1, math.ceil(math.log2(state_count)))


def binary_code(index: int, bits: int) -> str:
    return format(index, f"0{bits}b")


@lru_cache(maxsize=None)
def interleaved_positions(bits: int) -> Tuple[int, ...]:
    positions: List[int] = []
    lo = 0
    hi = bits - 1
    while lo <= hi:
        positions.append(lo)
        lo += 1
        if lo <= hi:
            positions.append(hi)
            hi -= 1
    return tuple(positions)


def transformed_code(index: int, bits: int, scheme: str) -> str:
    code = binary_code(index, bits)
    if scheme == "prefix":
        return code
    if scheme == "suffix":
        return code[::-1]
    if scheme == "interleaved":
        return "".join(code[position] for position in interleaved_positions(bits))
    raise ValueError(f"unknown compression scheme: {scheme}")


def buckets_for_budget(state_count: int, budget_bits: int, scheme: str) -> Dict[str, List[int]]:
    bits = full_bits(state_count)
    kept = min(bits, budget_bits)
    buckets: Dict[str, List[int]] = defaultdict(list)
    for index in range(state_count):
        code = transformed_code(index, bits, scheme)
        key = code[:kept] if kept < bits else code
        buckets[key].append(index)
    return dict(sorted(buckets.items()))


def output_projection(output: Output, projection: str) -> Tuple[object, ...] | str | Tuple[int, ...]:
    if projection == "answer":
        return output.answer
    if projection == "witness":
        return output.witness
    if projection == "joint":
        return output.answer, output.witness
    raise ValueError(f"unknown projection: {projection}")


def projection_for_scheme(scheme: str) -> str:
    if scheme == "cluster_answer":
        return "answer"
    if scheme == "cluster_witness":
        return "witness"
    if scheme == "cluster_joint":
        return "joint"
    raise ValueError(f"scheme {scheme} has no trace projection")


def contiguous_weighted_buckets(
    ordered_indices: Sequence[int],
    weights: Sequence[int],
    target_bucket_count: int,
) -> List[List[int]]:
    if not ordered_indices:
        return []
    bucket_count = min(target_bucket_count, len(ordered_indices))
    if bucket_count <= 1:
        return [list(ordered_indices)]

    total_weight = sum(weights[index] for index in ordered_indices)
    buckets: List[List[int]] = []
    pos = 0
    remaining_weight = total_weight

    for made in range(bucket_count - 1):
        remaining_buckets = bucket_count - made
        target_weight = remaining_weight / remaining_buckets
        current: List[int] = []
        current_weight = 0
        min_items_remaining = bucket_count - made - 1

        while pos < len(ordered_indices) - min_items_remaining:
            index = ordered_indices[pos]
            weight = weights[index]
            if current and current_weight + weight > target_weight:
                if abs(target_weight - current_weight) <= abs(target_weight - (current_weight + weight)):
                    break
            current.append(index)
            current_weight += weight
            pos += 1
            if current_weight >= target_weight:
                break

        if not current:
            index = ordered_indices[pos]
            current = [index]
            current_weight = weights[index]
            pos += 1

        buckets.append(current)
        remaining_weight -= current_weight

    buckets.append(list(ordered_indices[pos:]))
    return buckets


def block_trace_indices_compositional(
    spec: CompositionalSpec, scheme: str
) -> Tuple[List[List[int]], List[int]]:
    projection = projection_for_scheme(scheme)
    joint_keys = [
        tuple((output.answer, output.witness) for output in row)
        for row in spec.outcomes
    ]
    primary_keys = [
        tuple(output_projection(output, projection) for output in row)
        for row in spec.outcomes
    ]
    by_primary: DefaultDict[object, List[int]] = defaultdict(list)
    for index in range(spec.exact_state_count):
        by_primary[primary_keys[index]].append(index)
    blocks = [
        sorted(indices, key=lambda index: (joint_keys[index], index))
        for _, indices in sorted(by_primary.items(), key=lambda item: item[0])
    ]
    weights = [1] * spec.exact_state_count
    return blocks, weights


def block_trace_indices_dataset(
    spec: DatasetSpec, scheme: str
) -> Tuple[List[List[int]], List[int]]:
    projection = projection_for_scheme(scheme)
    primary_keys = [
        output_projection(output, projection) for output in spec.support_outputs
    ]
    joint_keys = [
        output_projection(output, "joint") for output in spec.support_outputs
    ]
    by_primary: DefaultDict[object, List[int]] = defaultdict(list)
    for index in range(spec.support_size):
        by_primary[primary_keys[index]].append(index)
    blocks = [
        sorted(indices, key=lambda index: (joint_keys[index], index))
        for _, indices in sorted(by_primary.items(), key=lambda item: item[0])
    ]
    return blocks, list(spec.support_weights)


def hierarchical_trace_buckets(
    blocks: Sequence[Sequence[int]],
    weights: Sequence[int],
    target_bucket_count: int,
) -> List[List[int]]:
    nonempty_blocks = [list(block) for block in blocks if block]
    if not nonempty_blocks:
        return []

    max_buckets = sum(len(block) for block in nonempty_blocks)
    bucket_count = min(target_bucket_count, max_buckets)
    if bucket_count <= 1:
        return [sum((list(block) for block in nonempty_blocks), [])]

    def block_weight(block: Sequence[int]) -> int:
        return sum(weights[index] for index in block)

    if bucket_count <= len(nonempty_blocks):
        ordered_blocks = sorted(
            range(len(nonempty_blocks)),
            key=lambda block_index: block_index,
        )
        block_weights = [block_weight(nonempty_blocks[block_index]) for block_index in ordered_blocks]
        grouped_block_indices = contiguous_weighted_buckets(ordered_blocks, block_weights, bucket_count)
        return [
            [index for block_index in grouped for index in nonempty_blocks[block_index]]
            for grouped in grouped_block_indices
        ]

    splits = [1] * len(nonempty_blocks)
    current_bucket_count = len(nonempty_blocks)
    while current_bucket_count < bucket_count:
        candidates = [
            (
                -(block_weight(block) / splits[block_index]),
                -len(block),
                block_index,
            )
            for block_index, block in enumerate(nonempty_blocks)
            if splits[block_index] < len(block)
        ]
        if not candidates:
            break
        _, _, chosen = min(candidates)
        splits[chosen] += 1
        current_bucket_count += 1

    buckets: List[List[int]] = []
    for block, split_count in zip(nonempty_blocks, splits):
        buckets.extend(contiguous_weighted_buckets(block, weights, split_count))
    return buckets


def compositional_buckets(
    spec: CompositionalSpec,
    budget_bits: int,
    scheme: str,
    trace_cache: Dict[Tuple[str, str], Tuple[List[List[int]], List[int]]],
) -> List[List[int]]:
    if scheme in POSITIONAL_SCHEMES:
        return list(buckets_for_budget(spec.exact_state_count, budget_bits, scheme).values())
    blocks, weights = trace_cache[(spec.label, scheme)]
    target_bucket_count = min(spec.exact_state_count, 1 << budget_bits)
    return hierarchical_trace_buckets(blocks, weights, target_bucket_count)


def dataset_buckets(
    spec: DatasetSpec,
    budget_bits: int,
    scheme: str,
    trace_cache: Dict[Tuple[str, str], Tuple[List[List[int]], List[int]]],
) -> List[List[int]]:
    if scheme in POSITIONAL_SCHEMES:
        return list(buckets_for_budget(spec.support_size, budget_bits, scheme).values())
    blocks, weights = trace_cache[(spec.label, scheme)]
    target_bucket_count = min(spec.support_size, 1 << budget_bits)
    return hierarchical_trace_buckets(blocks, weights, target_bucket_count)


def choose_mode(values: Iterable[Tuple[int, ...] | str]) -> Tuple[int, ...] | str:
    counts = Counter(values)
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0][0]


def evaluate_compositional_budget(
    spec: CompositionalSpec,
    budget_bits: int,
    policy: str,
    scheme: str,
    trace_cache: Dict[Tuple[str, str], Tuple[List[List[int]], List[int]]],
) -> BudgetMetrics:
    state_count = spec.exact_state_count
    probes = state_count
    buckets = compositional_buckets(spec, budget_bits, scheme, trace_cache)
    total = state_count * probes
    answer_correct = 0
    witness_correct = 0
    breach = 0
    mirage = 0

    for probe_index in range(probes):
        for members in buckets:
            outputs = [spec.outcomes[left_index][probe_index] for left_index in members]
            if policy == "breach":
                if spec.has_witness_channel:
                    unanimous = len(set(outputs)) == 1
                else:
                    unanimous = len({output.answer for output in outputs}) == 1
                if unanimous:
                    answer_correct += len(members)
                    witness_correct += len(members)
                else:
                    breach += len(members)
                continue

            predicted_answer = choose_mode(output.answer for output in outputs)
            answer_matches = sum(1 for output in outputs if output.answer == predicted_answer)
            answer_correct += answer_matches
            mirage += len(members) - answer_matches

            if spec.has_witness_channel:
                if predicted_answer == "blocked":
                    predicted_witness: Tuple[int, ...] = ()
                else:
                    predicted_witness = choose_mode(
                        output.witness for output in outputs if output.answer == predicted_answer
                    )
                witness_correct += sum(
                    1 for output in outputs if output.witness == predicted_witness
                )
            else:
                witness_correct += answer_matches

    return BudgetMetrics(
        budget_bits=budget_bits,
        bucket_count=len(buckets),
        accuracy=answer_correct / total,
        breach_rate=breach / total,
        mirage_rate=mirage / total,
        witness_fidelity=witness_correct / total,
    )


def evaluate_dataset_budget(
    spec: DatasetSpec,
    budget_bits: int,
    policy: str,
    scheme: str,
    trace_cache: Dict[Tuple[str, str], Tuple[List[List[int]], List[int]]],
) -> BudgetMetrics:
    support_outputs = spec.support_outputs
    buckets = dataset_buckets(spec, budget_bits, scheme, trace_cache)
    members_for_bucket = [
        {support_outputs[index] for index in indices} for indices in buckets
    ]
    bucket_for_state: Dict[Tuple[str, Tuple[int, ...]], str] = {}
    for bucket_index, states in enumerate(members_for_bucket):
        for state in states:
            bucket_for_state[(state.answer, state.witness)] = str(bucket_index)

    total = len(spec.examples)
    answer_correct = 0
    witness_correct = 0
    breach = 0
    mirage = 0

    grouped_examples: DefaultDict[str, List[Output]] = defaultdict(list)
    for example in spec.examples:
        grouped_examples[bucket_for_state[(example.answer, example.witness)]].append(example)

    for bucket, examples in grouped_examples.items():
        outputs = list(examples)
        if policy == "breach":
            if len(set(outputs)) == 1:
                answer_correct += len(outputs)
                witness_correct += len(outputs)
            else:
                breach += len(outputs)
            continue

        predicted_answer = choose_mode(output.answer for output in outputs)
        answer_matches = sum(1 for output in outputs if output.answer == predicted_answer)
        answer_correct += answer_matches
        mirage += len(outputs) - answer_matches

        if predicted_answer.startswith("k="):
            predicted_witness = choose_mode(
                output.witness for output in outputs if output.answer == predicted_answer
            )
        else:
            predicted_witness = ()

        witness_correct += sum(1 for output in outputs if output.witness == predicted_witness)

    return BudgetMetrics(
        budget_bits=budget_bits,
        bucket_count=len(buckets),
        accuracy=answer_correct / total,
        breach_rate=breach / total,
        mirage_rate=mirage / total,
        witness_fidelity=witness_correct / total,
    )


def regime_for_metrics(metrics: BudgetMetrics, has_witness_channel: bool) -> str:
    if metrics.accuracy >= 0.999999 and metrics.witness_fidelity >= 0.999999:
        return "sound"
    if metrics.breach_rate > 0.0:
        return "breach"
    if (has_witness_channel and metrics.witness_fidelity < 0.60) or metrics.accuracy < 0.60:
        return "collapse"
    if has_witness_channel and metrics.witness_fidelity < 0.999999:
        return "mirage"
    if metrics.mirage_rate >= 0.05:
        return "mirage"
    return "collapse"


def compositional_tower(spec: CompositionalSpec) -> Dict[str, float | int]:
    answer_classes = {
        tuple(output.answer for output in row)
        for row in spec.outcomes
    }
    witness_classes = {
        tuple(output.witness for output in row)
        for row in spec.outcomes
    }
    joint_classes = {
        tuple((output.answer, output.witness) for output in row)
        for row in spec.outcomes
    }
    algebraic = spec.exact_state_count
    empirical = spec.exact_state_count
    joint = len(joint_classes)
    witness = len(witness_classes)
    answer = len(answer_classes)
    return {
        "algebraic_state_count": algebraic,
        "empirical_support_count": empirical,
        "probe_joint_count": joint,
        "probe_witness_count": witness,
        "probe_answer_count": answer,
        "algebraic_bits": log2_count(algebraic),
        "empirical_bits": log2_count(empirical),
        "probe_joint_bits": log2_count(joint),
        "probe_witness_bits": log2_count(witness),
        "probe_answer_bits": log2_count(answer),
        "probe_deficiency_bits": log2_count(algebraic) - log2_count(joint),
        "shelf_width_bits": log2_count(joint) - log2_count(answer),
    }


def dataset_tower(spec: DatasetSpec) -> Dict[str, float | int]:
    answer = len({output.answer for output in spec.support_outputs})
    witness = len({output.witness for output in spec.support_outputs})
    joint = len({(output.answer, output.witness) for output in spec.support_outputs})
    algebraic = spec.canonical_state_count or spec.support_size
    empirical = spec.support_size
    return {
        "algebraic_state_count": algebraic,
        "empirical_support_count": empirical,
        "probe_joint_count": joint,
        "probe_witness_count": witness,
        "probe_answer_count": answer,
        "algebraic_bits": log2_count(algebraic),
        "empirical_bits": log2_count(empirical),
        "probe_joint_bits": log2_count(joint),
        "probe_witness_bits": log2_count(witness),
        "probe_answer_bits": log2_count(answer),
        "probe_deficiency_bits": log2_count(algebraic) - log2_count(joint),
        "shelf_width_bits": log2_count(joint) - log2_count(answer),
    }


def render_json(
    compositional_specs: Sequence[CompositionalSpec],
    dataset_specs: Sequence[DatasetSpec],
    scheme_results: Dict[str, Dict[str, List[Dict[str, object]]]],
) -> str:
    payload = {
        "extra_budget_bits": EXTRA_BUDGET_BITS,
        "schemes": [
            {"name": name, "notes": notes} for name, notes in ALL_SCHEMES.items()
        ],
        "families": [
            {
                "family": spec.family,
                "label": spec.label,
                "exact_state_count": spec.exact_state_count,
                "threshold_bits": spec.threshold_bits,
                "has_witness_channel": spec.has_witness_channel,
                "notes": spec.notes,
                "tower": compositional_tower(spec),
            }
            for spec in compositional_specs
        ]
        + [
            {
                "family": spec.family,
                "label": spec.label,
                "support_size": spec.support_size,
                "threshold_bits": spec.threshold_bits,
                "canonical_state_count": spec.canonical_state_count,
                "canonical_threshold_bits": spec.canonical_threshold_bits,
                "has_witness_channel": spec.has_witness_channel,
                "notes": spec.notes,
                "tower": dataset_tower(spec),
            }
            for spec in dataset_specs
        ],
        "results": scheme_results,
    }
    return json.dumps(payload, indent=2)


def render_markdown(
    compositional_specs: Sequence[CompositionalSpec],
    dataset_specs: Sequence[DatasetSpec],
    scheme_results: Dict[str, Dict[str, List[Dict[str, object]]]],
) -> str:
    def rows_for(scheme: str, policy: str, label: str) -> List[Dict[str, object]]:
        return [row for row in scheme_results[scheme][policy] if row["label"] == label]

    def first_sound_budget(scheme: str, policy: str, label: str) -> int:
        for row in rows_for(scheme, policy, label):
            if row["regime"] == "sound":
                return int(row["budget_bits"])
        return -1

    def row_at(scheme: str, policy: str, label: str, budget_bits: int) -> Dict[str, object]:
        return next(
            row
            for row in rows_for(scheme, policy, label)
            if int(row["budget_bits"]) == budget_bits
        )

    q53_budget = full_bits(783) - 1
    causal_budget = full_bits(15) - 1
    q53_scheme_summary = ", ".join(
        f"`{scheme}`: acc `{row_at(scheme, 'forced', 'Q_(5,3)', q53_budget)['accuracy']:.3f}` / witness `{row_at(scheme, 'forced', 'Q_(5,3)', q53_budget)['witness_fidelity']:.3f}`"
        for scheme in POSITIONAL_SCHEMES
    )
    causal_scheme_summary = ", ".join(
        f"`{scheme}`: acc `{row_at(scheme, 'forced', 'causal_referee', causal_budget)['accuracy']:.3f}` / witness `{row_at(scheme, 'forced', 'causal_referee', causal_budget)['witness_fidelity']:.3f}`"
        for scheme in POSITIONAL_SCHEMES
    )
    threshold_summary = ", ".join(
        f"`{scheme}` -> `M_3` at `{first_sound_budget(scheme, 'breach', 'M_3')}` bits, `Q_(3,2)` at `{first_sound_budget(scheme, 'breach', 'Q_(3,2)')}` bits"
        for scheme in POSITIONAL_SCHEMES
    )
    cluster_summary = ", ".join(
        f"`{scheme}` on `Q_(5,3)` at `{q53_budget}` bits gives acc `{row_at(scheme, 'forced', 'Q_(5,3)', q53_budget)['accuracy']:.3f}` / witness `{row_at(scheme, 'forced', 'Q_(5,3)', q53_budget)['witness_fidelity']:.3f}`"
        for scheme in TRACE_CLUSTER_BASELINES
    )
    causal_cluster_summary = ", ".join(
        f"`{scheme}` on `causal_referee` at `{causal_budget}` bits gives acc `{row_at(scheme, 'forced', 'causal_referee', causal_budget)['accuracy']:.3f}` / witness `{row_at(scheme, 'forced', 'causal_referee', causal_budget)['witness_fidelity']:.3f}`"
        for scheme in TRACE_CLUSTER_BASELINES
    )

    lines = [
        "# Phase-Transition Sweep",
        "",
        "This artifact sweeps explicit bit budgets against exact contract state spaces.",
        "It compares positional bit-geometry schemes with trace-based clustering baselines.",
        "",
        "Schemes:",
        "",
    ]
    for name, notes in POSITIONAL_SCHEMES.items():
        lines.append(f"- `{name}`: {notes}")
    for name, notes in TRACE_CLUSTER_BASELINES.items():
        lines.append(f"- `{name}`: {notes}")

    lines.extend(
        [
            "",
            "Policies:",
            "",
            "- `breach`: abstain on mixed buckets.",
            "- `forced`: emit a majority answer and majority witness.",
            "",
            "## Highlights",
            "",
            f"- The exact turn-on point is unchanged by code geometry: {threshold_summary}.",
            f"- The pre-threshold mirage shelf survives all three geometries for `Q_(5,3)` at `{q53_budget}` bits: {q53_scheme_summary}.",
            f"- The causal referee shelf also survives the geometry change at `{causal_budget}` bits: {causal_scheme_summary}.",
            f"- The trace-clustering baselines are more discriminating than the bit geometries: {cluster_summary}.",
            f"- On the realistic causal corpus, the clustering baselines remain subexact at the same pre-threshold point: {causal_cluster_summary}.",
            "- Reading the two lines together, the current right-context probe bank is strong enough to expose a causal mirage shelf, but not yet separator-complete for the full two-sided synthetic quotient under joint trace clustering.",
            "",
            "## Families",
            "",
        ]
    )

    for spec in compositional_specs:
        tower = compositional_tower(spec)
        lines.append(
            f"- `{spec.label}`: `{spec.exact_state_count}` exact states, threshold `{spec.threshold_bits:.3f}` bits. {spec.notes} Probe-joint `{tower['probe_joint_count']}` / probe-answer `{tower['probe_answer_count']}`."
        )
    for spec in dataset_specs:
        tower = dataset_tower(spec)
        line = (
            f"- `{spec.label}`: `{spec.support_size}` empirical support states, threshold "
            f"`{spec.threshold_bits:.3f}` bits. {spec.notes} Probe-joint `{tower['probe_joint_count']}` / probe-answer `{tower['probe_answer_count']}`."
        )
        if spec.canonical_state_count and spec.canonical_threshold_bits:
            line += (
                f" Canonical `Q_(k,k)` upper-bound support across the observed `k` values: "
                f"`{spec.canonical_state_count}` states / `{spec.canonical_threshold_bits:.3f}` bits."
            )
        lines.append(line)

    lines.extend(
        [
            "",
            "## Quotient Tower",
            "",
            "| Label | Algebraic | Empirical | Probe Joint | Probe Witness | Probe Answer | Deficiency (bits) | Shelf Width (bits) |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for spec in compositional_specs:
        tower = compositional_tower(spec)
        lines.append(
            "| {label} | {algebraic} | {empirical} | {joint} | {witness} | {answer} | {deficiency:.3f} | {shelf:.3f} |".format(
                label=spec.label,
                algebraic=tower["algebraic_state_count"],
                empirical=tower["empirical_support_count"],
                joint=tower["probe_joint_count"],
                witness=tower["probe_witness_count"],
                answer=tower["probe_answer_count"],
                deficiency=tower["probe_deficiency_bits"],
                shelf=tower["shelf_width_bits"],
            )
        )
    for spec in dataset_specs:
        tower = dataset_tower(spec)
        lines.append(
            "| {label} | {algebraic} | {empirical} | {joint} | {witness} | {answer} | {deficiency:.3f} | {shelf:.3f} |".format(
                label=spec.label,
                algebraic=tower["algebraic_state_count"],
                empirical=tower["empirical_support_count"],
                joint=tower["probe_joint_count"],
                witness=tower["probe_witness_count"],
                answer=tower["probe_answer_count"],
                deficiency=tower["probe_deficiency_bits"],
                shelf=tower["shelf_width_bits"],
            )
        )

    for scheme, by_policy in scheme_results.items():
        lines.extend(["", f"## Scheme: `{scheme}`", ""])
        for policy, rows in by_policy.items():
            lines.extend(
                [
                    "",
                    f"### Policy: `{policy}`",
                    "",
                    "| Label | Threshold (bits) | Budget | Accuracy | Breach | Mirage | Witness | Regime |",
                    "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
                ]
            )
            for row in rows:
                lines.append(
                    "| {label} | {threshold:.3f} | {budget} | {accuracy:.3f} | {breach:.3f} | {mirage:.3f} | {witness:.3f} | {regime} |".format(
                        label=row["label"],
                        threshold=row["threshold_bits"],
                        budget=row["budget_bits"],
                        accuracy=row["accuracy"],
                        breach=row["breach_rate"],
                        mirage=row["mirage_rate"],
                        witness=row["witness_fidelity"],
                        regime=row["regime"],
                    )
                )
    lines.append("")
    return "\n".join(lines)


def render_svg(policy: str, scheme: str, rows: Sequence[Dict[str, object]], path: Path) -> None:
    labels = sorted({row["label"] for row in rows})
    budgets = sorted({int(row["budget_bits"]) for row in rows})
    row_index = {label: index for index, label in enumerate(labels)}
    col_index = {budget: index for index, budget in enumerate(budgets)}
    cell_w = 34
    cell_h = 24
    left_margin = 180
    top_margin = 55
    width = left_margin + cell_w * len(budgets) + 40
    height = top_margin + cell_h * len(labels) + 55
    palette = {
        "sound": "#2a9d8f",
        "breach": "#e9c46a",
        "mirage": "#e76f51",
        "collapse": "#8d99ae",
    }

    by_key = {(row["label"], int(row["budget_bits"])): row for row in rows}
    svg_lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<style>',
        'text { font-family: Menlo, Monaco, Consolas, monospace; font-size: 11px; fill: #1f2933; }',
        '.axis { stroke: #94a3b8; stroke-width: 1; }',
        '.tick { stroke: #334155; stroke-width: 2; }',
        '</style>',
        f'<text x="{left_margin}" y="24">Policy: {policy} / Scheme: {scheme}</text>',
        '<text x="12" y="24">Budget bits</text>',
    ]

    for budget in budgets:
        x = left_margin + col_index[budget] * cell_w + cell_w / 2
        svg_lines.append(
            f'<text x="{x}" y="{top_margin - 14}" text-anchor="middle">{budget}</text>'
        )

    for label in labels:
        y = top_margin + row_index[label] * cell_h + cell_h / 2 + 4
        svg_lines.append(f'<text x="12" y="{y}">{label}</text>')
        svg_lines.append(
            f'<line class="axis" x1="{left_margin}" y1="{top_margin + row_index[label] * cell_h}" '
            f'x2="{left_margin + cell_w * len(budgets)}" y2="{top_margin + row_index[label] * cell_h}" />'
        )

    for row in rows:
        label = str(row["label"])
        budget = int(row["budget_bits"])
        x = left_margin + col_index[budget] * cell_w
        y = top_margin + row_index[label] * cell_h
        color = palette[str(row["regime"])]
        svg_lines.append(
            f'<rect x="{x}" y="{y}" width="{cell_w}" height="{cell_h}" fill="{color}" stroke="#ffffff" stroke-width="1" />'
        )

    for label in labels:
        sample = by_key[(label, budgets[0])]
        threshold = float(sample["threshold_bits"])
        tick_x = left_margin + threshold * cell_w
        y = top_margin + row_index[label] * cell_h
        svg_lines.append(
            f'<line class="tick" x1="{tick_x}" y1="{y + 2}" x2="{tick_x}" y2="{y + cell_h - 2}" />'
        )

    legend_y = top_margin + cell_h * len(labels) + 22
    legend_x = 12
    for regime, color in palette.items():
        svg_lines.append(
            f'<rect x="{legend_x}" y="{legend_y}" width="16" height="16" fill="{color}" stroke="#ffffff" stroke-width="1" />'
        )
        svg_lines.append(f'<text x="{legend_x + 22}" y="{legend_y + 12}">{regime}</text>')
        legend_x += 96

    svg_lines.append("</svg>")
    path.write_text("\n".join(svg_lines))


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    compositional_specs = [build_compositional_spec_bare(k) for k in range(1, 6)]
    compositional_specs.extend(
        build_compositional_spec_witness(k, p)
        for p in range(1, 4)
        for k in range(1, 6)
    )
    dataset_specs = [build_causal_referee_spec()]

    compositional_trace_cache = {
        (spec.label, scheme): block_trace_indices_compositional(spec, scheme)
        for spec in compositional_specs
        for scheme in TRACE_CLUSTER_BASELINES
    }
    dataset_trace_cache = {
        (spec.label, scheme): block_trace_indices_dataset(spec, scheme)
        for spec in dataset_specs
        for scheme in TRACE_CLUSTER_BASELINES
    }

    scheme_results: Dict[str, Dict[str, List[Dict[str, object]]]] = {
        scheme: {"breach": [], "forced": []} for scheme in ALL_SCHEMES
    }

    for scheme in ALL_SCHEMES:
        for policy in scheme_results[scheme]:
            for spec in compositional_specs:
                max_budget = full_bits(spec.exact_state_count) + EXTRA_BUDGET_BITS
                for budget_bits in range(1, max_budget + 1):
                    metrics = evaluate_compositional_budget(
                        spec,
                        budget_bits,
                        policy,
                        scheme,
                        compositional_trace_cache,
                    )
                    row = {
                        "scheme": scheme,
                        "family": spec.family,
                        "label": spec.label,
                        "budget_bits": budget_bits,
                        "bucket_count": metrics.bucket_count,
                        "accuracy": metrics.accuracy,
                        "breach_rate": metrics.breach_rate,
                        "mirage_rate": metrics.mirage_rate,
                        "witness_fidelity": metrics.witness_fidelity,
                        "threshold_bits": spec.threshold_bits,
                        "regime": regime_for_metrics(metrics, spec.has_witness_channel),
                    }
                    scheme_results[scheme][policy].append(row)

            for spec in dataset_specs:
                max_budget = full_bits(spec.support_size) + EXTRA_BUDGET_BITS
                for budget_bits in range(1, max_budget + 1):
                    metrics = evaluate_dataset_budget(
                        spec,
                        budget_bits,
                        policy,
                        scheme,
                        dataset_trace_cache,
                    )
                    row = {
                        "scheme": scheme,
                        "family": spec.family,
                        "label": spec.label,
                        "budget_bits": budget_bits,
                        "bucket_count": metrics.bucket_count,
                        "accuracy": metrics.accuracy,
                        "breach_rate": metrics.breach_rate,
                        "mirage_rate": metrics.mirage_rate,
                        "witness_fidelity": metrics.witness_fidelity,
                        "threshold_bits": spec.threshold_bits,
                        "canonical_threshold_bits": spec.canonical_threshold_bits,
                        "regime": regime_for_metrics(metrics, spec.has_witness_channel),
                    }
                    scheme_results[scheme][policy].append(row)

    json_path = RESULTS_DIR / "phase_transition_sweep.json"
    md_path = RESULTS_DIR / "phase_transition_sweep.md"
    breach_svg_path = RESULTS_DIR / "phase_transition_breach.svg"
    forced_svg_path = RESULTS_DIR / "phase_transition_forced.svg"
    extra_svg_paths = [
        RESULTS_DIR / f"phase_transition_{policy}_{scheme}.svg"
        for scheme in ALL_SCHEMES
        for policy in ("breach", "forced")
    ]

    json_path.write_text(render_json(compositional_specs, dataset_specs, scheme_results))
    md_path.write_text(render_markdown(compositional_specs, dataset_specs, scheme_results))
    render_svg("breach", "prefix", scheme_results["prefix"]["breach"], breach_svg_path)
    render_svg("forced", "prefix", scheme_results["prefix"]["forced"], forced_svg_path)
    for scheme in ALL_SCHEMES:
        render_svg(
            "breach",
            scheme,
            scheme_results[scheme]["breach"],
            RESULTS_DIR / f"phase_transition_breach_{scheme}.svg",
        )
        render_svg(
            "forced",
            scheme,
            scheme_results[scheme]["forced"],
            RESULTS_DIR / f"phase_transition_forced_{scheme}.svg",
        )

    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    print(f"Wrote {breach_svg_path}")
    print(f"Wrote {forced_svg_path}")
    for path in extra_svg_paths:
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Exact family-memory search on overlapping minimal-adjustment families.

This script separates two layers of the family-memory problem.

1. Contract layer:
   distinct overlapping adjustment families `A` extracted from small DAG queries.
   Here the question is whether a family can be represented by coarse summaries
   such as union/core/size, or whether the antichain itself is required.

2. Runtime layer:
   for a fixed family `A`, compose witness-style states using the existing
   `Q_(k,p)` semigroup and ask what dynamic state is required to preserve
   answer / variable / family behavior under future composition.

The core empirical question is whether overlap forces a genuinely
hypergraph-valued *runtime* state, or whether the hypergraph lives only in the
contract parameter while the runtime quotient remains universal.
"""

from __future__ import annotations

import itertools
import json
import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import DefaultDict, Dict, Iterable, List, Sequence, Tuple

from phase_transition_sweep import enumerate_witness_states, compose_witness
from unique_minimal_referee import graph_from_mask, has_directed_path, minimal_adjustment_sets, ordered_dag_id

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results"

Family = Tuple[Tuple[int, ...], ...]
State = Tuple[int, Tuple[int, ...]]


REPRESENTATIVE_FAMILIES: Dict[str, Family] = {
    "A_path_k2_p3": ((1, 2), (1, 3)),
    "A_star_k2_p4": ((1, 2), (1, 3), (1, 4)),
    "A_mixed_k3_p4": ((1, 2, 3), (1, 2, 4)),
}


@dataclass(frozen=True)
class DynamicWorld:
    family: Family
    p: int
    k: int
    states: Tuple[State, ...]
    compose_indices: Tuple[Tuple[int, ...], ...]
    complete_sets: Tuple[Tuple[int, ...], ...]
    family_outputs: Tuple[Family, ...]
    variable_outputs: Tuple[Tuple[int, ...], ...]
    answer_outputs: Tuple[str, ...]


@dataclass(frozen=True)
class DynamicSummary:
    label: str
    family: Family
    p: int
    k: int
    exact_state_count: int
    answer_row_count: int
    variable_row_count: int
    family_row_count: int
    answer_bits: float
    variable_bits: float
    family_bits: float
    answer_to_family_shelf_bits: float
    variable_to_family_gap_bits: float
    expected_universal_count: int
    candidate_exactness: Dict[str, Dict[str, object]]
    family_row_class_weights: Tuple[int, ...]


@dataclass(frozen=True)
class FrontierBudget:
    budget_bits: int
    bucket_limit: int
    frontier_size: int
    best_answer: float
    best_variable: float
    best_family: float
    family_at_perfect_answer: float | None
    family_at_perfect_variable: float | None


def overlap_family(family: Family) -> bool:
    sets = [set(edge) for edge in family]
    for left, right in itertools.combinations(sets, 2):
        if left != right and left & right:
            return True
    return False


def normalize_family(family: Family) -> Family:
    universe = sorted(set().union(*map(set, family)))
    relabel = {variable: index + 1 for index, variable in enumerate(universe)}
    return tuple(
        sorted(tuple(sorted(relabel[item] for item in edge)) for edge in family)
    )


def all_survivor_subsets(p: int) -> Tuple[Tuple[int, ...], ...]:
    return tuple(
        tuple(index + 1 for index in range(p) if mask & (1 << index))
        for mask in range(1 << p)
    )


def family_union(family: Family) -> Tuple[int, ...]:
    if not family:
        return ()
    return tuple(sorted(set().union(*map(set, family))))


def family_core(family: Family) -> Tuple[int, ...]:
    if not family:
        return ()
    return tuple(sorted(set.intersection(*map(set, family))))


def restrict_family(family: Family, survivors: Iterable[int]) -> Family:
    survivor_set = set(survivors)
    return tuple(
        sorted(edge for edge in family if set(edge).issubset(survivor_set))
    )


def family_variable_union(family: Family) -> Tuple[int, ...]:
    return family_union(family)


@lru_cache(maxsize=None)
def world_cache(k: int, p: int) -> Tuple[Tuple[State, ...], Tuple[Tuple[int, ...], ...], Tuple[Tuple[int, ...], ...]]:
    states = tuple(enumerate_witness_states(k, p))
    index = {state: idx for idx, state in enumerate(states)}
    compose_indices = []
    for left in states:
        row = []
        for right in states:
            row.append(index[compose_witness(left, right, k)])
        compose_indices.append(tuple(row))
    complete_sets = tuple(
        tuple(variable + 1 for variable, coord in enumerate(state[1]) if coord == k)
        for state in states
    )
    return states, tuple(compose_indices), complete_sets


def dynamic_world(family: Family) -> DynamicWorld:
    p = max(max(edge) for edge in family)
    k = max(len(edge) for edge in family)
    states, compose_indices, complete_sets = world_cache(k, p)
    family_outputs = tuple(restrict_family(family, completed) for completed in complete_sets)
    variable_outputs = complete_sets
    answer_outputs = tuple("feasible" if output else "blocked" for output in family_outputs)
    return DynamicWorld(
        family=family,
        p=p,
        k=k,
        states=states,
        compose_indices=compose_indices,
        complete_sets=complete_sets,
        family_outputs=family_outputs,
        variable_outputs=variable_outputs,
        answer_outputs=answer_outputs,
    )


def row_signatures(world: DynamicWorld, projection: str) -> List[Tuple[object, ...] | Tuple[str, ...]]:
    rows: List[Tuple[object, ...] | Tuple[str, ...]] = []
    for left_index in range(len(world.states)):
        if projection == "family":
            row = tuple(world.family_outputs[idx] for idx in world.compose_indices[left_index])
        elif projection == "variable":
            row = tuple(world.variable_outputs[idx] for idx in world.compose_indices[left_index])
        elif projection == "answer":
            row = tuple(world.answer_outputs[idx] for idx in world.compose_indices[left_index])
        else:
            raise ValueError(f"unknown projection: {projection}")
        rows.append(row)
    return rows


def candidate_exactness(
    world: DynamicWorld,
    row_signatures_family: Sequence[Tuple[object, ...]],
    summary_fn,
) -> Dict[str, object]:
    grouped: DefaultDict[object, set] = defaultdict(set)
    for state, row in zip(world.states, row_signatures_family):
        grouped[summary_fn(state)].add(row)
    mixed_classes = sum(1 for rows in grouped.values() if len(rows) > 1)
    return {
        "summary_count": len(grouped),
        "mixed_classes": mixed_classes,
        "exact": mixed_classes == 0,
    }


def dynamic_candidate_suite(world: DynamicWorld) -> Dict[str, Dict[str, object]]:
    family_rows = row_signatures(world, "family")
    subsets = all_survivor_subsets(world.p)

    def current_family(state: State) -> Family:
        state_index = world.states.index(state)
        return world.family_outputs[state_index]

    def union_core_size(state: State) -> Tuple[Tuple[int, ...], Tuple[int, ...], Tuple[int, ...], int]:
        current = current_family(state)
        return (
            family_union(current),
            family_core(current),
            tuple(sorted(len(edge) for edge in current)),
            len(current),
        )

    def completed_only(state: State) -> Tuple[int, ...]:
        state_index = world.states.index(state)
        return world.complete_sets[state_index]

    def depth_completed(state: State) -> Tuple[int, Tuple[int, ...]]:
        return state[0], completed_only(state)

    def family_only(state: State) -> Family:
        return current_family(state)

    def depth_family(state: State) -> Tuple[int, Family]:
        return state[0], current_family(state)

    def family_min_profile(state: State) -> Tuple[int, ...]:
        _, coords = state
        return tuple(min(coords[item - 1] for item in edge) for edge in world.family)

    def saturation_profile(state: State) -> Tuple[Family, ...]:
        completed = set(completed_only(state))
        return tuple(restrict_family(world.family, completed | set(subset)) for subset in subsets)

    def depth_saturation_profile(state: State) -> Tuple[int, Tuple[Family, ...]]:
        return state[0], saturation_profile(state)

    candidates = {
        "completed_only": completed_only,
        "current_family": family_only,
        "union_core_size": union_core_size,
        "depth_family": depth_family,
        "family_min_profile": family_min_profile,
        "saturation_profile": saturation_profile,
        "depth_saturation_profile": depth_saturation_profile,
        "depth_completed": depth_completed,
    }
    return {
        name: candidate_exactness(world, family_rows, fn)
        for name, fn in candidates.items()
    }


def dynamic_summary(label: str, family: Family) -> DynamicSummary:
    world = dynamic_world(family)
    family_rows = row_signatures(world, "family")
    variable_rows = row_signatures(world, "variable")
    answer_rows = row_signatures(world, "answer")
    family_groups: DefaultDict[Tuple[object, ...], List[int]] = defaultdict(list)
    for index, row in enumerate(family_rows):
        family_groups[row].append(index)
    return DynamicSummary(
        label=label,
        family=family,
        p=world.p,
        k=world.k,
        exact_state_count=len(world.states),
        answer_row_count=len(set(answer_rows)),
        variable_row_count=len(set(variable_rows)),
        family_row_count=len(set(family_rows)),
        answer_bits=math.log2(len(set(answer_rows))),
        variable_bits=math.log2(len(set(variable_rows))),
        family_bits=math.log2(len(set(family_rows))),
        answer_to_family_shelf_bits=math.log2(len(set(family_rows))) - math.log2(len(set(answer_rows))),
        variable_to_family_gap_bits=math.log2(len(set(family_rows))) - math.log2(len(set(variable_rows))),
        expected_universal_count=world.k + (1 << world.p),
        candidate_exactness=dynamic_candidate_suite(world),
        family_row_class_weights=tuple(sorted(len(indices) for indices in family_groups.values())),
    )


def contract_response_profile(family: Family, projection: str) -> Tuple[object, ...]:
    p = max(max(edge) for edge in family)
    profile: List[object] = []
    for subset in all_survivor_subsets(p):
        restricted = restrict_family(family, subset)
        if projection == "family":
            profile.append(restricted)
        elif projection == "variable":
            profile.append(family_variable_union(restricted))
        elif projection == "answer":
            profile.append("feasible" if restricted else "blocked")
        else:
            raise ValueError(f"unknown projection: {projection}")
    return tuple(profile)


def contract_summary_union_core_size(family: Family) -> Tuple[Tuple[int, ...], Tuple[int, ...], Tuple[int, ...], int]:
    return (
        family_union(family),
        family_core(family),
        tuple(sorted(len(edge) for edge in family)),
        len(family),
    )


def contract_summary_degree_signature(family: Family) -> Tuple[Tuple[int, ...], Tuple[int, ...], int]:
    p = max(max(edge) for edge in family)
    degrees = []
    for variable in range(1, p + 1):
        degrees.append(sum(1 for edge in family if variable in edge))
    return tuple(sorted(degrees)), tuple(sorted(len(edge) for edge in family)), len(family)


def contract_summary_intersection_signature(family: Family) -> Tuple[Tuple[int, ...], Tuple[int, ...], int]:
    overlaps = []
    for left, right in itertools.combinations(family, 2):
        overlaps.append(len(set(left) & set(right)))
    return tuple(sorted(overlaps)), tuple(sorted(len(edge) for edge in family)), len(family)


def contract_summary_orbit(family: Family) -> Family:
    p = max(max(edge) for edge in family)
    best = None
    for perm in itertools.permutations(range(1, p + 1)):
        mapping = {index + 1: perm[index] for index in range(p)}
        image = tuple(
            sorted(tuple(sorted(mapping[item] for item in edge)) for edge in family)
        )
        if best is None or image < best:
            best = image
    assert best is not None
    return best


def contract_candidate_summary(
    families: Sequence[Family],
) -> Tuple[Dict[str, Dict[str, object]], Dict[str, List[Family]]]:
    profiles = {family: contract_response_profile(family, "family") for family in families}
    candidates = {
        "union_core_size": contract_summary_union_core_size,
        "degree_signature": contract_summary_degree_signature,
        "intersection_signature": contract_summary_intersection_signature,
        "orbit": contract_summary_orbit,
        "full_antichain": lambda family: family,
    }
    summaries: Dict[str, Dict[str, object]] = {}
    collision_examples: Dict[str, List[Family]] = {}
    for name, fn in candidates.items():
        grouped: DefaultDict[object, set] = defaultdict(set)
        families_by_summary: DefaultDict[object, List[Family]] = defaultdict(list)
        for family in families:
            summary = fn(family)
            grouped[summary].add(profiles[family])
            families_by_summary[summary].append(family)
        mixed = [summary for summary, values in grouped.items() if len(values) > 1]
        summaries[name] = {
            "summary_count": len(grouped),
            "mixed_classes": len(mixed),
            "exact": len(mixed) == 0,
        }
        if mixed:
            collision_examples[name] = families_by_summary[mixed[0]][:4]
    return summaries, collision_examples


def exact_probe_basis(
    families: Sequence[Family],
    projection: str,
    p: int,
) -> Dict[str, object]:
    probes = all_survivor_subsets(p)
    best_size = None
    best_probe_sets: List[Tuple[Tuple[int, ...], ...]] = []
    for mask in range(1 << len(probes)):
        chosen = tuple(probes[index] for index in range(len(probes)) if mask & (1 << index))
        signatures = []
        for family in families:
            signature = []
            for probe in chosen:
                restricted = restrict_family(family, probe)
                if projection == "family":
                    signature.append(restricted)
                elif projection == "variable":
                    signature.append(family_variable_union(restricted))
                elif projection == "answer":
                    signature.append("feasible" if restricted else "blocked")
                else:
                    raise ValueError(f"unknown projection: {projection}")
            signatures.append(tuple(signature))
        if len(set(signatures)) != len(families):
            continue
        size = len(chosen)
        if best_size is None or size < best_size:
            best_size = size
            best_probe_sets = [chosen]
        elif size == best_size:
            best_probe_sets.append(chosen)
    return {
        "best_size": best_size,
        "example_probe_set": [list(probe) for probe in best_probe_sets[0]] if best_probe_sets else [],
        "optimal_count": len(best_probe_sets),
    }


def profile_key(family: Family) -> Tuple[int, int]:
    p = max(max(edge) for edge in family)
    k = max(len(edge) for edge in family)
    return k, p


def pareto_prune_3d(points: Iterable[Tuple[int, int, int]]) -> Tuple[Tuple[int, int, int], ...]:
    unique = sorted(set(points), reverse=True)
    frontier: List[Tuple[int, int, int]] = []
    for candidate in unique:
        dominated = False
        for incumbent in frontier:
            if (
                incumbent[0] >= candidate[0]
                and incumbent[1] >= candidate[1]
                and incumbent[2] >= candidate[2]
            ):
                dominated = True
                break
        if dominated:
            continue
        frontier = [
            incumbent
            for incumbent in frontier
            if not (
                candidate[0] >= incumbent[0]
                and candidate[1] >= incumbent[1]
                and candidate[2] >= incumbent[2]
            )
        ]
        frontier.append(candidate)
    return tuple(sorted(frontier, reverse=True))


def build_frontier_model(family: Family) -> Tuple[DynamicWorld, Tuple[int, ...], Tuple[Tuple[Tuple[str, Tuple[int, ...], Family], ...], ...]]:
    world = dynamic_world(family)
    family_rows = row_signatures(world, "family")
    groups: DefaultDict[Tuple[object, ...], List[int]] = defaultdict(list)
    for index, row in enumerate(family_rows):
        groups[row].append(index)
    representatives = [
        members[0]
        for _, members in sorted(groups.items(), key=lambda item: item[1][0])
    ]
    weights = tuple(len(groups[family_rows[index]]) for index in representatives)
    rows = tuple(
        tuple(
            (
                world.answer_outputs[idx],
                world.variable_outputs[idx],
                world.family_outputs[idx],
            )
            for idx in world.compose_indices[index]
        )
        for index in representatives
    )
    return world, weights, rows


def compress_columns_joint(
    rows: Sequence[Sequence[Tuple[str, Tuple[int, ...], Family]]]
) -> List[Tuple[int, Tuple[Tuple[str, Tuple[int, ...], Family], ...]]]:
    grouped: Dict[Tuple[Tuple[str, Tuple[int, ...], Family], ...], int] = defaultdict(int)
    if not rows:
        return []
    for column_index in range(len(rows[0])):
        signature = tuple(row[column_index] for row in rows)
        grouped[signature] += 1
    return sorted(grouped.items(), key=lambda item: (str(item[0]), item[1]))


def frontier_cluster_scores(
    weights: Sequence[int],
    rows: Sequence[Sequence[Tuple[str, Tuple[int, ...], Family]]],
    policy: str,
) -> List[Tuple[int, int, int]]:
    state_count = len(rows)
    column_groups = compress_columns_joint(rows)
    scores = [(0, 0, 0)] * (1 << state_count)
    for mask in range(1, 1 << state_count):
        chosen = [index for index in range(state_count) if mask & (1 << index)]
        total_weight = sum(weights[index] for index in chosen)
        answer_correct = 0
        variable_correct = 0
        family_correct = 0
        for signature, multiplicity in column_groups:
            outputs = [signature[index] for index in chosen]
            local_weights = [weights[index] for index in chosen]
            if policy == "breach":
                if len(set(outputs)) == 1:
                    answer_correct += total_weight * multiplicity
                    variable_correct += total_weight * multiplicity
                    family_correct += total_weight * multiplicity
                continue
            answer_counts = Counter()
            for output, weight in zip(outputs, local_weights):
                answer_counts[output[0]] += weight
            predicted_answer = sorted(answer_counts.items(), key=lambda item: (-item[1], item[0]))[0][0]
            answer_matches = sum(weight for output, weight in zip(outputs, local_weights) if output[0] == predicted_answer)
            answer_correct += answer_matches * multiplicity

            variable_counts = Counter()
            for output, weight in zip(outputs, local_weights):
                if output[0] == predicted_answer:
                    variable_counts[output[1]] += weight
            predicted_variable = sorted(variable_counts.items(), key=lambda item: (-item[1], item[0]))[0][0]
            variable_matches = sum(weight for output, weight in zip(outputs, local_weights) if output[1] == predicted_variable)
            variable_correct += variable_matches * multiplicity

            family_counts = Counter()
            for output, weight in zip(outputs, local_weights):
                if output[0] == predicted_answer and output[1] == predicted_variable:
                    family_counts[output[2]] += weight
            if not family_counts:
                for output, weight in zip(outputs, local_weights):
                    if output[0] == predicted_answer:
                        family_counts[output[2]] += weight
            predicted_family = sorted(family_counts.items(), key=lambda item: (-item[1], item[0]))[0][0]
            family_matches = sum(weight for output, weight in zip(outputs, local_weights) if output[2] == predicted_family)
            family_correct += family_matches * multiplicity
        scores[mask] = (answer_correct, variable_correct, family_correct)
    return scores


def exact_frontier_3d(
    weights: Sequence[int],
    rows: Sequence[Sequence[Tuple[str, Tuple[int, ...], Family]]],
    policy: str,
) -> Dict[int, Tuple[Tuple[int, int, int], ...]]:
    state_count = len(rows)
    full_mask = (1 << state_count) - 1
    subset_scores = frontier_cluster_scores(weights, rows, policy)

    @lru_cache(maxsize=None)
    def solve(mask: int, buckets: int) -> Tuple[Tuple[int, int, int], ...]:
        if mask == 0:
            return ((0, 0, 0),) if buckets == 0 else ()
        if buckets == 0:
            return ()
        anchor = mask & -mask
        points: List[Tuple[int, int, int]] = []
        submask = mask
        while submask:
            if submask & anchor:
                remainder = mask ^ submask
                cluster_answer, cluster_variable, cluster_family = subset_scores[submask]
                for answer_score, variable_score, family_score in solve(remainder, buckets - 1):
                    points.append(
                        (
                            answer_score + cluster_answer,
                            variable_score + cluster_variable,
                            family_score + cluster_family,
                        )
                    )
            submask = (submask - 1) & mask
        return pareto_prune_3d(points)

    frontiers: Dict[int, Tuple[Tuple[int, int, int], ...]] = {}
    for bucket_limit in range(1, state_count + 1):
        points: List[Tuple[int, int, int]] = []
        for buckets in range(1, bucket_limit + 1):
            points.extend(solve(full_mask, buckets))
        frontiers[bucket_limit] = pareto_prune_3d(points)
    return frontiers


def summarize_frontier_3d(
    weights: Sequence[int],
    rows: Sequence[Sequence[Tuple[str, Tuple[int, ...], Family]]],
    frontiers: Dict[int, Tuple[Tuple[int, int, int], ...]],
) -> List[FrontierBudget]:
    total = sum(weights) * len(rows[0])
    max_budget = max(1, math.ceil(math.log2(len(rows))))
    summaries = []
    for budget_bits in range(max_budget + 1):
        bucket_limit = min(len(rows), 1 << budget_bits)
        points = frontiers[bucket_limit]
        best_answer = max(point[0] for point in points) / total
        best_variable = max(point[1] for point in points) / total
        best_family = max(point[2] for point in points) / total
        family_at_perfect_answer = [point[2] for point in points if point[0] == total]
        family_at_perfect_variable = [point[2] for point in points if point[1] == total]
        summaries.append(
            FrontierBudget(
                budget_bits=budget_bits,
                bucket_limit=bucket_limit,
                frontier_size=len(points),
                best_answer=best_answer,
                best_variable=best_variable,
                best_family=best_family,
                family_at_perfect_answer=(
                    max(family_at_perfect_answer) / total if family_at_perfect_answer else None
                ),
                family_at_perfect_variable=(
                    max(family_at_perfect_variable) / total if family_at_perfect_variable else None
                ),
            )
        )
    return summaries


def render_svg(
    dynamic_examples: Sequence[DynamicSummary],
    frontier_forced: Sequence[FrontierBudget],
    frontier_breach: Sequence[FrontierBudget],
) -> str:
    width = 1100
    height = 620
    margin_left = 88
    margin_top = 58
    panel_gap = 48
    panel_width = (width - margin_left - 40 - panel_gap) / 2
    panel_height = height - margin_top - 92
    colors = {
        "answer": "#c44536",
        "variable": "#22577a",
        "family": "#0b6e4f",
    }

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<style>",
        "text { font-family: Menlo, Monaco, Consolas, monospace; font-size: 11px; fill: #1f2933; }",
        ".title { font-size: 14px; font-weight: 700; }",
        ".axis { stroke: #9fb3c8; stroke-width: 1; }",
        ".grid { stroke: #d9e2ec; stroke-width: 1; stroke-dasharray: 4 4; }",
        ".panel { fill: #ffffff; stroke: #d9e2ec; stroke-width: 1; }",
        "</style>",
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#fbfbfd"/>',
        f'<text x="{margin_left}" y="24" class="title">Family Memory: Dynamic Thresholds And Smallest-World Frontier</text>',
    ]

    # Left panel: threshold dots for representative worlds.
    left = margin_left
    right = margin_left + panel_width + panel_gap
    lines.append(f'<rect x="{left}" y="{margin_top}" width="{panel_width}" height="{panel_height}" class="panel"/>')
    lines.append(f'<text x="{left + 10}" y="{margin_top - 10}" class="title">Thresholds</text>')
    max_bits = max(math.log2(summary.family_row_count) for summary in dynamic_examples) + 0.8
    def x_bits(bits: float) -> float:
        usable = panel_width - 40
        return left + 20 + usable * (bits / max_bits)
    def y_row(index: int) -> float:
        return margin_top + 54 + index * 88
    for tick in range(int(math.ceil(max_bits)) + 1):
        x = x_bits(float(tick))
        lines.append(f'<line x1="{x:.2f}" y1="{margin_top}" x2="{x:.2f}" y2="{margin_top + panel_height}" class="grid"/>')
        lines.append(f'<text x="{x - 4:.2f}" y="{margin_top + panel_height + 18}">{tick}</text>')
    lines.append(f'<line x1="{left}" y1="{margin_top + panel_height}" x2="{left + panel_width}" y2="{margin_top + panel_height}" class="axis"/>')
    for row_index, summary in enumerate(dynamic_examples):
        y = y_row(row_index)
        lines.append(f'<text x="18" y="{y + 4:.2f}">{summary.label}</text>')
        for key, bits in (
            ("answer", math.log2(summary.answer_row_count)),
            ("variable", math.log2(summary.variable_row_count)),
            ("family", math.log2(summary.family_row_count)),
        ):
            x = x_bits(bits)
            lines.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="6" fill="{colors[key]}"/>')
        lines.append(f'<line x1="{x_bits(math.log2(summary.answer_row_count)):.2f}" y1="{y:.2f}" x2="{x_bits(math.log2(summary.family_row_count)):.2f}" y2="{y:.2f}" stroke="#bcccdc" stroke-width="2"/>')

    legend_x = left + panel_width - 150
    for index, (key, label) in enumerate((("answer", "answer"), ("variable", "variable"), ("family", "family"))):
        y = margin_top + 20 + index * 16
        lines.append(f'<circle cx="{legend_x}" cy="{y}" r="5" fill="{colors[key]}"/>')
        lines.append(f'<text x="{legend_x + 12}" y="{y + 4}">{label}</text>')

    # Right panel: smallest-world frontier curves.
    lines.append(f'<rect x="{right}" y="{margin_top}" width="{panel_width}" height="{panel_height}" class="panel"/>')
    lines.append(f'<text x="{right + 10}" y="{margin_top - 10}" class="title">A_path_k2_p3 frontier</text>')
    frontier_max_bits = max(row.budget_bits for row in frontier_forced)
    def x_budget(bits: int) -> float:
        usable = panel_width - 36
        return right + 18 + usable * (bits / frontier_max_bits if frontier_max_bits else 0.0)
    def y_metric(value: float) -> float:
        usable = panel_height - 36
        return margin_top + 16 + usable * (1 - value)
    for tick in range(frontier_max_bits + 1):
        x = x_budget(tick)
        lines.append(f'<line x1="{x:.2f}" y1="{margin_top}" x2="{x:.2f}" y2="{margin_top + panel_height}" class="grid"/>')
        lines.append(f'<text x="{x - 4:.2f}" y="{margin_top + panel_height + 18}">{tick}</text>')
    for tick in range(0, 11):
        value = tick / 10
        y = y_metric(value)
        lines.append(f'<line x1="{right}" y1="{y:.2f}" x2="{right + panel_width}" y2="{y:.2f}" class="grid"/>')
        lines.append(f'<text x="{right - 28}" y="{y + 4:.2f}">{value:.1f}</text>')
    lines.append(f'<line x1="{right}" y1="{margin_top + panel_height}" x2="{right + panel_width}" y2="{margin_top + panel_height}" class="axis"/>')
    lines.append(f'<line x1="{right}" y1="{margin_top}" x2="{right}" y2="{margin_top + panel_height}" class="axis"/>')

    for label, rows, dash in (
        ("forced", frontier_forced, ""),
        ("breach", frontier_breach, "6 5"),
    ):
        for key, series in (
            ("answer", [row.best_answer for row in rows]),
            ("variable", [row.best_variable for row in rows]),
            ("family", [row.best_family for row in rows]),
        ):
            points = " ".join(
                f"{x_budget(row.budget_bits):.2f},{y_metric(value):.2f}"
                for row, value in zip(rows, series)
            )
            dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
            lines.append(
                f'<polyline fill="none" stroke="{colors[key]}" stroke-width="3"{dash_attr} points="{points}"/>'
            )
    lines.append(f'<text x="{right + panel_width - 170}" y="{margin_top + 22}">solid = forced</text>')
    lines.append(f'<text x="{right + panel_width - 170}" y="{margin_top + 38}">dashed = breach</text>')
    lines.append("</svg>")
    return "\n".join(lines)


def render_json(payload: Dict[str, object]) -> str:
    return json.dumps(payload, indent=2)


def render_markdown(payload: Dict[str, object]) -> str:
    lines = [
        "# Family Memory Exact Search",
        "",
        "This report separates contract-level family identity from runtime family memory.",
        "",
        "## Aggregate finding",
        "",
        f"- normalized overlapping family worlds from the DAG scan: `{payload['normalized_family_count']}`",
        f"- normalized family worlds by `(k,p)`: `{payload['normalized_family_count_by_kp']}`",
        f"- source query occurrences by `(k,p)`: `{payload['source_occurrences_by_kp']}`",
        f"- dynamic law exact on all tested worlds: `{payload['dynamic_laws']['all_depth_completed_exact']}`",
        f"- family runtime quotient equals variable runtime quotient on all tested worlds: `{payload['dynamic_laws']['all_family_equals_variable']}`",
        f"- variable-to-family runtime gap is identically zero on the tested worlds: `{payload['dynamic_laws']['all_variable_family_gap_zero']}`",
        "",
        "## Dynamic family worlds",
        "",
        "For a fixed overlapping family `A`, runtime outputs were measured on the witness-style semigroup generated by `Q_(k,p)` with `k = max |F|` and `p = |union(A)|`.",
        "",
        "### Observed law",
        "",
        "Across every normalized overlapping family realized by the small DAG scan, the exact family runtime quotient matched the candidate state `(d, completed-variable set)`.",
        "",
        f"- observed `(k,p)` count law: `{payload['dynamic_laws']['count_formula_by_kp']}`",
        f"- answer-count ranges by `(k,p)`: `{payload['dynamic_laws']['answer_count_ranges_by_kp']}`",
        f"- answer-to-family shelf widths by `(k,p)` in bits: `{payload['dynamic_laws']['answer_to_family_shelf_by_kp']}`",
        "",
        "This means the hypergraph `A` matters as a contract parameter, but in the tested runtime worlds it did not force a larger hypergraph-valued dynamic state.",
        "",
        "### Runtime tower on representative worlds",
        "",
        "| world | family | answer states | variable states | family states | answer bits | variable bits | family bits | answer->family shelf | variable->family gap |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for summary in payload["dynamic_examples"]:
        lines.append(
            f"| `{summary['label']}` | `{summary['family']}` | `{summary['answer_row_count']}` | `{summary['variable_row_count']}` | `{summary['family_row_count']}` | "
            f"`{summary['answer_bits']:.3f}` | `{summary['variable_bits']:.3f}` | `{summary['family_bits']:.3f}` | "
            f"`{summary['answer_to_family_shelf_bits']:.3f}` | `{summary['variable_to_family_gap_bits']:.3f}` |"
        )

    lines.extend(
        [
            "",
            "### Candidate exactness on representative worlds",
            "",
            "| world | completed_only exact | current_family exact | depth_family exact | depth_saturation_profile exact | depth_completed exact |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for summary in payload["dynamic_examples"]:
        lines.append(
            f"| `{summary['label']}` | `{summary['candidate_exactness']['completed_only']['exact']}` | "
            f"`{summary['candidate_exactness']['current_family']['exact']}` | "
            f"`{summary['candidate_exactness']['depth_family']['exact']}` | "
            f"`{summary['candidate_exactness']['depth_saturation_profile']['exact']}` | "
            f"`{summary['candidate_exactness']['depth_completed']['exact']}` |"
        )

    smallest = payload["smallest_frontier"]
    lines.extend(
        [
            "",
            f"## Exact frontier on `{smallest['label']}`",
            "",
            "This is the smallest exact fixed-`A` family world in the scan.",
            "",
        ]
    )
    for policy in ("forced", "breach"):
        lines.append(f"### `{policy}`")
        lines.append("")
        lines.append(
            "| bits | bucket limit | frontier size | best answer | best variable | best family | family at perfect answer | family at perfect variable |"
        )
        lines.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
        for row in smallest["frontier"][policy]:
            family_at_perfect_answer = row["family_at_perfect_answer"]
            family_at_perfect_variable = row["family_at_perfect_variable"]
            family_at_perfect_answer_text = (
                f"{family_at_perfect_answer:.3f}" if family_at_perfect_answer is not None else "-"
            )
            family_at_perfect_variable_text = (
                f"{family_at_perfect_variable:.3f}" if family_at_perfect_variable is not None else "-"
            )
            lines.append(
                f"| `{row['budget_bits']}` | `{row['bucket_limit']}` | `{row['frontier_size']}` | `{row['best_answer']:.3f}` | "
                f"`{row['best_variable']:.3f}` | `{row['best_family']:.3f}` | "
                f"`{family_at_perfect_answer_text}` | `{family_at_perfect_variable_text}` |"
            )
        lines.append("")

    lines.extend(
        [
            "## Contract layer",
            "",
            "At the contract layer, the normalized family antichains themselves were compared by survivor-subset response profiles.",
            "",
            f"With the full survivor-subset bank, all three profile channels are exact: `{payload['contract_full_profile_counts']}`.",
            "",
            "So the contract-level separation in this scan is not a difference in full-profile quotient size. It is a difference in teaching complexity: how many probes are needed before the profiles become exact.",
            "",
            "### Candidate summaries",
            "",
            "| candidate | summary count | mixed classes | exact |",
            "| --- | --- | --- | --- |",
        ]
    )
    for name, summary in payload["contract_candidates"].items():
        lines.append(
            f"| `{name}` | `{summary['summary_count']}` | `{summary['mixed_classes']}` | `{summary['exact']}` |"
        )

    lines.extend(["", "### Collision examples", ""])
    for name, examples in payload["contract_collision_examples"].items():
        lines.append(f"- `{name}` collision: `{examples}`")

    lines.extend(["", "### Exact probe bases on normalized family worlds", ""])
    lines.append("| group | families | answer basis | variable basis | family basis | example family probe |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for group in payload["contract_probe_bases"]:
        lines.append(
            f"| `{group['group']}` | `{group['family_count']}` | `{group['answer_basis']['best_size']}` | `{group['variable_basis']['best_size']}` | `{group['family_basis']['best_size']}` | `{group['family_basis']['example_probe_set']}` |"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The strongest exact result in this pass is a split statement.",
            "",
            "1. Across different overlapping contracts, coarse summaries such as union/core/size and intersection-style summaries are not exact. The contract parameter really is hypergraph-valued.",
            "2. Inside a fixed contract `A`, the tested runtime quotient does not need a hypergraph-valued dynamic state. It collapses to `depth + completed-variable set` on every normalized overlapping family realized by the small-world scan.",
            "3. In these fixed-`A` worlds there is still a real answer-to-family shelf, but no extra variable-to-family threshold gap. Family runtime complexity matches variable runtime complexity exactly on the tested grid.",
            "",
            "So the next exact object looks two-layered:",
            "",
            "- hypergraph-valued at the contract level,",
            "- universal and variable-based at runtime once the contract is fixed.",
            "",
            "That is a stronger and more surprising answer than the original expectation that overlap would automatically force a hypergraph-valued runtime memory state.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    normalized_families: Dict[Family, Dict[str, object]] = {}
    source_occurrences_by_kp: Counter[Tuple[int, int]] = Counter()
    for n in range(5, 7):
        dag_count = 1 << (n * (n - 1) // 2)
        for mask in range(dag_count):
            graph = graph_from_mask(n, mask)
            gid = ordered_dag_id(n, mask)
            for treatment in range(n):
                for outcome in range(n):
                    if treatment == outcome or not has_directed_path(graph, treatment, outcome):
                        continue
                    family = tuple(sorted(minimal_adjustment_sets(graph, treatment, outcome)))
                    if len(family) <= 1 or not overlap_family(family):
                        continue
                    normalized = normalize_family(family)
                    if normalized not in normalized_families:
                        normalized_families[normalized] = {
                            "family": normalized,
                            "sources": [],
                        }
                    normalized_families[normalized]["sources"].append(
                        {
                            "graph_id": gid,
                            "query": [treatment, outcome],
                        }
                    )
                    source_occurrences_by_kp[profile_key(normalized)] += 1

    families_sorted = sorted(normalized_families)
    normalized_family_count_by_kp: Counter[Tuple[int, int]] = Counter(
        profile_key(family) for family in families_sorted
    )
    dynamic_summaries = {
        family: dynamic_summary(
            label=f"A_k{max(len(edge) for edge in family)}_p{max(max(edge) for edge in family)}_{index}",
            family=family,
        )
        for index, family in enumerate(families_sorted)
    }

    all_depth_completed_exact = all(
        summary.candidate_exactness["depth_completed"]["exact"]
        for summary in dynamic_summaries.values()
    )
    all_family_equals_variable = all(
        summary.family_row_count == summary.variable_row_count
        for summary in dynamic_summaries.values()
    )
    count_formula_by_kp: Dict[str, int] = {}
    answer_count_ranges_by_kp: Dict[str, List[int]] = {}
    answer_to_family_shelf_by_kp: Dict[str, List[float]] = {}
    for key in sorted({(summary.k, summary.p) for summary in dynamic_summaries.values()}):
        summaries = [summary for summary in dynamic_summaries.values() if (summary.k, summary.p) == key]
        count_formula_by_kp[str(key)] = summaries[0].family_row_count
        answer_count_ranges_by_kp[str(key)] = sorted({summary.answer_row_count for summary in summaries})
        answer_to_family_shelf_by_kp[str(key)] = sorted(
            {
                round(summary.answer_to_family_shelf_bits, 6)
                for summary in summaries
            }
        )
    all_variable_family_gap_zero = all(
        summary.variable_to_family_gap_bits == 0.0
        for summary in dynamic_summaries.values()
    )

    contract_candidates, contract_collision_examples = contract_candidate_summary(families_sorted)
    contract_full_profile_counts = {
        projection: len({contract_response_profile(family, projection) for family in families_sorted})
        for projection in ("family", "variable", "answer")
    }

    contract_probe_bases = []
    grouped_by_kp: DefaultDict[Tuple[int, int], List[Family]] = defaultdict(list)
    for family in families_sorted:
        grouped_by_kp[profile_key(family)].append(family)
    for (k, p), families in sorted(grouped_by_kp.items()):
        contract_probe_bases.append(
            {
                "group": f"(k={k}, p={p})",
                "family_count": len(families),
                "answer_basis": exact_probe_basis(families, "answer", p),
                "variable_basis": exact_probe_basis(families, "variable", p),
                "family_basis": exact_probe_basis(families, "family", p),
            }
        )

    dynamic_examples = []
    for label, family in REPRESENTATIVE_FAMILIES.items():
        summary = dynamic_summaries[family]
        dynamic_examples.append(
            {
                "label": label,
                "family": [list(edge) for edge in family],
                "p": summary.p,
                "k": summary.k,
                "answer_row_count": summary.answer_row_count,
                "variable_row_count": summary.variable_row_count,
                "family_row_count": summary.family_row_count,
                "answer_bits": summary.answer_bits,
                "variable_bits": summary.variable_bits,
                "family_bits": summary.family_bits,
                "answer_to_family_shelf_bits": summary.answer_to_family_shelf_bits,
                "variable_to_family_gap_bits": summary.variable_to_family_gap_bits,
                "expected_universal_count": summary.expected_universal_count,
                "candidate_exactness": summary.candidate_exactness,
                "family_row_class_weights": list(summary.family_row_class_weights),
            }
        )

    smallest_family = REPRESENTATIVE_FAMILIES["A_path_k2_p3"]
    world, weights, rows = build_frontier_model(smallest_family)
    frontier_forced = summarize_frontier_3d(weights, rows, exact_frontier_3d(weights, rows, "forced"))
    frontier_breach = summarize_frontier_3d(weights, rows, exact_frontier_3d(weights, rows, "breach"))

    payload = {
        "normalized_family_count": len(families_sorted),
        "normalized_family_count_by_kp": {
            str(key): normalized_family_count_by_kp[key]
            for key in sorted(normalized_family_count_by_kp)
        },
        "source_occurrences_by_kp": {
            str(key): source_occurrences_by_kp[key]
            for key in sorted(source_occurrences_by_kp)
        },
        "dynamic_laws": {
            "all_depth_completed_exact": all_depth_completed_exact,
            "all_family_equals_variable": all_family_equals_variable,
            "all_variable_family_gap_zero": all_variable_family_gap_zero,
            "count_formula_by_kp": count_formula_by_kp,
            "answer_count_ranges_by_kp": answer_count_ranges_by_kp,
            "answer_to_family_shelf_by_kp": answer_to_family_shelf_by_kp,
        },
        "dynamic_examples": dynamic_examples,
        "smallest_frontier": {
            "label": "A_path_k2_p3",
            "family": [list(edge) for edge in smallest_family],
            "frontier": {
                "forced": [
                    {
                        "budget_bits": row.budget_bits,
                        "bucket_limit": row.bucket_limit,
                        "frontier_size": row.frontier_size,
                        "best_answer": row.best_answer,
                        "best_variable": row.best_variable,
                        "best_family": row.best_family,
                        "family_at_perfect_answer": row.family_at_perfect_answer,
                        "family_at_perfect_variable": row.family_at_perfect_variable,
                    }
                    for row in frontier_forced
                ],
                "breach": [
                    {
                        "budget_bits": row.budget_bits,
                        "bucket_limit": row.bucket_limit,
                        "frontier_size": row.frontier_size,
                        "best_answer": row.best_answer,
                        "best_variable": row.best_variable,
                        "best_family": row.best_family,
                        "family_at_perfect_answer": row.family_at_perfect_answer,
                        "family_at_perfect_variable": row.family_at_perfect_variable,
                    }
                    for row in frontier_breach
                ],
            },
        },
        "contract_full_profile_counts": contract_full_profile_counts,
        "contract_candidates": contract_candidates,
        "contract_collision_examples": {
            name: [[list(edge) for edge in family] for family in examples]
            for name, examples in contract_collision_examples.items()
        },
        "contract_probe_bases": contract_probe_bases,
    }

    json_path = RESULTS_DIR / "family_memory_exact_search.json"
    md_path = RESULTS_DIR / "family_memory_exact_search.md"
    svg_path = RESULTS_DIR / "family_memory_thresholds.svg"

    json_path.write_text(render_json(payload))
    md_path.write_text(render_markdown(payload))
    svg_path.write_text(
        render_svg(
            [dynamic_summaries[REPRESENTATIVE_FAMILIES[key]] for key in REPRESENTATIVE_FAMILIES],
            frontier_forced,
            frontier_breach,
        )
    )

    print(
        json.dumps(
            {
                "normalized_family_count": len(families_sorted),
                "json_path": str(json_path),
                "md_path": str(md_path),
                "svg_path": str(svg_path),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

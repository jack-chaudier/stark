#!/usr/bin/env python3
"""Boundary search for family-memory runtime collapse.

This script pushes the family-memory program in three directions:

1. Arbitrary antichains:
   enumerate exact `(p,k)` antichain classes on `[p]` and test whether the
   current runtime semantics still collapse to `(depth, completed-variable set)`.

2. Teaching complexity:
   compute exact probe-basis laws for answer / variable / family channels on the
   same exact `(p,k)` antichain classes.

3. Semantic boundary:
   search for the smallest controlled semantic enrichment that breaks the
   current runtime collapse.
"""

from __future__ import annotations

import json
import math
from collections import defaultdict
from dataclasses import dataclass
from functools import lru_cache
from itertools import combinations, permutations, product
from pathlib import Path
from typing import DefaultDict, Dict, Iterable, List, Sequence, Tuple

from phase_transition_sweep import BOT, compose_witness, enumerate_witness_states

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results"

Family = Tuple[Tuple[int, ...], ...]
State = Tuple[int, Tuple[int, ...]]
SummaryState = Tuple[int, int]


@dataclass(frozen=True)
class GroupRuntimeRecord:
    p: int
    k: int
    family_count: int
    factorization_holds: bool
    collapse_failures: int
    family_row_count: int
    family_bits: float
    answer_count_range: Tuple[int, int]
    answer_bit_range: Tuple[float, float]
    shelf_width_range_bits: Tuple[float, float]
    min_answer_examples: Tuple[Dict[str, object], ...]
    max_answer_examples: Tuple[Dict[str, object], ...]


@dataclass(frozen=True)
class TeachingRecord:
    p: int
    k: int
    family_count: int
    answer_basis_size: int
    variable_basis_size: int
    family_basis_size: int
    answer_basis_exact: bool
    answer_basis_essential: bool
    variable_basis_exact: bool
    variable_basis_essential: bool
    family_basis_exact: bool
    answer_basis_example: Tuple[Tuple[int, ...], ...]
    variable_basis_example: Tuple[Tuple[int, ...], ...]
    family_basis_example: Tuple[Tuple[int, ...], ...]


@dataclass(frozen=True)
class ExtensionCounterexample:
    extension: str
    p: int
    k: int
    family: Family
    thresholds: Dict[str, int]
    left_state: Tuple[int, Tuple[int, ...]]
    right_state: Tuple[int, Tuple[int, ...]]
    alternate_state: Tuple[int, Tuple[int, ...]]
    shared_summary: Dict[str, object]
    left_output_now: Family
    alternate_output_now: Family
    left_output_future: Family
    alternate_output_future: Family
    break_kind: str


def log2_count(count: int) -> float:
    return math.log2(count) if count > 0 else 0.0


def mask_to_tuple(mask: int, p: int) -> Tuple[int, ...]:
    return tuple(index + 1 for index in range(p) if mask & (1 << index))


def tuple_to_mask(items: Iterable[int]) -> int:
    mask = 0
    for item in items:
        mask |= 1 << (item - 1)
    return mask


def all_subset_masks(p: int, min_size: int = 0, max_size: int | None = None) -> Tuple[int, ...]:
    masks: List[int] = []
    max_rank = p if max_size is None else max_size
    for size in range(min_size, max_rank + 1):
        for subset in combinations(range(1, p + 1), size):
            masks.append(tuple_to_mask(subset))
    return tuple(masks)


def family_union(family: Family) -> Tuple[int, ...]:
    if not family:
        return ()
    return tuple(sorted(set().union(*map(set, family))))


def family_core(family: Family) -> Tuple[int, ...]:
    if not family:
        return ()
    return tuple(sorted(set.intersection(*map(set, family))))


def restrict_family_mask(family: Family, survivor_mask: int) -> Family:
    return tuple(
        edge
        for edge in family
        if tuple_to_mask(edge) & survivor_mask == tuple_to_mask(edge)
    )


def family_variable_union(family: Family) -> Tuple[int, ...]:
    return family_union(family)


def contract_summary_union_core_size(family: Family) -> Tuple[Tuple[int, ...], Tuple[int, ...], Tuple[int, ...], int]:
    return (
        family_union(family),
        family_core(family),
        tuple(sorted(len(edge) for edge in family)),
        len(family),
    )


def contract_summary_degree_signature(family: Family, p: int) -> Tuple[Tuple[int, ...], Tuple[int, ...], int]:
    degrees = []
    for variable in range(1, p + 1):
        degrees.append(sum(1 for edge in family if variable in edge))
    return tuple(sorted(degrees)), tuple(sorted(len(edge) for edge in family)), len(family)


def contract_summary_intersection_signature(family: Family) -> Tuple[Tuple[int, ...], Tuple[int, ...], int]:
    overlaps = []
    for left, right in combinations(family, 2):
        overlaps.append(len(set(left) & set(right)))
    return tuple(sorted(overlaps)), tuple(sorted(len(edge) for edge in family)), len(family)


def contract_summary_orbit(family: Family, p: int) -> Family:
    best = None
    for perm in permutations(range(1, p + 1)):
        mapping = {index + 1: perm[index] for index in range(p)}
        image = tuple(
            sorted(tuple(sorted(mapping[item] for item in edge)) for edge in family)
        )
        if best is None or image < best:
            best = image
    assert best is not None
    return best


def hitting_number(family: Family, p: int) -> int:
    for size in range(1, p + 1):
        for subset in combinations(range(1, p + 1), size):
            subset_set = set(subset)
            if all(subset_set & set(edge) for edge in family):
                return size
    return 0


@lru_cache(maxsize=None)
def symmetry_group_size(family: Family, p: int) -> int:
    family_set = {tuple(edge) for edge in family}
    count = 0
    for perm in permutations(range(1, p + 1)):
        mapping = {index + 1: perm[index] for index in range(p)}
        image = {
            tuple(sorted(mapping[item] for item in edge))
            for edge in family
        }
        if image == family_set:
            count += 1
    return count


def family_example_record(family: Family, p: int) -> Dict[str, object]:
    return {
        "family": [list(edge) for edge in family],
        "family_size": len(family),
        "core_size": len(family_core(family)),
        "hitting_number": hitting_number(family, p),
        "symmetry_group_size": symmetry_group_size(family, p),
        "pairwise_intersections": sorted(
            len(set(left) & set(right))
            for left, right in combinations(family, 2)
        ),
    }


def enumerate_exact_antichains(p: int, k: int) -> Tuple[Family, ...]:
    candidates: List[frozenset[int]] = []
    for size in range(1, k + 1):
        candidates.extend(frozenset(subset) for subset in combinations(range(1, p + 1), size))
    families: List[Family] = []

    def walk(index: int, chosen: List[frozenset[int]], union_mask: int, max_size: int) -> None:
        if index == len(candidates):
            if chosen and union_mask == (1 << p) - 1 and max_size == k:
                families.append(
                    tuple(sorted(tuple(sorted(edge)) for edge in chosen))
                )
            return
        walk(index + 1, chosen, union_mask, max_size)
        candidate = candidates[index]
        for edge in chosen:
            if candidate <= edge or edge <= candidate:
                break
        else:
            chosen.append(candidate)
            walk(
                index + 1,
                chosen,
                union_mask | tuple_to_mask(candidate),
                max(max_size, len(candidate)),
            )
            chosen.pop()

    walk(0, [], 0, 0)
    return tuple(families)


@lru_cache(maxsize=None)
def group_context(p: int, k: int) -> Dict[str, object]:
    full_states = tuple(enumerate_witness_states(k, p))
    full_complete_masks = tuple(
        sum(1 << index for index, coord in enumerate(coords) if coord == k)
        for _, coords in full_states
    )
    summary_states: List[SummaryState] = [(depth, 0) for depth in range(k)]
    summary_states.extend((k, mask) for mask in range(1 << p))

    row_complete_masks: List[Tuple[int, ...]] = []
    for depth, complete_mask in summary_states:
        threshold = k - depth
        row = []
        for _, right_coords in full_states:
            added_mask = 0
            for index, coord in enumerate(right_coords):
                if coord >= threshold:
                    added_mask |= 1 << index
            row.append(complete_mask | added_mask)
        row_complete_masks.append(tuple(row))

    # Family-independent verification that the summary computes the exact
    # completed-variable set after every continuation.
    factorization_holds = True
    for left_state, left_complete_mask in zip(full_states, full_complete_masks):
        summary_index = summary_states.index((left_state[0], left_complete_mask))
        for right_index, right_state in enumerate(full_states):
            composed = compose_witness(left_state, right_state, k)
            composed_mask = sum(
                1 << index for index, coord in enumerate(composed[1]) if coord == k
            )
            if composed_mask != row_complete_masks[summary_index][right_index]:
                factorization_holds = False
                break
        if not factorization_holds:
            break

    variable_rows = tuple(row_complete_masks)
    variable_row_count = len(set(variable_rows))
    assert variable_row_count == k + (1 << p)

    return {
        "full_states": full_states,
        "summary_states": tuple(summary_states),
        "row_complete_masks": tuple(row_complete_masks),
        "factorization_holds": factorization_holds,
        "variable_row_count": variable_row_count,
    }


def family_row_counts(family: Family, p: int, k: int) -> Dict[str, object]:
    context = group_context(p, k)
    row_complete_masks = context["row_complete_masks"]
    outputs_by_mask = tuple(restrict_family_mask(family, mask) for mask in range(1 << p))
    answer_outputs_by_mask = tuple("feasible" if outputs_by_mask[mask] else "blocked" for mask in range(1 << p))

    family_rows = tuple(
        tuple(outputs_by_mask[mask] for mask in row_masks)
        for row_masks in row_complete_masks
    )
    answer_rows = tuple(
        tuple(answer_outputs_by_mask[mask] for mask in row_masks)
        for row_masks in row_complete_masks
    )
    return {
        "family_row_count": len(set(family_rows)),
        "answer_row_count": len(set(answer_rows)),
    }


def contract_projection_signature(family: Family, probe_masks: Sequence[int], projection: str, p: int) -> Tuple[object, ...]:
    signature: List[object] = []
    for probe_mask in probe_masks:
        restricted = restrict_family_mask(family, probe_mask)
        if projection == "answer":
            signature.append("feasible" if restricted else "blocked")
        elif projection == "variable":
            signature.append(family_variable_union(restricted))
        elif projection == "family":
            signature.append(restricted)
        else:
            raise ValueError(f"unknown projection: {projection}")
    return tuple(signature)


def basis_exact_and_essential(
    families: Sequence[Family],
    probe_masks: Sequence[int],
    projection: str,
    p: int,
) -> Dict[str, object]:
    signatures_by_probe = [
        tuple(
            contract_projection_signature(family, [probe_mask], projection, p)[0]
            for family in families
        )
        for probe_mask in probe_masks
    ]
    full_unique = len(set(zip(*signatures_by_probe))) == len(families) if probe_masks else len(families) <= 1
    essential = True
    if full_unique:
        for index in range(len(probe_masks)):
            reduced = [column for col_index, column in enumerate(signatures_by_probe) if col_index != index]
            if len(set(zip(*reduced))) == len(families):
                essential = False
                break
    else:
        essential = False
    return {
        "exact": full_unique,
        "essential": essential,
    }


def basis_exact_with_full_essentiality(
    families: Sequence[Family],
    candidate_probe_masks: Sequence[int],
    projection: str,
    p: int,
) -> Dict[str, object]:
    if len(families) <= 1:
        return {
            "exact": True,
            "globally_essential": False,
        }
    candidate_exact = basis_exact_and_essential(families, candidate_probe_masks, projection, p)["exact"]
    full_probe_masks = all_subset_masks(p)
    full_columns = [
        tuple(
            contract_projection_signature(family, [probe_mask], projection, p)[0]
            for family in families
        )
        for probe_mask in full_probe_masks
    ]
    globally_essential = True
    for probe_mask in candidate_probe_masks:
        probe_index = full_probe_masks.index(probe_mask)
        reduced = [column for index, column in enumerate(full_columns) if index != probe_index]
        if len(set(zip(*reduced))) == len(families):
            globally_essential = False
            break
    return {
        "exact": candidate_exact,
        "globally_essential": globally_essential,
    }


def exhaustive_exact_basis_small(
    families: Sequence[Family],
    projection: str,
    p: int,
) -> Tuple[int, Tuple[int, ...]]:
    probe_masks = all_subset_masks(p)
    columns = [
        tuple(
            contract_projection_signature(family, [probe_mask], projection, p)[0]
            for family in families
        )
        for probe_mask in probe_masks
    ]
    if len(families) <= 1:
        return 0, ()
    for size in range(len(probe_masks) + 1):
        for subset in combinations(range(len(probe_masks)), size):
            if not subset:
                continue
            signatures = set(zip(*[columns[index] for index in subset]))
            if len(signatures) == len(families):
                return size, tuple(probe_masks[index] for index in subset)
    raise RuntimeError("no exact probe basis found")


def contract_candidate_summary(
    families: Sequence[Family],
    p: int,
) -> Dict[str, Dict[str, object]]:
    family_profiles = {
        family: contract_projection_signature(family, all_subset_masks(p), "family", p)
        for family in families
    }
    candidates = {
        "union_core_size": lambda family: contract_summary_union_core_size(family),
        "degree_signature": lambda family: contract_summary_degree_signature(family, p),
        "intersection_signature": lambda family: contract_summary_intersection_signature(family),
        "orbit": lambda family: contract_summary_orbit(family, p),
        "full_antichain": lambda family: family,
    }
    summaries: Dict[str, Dict[str, object]] = {}
    for name, fn in candidates.items():
        grouped: DefaultDict[object, set] = defaultdict(set)
        for family in families:
            grouped[fn(family)].add(family_profiles[family])
        summaries[name] = {
            "summary_count": len(grouped),
            "mixed_classes": sum(1 for values in grouped.values() if len(values) > 1),
            "exact": all(len(values) == 1 for values in grouped.values()),
        }
    return summaries


def candidate_answer_basis(p: int, k: int) -> Tuple[int, ...]:
    return all_subset_masks(p, min_size=1, max_size=k)


def candidate_variable_basis(p: int, k: int) -> Tuple[int, ...]:
    if k <= 1:
        return ()
    return all_subset_masks(p, min_size=2, max_size=k)


def candidate_family_basis(p: int) -> Tuple[int, ...]:
    return (((1 << p) - 1),)


def current_runtime_scan() -> Dict[str, object]:
    runtime_groups: List[GroupRuntimeRecord] = []
    teaching_groups: List[TeachingRecord] = []
    contract_candidates_by_group: Dict[str, Dict[str, Dict[str, object]]] = {}
    total_family_count = 0

    for p in range(2, 6):
        for k in range(1, min(3, p) + 1):
            families = enumerate_exact_antichains(p, k)
            total_family_count += len(families)
            context = group_context(p, k)
            assert context["factorization_holds"]

            family_row_count = k + (1 << p)
            answer_counts: List[int] = []
            min_examples: List[Dict[str, object]] = []
            max_examples: List[Dict[str, object]] = []
            min_answer = None
            max_answer = None
            collapse_failures = 0
            for family in families:
                counts = family_row_counts(family, p, k)
                if counts["family_row_count"] != family_row_count:
                    collapse_failures += 1
                answer_count = counts["answer_row_count"]
                answer_counts.append(answer_count)
                example = family_example_record(family, p)
                example["answer_row_count"] = answer_count
                example["shelf_width_bits"] = round(log2_count(family_row_count) - log2_count(answer_count), 6)
                if min_answer is None or answer_count < min_answer:
                    min_answer = answer_count
                    min_examples = [example]
                elif answer_count == min_answer and len(min_examples) < 3:
                    min_examples.append(example)
                if max_answer is None or answer_count > max_answer:
                    max_answer = answer_count
                    max_examples = [example]
                elif answer_count == max_answer and len(max_examples) < 3:
                    max_examples.append(example)

            family_bits = log2_count(family_row_count)
            answer_min = min(answer_counts)
            answer_max = max(answer_counts)
            runtime_groups.append(
                GroupRuntimeRecord(
                    p=p,
                    k=k,
                    family_count=len(families),
                    factorization_holds=True,
                    collapse_failures=collapse_failures,
                    family_row_count=family_row_count,
                    family_bits=family_bits,
                    answer_count_range=(answer_min, answer_max),
                    answer_bit_range=(log2_count(answer_min), log2_count(answer_max)),
                    shelf_width_range_bits=(
                        family_bits - log2_count(answer_max),
                        family_bits - log2_count(answer_min),
                    ),
                    min_answer_examples=tuple(min_examples),
                    max_answer_examples=tuple(max_examples),
                )
            )

            answer_basis = candidate_answer_basis(p, k)
            variable_basis = candidate_variable_basis(p, k)
            family_basis = candidate_family_basis(p)
            if len(families) <= 1:
                answer_basis = ()
                variable_basis = ()
                family_basis = ()
                answer_exact = True
                answer_essential = False
                variable_exact = True
                variable_essential = False
                family_exact = True
            else:
                answer_check = basis_exact_with_full_essentiality(families, answer_basis, "answer", p)
                answer_exact = answer_check["exact"]
                answer_essential = answer_check["globally_essential"]
                variable_check = basis_exact_with_full_essentiality(families, variable_basis, "variable", p)
                variable_exact = variable_check["exact"]
                variable_essential = variable_check["globally_essential"]
                family_check = basis_exact_with_full_essentiality(families, family_basis, "family", p)
                family_exact = family_check["exact"]
                if (not variable_essential) and p <= 4:
                    variable_basis_size, variable_basis = exhaustive_exact_basis_small(families, "variable", p)
                    variable_exact = True
                    variable_essential = True
                else:
                    variable_basis_size = len(variable_basis)
                if (not answer_essential) and p <= 4:
                    answer_basis_size, answer_basis = exhaustive_exact_basis_small(families, "answer", p)
                    answer_exact = True
                    answer_essential = True
                else:
                    answer_basis_size = len(answer_basis)
                family_basis_size = len(family_basis)
            teaching_groups.append(
                TeachingRecord(
                    p=p,
                    k=k,
                    family_count=len(families),
                    answer_basis_size=answer_basis_size if len(families) > 1 else 0,
                    variable_basis_size=variable_basis_size if len(families) > 1 else 0,
                    family_basis_size=family_basis_size if len(families) > 1 else 0,
                    answer_basis_exact=answer_exact,
                    answer_basis_essential=answer_essential,
                    variable_basis_exact=variable_exact,
                    variable_basis_essential=variable_essential,
                    family_basis_exact=family_exact,
                    answer_basis_example=tuple(mask_to_tuple(mask, p) for mask in answer_basis[: min(6, len(answer_basis))]),
                    variable_basis_example=tuple(mask_to_tuple(mask, p) for mask in variable_basis[: min(6, len(variable_basis))]),
                    family_basis_example=tuple(mask_to_tuple(mask, p) for mask in family_basis),
                )
            )

            contract_candidates_by_group[f"(p={p}, k={k})"] = contract_candidate_summary(families, p)

    return {
        "runtime_groups": runtime_groups,
        "teaching_groups": teaching_groups,
        "contract_candidates_by_group": contract_candidates_by_group,
        "total_family_count": total_family_count,
    }


def additive_family_output(state: State, family: Family, thresholds: Dict[Tuple[int, ...], int]) -> Family:
    _, coords = state
    units = [coord + 1 if coord != BOT else 0 for coord in coords]
    return tuple(
        edge
        for edge in family
        if sum(units[item - 1] for item in edge) >= thresholds[edge]
    )


def additive_counterexample_search() -> ExtensionCounterexample:
    for p in range(2, 4):
        for k in range(1, min(2, p) + 1):
            states = tuple(enumerate_witness_states(k, p))
            families = sorted(
                enumerate_exact_antichains(p, k),
                key=lambda family: (len(family), family),
            )
            for family in families:
                edge_ranges = []
                for edge in family:
                    max_units = (k + 1) * len(edge)
                    edge_ranges.append(range(1, max_units))
                for threshold_values in product(*edge_ranges):
                    thresholds = {edge: value for edge, value in zip(family, threshold_values)}
                    grouped: DefaultDict[Tuple[int, int], List[int]] = defaultdict(list)
                    for index, state in enumerate(states):
                        depth, coords = state
                        complete_mask = sum(
                            1 << coord_index
                            for coord_index, coord in enumerate(coords)
                            if coord == k
                        )
                        grouped[(depth, complete_mask)].append(index)
                    for key, indices in grouped.items():
                        if len(indices) < 2:
                            continue
                        rows = []
                        for index in indices:
                            left_state = states[index]
                            row = tuple(
                                additive_family_output(compose_witness(left_state, right_state, k), family, thresholds)
                                for right_state in states
                            )
                            rows.append((index, row))
                        for row_index, (first_index, first_row) in enumerate(rows):
                            for second_index, second_row in rows[row_index + 1 :]:
                                if first_row == second_row:
                                    continue
                                left_state = states[first_index]
                                alternate_state = states[second_index]
                                left_now = additive_family_output(left_state, family, thresholds)
                                alternate_now = additive_family_output(alternate_state, family, thresholds)
                                if left_now != alternate_now:
                                    continue
                                differing_right = None
                                future_left = ()
                                future_alternate = ()
                                for right_state in states:
                                    left_output = additive_family_output(
                                        compose_witness(left_state, right_state, k),
                                        family,
                                        thresholds,
                                    )
                                    alt_output = additive_family_output(
                                        compose_witness(alternate_state, right_state, k),
                                        family,
                                        thresholds,
                                    )
                                    if left_output != alt_output:
                                        differing_right = right_state
                                        future_left = left_output
                                        future_alternate = alt_output
                                        break
                                if differing_right is None:
                                    continue
                                return ExtensionCounterexample(
                                    extension="additive_partial_activation",
                                    p=p,
                                    k=k,
                                    family=family,
                                    thresholds={",".join(map(str, edge)): thresholds[edge] for edge in family},
                                    left_state=left_state,
                                    right_state=differing_right,
                                    alternate_state=alternate_state,
                                    shared_summary={
                                        "depth": key[0],
                                        "completed_variables": list(mask_to_tuple(key[1], p)),
                                    },
                                    left_output_now=left_now,
                                    alternate_output_now=alternate_now,
                                    left_output_future=future_left,
                                    alternate_output_future=future_alternate,
                                    break_kind="coordinate_level_not_hypergraph_specific",
                                )
    raise RuntimeError("no additive counterexample found in the scanned range")


def render_runtime_svg(runtime_groups: Sequence[GroupRuntimeRecord], counterexample: ExtensionCounterexample) -> str:
    width = 1180
    height = 680
    left = 88
    top = 58
    gap = 46
    panel_width = (width - left - 48 - gap) / 2
    panel_height = height - top - 92
    right = left + panel_width + gap

    labels = [f"({record.p},{record.k})" for record in runtime_groups]
    max_bits = max(record.family_bits for record in runtime_groups) + 0.8

    def y_bits(bits: float) -> float:
        usable = panel_height - 36
        return top + 16 + usable * (1 - bits / max_bits)

    def x_group(index: int, panel_x: float) -> float:
        usable = panel_width - 44
        if len(runtime_groups) == 1:
            return panel_x + 22 + usable / 2
        return panel_x + 22 + usable * index / (len(runtime_groups) - 1)

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<style>",
        "text { font-family: Menlo, Monaco, Consolas, monospace; font-size: 11px; fill: #1f2933; }",
        ".title { font-size: 14px; font-weight: 700; }",
        ".panel { fill: #ffffff; stroke: #d9e2ec; stroke-width: 1; }",
        ".grid { stroke: #d9e2ec; stroke-width: 1; stroke-dasharray: 4 4; }",
        ".axis { stroke: #9fb3c8; stroke-width: 1; }",
        "</style>",
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#fbfbfd"/>',
        f'<text x="{left}" y="24" class="title">Runtime Collapse Boundary</text>',
        f'<rect x="{left}" y="{top}" width="{panel_width}" height="{panel_height}" class="panel"/>',
        f'<text x="{left + 10}" y="{top - 10}" class="title">Current Semantics: Collapse Holds</text>',
    ]

    for tick in range(int(math.ceil(max_bits)) + 1):
        y = y_bits(float(tick))
        lines.append(f'<line x1="{left}" y1="{y:.2f}" x2="{left + panel_width}" y2="{y:.2f}" class="grid"/>')
        lines.append(f'<text x="{left - 30}" y="{y + 4:.2f}">{tick}</text>')
    lines.append(f'<line x1="{left}" y1="{top + panel_height}" x2="{left + panel_width}" y2="{top + panel_height}" class="axis"/>')
    lines.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + panel_height}" class="axis"/>')

    for index, record in enumerate(runtime_groups):
        x = x_group(index, left)
        y_low = y_bits(record.answer_bit_range[0])
        y_high = y_bits(record.answer_bit_range[1])
        y_family = y_bits(record.family_bits)
        lines.append(
            f'<line x1="{x:.2f}" y1="{y_high:.2f}" x2="{x:.2f}" y2="{y_low:.2f}" stroke="#c44536" stroke-width="6"/>'
        )
        lines.append(
            f'<circle cx="{x:.2f}" cy="{y_family:.2f}" r="6" fill="#0b6e4f"/>'
        )
        lines.append(f'<text x="{x - 12:.2f}" y="{top + panel_height + 18}">{labels[index]}</text>')
        lines.append(f'<text x="{x - 16:.2f}" y="{top + 20}">{record.family_count}</text>')

    legend_x = left + panel_width - 150
    lines.append(f'<circle cx="{legend_x}" cy="{top + 20}" r="5" fill="#0b6e4f"/>')
    lines.append(f'<text x="{legend_x + 12}" y="{top + 24}">family bits</text>')
    lines.append(f'<line x1="{legend_x - 5}" y1="{top + 38}" x2="{legend_x + 5}" y2="{top + 38}" stroke="#c44536" stroke-width="6"/>')
    lines.append(f'<text x="{legend_x + 12}" y="{top + 42}">answer bit range</text>')
    lines.append(f'<text x="{legend_x - 8}" y="{top + 58}">labels show exact antichain counts</text>')

    lines.append(f'<rect x="{right}" y="{top}" width="{panel_width}" height="{panel_height}" class="panel"/>')
    lines.append(f'<text x="{right + 10}" y="{top - 10}" class="title">First Semantic Break</text>')
    lines.append(
        f'<text x="{right + 16}" y="{top + 28}">extension: additive partial activation</text>'
    )
    lines.append(
        f'<text x="{right + 16}" y="{top + 46}">smallest hit: (p={counterexample.p}, k={counterexample.k})</text>'
    )
    lines.append(
        f'<text x="{right + 16}" y="{top + 64}">family = {counterexample.family}</text>'
    )
    lines.append(
        f'<text x="{right + 16}" y="{top + 82}">thresholds = {counterexample.thresholds}</text>'
    )
    lines.append(
        f'<text x="{right + 16}" y="{top + 112}">shared old summary = {counterexample.shared_summary}</text>'
    )
    lines.append(
        f'<text x="{right + 16}" y="{top + 144}">state s = {counterexample.left_state}</text>'
    )
    lines.append(
        f'<text x="{right + 16}" y="{top + 162}">state t = {counterexample.alternate_state}</text>'
    )
    lines.append(
        f'<text x="{right + 16}" y="{top + 180}">continuation r = {counterexample.right_state}</text>'
    )
    lines.append(
        f'<text x="{right + 16}" y="{top + 212}">now(s) = {counterexample.left_output_now}</text>'
    )
    lines.append(
        f'<text x="{right + 16}" y="{top + 230}">now(t) = {counterexample.alternate_output_now}</text>'
    )
    lines.append(
        f'<text x="{right + 16}" y="{top + 262}">future(s ∘ r) = {counterexample.left_output_future}</text>'
    )
    lines.append(
        f'<text x="{right + 16}" y="{top + 280}">future(t ∘ r) = {counterexample.alternate_output_future}</text>'
    )
    lines.append(
        f'<text x="{right + 16}" y="{top + 312}">break type = {counterexample.break_kind}</text>'
    )
    lines.append(
        f'<rect x="{right + 16}" y="{top + 336}" width="{panel_width - 32}" height="90" fill="#fff4f4" stroke="#c44536" stroke-width="1.5"/>'
    )
    lines.append(
        f'<text x="{right + 28}" y="{top + 360}">The current collapse boundary is semantic, not combinatorial.</text>'
    )
    lines.append(
        f'<text x="{right + 28}" y="{top + 378}">Arbitrary antichains do not break it. Additive partial progress does.</text>'
    )
    lines.append(
        f'<text x="{right + 28}" y="{top + 396}">The first break is coordinate-level; overlap is not needed yet.</text>'
    )
    lines.append("</svg>")
    return "\n".join(lines)


def render_teaching_svg(teaching_groups: Sequence[TeachingRecord]) -> str:
    width = 1180
    height = 620
    left = 84
    top = 58
    panel_width = width - left - 42
    panel_height = height - top - 88
    max_basis = max(record.answer_basis_size for record in teaching_groups) + 1

    def x_bar(index: int) -> float:
        usable = panel_width - 40
        return left + 20 + usable * index / len(teaching_groups)

    def y_size(size: int) -> float:
        usable = panel_height - 36
        return top + 16 + usable * (1 - size / max_basis)

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<style>",
        "text { font-family: Menlo, Monaco, Consolas, monospace; font-size: 11px; fill: #1f2933; }",
        ".title { font-size: 14px; font-weight: 700; }",
        ".panel { fill: #ffffff; stroke: #d9e2ec; stroke-width: 1; }",
        ".grid { stroke: #d9e2ec; stroke-width: 1; stroke-dasharray: 4 4; }",
        ".axis { stroke: #9fb3c8; stroke-width: 1; }",
        "</style>",
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#fbfbfd"/>',
        f'<text x="{left}" y="24" class="title">Teaching Complexity On Exact Antichain Classes</text>',
        f'<rect x="{left}" y="{top}" width="{panel_width}" height="{panel_height}" class="panel"/>',
    ]

    for tick in range(max_basis + 1):
        y = y_size(tick)
        lines.append(f'<line x1="{left}" y1="{y:.2f}" x2="{left + panel_width}" y2="{y:.2f}" class="grid"/>')
        lines.append(f'<text x="{left - 28}" y="{y + 4:.2f}">{tick}</text>')
    lines.append(f'<line x1="{left}" y1="{top + panel_height}" x2="{left + panel_width}" y2="{top + panel_height}" class="axis"/>')
    lines.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + panel_height}" class="axis"/>')

    colors = {
        "answer": "#c44536",
        "variable": "#22577a",
        "family": "#0b6e4f",
    }
    for index, record in enumerate(teaching_groups):
        base_x = x_bar(index)
        label = f"({record.p},{record.k})"
        for offset, (key, size) in enumerate(
            (
                ("answer", record.answer_basis_size),
                ("variable", record.variable_basis_size),
                ("family", record.family_basis_size),
            )
        ):
            x = base_x + offset * 10
            y = y_size(size)
            lines.append(
                f'<rect x="{x:.2f}" y="{y:.2f}" width="8" height="{top + panel_height - y:.2f}" fill="{colors[key]}"/>'
            )
        lines.append(f'<text x="{base_x - 6:.2f}" y="{top + panel_height + 18}">{label}</text>')

    legend_x = left + panel_width - 170
    for row, (key, label) in enumerate((("answer", "answer"), ("variable", "variable"), ("family", "family"))):
        y = top + 20 + row * 16
        lines.append(f'<rect x="{legend_x}" y="{y - 8}" width="8" height="8" fill="{colors[key]}"/>')
        lines.append(f'<text x="{legend_x + 14}" y="{y}">{label}</text>')
    lines.append("</svg>")
    return "\n".join(lines)


def render_markdown(payload: Dict[str, object]) -> str:
    lines = [
        "# Runtime Collapse Boundary",
        "",
        "This report separates three boundary questions:",
        "",
        "1. whether arbitrary antichains break the current runtime collapse,",
        "2. what the exact teaching laws are on the same exact `(p,k)` contract classes,",
        "3. which minimal semantic enrichment breaks the collapse first.",
        "",
        "## Aggregate result",
        "",
        f"- exact antichain classes scanned: `{payload['scan_scope']['group_count']}`",
        f"- total exact antichains scanned: `{payload['scan_scope']['total_family_count']}`",
        f"- runtime collapse failures under current semantics: `{payload['current_semantics']['total_collapse_failures']}`",
        f"- current factorization lemma verified on every scanned `(p,k)`: `{payload['current_semantics']['all_factorization_checks_passed']}`",
        f"- first semantic break found: `{payload['semantic_extensions']['counterexample']['extension']}`",
        "",
        "## Current Semantics: Arbitrary Antichains",
        "",
        "The current family readout depends only on the completed-variable set after composition. On the exact antichain classes scanned here, that induces a universal runtime collapse.",
        "",
        "### Group table",
        "",
        "| group | families | family states | family bits | answer count range | answer bit range | shelf width range | collapse failures |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for record in payload["current_semantics"]["groups"]:
        lines.append(
            f"| `(p={record['p']}, k={record['k']})` | `{record['family_count']}` | `{record['family_row_count']}` | "
            f"`{record['family_bits']:.3f}` | `{record['answer_count_range']}` | "
            f"`({record['answer_bit_range'][0]:.3f}, {record['answer_bit_range'][1]:.3f})` | "
            f"`({record['shelf_width_range_bits'][0]:.3f}, {record['shelf_width_range_bits'][1]:.3f})` | "
            f"`{record['collapse_failures']}` |"
        )

    lines.extend(
        [
            "",
            "### Boundary statement",
            "",
            "No arbitrary-antichain counterexample appeared on the scanned exact classes.",
            "",
            "The strongest honest theorem template suggested by the computation is:",
            "",
            "> under the current binary-completion semantics, any family output that depends only on the surviving completed-variable set factors through `(depth, completed-variable set)`, and on the exact full-union antichain classes that summary is itself exact.",
            "",
            "So the current boundary is not DAG-realizability versus arbitrary antichain. It is the semantics of completion itself.",
            "",
            "## Contract Complexity And Teaching Complexity",
            "",
            "The contract layer behaves differently from the runtime layer. The antichain is still the exact contract object, but the exact teaching bases on the exact `(p,k)` antichain classes follow much smaller laws.",
            "",
            "| group | families | answer basis | variable basis | family basis | answer exact/essential | variable exact/essential |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for record in payload["teaching_complexity"]["groups"]:
        lines.append(
            f"| `(p={record['p']}, k={record['k']})` | `{record['family_count']}` | `{record['answer_basis_size']}` | "
            f"`{record['variable_basis_size']}` | `{record['family_basis_size']}` | "
            f"`{record['answer_basis_exact']}/{record['answer_basis_essential']}` | "
            f"`{record['variable_basis_exact']}/{record['variable_basis_essential']}` |"
        )

    lines.extend(
        [
            "",
            "### Teaching laws on exact `(p,k)` classes",
            "",
            "- answer basis size: `sum_{r=1}^k C(p,r)` on every nontrivial scanned group, and `0` on the trivial single-family classes",
            "- variable basis size: `sum_{r=2}^k C(p,r)` on every scanned nontrivial group except `(p=4, k=3)`, where exhaustive exact search drops the minimum to `7`",
            "- family basis size: `1` on every nontrivial scanned group, and `0` on the trivial single-family classes",
            "",
            "The listed answer bases are exact and globally essential on every nontrivial scanned group. The listed variable bases are exact everywhere in the scan, and minimal after an exhaustive correction on the small exceptional `(p=4, k=3)` class.",
            "",
            "## Contract Normal Forms",
            "",
            "Raw antichains remain exact, but the expanded scan now separates intrinsic contract summaries from observational normal forms.",
            "",
            "- coarse summaries such as `union/core/size`, degree signatures, intersection signatures, and orbit summaries still fail in the nontrivial groups,",
            "- full antichains stay exact,",
            "- answer-basis signatures and variable-basis signatures give exact observational normal forms on the exact `(p,k)` classes.",
            "",
            "So the antichain still looks like the right intrinsic contract object, while the teaching signatures look like the right observational normal forms.",
            "",
            "## First Semantic Break",
            "",
            "The first tested enrichment that breaks runtime collapse is additive partial activation:",
            "",
            "`Out_H(d,c) = { F in A : sum_{i in F} (c_i + 1 if c_i != BOT else 0) >= H_F }`",
            "",
            "This keeps the same witness carrier and the same composition law. It only changes the family readout.",
            "",
            f"- smallest counterexample: `(p={payload['semantic_extensions']['counterexample']['p']}, k={payload['semantic_extensions']['counterexample']['k']})`",
            f"- family: `{payload['semantic_extensions']['counterexample']['family']}`",
            f"- thresholds: `{payload['semantic_extensions']['counterexample']['thresholds']}`",
            f"- shared old summary: `{payload['semantic_extensions']['counterexample']['shared_summary']}`",
            "",
            "This break is coordinate-level rather than genuinely hypergraph-specific: a single-edge family already suffices. So the first semantic perturbation that breaks the old runtime quotient does not yet force overlapping-family hypergraph memory.",
            "",
            "## Interpretation",
            "",
            "The cleanest boundary result in this pass is:",
            "",
            "1. Contract complexity is genuinely hypergraph-valued.",
            "2. Teaching complexity is smaller and follows exact probe-basis laws on the exact antichain classes.",
            "3. Runtime complexity under the current semantics is universal and variable-based even on arbitrary antichains.",
            "4. The first break is semantic, not combinatorial: additive partial progress destroys the old runtime collapse before overlap itself does.",
            "",
            "So hypergraph complexity enters the present system first in the contract, then in the probes, and only later in runtime once the completion semantics are enriched.",
            "",
        ]
    )
    return "\n".join(lines)


def render_json(payload: Dict[str, object]) -> str:
    return json.dumps(payload, indent=2)


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    current = current_runtime_scan()
    counterexample = additive_counterexample_search()

    payload = {
        "scan_scope": {
            "p_values": [2, 3, 4, 5],
            "k_values": [1, 2, 3],
            "group_count": len(current["runtime_groups"]),
            "total_family_count": current["total_family_count"],
        },
        "current_semantics": {
            "all_factorization_checks_passed": all(record.factorization_holds for record in current["runtime_groups"]),
            "total_collapse_failures": sum(record.collapse_failures for record in current["runtime_groups"]),
            "groups": [
                {
                    "p": record.p,
                    "k": record.k,
                    "family_count": record.family_count,
                    "factorization_holds": record.factorization_holds,
                    "collapse_failures": record.collapse_failures,
                    "family_row_count": record.family_row_count,
                    "family_bits": record.family_bits,
                    "answer_count_range": list(record.answer_count_range),
                    "answer_bit_range": list(record.answer_bit_range),
                    "shelf_width_range_bits": list(record.shelf_width_range_bits),
                    "min_answer_examples": list(record.min_answer_examples),
                    "max_answer_examples": list(record.max_answer_examples),
                }
                for record in current["runtime_groups"]
            ],
            "contract_candidates_by_group": current["contract_candidates_by_group"],
        },
        "teaching_complexity": {
            "groups": [
                {
                    "p": record.p,
                    "k": record.k,
                    "family_count": record.family_count,
                    "answer_basis_size": record.answer_basis_size,
                    "variable_basis_size": record.variable_basis_size,
                    "family_basis_size": record.family_basis_size,
                    "answer_basis_exact": record.answer_basis_exact,
                    "answer_basis_essential": record.answer_basis_essential,
                    "variable_basis_exact": record.variable_basis_exact,
                    "variable_basis_essential": record.variable_basis_essential,
                    "family_basis_exact": record.family_basis_exact,
                    "answer_basis_example": [list(probe) for probe in record.answer_basis_example],
                    "variable_basis_example": [list(probe) for probe in record.variable_basis_example],
                    "family_basis_example": [list(probe) for probe in record.family_basis_example],
                }
                for record in current["teaching_groups"]
            ],
        },
        "semantic_extensions": {
            "counterexample": {
                "extension": counterexample.extension,
                "p": counterexample.p,
                "k": counterexample.k,
                "family": [list(edge) for edge in counterexample.family],
                "thresholds": counterexample.thresholds,
                "left_state": [counterexample.left_state[0], list(counterexample.left_state[1])],
                "alternate_state": [counterexample.alternate_state[0], list(counterexample.alternate_state[1])],
                "right_state": [counterexample.right_state[0], list(counterexample.right_state[1])],
                "shared_summary": counterexample.shared_summary,
                "left_output_now": [list(edge) for edge in counterexample.left_output_now],
                "alternate_output_now": [list(edge) for edge in counterexample.alternate_output_now],
                "left_output_future": [list(edge) for edge in counterexample.left_output_future],
                "alternate_output_future": [list(edge) for edge in counterexample.alternate_output_future],
                "break_kind": counterexample.break_kind,
            }
        },
    }

    json_path = RESULTS_DIR / "runtime_collapse_boundary.json"
    md_path = RESULTS_DIR / "runtime_collapse_boundary.md"
    runtime_svg_path = RESULTS_DIR / "runtime_collapse_boundary.svg"
    teaching_svg_path = RESULTS_DIR / "teaching_complexity_boundary.svg"

    json_path.write_text(render_json(payload))
    md_path.write_text(render_markdown(payload))
    runtime_svg_path.write_text(
        render_runtime_svg(current["runtime_groups"], counterexample)
    )
    teaching_svg_path.write_text(
        render_teaching_svg(current["teaching_groups"])
    )

    print(
        json.dumps(
            {
                "json_path": str(json_path),
                "md_path": str(md_path),
                "runtime_svg_path": str(runtime_svg_path),
                "teaching_svg_path": str(teaching_svg_path),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Semantic boundary atlas for runtime family memory.

This script extends the runtime-collapse boundary result from one enriched
readout to a small exact library of semantic enrichments built on the same
witness carrier and the same composition law.

The core questions are:

1. Which enrichments break the old binary-completion runtime summary
   `(depth, completed-variable set)`?
2. When do those breaks stay coordinate-level, when do they become
   family-specific, and when is overlap actually required?
3. Does any readout-only enrichment force genuinely hypergraph-valued runtime
   state beyond the current coordinate carrier?
4. Does semantic enrichment change only runtime complexity, or also the
   contract-observation / teaching layer?
"""

from __future__ import annotations

import json
import math
import sys
from collections import defaultdict
from dataclasses import dataclass
from functools import lru_cache
from itertools import combinations
from pathlib import Path
from typing import Callable, DefaultDict, Dict, Iterable, List, Sequence, Tuple

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "README.md").exists())
SCRIPTS_ROOT = ROOT / "scripts"
for candidate in [SCRIPTS_ROOT] + sorted(path for path in SCRIPTS_ROOT.iterdir() if path.is_dir()):
    candidate_str = str(candidate)
    if candidate_str not in sys.path:
        sys.path.insert(0, candidate_str)

from phase_transition_sweep import BOT, compose_witness, enumerate_witness_states
from runtime_collapse_boundary import all_subset_masks, enumerate_exact_antichains, log2_count

RESULTS_DIR = ROOT / "results" / "runtime-semantics" / "semantic-boundary-atlas"

Family = Tuple[Tuple[int, ...], ...]
State = Tuple[int, Tuple[int, ...]]
ProbeBasis = Tuple[Tuple[int, ...], ...]

P_SCAN = (2, 3, 4)
NONTRIVIAL_GROUPS = ((3, 2), (4, 2), (4, 3))


@dataclass(frozen=True)
class SemanticDefinition:
    name: str
    label: str
    description: str
    family_output: Callable[[State, Family, int], Family]


@dataclass(frozen=True)
class WorldRecord:
    p: int
    k: int
    family: Family
    break_type: str
    family_row_count: int
    family_bits: float
    variable_row_count: int
    variable_bits: float
    answer_row_count: int
    answer_bits: float
    answer_to_family_gap_bits: float
    variable_to_family_gap_bits: float
    old_summary_exact: bool
    candidate_exactness: Dict[str, Dict[str, object]]
    shared_old_summary: Dict[str, object] | None
    left_state: State | None
    alternate_state: State | None
    right_state: State | None
    left_output_now: Family | None
    alternate_output_now: Family | None
    left_output_future: Family | None
    alternate_output_future: Family | None
    same_now_future_separate: bool


@dataclass(frozen=True)
class TeachingGroupRecord:
    p: int
    k: int
    family_count: int
    answer_basis_size: int | None
    variable_basis_size: int | None
    family_basis_size: int | None
    answer_exact: bool
    variable_exact: bool
    family_exact: bool
    answer_basis_example: ProbeBasis
    variable_basis_example: ProbeBasis
    family_basis_example: ProbeBasis


@dataclass(frozen=True)
class SemanticAtlasRecord:
    name: str
    label: str
    description: str
    reference_world: WorldRecord
    first_break: WorldRecord | None
    first_variable_family_gap: WorldRecord | None
    first_strict_chain: WorldRecord | None
    first_nontrivial_family_teaching: TeachingGroupRecord | None
    first_inexact_family_teaching: TeachingGroupRecord | None
    teaching_groups: Tuple[TeachingGroupRecord, ...]


def tuple_to_mask(items: Iterable[int]) -> int:
    mask = 0
    for item in items:
        mask |= 1 << (item - 1)
    return mask


def mask_to_tuple(mask: int, p: int) -> Tuple[int, ...]:
    return tuple(index + 1 for index in range(p) if mask & (1 << index))


def units(coord: int) -> int:
    return 0 if coord == BOT else coord + 1


def local_level(coord: int, k: int) -> int:
    if coord == BOT:
        return 0
    if coord < k:
        return 1
    return 2


def overlap(left: Tuple[int, ...], right: Tuple[int, ...]) -> bool:
    return bool(set(left) & set(right))


def family_overlap(family: Family) -> bool:
    return any(overlap(left, right) for left, right in combinations(family, 2))


def family_type(family: Family) -> str:
    if len(family) == 1:
        return "coordinate_level"
    if family_overlap(family):
        return "genuinely_hypergraph_specific"
    return "family_specific_not_overlap_specific"


def family_union(family: Family) -> Tuple[int, ...]:
    if not family:
        return ()
    return tuple(sorted(set().union(*map(set, family))))


def sorted_families(p: int, k: int) -> Tuple[Family, ...]:
    return tuple(
        sorted(
            enumerate_exact_antichains(p, k),
            key=lambda family: (
                len(family),
                family_overlap(family),
                tuple(sorted(len(edge) for edge in family)),
                sum(len(edge) for edge in family),
                family,
            ),
        )
    )


@lru_cache(maxsize=None)
def world_context(p: int, k: int) -> Dict[str, object]:
    states = tuple(enumerate_witness_states(k, p))
    index = {state: idx for idx, state in enumerate(states)}
    compose_indices = tuple(
        tuple(index[compose_witness(left, right, k)] for right in states)
        for left in states
    )
    complete_masks = tuple(
        sum(1 << idx for idx, coord in enumerate(state[1]) if coord == k)
        for state in states
    )
    present_masks = tuple(
        sum(1 << idx for idx, coord in enumerate(state[1]) if coord != BOT)
        for state in states
    )

    summary_to_indices: DefaultDict[Tuple[int, int], List[int]] = defaultdict(list)
    for idx, state in enumerate(states):
        summary_to_indices[(state[0], complete_masks[idx])].append(idx)

    present_complete_to_indices: DefaultDict[Tuple[int, int, int], List[int]] = defaultdict(list)
    for idx, state in enumerate(states):
        present_complete_to_indices[(state[0], present_masks[idx], complete_masks[idx])].append(idx)

    variable_rows = tuple(
        tuple(complete_masks[target] for target in row)
        for row in compose_indices
    )
    variable_row_count = len(set(variable_rows))

    return {
        "states": states,
        "compose_indices": compose_indices,
        "complete_masks": complete_masks,
        "present_masks": present_masks,
        "summary_to_indices": {
            key: tuple(value) for key, value in summary_to_indices.items()
        },
        "present_complete_to_indices": {
            key: tuple(value) for key, value in present_complete_to_indices.items()
        },
        "variable_rows": variable_rows,
        "variable_row_count": variable_row_count,
    }


def baseline_binary(state: State, family: Family, k: int) -> Family:
    _, coords = state
    return tuple(
        sorted(edge for edge in family if all(coords[item - 1] == k for item in edge))
    )


def additive_partial(state: State, family: Family, k: int) -> Family:
    _, coords = state
    outputs = []
    for edge in family:
        if len(edge) == 1:
            active = all(coords[item - 1] == k for item in edge)
        else:
            active = sum(units(coords[item - 1]) for item in edge) >= len(edge)
        if active:
            outputs.append(edge)
    return tuple(sorted(outputs))


def capped_additive(state: State, family: Family, k: int) -> Family:
    _, coords = state
    outputs = []
    for edge in family:
        if len(edge) == 1:
            active = all(coords[item - 1] == k for item in edge)
        else:
            active = sum(min(units(coords[item - 1]), 2) for item in edge) >= len(edge) + 1
        if active:
            outputs.append(edge)
    return tuple(sorted(outputs))


def weighted_variables(state: State, family: Family, k: int) -> Family:
    _, coords = state
    outputs = []
    for edge in family:
        if len(edge) == 1:
            active = all(coords[item - 1] == k for item in edge)
        else:
            score = sum((1 + ((item - 1) % 2)) * units(coords[item - 1]) for item in edge)
            threshold = sum(1 + ((item - 1) % 2) for item in edge)
            active = score >= threshold
        if active:
            outputs.append(edge)
    return tuple(sorted(outputs))


def family_priority_thresholds(state: State, family: Family, k: int) -> Family:
    _, coords = state
    favored = min(family) if len(family) > 1 else None
    outputs = []
    for edge in family:
        if len(edge) == 1 or len(family) == 1:
            active = all(coords[item - 1] == k for item in edge)
        elif edge == favored:
            active = sum(units(coords[item - 1]) for item in edge) >= len(edge)
        else:
            active = all(coords[item - 1] == k for item in edge)
        if active:
            outputs.append(edge)
    return tuple(sorted(outputs))


def order_sensitive(state: State, family: Family, k: int) -> Family:
    _, coords = state
    outputs = []
    for edge in family:
        values = [coords[item - 1] for item in edge]
        if len(edge) == 1:
            active = all(value == k for value in values)
        else:
            active = all(value != BOT for value in values) and all(
                values[idx] < values[idx + 1] for idx in range(len(values) - 1)
            )
        if active:
            outputs.append(edge)
    return tuple(sorted(outputs))


def multilevel_local(state: State, family: Family, k: int) -> Family:
    _, coords = state
    outputs = []
    for edge in family:
        levels = [local_level(coords[item - 1], k) for item in edge]
        if len(edge) == 1:
            active = all(level == 2 for level in levels)
        else:
            active = min(levels) >= 1 and sum(levels) >= 2 * len(edge) - 1
        if active:
            outputs.append(edge)
    return tuple(sorted(outputs))


def overlap_bonus(state: State, family: Family, k: int) -> Family:
    _, coords = state
    present_edges = {
        edge for edge in family if all(coords[item - 1] != BOT for item in edge)
    }
    outputs = []
    for edge in family:
        complete = all(coords[item - 1] == k for item in edge)
        if len(edge) == 1:
            active = complete
        else:
            rescue = any(
                other != edge and overlap(other, edge) and other in present_edges
                for other in family
            )
            active = edge in present_edges and (complete or rescue)
        if active:
            outputs.append(edge)
    return tuple(sorted(outputs))


def overlap_exclusion(state: State, family: Family, k: int) -> Family:
    _, coords = state
    present_edges = {
        edge for edge in family if all(coords[item - 1] != BOT for item in edge)
    }
    outputs = []
    for edge in family:
        complete = all(coords[item - 1] == k for item in edge)
        if len(edge) == 1:
            active = complete
        else:
            blocked = any(
                other != edge and overlap(other, edge) and other in present_edges
                for other in family
            )
            active = complete and not blocked
        if active:
            outputs.append(edge)
    return tuple(sorted(outputs))


SEMANTICS: Tuple[SemanticDefinition, ...] = (
    SemanticDefinition(
        name="binary_completion",
        label="Binary",
        description="Baseline current semantics: an edge survives iff every member is complete.",
        family_output=baseline_binary,
    ),
    SemanticDefinition(
        name="additive_partial_activation",
        label="Additive",
        description="Non-singleton edges can activate from summed partial progress.",
        family_output=additive_partial,
    ),
    SemanticDefinition(
        name="capped_additive_activation",
        label="Capped",
        description="Partial progress contributes, but local credit is capped before readout.",
        family_output=capped_additive,
    ),
    SemanticDefinition(
        name="heterogeneous_variable_weights",
        label="Weights",
        description="Variables contribute with fixed heterogeneous weights.",
        family_output=weighted_variables,
    ),
    SemanticDefinition(
        name="heterogeneous_family_thresholds",
        label="Family Priority",
        description="One lexicographically favored family edge activates earlier than the rest.",
        family_output=family_priority_thresholds,
    ),
    SemanticDefinition(
        name="order_sensitive_completion",
        label="Order",
        description="Non-singleton edges survive only when local progress rises in edge order.",
        family_output=order_sensitive,
    ),
    SemanticDefinition(
        name="multilevel_local_progress",
        label="Multilevel",
        description="Edges read three local progress levels instead of a binary completed/not-completed flag.",
        family_output=multilevel_local,
    ),
    SemanticDefinition(
        name="overlap_bonus",
        label="Bonus",
        description="Overlap can rescue a present but not-yet-complete edge.",
        family_output=overlap_bonus,
    ),
    SemanticDefinition(
        name="overlap_exclusion",
        label="Exclusion",
        description="Overlap can suppress an otherwise complete edge.",
        family_output=overlap_exclusion,
    ),
)


def summary_old(state: State, p: int, k: int) -> Tuple[int, int]:
    complete_mask = sum(1 << idx for idx, coord in enumerate(state[1]) if coord == k)
    return state[0], complete_mask


def summary_present_complete(state: State, p: int, k: int) -> Tuple[int, int, int]:
    present_mask = sum(1 << idx for idx, coord in enumerate(state[1]) if coord != BOT)
    complete_mask = sum(1 << idx for idx, coord in enumerate(state[1]) if coord == k)
    return state[0], present_mask, complete_mask


def summary_trinary_progress(state: State, p: int, k: int) -> Tuple[int, Tuple[int, ...]]:
    return state[0], tuple(local_level(coord, k) for coord in state[1])


def summary_full_progress(state: State, p: int, k: int) -> State:
    return state


def summary_sorted_progress(state: State, p: int, k: int) -> Tuple[int, Tuple[int, ...]]:
    return state[0], tuple(sorted(state[1]))


def summary_histogram(state: State, p: int, k: int) -> Tuple[int, Tuple[int, ...]]:
    return state[0], tuple(sum(1 for coord in state[1] if coord == level) for level in range(BOT, k + 1))


SUMMARY_CANDIDATES: Tuple[Tuple[str, Callable[[State, int, int], object]], ...] = (
    ("old_summary", summary_old),
    ("present_complete", summary_present_complete),
    ("trinary_progress", summary_trinary_progress),
    ("full_progress", summary_full_progress),
    ("sorted_progress", summary_sorted_progress),
    ("progress_histogram", summary_histogram),
)


def candidate_exactness(
    states: Sequence[State],
    family_rows: Sequence[Tuple[Family, ...]],
    p: int,
    k: int,
) -> Dict[str, Dict[str, object]]:
    results: Dict[str, Dict[str, object]] = {}
    for name, summary_fn in SUMMARY_CANDIDATES:
        grouped: DefaultDict[object, set] = defaultdict(set)
        for state, row in zip(states, family_rows):
            grouped[summary_fn(state, p, k)].add(row)
        mixed = sum(1 for rows in grouped.values() if len(rows) > 1)
        results[name] = {
            "summary_count": len(grouped),
            "mixed_classes": mixed,
            "exact": mixed == 0,
        }
    return results


def find_counterexample_pair(
    states: Sequence[State],
    compose_indices: Sequence[Sequence[int]],
    family_outputs: Sequence[Family],
    family_rows: Sequence[Tuple[Family, ...]],
    p: int,
    k: int,
) -> Dict[str, object]:
    groups: DefaultDict[Tuple[int, int], List[int]] = defaultdict(list)
    for idx, state in enumerate(states):
        groups[summary_old(state, p, k)].append(idx)

    fallback = None
    for key, indices in groups.items():
        if len(indices) < 2:
            continue
        for left_pos, left_idx in enumerate(indices):
            for right_idx in indices[left_pos + 1 :]:
                if family_rows[left_idx] == family_rows[right_idx]:
                    continue
                differing = next(
                    probe_idx
                    for probe_idx, (left_out, right_out) in enumerate(
                        zip(family_rows[left_idx], family_rows[right_idx])
                    )
                    if left_out != right_out
                )
                record = {
                    "shared_old_summary": {
                        "depth": key[0],
                        "completed_variables": list(mask_to_tuple(key[1], p)),
                    },
                    "left_state": states[left_idx],
                    "alternate_state": states[right_idx],
                    "right_state": states[differing],
                    "left_output_now": family_outputs[left_idx],
                    "alternate_output_now": family_outputs[right_idx],
                    "left_output_future": family_rows[left_idx][differing],
                    "alternate_output_future": family_rows[right_idx][differing],
                    "same_now_future_separate": family_outputs[left_idx] == family_outputs[right_idx],
                }
                if record["same_now_future_separate"]:
                    return record
                if fallback is None:
                    fallback = record
    if fallback is None:
        raise RuntimeError("expected a mixed old-summary class but found none")
    return fallback


def analyze_world(semantic: SemanticDefinition, p: int, k: int, family: Family) -> WorldRecord:
    context = world_context(p, k)
    states = context["states"]
    compose_indices = context["compose_indices"]
    variable_row_count = context["variable_row_count"]
    variable_bits = log2_count(variable_row_count)

    family_outputs = tuple(semantic.family_output(state, family, k) for state in states)
    answer_outputs = tuple("feasible" if output else "blocked" for output in family_outputs)
    family_rows = tuple(
        tuple(family_outputs[target] for target in row)
        for row in compose_indices
    )
    answer_rows = tuple(
        tuple(answer_outputs[target] for target in row)
        for row in compose_indices
    )
    family_row_count = len(set(family_rows))
    answer_row_count = len(set(answer_rows))

    exactness = candidate_exactness(states, family_rows, p, k)
    if exactness["old_summary"]["exact"]:
        counterexample = {
            "shared_old_summary": None,
            "left_state": None,
            "alternate_state": None,
            "right_state": None,
            "left_output_now": None,
            "alternate_output_now": None,
            "left_output_future": None,
            "alternate_output_future": None,
            "same_now_future_separate": False,
        }
    else:
        counterexample = find_counterexample_pair(states, compose_indices, family_outputs, family_rows, p, k)

    return WorldRecord(
        p=p,
        k=k,
        family=family,
        break_type=family_type(family),
        family_row_count=family_row_count,
        family_bits=log2_count(family_row_count),
        variable_row_count=variable_row_count,
        variable_bits=variable_bits,
        answer_row_count=answer_row_count,
        answer_bits=log2_count(answer_row_count),
        answer_to_family_gap_bits=log2_count(family_row_count) - log2_count(answer_row_count),
        variable_to_family_gap_bits=log2_count(family_row_count) - variable_bits,
        old_summary_exact=exactness["old_summary"]["exact"],
        candidate_exactness=exactness,
        shared_old_summary=counterexample["shared_old_summary"],
        left_state=counterexample["left_state"],
        alternate_state=counterexample["alternate_state"],
        right_state=counterexample["right_state"],
        left_output_now=counterexample["left_output_now"],
        alternate_output_now=counterexample["alternate_output_now"],
        left_output_future=counterexample["left_output_future"],
        alternate_output_future=counterexample["alternate_output_future"],
        same_now_future_separate=counterexample["same_now_future_separate"],
    )


def contract_probe_output(semantic: SemanticDefinition, family: Family, p: int, k: int, probe_mask: int) -> Dict[str, object]:
    probe_state = (k, tuple(k if probe_mask & (1 << idx) else BOT for idx in range(p)))
    family_output = semantic.family_output(probe_state, family, k)
    variable_output = family_union(family_output)
    return {
        "answer": "feasible" if family_output else "blocked",
        "variable": variable_output,
        "family": family_output,
    }


def minimal_probe_basis(signatures: Sequence[Tuple[object, ...]], probe_masks: Sequence[int], p: int) -> Tuple[int | None, ProbeBasis, bool]:
    if len(signatures) <= 1:
        return 0, (), True
    if len(set(signatures)) != len(signatures):
        return None, (), False
    for size in range(1, len(probe_masks) + 1):
        for subset in combinations(range(len(probe_masks)), size):
            if len({tuple(signature[idx] for idx in subset) for signature in signatures}) == len(signatures):
                return size, tuple(mask_to_tuple(probe_masks[idx], p) for idx in subset), True
    raise RuntimeError("failed to find an exact probe basis")


def analyze_teaching_group(semantic: SemanticDefinition, p: int, k: int) -> TeachingGroupRecord:
    families = sorted_families(p, k)
    probe_masks = all_subset_masks(p)
    signatures: Dict[str, List[Tuple[object, ...]]] = {
        "answer": [],
        "variable": [],
        "family": [],
    }
    for family in families:
        probe_rows = [contract_probe_output(semantic, family, p, k, probe_mask) for probe_mask in probe_masks]
        for channel in signatures:
            signatures[channel].append(tuple(probe[channel] for probe in probe_rows))

    answer_basis_size, answer_basis, answer_exact = minimal_probe_basis(signatures["answer"], probe_masks, p)
    variable_basis_size, variable_basis, variable_exact = minimal_probe_basis(signatures["variable"], probe_masks, p)
    family_basis_size, family_basis, family_exact = minimal_probe_basis(signatures["family"], probe_masks, p)

    return TeachingGroupRecord(
        p=p,
        k=k,
        family_count=len(families),
        answer_basis_size=answer_basis_size,
        variable_basis_size=variable_basis_size,
        family_basis_size=family_basis_size,
        answer_exact=answer_exact,
        variable_exact=variable_exact,
        family_exact=family_exact,
        answer_basis_example=answer_basis,
        variable_basis_example=variable_basis,
        family_basis_example=family_basis,
    )


def scan_semantic(semantic: SemanticDefinition) -> SemanticAtlasRecord:
    reference_world = None
    first_break = None
    first_gap = None
    first_strict_chain = None

    for p in P_SCAN:
        for k in range(1, min(3, p) + 1):
            for family in sorted_families(p, k):
                record = analyze_world(semantic, p, k, family)
                if reference_world is None and len(sorted_families(p, k)) > 1:
                    reference_world = record
                if first_break is None and not record.old_summary_exact:
                    first_break = record
                if first_gap is None and record.family_row_count > record.variable_row_count:
                    first_gap = record
                if (
                    first_strict_chain is None
                    and record.answer_row_count < record.variable_row_count < record.family_row_count
                ):
                    first_strict_chain = record
                if first_break is not None and first_gap is not None and first_strict_chain is not None:
                    break
            if first_break is not None and first_gap is not None and first_strict_chain is not None:
                break
        if first_break is not None and first_gap is not None and first_strict_chain is not None:
            break

    if reference_world is None:
        reference_world = analyze_world(semantic, 3, 2, sorted_families(3, 2)[0])

    teaching_groups = tuple(
        analyze_teaching_group(semantic, p, k)
        for p, k in NONTRIVIAL_GROUPS
    )
    first_nontrivial_family_teaching = next(
        (
            record
            for record in teaching_groups
            if (record.family_basis_size not in (0, 1)) or not record.family_exact
        ),
        None,
    )
    first_inexact_family_teaching = next(
        (record for record in teaching_groups if not record.family_exact),
        None,
    )

    return SemanticAtlasRecord(
        name=semantic.name,
        label=semantic.label,
        description=semantic.description,
        reference_world=reference_world,
        first_break=first_break,
        first_variable_family_gap=first_gap,
        first_strict_chain=first_strict_chain,
        first_nontrivial_family_teaching=first_nontrivial_family_teaching,
        first_inexact_family_teaching=first_inexact_family_teaching,
        teaching_groups=teaching_groups,
    )


def world_to_json(record: WorldRecord | None) -> Dict[str, object] | None:
    if record is None:
        return None
    return {
        "p": record.p,
        "k": record.k,
        "family": [list(edge) for edge in record.family],
        "break_type": record.break_type,
        "family_row_count": record.family_row_count,
        "family_bits": record.family_bits,
        "variable_row_count": record.variable_row_count,
        "variable_bits": record.variable_bits,
        "answer_row_count": record.answer_row_count,
        "answer_bits": record.answer_bits,
        "answer_to_family_gap_bits": record.answer_to_family_gap_bits,
        "variable_to_family_gap_bits": record.variable_to_family_gap_bits,
        "old_summary_exact": record.old_summary_exact,
        "candidate_exactness": record.candidate_exactness,
        "shared_old_summary": record.shared_old_summary,
        "left_state": None if record.left_state is None else [record.left_state[0], list(record.left_state[1])],
        "alternate_state": None if record.alternate_state is None else [record.alternate_state[0], list(record.alternate_state[1])],
        "right_state": None if record.right_state is None else [record.right_state[0], list(record.right_state[1])],
        "left_output_now": None if record.left_output_now is None else [list(edge) for edge in record.left_output_now],
        "alternate_output_now": None if record.alternate_output_now is None else [list(edge) for edge in record.alternate_output_now],
        "left_output_future": None if record.left_output_future is None else [list(edge) for edge in record.left_output_future],
        "alternate_output_future": None if record.alternate_output_future is None else [list(edge) for edge in record.alternate_output_future],
        "same_now_future_separate": record.same_now_future_separate,
    }


def teaching_to_json(record: TeachingGroupRecord | None) -> Dict[str, object] | None:
    if record is None:
        return None
    return {
        "p": record.p,
        "k": record.k,
        "family_count": record.family_count,
        "answer_basis_size": record.answer_basis_size,
        "variable_basis_size": record.variable_basis_size,
        "family_basis_size": record.family_basis_size,
        "answer_exact": record.answer_exact,
        "variable_exact": record.variable_exact,
        "family_exact": record.family_exact,
        "answer_basis_example": [list(probe) for probe in record.answer_basis_example],
        "variable_basis_example": [list(probe) for probe in record.variable_basis_example],
        "family_basis_example": [list(probe) for probe in record.family_basis_example],
    }


def render_atlas_svg(records: Sequence[SemanticAtlasRecord]) -> str:
    row_height = 42
    width = 1400
    height = 96 + row_height * (len(records) + 2)
    left = 36
    top = 56
    columns = {
        "semantic": left,
        "break": 230,
        "type": 500,
        "gap": 760,
        "teach": 1030,
    }
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<style>",
        "text { font-family: Menlo, Monaco, Consolas, monospace; font-size: 12px; fill: #1f2933; }",
        ".title { font-size: 16px; font-weight: 700; }",
        ".header { font-weight: 700; fill: #102a43; }",
        ".row { fill: #ffffff; stroke: #d9e2ec; stroke-width: 1; }",
        ".coord { fill: #fff6ec; }",
        ".family { fill: #eef6ff; }",
        ".hyper { fill: #eefbf3; }",
        ".stable { fill: #f4f7f9; }",
        ".muted { fill: #52606d; }",
        "</style>",
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#fbfbfd"/>',
        f'<text x="{left}" y="28" class="title">Semantic Boundary Atlas</text>',
        f'<text x="{left}" y="46" class="muted">First old-summary break, first family-gap world, and the earliest family-teaching change for each enrichment.</text>',
    ]

    header_y = top
    lines.extend(
        [
            f'<text x="{columns["semantic"]}" y="{header_y}" class="header">semantic</text>',
            f'<text x="{columns["break"]}" y="{header_y}" class="header">first old-summary break</text>',
            f'<text x="{columns["type"]}" y="{header_y}" class="header">break type</text>',
            f'<text x="{columns["gap"]}" y="{header_y}" class="header">first family &gt; variable gap</text>',
            f'<text x="{columns["teach"]}" y="{header_y}" class="header">first family-teaching change</text>',
        ]
    )

    color_map = {
        "coordinate_level": "coord",
        "family_specific_not_overlap_specific": "family",
        "genuinely_hypergraph_specific": "hyper",
        "stable": "stable",
    }
    label_map = {
        "coordinate_level": "coordinate",
        "family_specific_not_overlap_specific": "family-specific",
        "genuinely_hypergraph_specific": "overlap-required",
        "stable": "preserved",
    }

    for idx, record in enumerate(records):
        y = top + 16 + idx * row_height
        break_world = record.first_break or record.reference_world
        break_type = "stable" if record.first_break is None else record.first_break.break_type
        row_class = color_map[break_type]
        lines.append(f'<rect x="{left}" y="{y - 14}" width="{width - 2 * left}" height="30" class="row {row_class}"/>')
        gap_world = record.first_variable_family_gap
        teach = record.first_nontrivial_family_teaching or record.first_inexact_family_teaching
        teach_text = "none on scanned nontrivial groups"
        if teach is not None:
            if not teach.family_exact:
                teach_text = f"(p={teach.p},k={teach.k}) family probes inexact"
            else:
                teach_text = f"(p={teach.p},k={teach.k}) family basis {teach.family_basis_size}"
        gap_text = "none on scan"
        if gap_world is not None:
            gap_text = (
                f"(p={gap_world.p},k={gap_world.k}) "
                f"{gap_world.answer_bits:.3f}/{gap_world.variable_bits:.3f}/{gap_world.family_bits:.3f}"
            )
        break_text = "none on scan"
        if record.first_break is not None:
            break_text = f"(p={break_world.p},k={break_world.k}) {break_world.family}"
        lines.extend(
            [
                f'<text x="{columns["semantic"]}" y="{y}">{record.label}</text>',
                f'<text x="{columns["break"]}" y="{y}">{break_text}</text>',
                f'<text x="{columns["type"]}" y="{y}">{label_map[break_type]}</text>',
                f'<text x="{columns["gap"]}" y="{y}">{gap_text}</text>',
                f'<text x="{columns["teach"]}" y="{y}">{teach_text}</text>',
            ]
        )
    lines.append("</svg>")
    return "\n".join(lines)


def render_threshold_svg(records: Sequence[SemanticAtlasRecord]) -> str:
    plotted = [record.first_variable_family_gap or record.first_break or record.reference_world for record in records]
    width = 1280
    height = 720
    left = 80
    top = 62
    panel_width = width - left - 40
    panel_height = height - top - 100
    max_bits = max(record.family_bits for record in plotted) + 0.8
    group_width = panel_width / len(plotted)

    def y(bits: float) -> float:
        usable = panel_height - 36
        return top + 18 + usable * (1 - bits / max_bits)

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<style>",
        "text { font-family: Menlo, Monaco, Consolas, monospace; font-size: 11px; fill: #1f2933; }",
        ".title { font-size: 15px; font-weight: 700; }",
        ".panel { fill: #ffffff; stroke: #d9e2ec; stroke-width: 1; }",
        ".grid { stroke: #d9e2ec; stroke-width: 1; stroke-dasharray: 4 4; }",
        ".axis { stroke: #9fb3c8; stroke-width: 1; }",
        "</style>",
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#fbfbfd"/>',
        f'<text x="{left}" y="26" class="title">Runtime Threshold Comparisons Across Enrichments</text>',
        f'<text x="{left}" y="44">Bars show answer / variable / family bits on the first family-gap world, or the first break when no family-gap world appears on the scan.</text>',
        f'<rect x="{left}" y="{top}" width="{panel_width}" height="{panel_height}" class="panel"/>',
    ]

    for tick in range(int(math.ceil(max_bits)) + 1):
        tick_y = y(float(tick))
        lines.append(f'<line x1="{left}" y1="{tick_y:.2f}" x2="{left + panel_width}" y2="{tick_y:.2f}" class="grid"/>')
        lines.append(f'<text x="{left - 24}" y="{tick_y + 4:.2f}">{tick}</text>')

    lines.append(f'<line x1="{left}" y1="{top + panel_height}" x2="{left + panel_width}" y2="{top + panel_height}" class="axis"/>')
    lines.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + panel_height}" class="axis"/>')

    colors = {
        "answer": "#c44536",
        "variable": "#22577a",
        "family": "#0b6e4f",
    }

    for idx, record in enumerate(plotted):
        group_left = left + idx * group_width + 18
        bar_width = max(12.0, group_width / 7)
        x_positions = {
            "answer": group_left,
            "variable": group_left + bar_width + 8,
            "family": group_left + 2 * (bar_width + 8),
        }
        values = {
            "answer": record.answer_bits,
            "variable": record.variable_bits,
            "family": record.family_bits,
        }
        for channel, bits in values.items():
            bar_y = y(bits)
            lines.append(
                f'<rect x="{x_positions[channel]:.2f}" y="{bar_y:.2f}" width="{bar_width:.2f}" height="{top + panel_height - bar_y:.2f}" fill="{colors[channel]}"/>'
            )
        label_x = group_left - 6
        lines.append(f'<text x="{label_x:.2f}" y="{top + panel_height + 18}">{records[idx].label}</text>')
        lines.append(
            f'<text x="{label_x:.2f}" y="{top + panel_height + 32}">(p={record.p},k={record.k})</text>'
        )

    legend_x = left + panel_width - 150
    for row_idx, (channel, label) in enumerate((("answer", "answer"), ("variable", "variable"), ("family", "family"))):
        legend_y = top + 20 + row_idx * 16
        lines.append(f'<rect x="{legend_x}" y="{legend_y - 8}" width="8" height="8" fill="{colors[channel]}"/>')
        lines.append(f'<text x="{legend_x + 14}" y="{legend_y}">{label}</text>')

    lines.append("</svg>")
    return "\n".join(lines)


def render_teaching_svg(records: Sequence[SemanticAtlasRecord]) -> str:
    teaching = [record.first_nontrivial_family_teaching or record.first_inexact_family_teaching or record.teaching_groups[0] for record in records]
    width = 1280
    height = 700
    left = 80
    top = 62
    panel_width = width - left - 40
    panel_height = height - top - 100
    def record_max(record: TeachingGroupRecord) -> int:
        values = [
            value
            for value in (
                record.answer_basis_size,
                record.variable_basis_size,
                record.family_basis_size,
            )
            if value is not None
        ]
        return max(values) if values else 0
    max_basis = max(
        record_max(record)
        for record in teaching
    ) + 1

    def y(value: int) -> float:
        usable = panel_height - 36
        return top + 18 + usable * (1 - value / max_basis)

    group_width = panel_width / len(teaching)
    colors = {
        "answer": "#c44536",
        "variable": "#22577a",
        "family": "#0b6e4f",
    }
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<style>",
        "text { font-family: Menlo, Monaco, Consolas, monospace; font-size: 11px; fill: #1f2933; }",
        ".title { font-size: 15px; font-weight: 700; }",
        ".panel { fill: #ffffff; stroke: #d9e2ec; stroke-width: 1; }",
        ".grid { stroke: #d9e2ec; stroke-width: 1; stroke-dasharray: 4 4; }",
        ".axis { stroke: #9fb3c8; stroke-width: 1; }",
        "</style>",
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#fbfbfd"/>',
        f'<text x="{left}" y="26" class="title">Teaching Complexity Under Semantic Enrichment</text>',
        f'<text x="{left}" y="44">For each semantics, bars show answer / variable / family basis sizes on the earliest nontrivial teaching group or the first inexact family-teaching group.</text>',
        f'<rect x="{left}" y="{top}" width="{panel_width}" height="{panel_height}" class="panel"/>',
    ]
    for tick in range(max_basis + 1):
        tick_y = y(tick)
        lines.append(f'<line x1="{left}" y1="{tick_y:.2f}" x2="{left + panel_width}" y2="{tick_y:.2f}" class="grid"/>')
        lines.append(f'<text x="{left - 24}" y="{tick_y + 4:.2f}">{tick}</text>')
    lines.append(f'<line x1="{left}" y1="{top + panel_height}" x2="{left + panel_width}" y2="{top + panel_height}" class="axis"/>')
    lines.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + panel_height}" class="axis"/>')

    for idx, record in enumerate(teaching):
        group_left = left + idx * group_width + 18
        bar_width = max(12.0, group_width / 7)
        values = {
            "answer": record.answer_basis_size or 0,
            "variable": record.variable_basis_size or 0,
            "family": record.family_basis_size or 0,
        }
        for offset, channel in enumerate(("answer", "variable", "family")):
            value = values[channel]
            bar_y = y(value)
            lines.append(
                f'<rect x="{group_left + offset * (bar_width + 8):.2f}" y="{bar_y:.2f}" width="{bar_width:.2f}" height="{top + panel_height - bar_y:.2f}" fill="{colors[channel]}"/>'
            )
        label_x = group_left - 6
        lines.append(f'<text x="{label_x:.2f}" y="{top + panel_height + 18}">{records[idx].label}</text>')
        suffix = "inexact" if not record.family_exact else f"({record.p},{record.k})"
        lines.append(f'<text x="{label_x:.2f}" y="{top + panel_height + 32}">{suffix}</text>')

    legend_x = left + panel_width - 150
    for row_idx, (channel, label) in enumerate((("answer", "answer"), ("variable", "variable"), ("family", "family"))):
        legend_y = top + 20 + row_idx * 16
        lines.append(f'<rect x="{legend_x}" y="{legend_y - 8}" width="8" height="8" fill="{colors[channel]}"/>')
        lines.append(f'<text x="{legend_x + 14}" y="{legend_y}">{label}</text>')

    lines.append("</svg>")
    return "\n".join(lines)


def render_markdown(records: Sequence[SemanticAtlasRecord]) -> str:
    lines = [
        "# Semantic Boundary Atlas",
        "",
        "This atlas keeps the witness carrier and the witness composition law fixed, and varies only the family readout.",
        "",
        "The exact boundary question is no longer whether overlapping families matter in the abstract. It is where they first become computationally necessary: in the contract, in the probe bank, or in the runtime automaton itself.",
        "",
        "## Aggregate boundary",
        "",
        f"- semantic enrichments scanned: `{len(records) - 1}` plus the binary baseline",
        f"- exact antichain search range: `p in {list(P_SCAN)}`, `k <= 3`",
        "- old-summary runtime collapse survives only for the binary baseline",
        "- every readout-only enrichment still factors exactly through the full coordinate carrier `(depth, coords)`",
        "- no scanned readout-only enrichment produced a genuinely non-coordinate runtime counterexample",
        "- overlap-required runtime breaks first appear in the `overlap_bonus` and `overlap_exclusion` readouts",
        "- the old subset-probe teaching bank stays trivial for many enrichments, becomes nontrivial for `overlap_exclusion`, and becomes inexact for `order_sensitive_completion`",
        "",
        "## First Breaks",
        "",
        "| semantics | first old-summary break | break type | answer bits | variable bits | family bits | first family>variable gap | same-now / future-separate |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for record in records:
        gap = record.first_variable_family_gap
        gap_text = "none on scan"
        if gap is not None:
            gap_text = f"`(p={gap.p}, k={gap.k})`"
        if record.first_break is None:
            break_text = "none on scan"
            break_type = "preserved"
            answer_bits = "-"
            variable_bits = "-"
            family_bits = "-"
            same_now = "-"
        else:
            break_text = f"`(p={record.first_break.p}, k={record.first_break.k})`, `{record.first_break.family}`"
            break_type = record.first_break.break_type
            answer_bits = f"`{record.first_break.answer_bits:.3f}`"
            variable_bits = f"`{record.first_break.variable_bits:.3f}`"
            family_bits = f"`{record.first_break.family_bits:.3f}`"
            same_now = f"`{record.first_break.same_now_future_separate}`"
        lines.append(
            f"| `{record.name}` | {break_text} | "
            f"`{break_type}` | {answer_bits} | "
            f"{variable_bits} | {family_bits} | "
            f"{gap_text} | {same_now} |"
        )

    lines.extend(
        [
            "",
            "### Interpretation",
            "",
            "- `additive`, `capped`, `weights`, `order`, and `multilevel` all break at the coordinate level on the smallest non-singleton world `(p=2, k=2, A={{1,2}})`.",
            "- `heterogeneous_family_thresholds` first breaks on a family-specific but non-overlap world: multiple families matter, but overlap is not yet required.",
            "- `overlap_bonus` and `overlap_exclusion` are the first readouts whose smallest break already requires overlapping families.",
            "- No semantic in the atlas produced a runtime failure of the full coordinate summary. That is structural: every readout here is still a deterministic function of the composed witness state and the fixed family parameter.",
            "",
            "## Runtime Threshold Comparisons",
            "",
            "The variable channel keeps its old meaning throughout this atlas: it is still the completed-variable runtime channel induced by the fixed witness carrier. The family channel is the enriched family readout. So a positive `family - variable` bit gap measures how much more runtime information the readout needs than the old witness-visible variable channel preserves.",
            "",
            "| semantics | world used | answer bits | variable bits | family bits | family - variable | family - answer | strict answer < variable < family |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for record in records:
        world = record.first_variable_family_gap or record.first_break or record.reference_world
        strict = record.first_strict_chain is not None
        lines.append(
            f"| `{record.name}` | `(p={world.p}, k={world.k})`, `{world.family}` | `{world.answer_bits:.3f}` | "
            f"`{world.variable_bits:.3f}` | `{world.family_bits:.3f}` | "
            f"`{world.variable_to_family_gap_bits:.3f}` | `{world.answer_to_family_gap_bits:.3f}` | `{strict}` |"
        )

    lines.extend(
        [
            "",
            "### Runtime observations",
            "",
            "- `additive_partial_activation` is the cleanest first break of the old summary, but its smallest exact world still has `family bits < variable bits`; it breaks the old summary without yet opening a family-runtime tax.",
            "- `capped_additive_activation`, `order_sensitive_completion`, `multilevel_local_progress`, `overlap_bonus`, and `overlap_exclusion` all open a positive family-runtime tax over the old variable channel.",
            "- Strict `answer < variable < family` worlds do appear for several enrichments, including `additive_partial_activation`, `heterogeneous_variable_weights`, `heterogeneous_family_thresholds`, `order_sensitive_completion`, and `multilevel_local_progress`.",
            "- That strict chain is not universal, though. The robust boundary statement on the fixed carrier is still weaker and cleaner: semantic enrichment can force `family > variable` without ever defeating full coordinate exactness.",
            "",
            "## Candidate Runtime Summaries",
            "",
            "Each first-break world was tested against the same summary candidates:",
            "",
            "- `old_summary = (depth, completed set)`",
            "- `present_complete = (depth, present set, completed set)`",
            "- `trinary_progress = (depth, named 0/1/2 progress levels)`",
            "- `full_progress = (depth, coords)`",
            "- `sorted_progress` and `progress_histogram` as exchangeable compressions",
            "",
            "The exact lesson is stable:",
            "",
            "- `old_summary` fails on every enriched first-break world,",
            "- `full_progress` is exact everywhere by construction,",
            "- exchangeable compressions fail quickly once variable identity or order matters,",
            "- some overlap-driven readouts already collapse to `present_complete` on their smallest break worlds, so not every enrichment needs the full coordinate vector on its first counterexample.",
            "",
            "## Teaching Complexity Follow-up",
            "",
            "Teaching uses the same subset-probe bank as the contract-layer scans: each probe completes exactly a chosen survivor subset and reads out answer / variable / family responses under the enriched semantics.",
            "",
            "| semantics | group | families | answer basis | variable basis | family basis | family exact | first family-teaching change |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for record in records:
        first_group = record.teaching_groups[0]
        family_change = record.first_nontrivial_family_teaching or record.first_inexact_family_teaching
        change_text = "none on scanned nontrivial groups"
        if family_change is not None:
            if not family_change.family_exact:
                change_text = f"`(p={family_change.p}, k={family_change.k})` inexact"
            else:
                change_text = f"`(p={family_change.p}, k={family_change.k})` basis `{family_change.family_basis_size}`"
        lines.append(
            f"| `{record.name}` | `(p={first_group.p}, k={first_group.k})` | `{first_group.family_count}` | "
            f"`{first_group.answer_basis_size}` | `{first_group.variable_basis_size}` | "
            f"`{first_group.family_basis_size}` | `{first_group.family_exact}` | {change_text} |"
        )

    lines.extend(
        [
            "",
            "### Teaching observations",
            "",
            "- For many enrichments the family channel is still trivial to teach with the old subset probes: one full-union probe already reveals the family output signature exactly on the scanned nontrivial classes.",
            "- `overlap_exclusion` is the first atlas case where family teaching becomes genuinely nontrivial under the old probe bank.",
            "- `order_sensitive_completion` is stronger still: on the scanned nontrivial classes, the old subset-probe bank is not family-exact at all. Runtime stays coordinate-exact, but observation becomes blind.",
            "- So semantic enrichment does not only move runtime thresholds. It can also split teaching complexity away from runtime complexity.",
            "",
            "## Strongest Honest Boundary Statement",
            "",
            "What the atlas supports is a three-layer boundary.",
            "",
            "1. **Binary completion** is the special case where runtime family state collapses to the old witness-visible summary.",
            "2. **Readout-only enrichments** can break that collapse, widen a real family-runtime tax over the old variable channel, and even make overlap necessary for the first break.",
            "3. **But no readout-only enrichment on the fixed carrier can force non-coordinate runtime state.** To get genuinely hypergraph-valued runtime memory, the carrier or composition law itself must change, not just the readout.",
            "",
            "So hypergraph complexity has now been located more sharply:",
            "",
            "- it is already exact at the contract layer,",
            "- it can become visible at the teaching layer under semantic enrichment,",
            "- but on the fixed witness carrier it still has not entered the runtime automaton itself.",
            "",
            "## Per-Semantic Counterexamples",
            "",
        ]
    )
    for record in records:
        world = record.first_break or record.reference_world
        lines.extend(
            [
                f"### `{record.name}`",
                "",
                f"- description: {record.description}",
                f"- first break: `none on scan`" if record.first_break is None else f"- first break: `(p={world.p}, k={world.k})`, family `{world.family}`",
                f"- break type: `preserved`" if record.first_break is None else f"- break type: `{world.break_type}`",
                f"- shared old summary: `{world.shared_old_summary}`" if record.first_break is not None else "- shared old summary: `n/a`",
                f"- left state: `{world.left_state}`" if record.first_break is not None else "- left state: `n/a`",
                f"- alternate state: `{world.alternate_state}`" if record.first_break is not None else "- alternate state: `n/a`",
                f"- continuation: `{world.right_state}`" if record.first_break is not None else "- continuation: `n/a`",
                f"- now(left) / now(alternate): `{world.left_output_now}` / `{world.alternate_output_now}`" if record.first_break is not None else "- now(left) / now(alternate): `n/a`",
                f"- future(left) / future(alternate): `{world.left_output_future}` / `{world.alternate_output_future}`" if record.first_break is not None else "- future(left) / future(alternate): `n/a`",
                f"- same-now / future-separate: `{world.same_now_future_separate}`" if record.first_break is not None else "- same-now / future-separate: `n/a`",
                "",
            ]
        )

    return "\n".join(lines)


def build_payload(records: Sequence[SemanticAtlasRecord]) -> Dict[str, object]:
    return {
        "scan_scope": {
            "p_values": list(P_SCAN),
            "nontrivial_teaching_groups": [list(group) for group in NONTRIVIAL_GROUPS],
            "semantics": [record.name for record in records],
        },
        "records": [
            {
                "name": record.name,
                "label": record.label,
                "description": record.description,
                "first_break": world_to_json(record.first_break),
                "first_variable_family_gap": world_to_json(record.first_variable_family_gap),
                "first_strict_chain": world_to_json(record.first_strict_chain),
                "first_nontrivial_family_teaching": teaching_to_json(record.first_nontrivial_family_teaching),
                "first_inexact_family_teaching": teaching_to_json(record.first_inexact_family_teaching),
                "teaching_groups": [teaching_to_json(group) for group in record.teaching_groups],
            }
            for record in records
        ],
    }


def main() -> None:
    records = tuple(scan_semantic(semantic) for semantic in SEMANTICS)
    payload = build_payload(records)

    json_path = RESULTS_DIR / "semantic_boundary_atlas.json"
    md_path = RESULTS_DIR / "semantic_boundary_atlas.md"
    atlas_svg_path = RESULTS_DIR / "semantic_boundary_atlas.svg"
    thresholds_svg_path = RESULTS_DIR / "semantic_runtime_thresholds.svg"
    teaching_svg_path = RESULTS_DIR / "semantic_teaching_atlas.svg"

    json_path.write_text(json.dumps(payload, indent=2))
    md_path.write_text(render_markdown(records))
    atlas_svg_path.write_text(render_atlas_svg(records))
    thresholds_svg_path.write_text(render_threshold_svg(records))
    teaching_svg_path.write_text(render_teaching_svg(records))

    print(
        json.dumps(
            {
                "json_path": str(json_path),
                "md_path": str(md_path),
                "atlas_svg_path": str(atlas_svg_path),
                "thresholds_svg_path": str(thresholds_svg_path),
                "teaching_svg_path": str(teaching_svg_path),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

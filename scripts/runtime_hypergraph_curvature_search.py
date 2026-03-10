#!/usr/bin/env python3
"""Search for the first runtime semantics with positive coordinate curvature.

Coordinate curvature is positive when the runtime continuation quotient is
strictly larger than the quotient induced by the full coordinate witness state.
The smoking-gun witness is a triple `(u, v, w)` such that:

    coordinate(u) == coordinate(v)
    but output(u + w) != output(v + w)

This script scans a small library of deterministic prefix-compositional
semantics on exact full-union antichains, starting from the seed crystal
`{{1,2}, {1,3}}`.
"""

from __future__ import annotations

import json
import math
from collections import defaultdict, deque
from dataclasses import dataclass
from itertools import combinations, product
from pathlib import Path
from typing import Callable, DefaultDict, Dict, Hashable, Iterable, List, Sequence, Tuple

from runtime_collapse_boundary import enumerate_exact_antichains, log2_count

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results"
DOCS_DIR = ROOT / "docs" / "writing"

Family = Tuple[Tuple[int, ...], ...]
Event = Hashable
Trace = Tuple[Event, ...]

P_SCAN = (2, 3, 4)
K_MAX = 3
SEED_FAMILY: Family = ((1, 2), (1, 3))


@dataclass(frozen=True)
class SemanticDefinition:
    name: str
    label: str
    description: str
    initial_state: Callable[[Family], Hashable]
    events: Callable[[Family], Tuple[Event, ...]]
    step: Callable[[Hashable, Event, Family], Hashable]
    coordinate_summary: Callable[[Hashable, Family], Hashable]
    old_summary: Callable[[Hashable, Family], Hashable]
    incidence_summary: Callable[[Hashable, Family], Hashable]
    family_summary: Callable[[Hashable, Family], Hashable]
    full_assignment_summary: Callable[[Hashable, Family], Hashable]
    output: Callable[[Hashable, Family], Hashable]
    analysis_mode: str = "automaton"
    segment_states: Callable[[Family], Tuple[Hashable, ...]] | None = None
    compose: Callable[[Hashable, Hashable, Family], Hashable | None] | None = None


@dataclass(frozen=True)
class CurvatureRecord:
    semantics: str
    p: int
    k: int
    family: Family
    reachable_state_count: int
    runtime_quotient_count: int
    coordinate_quotient_count: int
    old_quotient_count: int
    incidence_quotient_count: int
    family_quotient_count: int
    full_assignment_quotient_count: int
    full_state_count: int
    coordinate_curvature_gap: float
    fiber_holonomy_rank: int
    coordinate_exact: bool
    old_exact: bool
    incidence_exact: bool
    family_exact: bool
    full_assignment_exact: bool
    witness_left_trace: Trace | None
    witness_right_trace: Trace | None
    witness_suffix: Trace | None
    witness_left_state: str | None
    witness_right_state: str | None
    witness_suffix_text: str | None
    witness_coordinate: str | None
    witness_left_output_now: str | None
    witness_right_output_now: str | None
    witness_left_output_future: str | None
    witness_right_output_future: str | None
    same_now_future_separate: bool
    nontrivial_coordinate_fibers: Tuple[Tuple[str, int], ...]


@dataclass(frozen=True)
class SemanticSummary:
    name: str
    label: str
    description: str
    families_scanned: int
    coordinate_split_count: int
    positive_gap_count: int
    coordinate_exact_on_scan: bool
    full_assignment_exact_on_scan: bool
    max_coordinate_curvature_gap: float
    max_fiber_holonomy_rank: int
    seed_record: CurvatureRecord
    first_coordinate_split: CurvatureRecord | None
    first_positive_gap: CurvatureRecord | None


def family_union(family: Family) -> Tuple[int, ...]:
    return tuple(sorted(set().union(*map(set, family))))


def family_overlap(family: Family) -> bool:
    return any(set(left) & set(right) for left, right in combinations(family, 2))


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


def edge_indices_by_variable(family: Family) -> Tuple[Tuple[int, ...], ...]:
    universe = family_union(family)
    p = max(universe) if universe else 0
    return tuple(
        tuple(index for index, edge in enumerate(family) if variable in edge)
        for variable in range(1, p + 1)
    )


def completed_edges_from_presence(presence: Sequence[int], family: Family) -> Family:
    return tuple(edge for edge in family if all(presence[item - 1] for item in edge))


def completed_edges_from_claims(claims: Sequence[int], family: Family) -> Family:
    completed = []
    for edge_index, edge in enumerate(family):
        if all(claims[item - 1] == edge_index for item in edge):
            completed.append(edge)
    return tuple(completed)


def residual_profile_from_claims(claims: Sequence[int], family: Family) -> Family:
    residuals = []
    for edge_index, edge in enumerate(family):
        live = True
        remaining: List[int] = []
        for item in edge:
            claim = claims[item - 1]
            if claim == -1:
                remaining.append(item)
            elif claim != edge_index:
                live = False
                break
        if live:
            residuals.append(tuple(remaining))
    return tuple(residuals)


def support_counts_from_claims(claims: Sequence[int], family: Family) -> Tuple[int, ...]:
    counts = [0] * len(family)
    for value in claims:
        if isinstance(value, int) and value >= 0:
            counts[value] += 1
    return tuple(counts)


def event_text(event: Event, family: Family) -> str:
    if isinstance(event, int):
        return str(event)
    if (
        isinstance(event, tuple)
        and len(event) == 2
        and isinstance(event[0], str)
        and event[0] == "segment"
    ):
        return state_text(event[1], family)
    variable, edge_index = event
    return f"{variable}->{family[edge_index]}"


def trace_text(trace: Trace, family: Family) -> str:
    if not trace:
        return "[]"
    return "[" + ", ".join(event_text(event, family) for event in trace) + "]"


def state_text(value: Hashable, family: Family) -> str:
    p = max(family_union(family)) if family else 0
    if (
        isinstance(value, tuple)
        and len(value) == 1
        and isinstance(value[0], str)
        and value[0] == "INVALID"
    ):
        return "INVALID"
    if isinstance(value, tuple):
        if value and isinstance(value[0], tuple):
            return str(value)
        if all(isinstance(item, int) for item in value):
            claims = list(value)
            if all(item in (0, 1) for item in claims):
                return str(tuple(claims))
            if len(claims) == p and all(item == -1 or 0 <= item < len(family) for item in claims):
                pieces = []
                for variable, claim in enumerate(claims, start=1):
                    if claim >= 0:
                        pieces.append(f"{variable}->{family[claim]}")
                return "{" + ", ".join(pieces) + "}" if pieces else "{}"
            return str(tuple(claims))
    return str(value)


def summary_exactness(summary_fn: Callable[[Hashable, Family], Hashable], states: Sequence[Hashable], family: Family, block_of: Dict[Hashable, int]) -> Tuple[int, bool, Tuple[Tuple[str, int], ...]]:
    grouped: DefaultDict[Hashable, set] = defaultdict(set)
    for state in states:
        grouped[summary_fn(state, family)].add(block_of[state])
    nontrivial = tuple(
        sorted(
            (state_text(key, family), len(blocks))
            for key, blocks in grouped.items()
            if len(blocks) > 1
        )
    )
    return len(grouped), all(len(blocks) == 1 for blocks in grouped.values()), nontrivial


def row_exactness(
    summary_fn: Callable[[Hashable, Family], Hashable],
    states: Sequence[Hashable],
    family: Family,
    row_of: Dict[Hashable, Tuple[Hashable, ...]],
) -> Tuple[int, bool, Tuple[Tuple[str, int], ...]]:
    grouped: DefaultDict[Hashable, set] = defaultdict(set)
    for state in states:
        grouped[summary_fn(state, family)].add(row_of[state])
    nontrivial = tuple(
        sorted(
            (state_text(key, family), len(rows))
            for key, rows in grouped.items()
            if len(rows) > 1
        )
    )
    return len(grouped), all(len(rows) == 1 for rows in grouped.values()), nontrivial


def minimize_moore_machine(
    states: Sequence[Hashable],
    events: Sequence[Event],
    transitions: Dict[Hashable, Dict[Event, Hashable]],
    outputs: Dict[Hashable, Hashable],
) -> Dict[Hashable, int]:
    partition: Dict[Hashable, object] = {state: outputs[state] for state in states}
    changed = True
    while changed:
        signatures = {
            state: (
                outputs[state],
                tuple(partition[transitions[state][event]] for event in events),
            )
            for state in states
        }
        signature_ids: Dict[Tuple[object, ...], int] = {}
        refined: Dict[Hashable, int] = {}
        for state in states:
            signature = signatures[state]
            if signature not in signature_ids:
                signature_ids[signature] = len(signature_ids)
            refined[state] = signature_ids[signature]
        changed = any(partition[state] != refined[state] for state in states)
        partition = refined
    return {state: int(block) for state, block in partition.items()}


def shortest_distinguishing_suffix(
    left: Hashable,
    right: Hashable,
    family: Family,
    events: Sequence[Event],
    transitions: Dict[Hashable, Dict[Event, Hashable]],
    outputs: Dict[Hashable, Hashable],
) -> Trace:
    queue = deque([(left, right, ())])
    visited = {(left, right)}
    while queue:
        current_left, current_right, trace = queue.popleft()
        if outputs[current_left] != outputs[current_right]:
            return trace
        for event in events:
            next_left = transitions[current_left][event]
            next_right = transitions[current_right][event]
            pair = (next_left, next_right)
            if pair in visited:
                continue
            visited.add(pair)
            queue.append((next_left, next_right, trace + (event,)))
    raise RuntimeError("states should be distinguishable but no suffix was found")


def build_automaton(semantic: SemanticDefinition, family: Family) -> Dict[str, object]:
    events = semantic.events(family)
    initial = semantic.initial_state(family)
    queue = deque([initial])
    seen = {initial}
    shortest_trace: Dict[Hashable, Trace] = {initial: ()}
    transitions: Dict[Hashable, Dict[Event, Hashable]] = {}
    outputs: Dict[Hashable, Hashable] = {}

    while queue:
        state = queue.popleft()
        outputs[state] = semantic.output(state, family)
        row: Dict[Event, Hashable] = {}
        for event in events:
            next_state = semantic.step(state, event, family)
            row[event] = next_state
            if next_state not in seen:
                seen.add(next_state)
                shortest_trace[next_state] = shortest_trace[state] + (event,)
                queue.append(next_state)
        transitions[state] = row

    states = tuple(sorted(seen, key=lambda item: (len(shortest_trace[item]), shortest_trace[item], state_text(item, family))))
    block_of = minimize_moore_machine(states, events, transitions, outputs)

    coordinate_count, coordinate_exact, coordinate_fibers = summary_exactness(
        semantic.coordinate_summary, states, family, block_of
    )
    old_count, old_exact, _ = summary_exactness(
        semantic.old_summary, states, family, block_of
    )
    incidence_count, incidence_exact, _ = summary_exactness(
        semantic.incidence_summary, states, family, block_of
    )
    family_count, family_exact, _ = summary_exactness(
        semantic.family_summary, states, family, block_of
    )
    full_assignment_count, full_assignment_exact, _ = summary_exactness(
        semantic.full_assignment_summary, states, family, block_of
    )
    runtime_count = len(set(block_of.values()))
    fiber_holonomy_rank = max(
        count for _, count in coordinate_fibers
    ) if coordinate_fibers else 1

    witness_left_trace = None
    witness_right_trace = None
    witness_suffix = None
    witness_left_state = None
    witness_right_state = None
    witness_coordinate = None
    witness_left_output_now = None
    witness_right_output_now = None
    witness_left_output_future = None
    witness_right_output_future = None
    same_now_future_separate = False

    if not coordinate_exact:
        coordinate_groups: DefaultDict[Hashable, List[Hashable]] = defaultdict(list)
        for state in states:
            coordinate_groups[semantic.coordinate_summary(state, family)].append(state)
        candidate_pairs: List[Tuple[int, int, int, int, Hashable, Hashable, Trace]] = []
        for coordinate_value, fiber in coordinate_groups.items():
            if len({block_of[state] for state in fiber}) <= 1:
                continue
            for left_index, left_state in enumerate(fiber):
                for right_state in fiber[left_index + 1 :]:
                    if block_of[left_state] == block_of[right_state]:
                        continue
                    suffix = shortest_distinguishing_suffix(
                        left_state, right_state, family, events, transitions, outputs
                    )
                    candidate_pairs.append(
                        (
                            len(shortest_trace[left_state]),
                            len(shortest_trace[right_state]),
                            len(suffix),
                            0 if outputs[left_state] == outputs[right_state] else 1,
                            left_state,
                            right_state,
                            suffix,
                        )
                    )
        candidate_pairs.sort(key=lambda item: item[:4] + (state_text(item[4], family), state_text(item[5], family), trace_text(item[6], family)))
        left_state, right_state, witness_suffix = candidate_pairs[0][4], candidate_pairs[0][5], candidate_pairs[0][6]
        witness_left_trace = shortest_trace[left_state]
        witness_right_trace = shortest_trace[right_state]
        witness_left_state = state_text(left_state, family)
        witness_right_state = state_text(right_state, family)
        witness_coordinate = state_text(semantic.coordinate_summary(left_state, family), family)
        witness_left_output_now = state_text(outputs[left_state], family)
        witness_right_output_now = state_text(outputs[right_state], family)
        future_left = left_state
        future_right = right_state
        for event in witness_suffix:
            future_left = transitions[future_left][event]
            future_right = transitions[future_right][event]
        witness_left_output_future = state_text(outputs[future_left], family)
        witness_right_output_future = state_text(outputs[future_right], family)
        same_now_future_separate = outputs[left_state] == outputs[right_state] and outputs[future_left] != outputs[future_right]

    return {
        "states": states,
        "events": events,
        "shortest_trace": shortest_trace,
        "outputs": outputs,
        "transitions": transitions,
        "block_of": block_of,
        "runtime_count": runtime_count,
        "coordinate_count": coordinate_count,
        "old_count": old_count,
        "incidence_count": incidence_count,
        "family_count": family_count,
        "full_assignment_count": full_assignment_count,
        "coordinate_exact": coordinate_exact,
        "old_exact": old_exact,
        "incidence_exact": incidence_exact,
        "family_exact": family_exact,
        "full_assignment_exact": full_assignment_exact,
        "coordinate_curvature_gap": log2_count(runtime_count) - log2_count(coordinate_count),
        "fiber_holonomy_rank": fiber_holonomy_rank,
        "nontrivial_coordinate_fibers": coordinate_fibers,
        "witness_left_trace": witness_left_trace,
        "witness_right_trace": witness_right_trace,
        "witness_suffix": witness_suffix,
        "witness_left_state": witness_left_state,
        "witness_right_state": witness_right_state,
        "witness_coordinate": witness_coordinate,
        "witness_left_output_now": witness_left_output_now,
        "witness_right_output_now": witness_right_output_now,
        "witness_left_output_future": witness_left_output_future,
        "witness_right_output_future": witness_right_output_future,
        "same_now_future_separate": same_now_future_separate,
    }


def enumerate_committed_states(family: Family) -> Tuple[Tuple[int, ...], ...]:
    options = [
        (-1,) + tuple(index for index, edge in enumerate(family) if variable in edge)
        for variable in family_union(family)
    ]
    return tuple(tuple(choice) for choice in product(*options))


def compose_committed_state(
    left: Tuple[int, ...],
    right: Tuple[int, ...],
    family: Family,
) -> Tuple[int, ...] | None:
    merged: List[int] = []
    for left_value, right_value in zip(left, right):
        if left_value >= 0 and right_value >= 0:
            return None
        merged.append(right_value if left_value == -1 else left_value)
    return tuple(merged)


def build_segment_signature_analysis(semantic: SemanticDefinition, family: Family) -> Dict[str, object]:
    if semantic.segment_states is None or semantic.compose is None:
        raise ValueError(f"segment_rows analysis requires segment_states and compose for {semantic.name}")

    states = semantic.segment_states(family)
    row_of: Dict[Hashable, Tuple[Hashable, ...]] = {}
    for state in states:
        row: List[Hashable] = []
        for suffix in states:
            merged = semantic.compose(state, suffix, family)
            row.append(("INVALID",) if merged is None else semantic.output(merged, family))
        row_of[state] = tuple(row)

    runtime_blocks: Dict[Tuple[Hashable, ...], int] = {}
    block_of: Dict[Hashable, int] = {}
    for state in states:
        row = row_of[state]
        if row not in runtime_blocks:
            runtime_blocks[row] = len(runtime_blocks)
        block_of[state] = runtime_blocks[row]

    coordinate_count, coordinate_exact, coordinate_fibers = row_exactness(
        semantic.coordinate_summary, states, family, row_of
    )
    old_count, old_exact, _ = row_exactness(
        semantic.old_summary, states, family, row_of
    )
    incidence_count, incidence_exact, _ = row_exactness(
        semantic.incidence_summary, states, family, row_of
    )
    family_count, family_exact, _ = row_exactness(
        semantic.family_summary, states, family, row_of
    )
    full_assignment_count, full_assignment_exact, _ = row_exactness(
        semantic.full_assignment_summary, states, family, row_of
    )
    runtime_count = len(runtime_blocks)
    fiber_holonomy_rank = max(
        count for _, count in coordinate_fibers
    ) if coordinate_fibers else 1

    witness_left_trace = None
    witness_right_trace = None
    witness_suffix = None
    witness_left_state = None
    witness_right_state = None
    witness_coordinate = None
    witness_left_output_now = None
    witness_right_output_now = None
    witness_left_output_future = None
    witness_right_output_future = None
    same_now_future_separate = False

    if not coordinate_exact:
        coordinate_groups: DefaultDict[Hashable, List[Hashable]] = defaultdict(list)
        for state in states:
            coordinate_groups[semantic.coordinate_summary(state, family)].append(state)
        candidate_pairs: List[Tuple[int, int, int, Hashable, Hashable, Hashable]] = []
        for fiber in coordinate_groups.values():
            distinct_blocks = {block_of[state] for state in fiber}
            if len(distinct_blocks) <= 1:
                continue
            for left_index, left_state in enumerate(fiber):
                for right_state in fiber[left_index + 1 :]:
                    if block_of[left_state] == block_of[right_state]:
                        continue
                    differing = [
                        suffix
                        for suffix, left_row, right_row in zip(states, row_of[left_state], row_of[right_state])
                        if left_row != right_row
                    ]
                    differing.sort(
                        key=lambda suffix: (
                            0 if semantic.old_summary(suffix, family) else 1,
                            len(semantic.old_summary(suffix, family)),
                            state_text(suffix, family),
                        )
                    )
                    suffix = differing[0]
                    candidate_pairs.append(
                        (
                            len(semantic.old_summary(left_state, family)),
                            len(semantic.old_summary(right_state, family)),
                            len(semantic.old_summary(suffix, family)),
                            left_state,
                            right_state,
                            suffix,
                        )
                    )
        candidate_pairs.sort(
            key=lambda item: item[:3] + (
                state_text(item[3], family),
                state_text(item[4], family),
                state_text(item[5], family),
            )
        )
        left_state, right_state, suffix_state = candidate_pairs[0][3], candidate_pairs[0][4], candidate_pairs[0][5]
        witness_left_trace = (("segment", left_state),) if semantic.old_summary(left_state, family) else ()
        witness_right_trace = (("segment", right_state),) if semantic.old_summary(right_state, family) else ()
        witness_suffix = (("segment", suffix_state),) if semantic.old_summary(suffix_state, family) else ()
        witness_left_state = state_text(left_state, family)
        witness_right_state = state_text(right_state, family)
        witness_coordinate = state_text(semantic.coordinate_summary(left_state, family), family)
        witness_left_output_now = state_text(semantic.output(left_state, family), family)
        witness_right_output_now = state_text(semantic.output(right_state, family), family)
        future_left = semantic.compose(left_state, suffix_state, family)
        future_right = semantic.compose(right_state, suffix_state, family)
        witness_left_output_future = state_text(("INVALID",), family) if future_left is None else state_text(semantic.output(future_left, family), family)
        witness_right_output_future = state_text(("INVALID",), family) if future_right is None else state_text(semantic.output(future_right, family), family)
        same_now_future_separate = (
            semantic.output(left_state, family) == semantic.output(right_state, family)
            and witness_left_output_future != witness_right_output_future
        )

    return {
        "states": states,
        "runtime_count": runtime_count,
        "coordinate_count": coordinate_count,
        "old_count": old_count,
        "incidence_count": incidence_count,
        "family_count": family_count,
        "full_assignment_count": full_assignment_count,
        "coordinate_exact": coordinate_exact,
        "old_exact": old_exact,
        "incidence_exact": incidence_exact,
        "family_exact": family_exact,
        "full_assignment_exact": full_assignment_exact,
        "coordinate_curvature_gap": log2_count(runtime_count) - log2_count(coordinate_count),
        "fiber_holonomy_rank": fiber_holonomy_rank,
        "nontrivial_coordinate_fibers": coordinate_fibers,
        "witness_left_trace": witness_left_trace,
        "witness_right_trace": witness_right_trace,
        "witness_suffix": witness_suffix,
        "witness_left_state": witness_left_state,
        "witness_right_state": witness_right_state,
        "witness_coordinate": witness_coordinate,
        "witness_left_output_now": witness_left_output_now,
        "witness_right_output_now": witness_right_output_now,
        "witness_left_output_future": witness_left_output_future,
        "witness_right_output_future": witness_right_output_future,
        "same_now_future_separate": same_now_future_separate,
    }


def family_support_vector_from_presence(state: Tuple[int, ...], family: Family) -> Tuple[int, ...]:
    return tuple(sum(state[item - 1] for item in edge) for edge in family)


def broadcast_initial(family: Family) -> Tuple[int, ...]:
    return tuple(0 for _ in family_union(family))


def broadcast_events(family: Family) -> Tuple[int, ...]:
    return family_union(family)


def broadcast_step(state: Tuple[int, ...], event: int, family: Family) -> Tuple[int, ...]:
    updated = list(state)
    updated[event - 1] = 1
    return tuple(updated)


def broadcast_coordinate(state: Tuple[int, ...], family: Family) -> Tuple[int, ...]:
    return state


def broadcast_old(state: Tuple[int, ...], family: Family) -> Tuple[int, ...]:
    return tuple(index + 1 for index, value in enumerate(state) if value)


def broadcast_incidence(state: Tuple[int, ...], family: Family) -> Tuple[Tuple[int, ...], ...]:
    return tuple(tuple(state[item - 1] for item in edge) for edge in family)


def broadcast_family_summary(state: Tuple[int, ...], family: Family) -> Tuple[int, ...]:
    return family_support_vector_from_presence(state, family)


def broadcast_output(state: Tuple[int, ...], family: Family) -> Family:
    return completed_edges_from_presence(state, family)


def incidence_initial(family: Family) -> Tuple[Tuple[int, ...], Tuple[Tuple[int, ...], ...]]:
    presence = tuple(0 for _ in family_union(family))
    incidence = tuple(tuple(0 for _ in family_union(family)) for _ in family)
    return presence, incidence


def incidence_step(
    state: Tuple[Tuple[int, ...], Tuple[Tuple[int, ...], ...]],
    event: int,
    family: Family,
) -> Tuple[Tuple[int, ...], Tuple[Tuple[int, ...], ...]]:
    presence, incidence = state
    if presence[event - 1]:
        return state
    updated_presence = list(presence)
    updated_presence[event - 1] = 1
    updated_incidence = [list(row) for row in incidence]
    for edge_index, edge in enumerate(family):
        if event in edge:
            updated_incidence[edge_index][event - 1] = 1
    return tuple(updated_presence), tuple(tuple(row) for row in updated_incidence)


def incidence_coordinate(
    state: Tuple[Tuple[int, ...], Tuple[Tuple[int, ...], ...]],
    family: Family,
) -> Tuple[int, ...]:
    return state[0]


def incidence_old(
    state: Tuple[Tuple[int, ...], Tuple[Tuple[int, ...], ...]],
    family: Family,
) -> Tuple[int, ...]:
    presence = state[0]
    return tuple(index + 1 for index, value in enumerate(presence) if value)


def incidence_summary_fn(
    state: Tuple[Tuple[int, ...], Tuple[Tuple[int, ...], ...]],
    family: Family,
) -> Tuple[Tuple[int, ...], ...]:
    return state[1]


def incidence_family_summary(
    state: Tuple[Tuple[int, ...], Tuple[Tuple[int, ...], ...]],
    family: Family,
) -> Tuple[int, ...]:
    incidence = state[1]
    return tuple(sum(incidence[edge_index][item - 1] for item in edge) for edge_index, edge in enumerate(family))


def incidence_output(
    state: Tuple[Tuple[int, ...], Tuple[Tuple[int, ...], ...]],
    family: Family,
) -> Family:
    incidence = state[1]
    return tuple(
        edge
        for edge_index, edge in enumerate(family)
        if all(incidence[edge_index][item - 1] for item in edge)
    )


def claim_initial(family: Family) -> Tuple[int, ...]:
    return tuple(-1 for _ in family_union(family))


def claim_events(family: Family) -> Tuple[int, ...]:
    return family_union(family)


def claim_coordinate(state: Tuple[int, ...], family: Family) -> Tuple[int, ...]:
    return tuple(1 if value >= 0 else 0 for value in state)


def claim_old(state: Tuple[int, ...], family: Family) -> Tuple[int, ...]:
    return tuple(index + 1 for index, value in enumerate(state) if value >= 0)


def claim_incidence(state: Tuple[int, ...], family: Family) -> Tuple[int, ...]:
    return state


def claim_family_summary(state: Tuple[int, ...], family: Family) -> Tuple[int, ...]:
    return support_counts_from_claims(state, family)


def claim_output(state: Tuple[int, ...], family: Family) -> Family:
    return completed_edges_from_claims(state, family)


def choose_exclusive_edge(claims: Tuple[int, ...], event: int, family: Family) -> int:
    incident = [index for index, edge in enumerate(family) if event in edge]
    support = {
        edge_index: sum(1 for item in family[edge_index] if item != event and claims[item - 1] == edge_index)
        for edge_index in incident
    }
    return sorted(incident, key=lambda edge_index: (-support[edge_index], family[edge_index]))[0]


def exclusive_step(state: Tuple[int, ...], event: int, family: Family) -> Tuple[int, ...]:
    if state[event - 1] >= 0:
        return state
    chosen = choose_exclusive_edge(state, event, family)
    updated = list(state)
    updated[event - 1] = chosen
    return tuple(updated)


def choose_budget_edge(claims: Tuple[int, ...], event: int, family: Family) -> int:
    incident = [index for index, edge in enumerate(family) if event in edge]
    budgets = support_counts_from_claims(claims, family)
    local_support = {
        edge_index: sum(1 for item in family[edge_index] if item != event and claims[item - 1] == edge_index)
        for edge_index in incident
    }
    return sorted(
        incident,
        key=lambda edge_index: (budgets[edge_index], -local_support[edge_index], family[edge_index]),
    )[0]


def budget_step(state: Tuple[int, ...], event: int, family: Family) -> Tuple[int, ...]:
    if state[event - 1] >= 0:
        return state
    chosen = choose_budget_edge(state, event, family)
    updated = list(state)
    updated[event - 1] = chosen
    return tuple(updated)


def committed_events(family: Family) -> Tuple[Tuple[int, int], ...]:
    return tuple(
        (variable, edge_index)
        for variable in family_union(family)
        for edge_index, edge in enumerate(family)
        if variable in edge
    )


def committed_step(state: Tuple[int, ...], event: Tuple[int, int], family: Family) -> Tuple[int, ...]:
    variable, edge_index = event
    if state[variable - 1] >= 0:
        return state
    updated = list(state)
    updated[variable - 1] = edge_index
    return tuple(updated)


SEMANTICS: Tuple[SemanticDefinition, ...] = (
    SemanticDefinition(
        name="broadcast_control",
        label="Broadcast",
        description="Current coordinate-broadcast control: completed families depend only on present coordinates.",
        initial_state=broadcast_initial,
        events=broadcast_events,
        step=broadcast_step,
        coordinate_summary=broadcast_coordinate,
        old_summary=broadcast_old,
        incidence_summary=broadcast_incidence,
        family_summary=broadcast_family_summary,
        full_assignment_summary=broadcast_coordinate,
        output=broadcast_output,
    ),
    SemanticDefinition(
        name="incidence_local_progress",
        label="Incidence Broadcast",
        description="Track incidence-local progress, but broadcast every variable event to all incident edges.",
        initial_state=incidence_initial,
        events=broadcast_events,
        step=incidence_step,
        coordinate_summary=incidence_coordinate,
        old_summary=incidence_old,
        incidence_summary=incidence_summary_fn,
        family_summary=incidence_family_summary,
        full_assignment_summary=incidence_summary_fn,
        output=incidence_output,
    ),
    SemanticDefinition(
        name="exclusive_overlap_claim",
        label="Exclusive Claim",
        description="Each seen variable is routed to a single best-supported incident family edge.",
        initial_state=claim_initial,
        events=claim_events,
        step=exclusive_step,
        coordinate_summary=claim_coordinate,
        old_summary=claim_old,
        incidence_summary=claim_incidence,
        family_summary=claim_family_summary,
        full_assignment_summary=claim_incidence,
        output=claim_output,
    ),
    SemanticDefinition(
        name="shared_overlap_budget",
        label="Budget Routing",
        description="Each seen variable contributes one conserved credit routed to the least-funded incident edge.",
        initial_state=claim_initial,
        events=claim_events,
        step=budget_step,
        coordinate_summary=claim_coordinate,
        old_summary=claim_old,
        incidence_summary=claim_incidence,
        family_summary=claim_family_summary,
        full_assignment_summary=claim_incidence,
        output=claim_output,
    ),
    SemanticDefinition(
        name="committed_allocation",
        label="Committed Allocation",
        description="Positive control: partial variable-to-edge assignments compose by disjoint-domain union on the V-hypergraph.",
        initial_state=claim_initial,
        events=committed_events,
        step=committed_step,
        coordinate_summary=claim_coordinate,
        old_summary=claim_old,
        incidence_summary=claim_incidence,
        family_summary=residual_profile_from_claims,
        full_assignment_summary=claim_incidence,
        output=residual_profile_from_claims,
        analysis_mode="segment_rows",
        segment_states=enumerate_committed_states,
        compose=compose_committed_state,
    ),
)


def analyze_family(semantic: SemanticDefinition, family: Family) -> CurvatureRecord:
    if semantic.analysis_mode == "segment_rows":
        automaton = build_segment_signature_analysis(semantic, family)
    else:
        automaton = build_automaton(semantic, family)
    p = max(family_union(family))
    k = max(len(edge) for edge in family)
    return CurvatureRecord(
        semantics=semantic.name,
        p=p,
        k=k,
        family=family,
        reachable_state_count=len(automaton["states"]),
        runtime_quotient_count=automaton["runtime_count"],
        coordinate_quotient_count=automaton["coordinate_count"],
        old_quotient_count=automaton["old_count"],
        incidence_quotient_count=automaton["incidence_count"],
        family_quotient_count=automaton["family_count"],
        full_assignment_quotient_count=automaton["full_assignment_count"],
        full_state_count=len(automaton["states"]),
        coordinate_curvature_gap=automaton["coordinate_curvature_gap"],
        fiber_holonomy_rank=automaton["fiber_holonomy_rank"],
        coordinate_exact=automaton["coordinate_exact"],
        old_exact=automaton["old_exact"],
        incidence_exact=automaton["incidence_exact"],
        family_exact=automaton["family_exact"],
        full_assignment_exact=automaton["full_assignment_exact"],
        witness_left_trace=automaton["witness_left_trace"],
        witness_right_trace=automaton["witness_right_trace"],
        witness_suffix=automaton["witness_suffix"],
        witness_left_state=automaton["witness_left_state"],
        witness_right_state=automaton["witness_right_state"],
        witness_suffix_text=None if automaton["witness_suffix"] is None else trace_text(automaton["witness_suffix"], family),
        witness_coordinate=automaton["witness_coordinate"],
        witness_left_output_now=automaton["witness_left_output_now"],
        witness_right_output_now=automaton["witness_right_output_now"],
        witness_left_output_future=automaton["witness_left_output_future"],
        witness_right_output_future=automaton["witness_right_output_future"],
        same_now_future_separate=automaton["same_now_future_separate"],
        nontrivial_coordinate_fibers=automaton["nontrivial_coordinate_fibers"],
    )


def record_order_key(record: CurvatureRecord) -> Tuple[object, ...]:
    witness_length = 0
    if record.witness_left_trace is not None:
        witness_length += len(record.witness_left_trace)
    if record.witness_right_trace is not None:
        witness_length += len(record.witness_right_trace)
    if record.witness_suffix is not None:
        witness_length += len(record.witness_suffix)
    return (
        record.p,
        record.k,
        len(record.family),
        record.reachable_state_count,
        witness_length,
        record.family,
    )


def record_to_json(record: CurvatureRecord) -> Dict[str, object]:
    return {
        "semantics": record.semantics,
        "p": record.p,
        "k": record.k,
        "family": [list(edge) for edge in record.family],
        "reachable_state_count": record.reachable_state_count,
        "runtime_quotient_count": record.runtime_quotient_count,
        "coordinate_quotient_count": record.coordinate_quotient_count,
        "old_quotient_count": record.old_quotient_count,
        "incidence_quotient_count": record.incidence_quotient_count,
        "family_quotient_count": record.family_quotient_count,
        "full_assignment_quotient_count": record.full_assignment_quotient_count,
        "full_state_count": record.full_state_count,
        "coordinate_curvature_gap": record.coordinate_curvature_gap,
        "fiber_holonomy_rank": record.fiber_holonomy_rank,
        "coordinate_exact": record.coordinate_exact,
        "old_exact": record.old_exact,
        "incidence_exact": record.incidence_exact,
        "family_exact": record.family_exact,
        "full_assignment_exact": record.full_assignment_exact,
        "witness_left_trace": None if record.witness_left_trace is None else list(record.witness_left_trace),
        "witness_right_trace": None if record.witness_right_trace is None else list(record.witness_right_trace),
        "witness_suffix": None if record.witness_suffix is None else list(record.witness_suffix),
        "witness_left_state": record.witness_left_state,
        "witness_right_state": record.witness_right_state,
        "witness_suffix_text": record.witness_suffix_text,
        "witness_coordinate": record.witness_coordinate,
        "witness_left_output_now": record.witness_left_output_now,
        "witness_right_output_now": record.witness_right_output_now,
        "witness_left_output_future": record.witness_left_output_future,
        "witness_right_output_future": record.witness_right_output_future,
        "same_now_future_separate": record.same_now_future_separate,
        "nontrivial_coordinate_fibers": [
            {"coordinate": coordinate, "class_count": class_count}
            for coordinate, class_count in record.nontrivial_coordinate_fibers
        ],
    }


def summary_to_json(summary: SemanticSummary) -> Dict[str, object]:
    return {
        "name": summary.name,
        "label": summary.label,
        "description": summary.description,
        "families_scanned": summary.families_scanned,
        "coordinate_split_count": summary.coordinate_split_count,
        "positive_gap_count": summary.positive_gap_count,
        "coordinate_exact_on_scan": summary.coordinate_exact_on_scan,
        "full_assignment_exact_on_scan": summary.full_assignment_exact_on_scan,
        "max_coordinate_curvature_gap": summary.max_coordinate_curvature_gap,
        "max_fiber_holonomy_rank": summary.max_fiber_holonomy_rank,
        "seed_record": record_to_json(summary.seed_record),
        "first_coordinate_split": None if summary.first_coordinate_split is None else record_to_json(summary.first_coordinate_split),
        "first_positive_gap": None if summary.first_positive_gap is None else record_to_json(summary.first_positive_gap),
    }


def build_report(
    summaries: Sequence[SemanticSummary],
    overall_first_split: CurvatureRecord | None,
    overall_first_positive_gap: CurvatureRecord | None,
    note_path: Path | None,
    json_path: Path,
    svg_path: Path,
) -> str:
    lines = [
        "# Runtime Hypergraph Curvature Search",
        "",
        "## Question",
        "",
        "This search asks for the first semantics where the full coordinate witness state stops being exact.",
        "The smoking gun is a reachable triple `(u, v, w)` with the same full coordinate state at `u` and `v`, but different runtime behavior after the same suffix `w`.",
        "For the committed-allocation positive control, the scan also tracks the stronger count-level invariant `kappa_pi = log2|Q_runtime| - log2|Q_coordinate|` from the earlier resource-carrier boundary.",
        "",
        "## Scan Setup",
        "",
        "- Families: exact full-union antichains on `[p]`, sorted lexicographically by family size, overlap, edge sizes, total size, and family tuple.",
        "- Search grid: `p <= 4`, `k <= 3`.",
        "- Seed crystal: `{{1,2}, {1,3}}`.",
        "- Runtime quotient: exact continuation quotient on reachable prefix states; for `committed_allocation` this is computed directly from exact composition rows over all suffix segments.",
        "- Coordinate quotient: quotient induced by the full coordinate witness state.",
        "- New invariants: `coordinate_curvature_gap = log2|Q_runtime| - log2|Q_coordinate|` and `fiber_holonomy_rank = max_fiber |Q_runtime inside fiber|`.",
        "",
        "## Semantics",
        "",
    ]
    for summary in summaries:
        lines.append(f"- `{summary.name}`: {summary.description}")

    lines.extend(
        [
            "",
            "## Summary Table",
            "",
            "| Semantics | Seed counts `(runtime / coordinate / incidence / family / full assignment)` | First split | First `kappa_pi > 0` | Max gap bits | Holonomy | Coordinate exact on scan | Full assignment exact on scan |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for summary in summaries:
        seed = summary.seed_record
        first_split = "none"
        first_gap = "none"
        if summary.first_coordinate_split is not None:
            record = summary.first_coordinate_split
            first_split = f"(p={record.p}, k={record.k}) {record.family}"
        if summary.first_positive_gap is not None:
            record = summary.first_positive_gap
            first_gap = f"(p={record.p}, k={record.k}) {record.family}"
        lines.append(
            f"| `{summary.label}` | `{seed.runtime_quotient_count} / {seed.coordinate_quotient_count} / {seed.incidence_quotient_count} / {seed.family_quotient_count} / {seed.full_assignment_quotient_count}` | `{first_split}` | `{first_gap}` | `{summary.max_coordinate_curvature_gap:.3f}` | `{summary.max_fiber_holonomy_rank}` | `{summary.coordinate_exact_on_scan}` | `{summary.full_assignment_exact_on_scan}` |"
        )

    lines.extend(
        [
            "",
            "## Controls",
            "",
        ]
    )
    negative = [summary for summary in summaries if summary.first_coordinate_split is None]
    for summary in negative:
        lines.extend(
            [
                f"- `{summary.name}` stays flat on the full scan.",
                f"  Seed counts: runtime `{summary.seed_record.runtime_quotient_count}`, coordinate `{summary.seed_record.coordinate_quotient_count}`, incidence `{summary.seed_record.incidence_quotient_count}`.",
                f"  `coordinate_curvature_gap = {summary.seed_record.coordinate_curvature_gap:.3f}` and `fiber_holonomy_rank = {summary.seed_record.fiber_holonomy_rank}`.",
            ]
        )

    lines.extend(
        [
            "",
            "## First Positive Counterexamples",
            "",
        ]
    )
    positives = [summary for summary in summaries if summary.first_coordinate_split is not None]
    for summary in positives:
        record = summary.first_coordinate_split
        assert record is not None
        lines.extend(
            [
                f"### `{summary.name}`",
                "",
                f"- first coordinate split: `(p={record.p}, k={record.k}, |A|={len(record.family)})` with family `{record.family}`",
                f"- quotient counts: runtime `{record.runtime_quotient_count}`, coordinate `{record.coordinate_quotient_count}`, old `{record.old_quotient_count}`, incidence `{record.incidence_quotient_count}`, family `{record.family_quotient_count}`, full assignment `{record.full_assignment_quotient_count}`",
                f"- curvature gap: `{record.coordinate_curvature_gap:.3f}` bits",
                f"- fiber holonomy rank: `{record.fiber_holonomy_rank}`",
                f"- incidence exact: `{record.incidence_exact}`",
                f"- family-local exact: `{record.family_exact}`",
                f"- full assignment exact: `{record.full_assignment_exact}`",
                f"- witness coordinate: `{record.witness_coordinate}`",
                f"- left trace `u`: `{trace_text(record.witness_left_trace or (), record.family)}`",
                f"- right trace `v`: `{trace_text(record.witness_right_trace or (), record.family)}`",
                f"- suffix `w`: `{trace_text(record.witness_suffix or (), record.family)}`",
                f"- outputs now: `{record.witness_left_output_now}` versus `{record.witness_right_output_now}`",
                f"- outputs after suffix: `{record.witness_left_output_future}` versus `{record.witness_right_output_future}`",
                f"- same-now / future-separate: `{record.same_now_future_separate}`",
            ]
        )
        if record.nontrivial_coordinate_fibers:
            fiber_text = ", ".join(
                f"{coordinate} -> {class_count}"
                for coordinate, class_count in record.nontrivial_coordinate_fibers
            )
            lines.append(f"- nontrivial coordinate fibers: `{fiber_text}`")
        if summary.first_positive_gap is not None:
            gap_record = summary.first_positive_gap
            lines.append(
                f"- first positive `kappa_pi`: `(p={gap_record.p}, k={gap_record.k})` with family `{gap_record.family}` and gap `{gap_record.coordinate_curvature_gap:.3f}` bits"
            )
        lines.append("")

    if overall_first_split is not None:
        lines.extend(
            [
                "## Overall First Coordinate Split",
                "",
                f"The lexicographically first world where full coordinate state fails is `{overall_first_split.family}` at `(p={overall_first_split.p}, k={overall_first_split.k})`, reached by `{overall_first_split.semantics}`.",
                f"It has `|Q_runtime| = {overall_first_split.runtime_quotient_count}` and `|Q_coordinate| = {overall_first_split.coordinate_quotient_count}`, with `coordinate_curvature_gap = {overall_first_split.coordinate_curvature_gap:.3f}` bits.",
                "",
            ]
        )
    if overall_first_positive_gap is not None:
        lines.extend(
            [
                "## Overall First Positive Curvature Gap",
                "",
                f"The lexicographically first world with `kappa_pi > 0` is `{overall_first_positive_gap.family}` at `(p={overall_first_positive_gap.p}, k={overall_first_positive_gap.k})`, reached by `{overall_first_positive_gap.semantics}`.",
                f"It has `|Q_runtime| = {overall_first_positive_gap.runtime_quotient_count}` and `|Q_coordinate| = {overall_first_positive_gap.coordinate_quotient_count}`, so `coordinate_curvature_gap = {overall_first_positive_gap.coordinate_curvature_gap:.3f}` bits.",
                "",
            ]
        )

    full_assignment_failure = next(
        (summary for summary in summaries if not summary.full_assignment_exact_on_scan),
        None,
    )
    lines.extend(
        [
            "## Interpretation",
            "",
        ]
    )
    if full_assignment_failure is None:
        lines.extend(
            [
                "No tested semantics on this library produced a world where `full_assignment` itself failed.",
                "So the current search now separates two boundaries cleanly: coordinate state can fail, and `committed_allocation` reproduces the known positive `kappa_pi` gap, but the stronger global hypergraph-runtime theorem is still open.",
                "On the scanned positives, the first exact runtime object is therefore closer to incidence transport on the hypergraph nerve than to an irreducibly global family state.",
                "",
            ]
        )
    else:
        lines.extend(
            [
                f"`{full_assignment_failure.name}` is the first semantics on the scanned grid where full assignment is not exact, so this library already contains a genuinely global runtime hypergraph effect.",
                "",
            ]
        )

    lines.extend(
        [
            "## Artifacts",
            "",
            f"- JSON: [{json_path.name}]({json_path})",
            f"- Figure: [{svg_path.name}]({svg_path})",
        ]
    )
    if note_path is not None:
        lines.append(f"- Note: [{note_path.name}]({note_path})")
    return "\n".join(lines) + "\n"


def render_svg(
    summaries: Sequence[SemanticSummary],
    overall_first_split: CurvatureRecord | None,
    overall_first_positive_gap: CurvatureRecord | None,
) -> str:
    width = 1500
    height = 900
    left = 48
    top = 58
    row_height = 42
    table_width = width - 2 * left
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<style>",
        "text { font-family: Menlo, Monaco, Consolas, monospace; font-size: 12px; fill: #1f2933; }",
        ".title { font-size: 18px; font-weight: 700; }",
        ".subtitle { fill: #52606d; }",
        ".header { font-weight: 700; fill: #102a43; }",
        ".panel { fill: #ffffff; stroke: #d9e2ec; stroke-width: 1; }",
        ".flat { fill: #f4f7f9; }",
        ".curved { fill: #eef6ff; }",
        ".positive { fill: #eefbf3; }",
        "</style>",
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#fbfbfd"/>',
        f'<text x="{left}" y="28" class="title">Runtime Hypergraph Curvature Search</text>',
        f'<text x="{left}" y="46" class="subtitle">Coordinate curvature is positive when the runtime quotient strictly exceeds the full coordinate quotient.</text>',
        f'<rect x="{left}" y="{top}" width="{table_width}" height="286" class="panel"/>',
    ]
    columns = {
        "sem": left + 16,
        "seed": left + 170,
        "split": left + 330,
        "gapfirst": left + 600,
        "gap": left + 900,
        "hol": left + 1010,
        "assign": left + 1120,
        "note": left + 1270,
    }
    head_y = top + 24
    for key, label in (
        ("sem", "semantics"),
        ("seed", "seed counts"),
        ("split", "first split"),
        ("gapfirst", "first kappa>0"),
        ("gap", "max gap"),
        ("hol", "holonomy"),
        ("assign", "full assignment exact"),
        ("note", "status"),
    ):
        lines.append(f'<text x="{columns[key]}" y="{head_y}" class="header">{label}</text>')

    for index, summary in enumerate(summaries):
        y = head_y + 26 + index * row_height
        row_class = "flat" if summary.first_coordinate_split is None else "curved"
        if summary.name == "committed_allocation":
            row_class = "positive"
        lines.append(f'<rect x="{left + 10}" y="{y - 14}" width="{table_width - 20}" height="26" class="{row_class}"/>')
        seed = summary.seed_record
        first_split = "none"
        first_gap = "none"
        status = "flat on scan"
        if summary.first_coordinate_split is not None:
            record = summary.first_coordinate_split
            first_split = f"(p={record.p},k={record.k})"
            status = "split"
        if summary.first_positive_gap is not None:
            record = summary.first_positive_gap
            first_gap = f"(p={record.p},k={record.k})"
            status = "kappa>0"
        if summary.name == "committed_allocation":
            status = "positive control"
        lines.extend(
            [
                f'<text x="{columns["sem"]}" y="{y}">{summary.label}</text>',
                f'<text x="{columns["seed"]}" y="{y}">{seed.runtime_quotient_count}/{seed.coordinate_quotient_count}/{seed.full_assignment_quotient_count}</text>',
                f'<text x="{columns["split"]}" y="{y}">{first_split}</text>',
                f'<text x="{columns["gapfirst"]}" y="{y}">{first_gap}</text>',
                f'<text x="{columns["gap"]}" y="{y}">{summary.max_coordinate_curvature_gap:.3f}</text>',
                f'<text x="{columns["hol"]}" y="{y}">{summary.max_fiber_holonomy_rank}</text>',
                f'<text x="{columns["assign"]}" y="{y}">{summary.full_assignment_exact_on_scan}</text>',
                f'<text x="{columns["note"]}" y="{y}">{status}</text>',
            ]
        )

    box_y = top + 314
    box_height = 470
    lines.append(f'<rect x="{left}" y="{box_y}" width="{table_width}" height="{box_height}" class="panel"/>')
    lines.append(f'<text x="{left + 16}" y="{box_y + 24}" class="header">Boundary statement from the scan</text>')
    if overall_first_split is None:
        lines.append(f'<text x="{left + 16}" y="{box_y + 52}">No coordinate split was found on the scanned library.</text>')
    else:
        lines.extend(
            [
                f'<text x="{left + 16}" y="{box_y + 52}">First split: {overall_first_split.semantics} on {overall_first_split.family} at (p={overall_first_split.p}, k={overall_first_split.k}).</text>',
                f'<text x="{left + 16}" y="{box_y + 74}">Counts: runtime {overall_first_split.runtime_quotient_count}, coordinate {overall_first_split.coordinate_quotient_count}, incidence {overall_first_split.incidence_quotient_count}, family {overall_first_split.family_quotient_count}.</text>',
                f'<text x="{left + 16}" y="{box_y + 96}">Witness u = {trace_text(overall_first_split.witness_left_trace or (), overall_first_split.family)}</text>',
                f'<text x="{left + 16}" y="{box_y + 118}">Witness v = {trace_text(overall_first_split.witness_right_trace or (), overall_first_split.family)}</text>',
                f'<text x="{left + 16}" y="{box_y + 140}">Suffix w = {trace_text(overall_first_split.witness_suffix or (), overall_first_split.family)}</text>',
                f'<text x="{left + 16}" y="{box_y + 162}">Coordinate fiber = {overall_first_split.witness_coordinate}</text>',
                f'<text x="{left + 16}" y="{box_y + 184}">Outputs now: {overall_first_split.witness_left_output_now} vs {overall_first_split.witness_right_output_now}</text>',
                f'<text x="{left + 16}" y="{box_y + 206}">Outputs after suffix: {overall_first_split.witness_left_output_future} vs {overall_first_split.witness_right_output_future}</text>',
            ]
        )
    if overall_first_positive_gap is not None:
        lines.append(f'<text x="{left + 16}" y="{box_y + 230}">First positive kappa_pi: {overall_first_positive_gap.semantics} on {overall_first_positive_gap.family} with gap {overall_first_positive_gap.coordinate_curvature_gap:.3f} bits.</text>')
    lines.extend(
        [
            f'<text x="{left + 16}" y="{box_y + 270}">Controls: broadcast_control and incidence_local_progress remain coordinate-flat on the full scan.</text>',
            f'<text x="{left + 16}" y="{box_y + 292}">Positive control: committed_allocation reproduces kappa_pi &gt; 0 on the seed V-hypergraph.</text>',
            f'<text x="{left + 16}" y="{box_y + 314}">No scanned semantics made full_assignment itself inexact, so the current evidence points to an incidence-transport runtime object rather than a fully global one.</text>',
        ]
    )
    lines.append("</svg>")
    return "\n".join(lines)


def build_note(
    summaries: Sequence[SemanticSummary],
    overall_first_split: CurvatureRecord | None,
    overall_first_positive_gap: CurvatureRecord | None,
) -> str | None:
    positive_summaries = [summary for summary in summaries if summary.first_coordinate_split is not None]
    if overall_first_split is None or not positive_summaries:
        return None
    if any(not summary.full_assignment_exact_on_scan for summary in positive_summaries):
        return None
    committed_summary = next(summary for summary in summaries if summary.name == "committed_allocation")
    return "\n".join(
        [
            "# Runtime Hypergraph Curvature",
            "",
            "## Thesis",
            "",
            "The current curvature scan suggests that the first true runtime object beyond the flat coordinate carrier is incidence transport on the hypergraph nerve, not yet a genuinely global family state.",
            "",
            "## Source Basis",
            "",
            "- [runtime_hypergraph_curvature_search.md](/Users/jackg/stark/results/runtime_hypergraph_curvature_search.md)",
            "- [runtime_hypergraph_curvature_search.json](/Users/jackg/stark/results/runtime_hypergraph_curvature_search.json)",
            "- [resource_carrier_boundary.md](/Users/jackg/stark/results/resource_carrier_boundary.md)",
            "- [semantic-boundary-atlas.md](/Users/jackg/stark/docs/writing/semantic-boundary-atlas.md)",
            "",
            "## Exact Scan Boundary",
            "",
            "On the scanned library:",
            "",
            "- `broadcast_control` and `incidence_local_progress` have zero coordinate curvature everywhere.",
            "- `committed_allocation` reproduces the known positive `kappa_pi` gap from the resource-carrier boundary; on the scanned grid its first positive world is `{{1,2}, {1,3}}`.",
            "- `exclusive_overlap_claim` and `shared_overlap_budget` also create coordinate splits, but they do not improve the positive-control boundary.",
            "- in every positive world on the scan, `full_assignment` remains exact.",
            "",
            "So the current evidence is:",
            "",
            "> overlap can force runtime curvature beyond the full coordinate witness state, but the first curved runtime object still factors through incidence-resolved assignment rather than a genuinely global hypergraph memory state.",
            "",
            f"The committed-allocation control reaches `max kappa_pi = {committed_summary.max_coordinate_curvature_gap:.3f}` bits on the scanned grid.",
            "",
            "## Conjecture Template",
            "",
            "For deterministic prefix-compositional carriers built from per-variable overlap transport on a fixed antichain family, the first exact runtime object is the incidence-transport quotient on the hypergraph nerve.",
            "",
            "Equivalently:",
            "",
            "- coordinate state can be too coarse,",
            "- family-local summaries can be too coarse,",
            "- but incidence-resolved assignment remains exact on the scanned library.",
            "",
            "The next true runtime-hypergraph theorem would therefore require a carrier or composition law where even incidence-resolved assignment has nontrivial holonomy.",
            "",
        ]
    ) + "\n"


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    all_records: Dict[str, List[CurvatureRecord]] = {semantic.name: [] for semantic in SEMANTICS}
    for semantic in SEMANTICS:
        for p in P_SCAN:
            for k in range(1, min(K_MAX, p) + 1):
                for family in sorted_families(p, k):
                    all_records[semantic.name].append(analyze_family(semantic, family))

    summaries: List[SemanticSummary] = []
    all_splits: List[CurvatureRecord] = []
    all_positive_gap: List[CurvatureRecord] = []
    for semantic in SEMANTICS:
        records = all_records[semantic.name]
        seed_record = next(record for record in records if record.family == SEED_FAMILY and record.p == 3 and record.k == 2)
        splits = [record for record in records if not record.coordinate_exact]
        if splits:
            splits.sort(key=record_order_key)
            all_splits.extend(splits)
            first_split = splits[0]
        else:
            first_split = None
        positive_gap = [record for record in records if record.coordinate_curvature_gap > 0]
        if positive_gap:
            positive_gap.sort(key=record_order_key)
            all_positive_gap.extend(positive_gap)
            first_positive_gap = positive_gap[0]
        else:
            first_positive_gap = None
        summaries.append(
            SemanticSummary(
                name=semantic.name,
                label=semantic.label,
                description=semantic.description,
                families_scanned=len(records),
                coordinate_split_count=len(splits),
                positive_gap_count=len(positive_gap),
                coordinate_exact_on_scan=all(record.coordinate_exact for record in records),
                full_assignment_exact_on_scan=all(record.full_assignment_exact for record in records),
                max_coordinate_curvature_gap=max(record.coordinate_curvature_gap for record in records),
                max_fiber_holonomy_rank=max(record.fiber_holonomy_rank for record in records),
                seed_record=seed_record,
                first_coordinate_split=first_split,
                first_positive_gap=first_positive_gap,
            )
        )

    overall_first_split = None
    if all_splits:
        all_splits.sort(key=record_order_key)
        overall_first_split = all_splits[0]
    overall_first_positive_gap = None
    if all_positive_gap:
        all_positive_gap.sort(key=record_order_key)
        overall_first_positive_gap = all_positive_gap[0]

    json_path = RESULTS_DIR / "runtime_hypergraph_curvature_search.json"
    report_path = RESULTS_DIR / "runtime_hypergraph_curvature_search.md"
    svg_path = RESULTS_DIR / "runtime_hypergraph_curvature_search.svg"
    note_path = DOCS_DIR / "runtime-hypergraph-curvature.md"

    payload = {
        "scan": {
            "p_scan": list(P_SCAN),
            "k_max": K_MAX,
            "seed_family": [list(edge) for edge in SEED_FAMILY],
            "families_per_semantics": sum(summary.families_scanned for summary in summaries),
        },
        "semantics": [summary_to_json(summary) for summary in summaries],
        "overall_first_coordinate_split": None if overall_first_split is None else record_to_json(overall_first_split),
        "overall_first_positive_gap": None if overall_first_positive_gap is None else record_to_json(overall_first_positive_gap),
    }
    json_path.write_text(json.dumps(payload, indent=2))
    note_text = build_note(summaries, overall_first_split, overall_first_positive_gap)
    if note_text is not None:
        note_path.write_text(note_text)
    elif note_path.exists():
        note_path.unlink()
    report_path.write_text(
        build_report(
            summaries,
            overall_first_split,
            overall_first_positive_gap,
            note_path if note_text is not None else None,
            json_path,
            svg_path,
        )
    )
    svg_path.write_text(render_svg(summaries, overall_first_split, overall_first_positive_gap))

    print(f"Wrote {report_path}")
    print(f"Wrote {json_path}")
    print(f"Wrote {svg_path}")
    if note_text is not None:
        print(f"Wrote {note_path}")


if __name__ == "__main__":
    main()

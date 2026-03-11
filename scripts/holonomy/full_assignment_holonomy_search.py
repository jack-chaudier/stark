#!/usr/bin/env python3
"""Search for the first semantics with full-assignment holonomy.

The target boundary is stronger than coordinate curvature. We want a
deterministic prefix-compositional semantics where the raw committed assignment
is no longer exact:

    full_assignment(u) == full_assignment(v)
    but u and v are not continuation-equivalent.

The strongest witness is hidden future:

    full_assignment(u) == full_assignment(v)
    output(u) == output(v)
    and there exists a non-empty suffix w with output(u + w) != output(v + w).
"""

from __future__ import annotations

import json
import math
import sys
from collections import defaultdict, deque
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from typing import Callable, DefaultDict, Dict, Hashable, Iterable, List, Sequence, Tuple

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "README.md").exists())
SCRIPTS_ROOT = ROOT / "scripts"
for candidate in [SCRIPTS_ROOT] + sorted(path for path in SCRIPTS_ROOT.iterdir() if path.is_dir()):
    candidate_str = str(candidate)
    if candidate_str not in sys.path:
        sys.path.insert(0, candidate_str)

from runtime_collapse_boundary import enumerate_exact_antichains, log2_count

RESULTS_DIR = ROOT / "results" / "holonomy" / "full-assignment-holonomy"
DOCS_DIR = ROOT / "docs" / "writing" / "experiments" / "holonomy"

Family = Tuple[Tuple[int, ...], ...]
Trace = Tuple[Hashable, ...]

BASE_P_SCAN = (2, 3, 4)
BASE_K_MAX = 3
EXPANDED_P_SCAN = (5,)
EXPANDED_K_MAX = 4

SEED_FAMILIES: Dict[str, Family] = {
    "V": ((1, 2), (1, 3)),
    "triangle": ((1, 2), (1, 3), (2, 3)),
    "overlap_star": ((1, 2), (1, 3), (1, 4)),
    "k4_pair_family": (
        (1, 2),
        (1, 3),
        (1, 4),
        (2, 3),
        (2, 4),
        (3, 4),
    ),
}


@dataclass(frozen=True)
class PairDescriptor:
    pair_index: int
    lower_edge: int
    upper_edge: int
    shared: Tuple[int, ...]
    lower_only: Tuple[int, ...]
    upper_only: Tuple[int, ...]


@dataclass(frozen=True)
class TriangleDescriptor:
    triangle_index: int
    edges: Tuple[int, int, int]


@dataclass(frozen=True)
class FamilyContext:
    family: Family
    universe: Tuple[int, ...]
    assignment_events: Tuple[Tuple[int, int], ...]
    pairs: Tuple[PairDescriptor, ...]
    pair_indices_by_edge: Tuple[Tuple[int, ...], ...]
    triangles: Tuple[TriangleDescriptor, ...]
    triangle_indices_by_edge: Tuple[Tuple[int, ...], ...]


@dataclass(frozen=True)
class WitnessRecord:
    left_trace: Trace | None
    right_trace: Trace | None
    suffix: Trace | None
    summary_value: str | None
    left_state: str | None
    right_state: str | None
    left_output_now: str | None
    right_output_now: str | None
    left_output_future: str | None
    right_output_future: str | None
    same_now: bool
    non_empty_suffix: bool


@dataclass(frozen=True)
class SemanticDefinition:
    name: str
    label: str
    description: str
    token_scope: str
    token_alphabet_size: int
    analysis_mode: str
    initial_state: Callable[[FamilyContext], Hashable]
    events: Callable[[FamilyContext], Tuple[Hashable, ...]]
    step: Callable[[Hashable, Hashable, FamilyContext], Hashable]
    output: Callable[[Hashable, FamilyContext], Hashable]
    coordinate_summary: Callable[[Hashable, FamilyContext], Hashable]
    full_assignment_summary: Callable[[Hashable, FamilyContext], Hashable]
    token_summary: Callable[[Hashable, FamilyContext], Hashable]
    incidence_summary: Callable[[Hashable, FamilyContext], Hashable]
    family_summary: Callable[[Hashable, FamilyContext], Hashable]
    segment_states: Callable[[FamilyContext], Tuple[Hashable, ...]] | None = None
    compose: Callable[[Hashable, Hashable, FamilyContext], Hashable | None] | None = None


@dataclass(frozen=True)
class AnalysisRecord:
    semantics: str
    token_scope: str
    token_alphabet_size: int
    p: int
    k: int
    family: Family
    reachable_state_count: int
    runtime_quotient_count: int
    coordinate_quotient_count: int
    full_assignment_quotient_count: int
    token_quotient_count: int
    incidence_quotient_count: int
    family_quotient_count: int
    coordinate_curvature_gap: float
    assignment_curvature_gap: float
    coordinate_exact: bool
    full_assignment_exact: bool
    token_exact: bool
    incidence_exact: bool
    family_exact: bool
    assignment_holonomy_rank: int
    hidden_future_rank: int
    coordinate_witness: WitnessRecord | None
    full_assignment_witness: WitnessRecord | None
    hidden_future_witness: WitnessRecord | None


@dataclass(frozen=True)
class SemanticSummary:
    name: str
    label: str
    description: str
    token_scope: str
    token_alphabet_size: int
    families_scanned: int
    coordinate_split_count: int
    coordinate_gap_count: int
    full_assignment_split_count: int
    hidden_future_count: int
    full_assignment_exact_on_scan: bool
    max_coordinate_curvature_gap: float
    max_assignment_curvature_gap: float
    max_assignment_holonomy_rank: int
    max_hidden_future_rank: int
    seed_record: AnalysisRecord | None
    first_coordinate_split: AnalysisRecord | None
    first_coordinate_gap: AnalysisRecord | None
    first_full_assignment_split: AnalysisRecord | None
    first_hidden_future_split: AnalysisRecord | None


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


def build_context(family: Family) -> FamilyContext:
    universe = family_union(family)
    assignment_events = tuple(
        (variable, edge_index)
        for variable in universe
        for edge_index, edge in enumerate(family)
        if variable in edge
    )
    pairs: List[PairDescriptor] = []
    for left, right in combinations(range(len(family)), 2):
        left_set = set(family[left])
        right_set = set(family[right])
        shared = tuple(sorted(left_set & right_set))
        if not shared:
            continue
        pairs.append(
            PairDescriptor(
                pair_index=len(pairs),
                lower_edge=left,
                upper_edge=right,
                shared=shared,
                lower_only=tuple(sorted(left_set - right_set)),
                upper_only=tuple(sorted(right_set - left_set)),
            )
        )
    pair_indices_by_edge = tuple(
        tuple(pair.pair_index for pair in pairs if edge_index in (pair.lower_edge, pair.upper_edge))
        for edge_index in range(len(family))
    )
    triangles: List[TriangleDescriptor] = []
    for edges in combinations(range(len(family)), 3):
        if all(set(family[left]) & set(family[right]) for left, right in combinations(edges, 2)):
            triangles.append(TriangleDescriptor(triangle_index=len(triangles), edges=edges))
    triangle_indices_by_edge = tuple(
        tuple(triangle.triangle_index for triangle in triangles if edge_index in triangle.edges)
        for edge_index in range(len(family))
    )
    return FamilyContext(
        family=family,
        universe=universe,
        assignment_events=assignment_events,
        pairs=tuple(pairs),
        pair_indices_by_edge=pair_indices_by_edge,
        triangles=tuple(triangles),
        triangle_indices_by_edge=triangle_indices_by_edge,
    )


def assignment_presence(assignment: Sequence[int]) -> Tuple[int, ...]:
    return tuple(1 if value >= 0 else 0 for value in assignment)


def edge_has_support(assignment: Sequence[int], edge_index: int) -> bool:
    return any(value == edge_index for value in assignment)


def edge_has_support_on(
    assignment: Sequence[int],
    edge_index: int,
    variables: Iterable[int],
) -> bool:
    return any(assignment[variable - 1] == edge_index for variable in variables)


def base_residual_profile(assignment: Sequence[int], family: Family) -> Family:
    residuals: List[Tuple[int, ...]] = []
    for edge_index, edge in enumerate(family):
        live = True
        remaining: List[int] = []
        for variable in edge:
            value = assignment[variable - 1]
            if value == -1:
                remaining.append(variable)
            elif value != edge_index:
                live = False
                break
        if live:
            residuals.append(tuple(remaining))
    return tuple(residuals)


def completed_edges_from_presence(presence: Sequence[int], family: Family) -> Family:
    return tuple(edge for edge in family if all(presence[item - 1] for item in edge))


def format_family(family: Family) -> str:
    return "{" + ", ".join("{" + ",".join(str(item) for item in edge) + "}" for edge in family) + "}"


def event_text(event: Hashable, family: Family) -> str:
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


def trace_text(trace: Trace | None, family: Family) -> str:
    if not trace:
        return "[]"
    return "[" + ", ".join(event_text(event, family) for event in trace) + "]"


def assignment_text(assignment: Sequence[int], family: Family) -> str:
    pieces = []
    for variable, edge_index in enumerate(assignment, start=1):
        if edge_index >= 0:
            pieces.append(f"{variable}->{family[edge_index]}")
    return "{" + ", ".join(pieces) + "}" if pieces else "{}"


def state_text(value: Hashable, family: Family) -> str:
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
            assignment = list(value)
            if all(item in (0, 1) for item in assignment):
                return str(tuple(assignment))
            if all(item == -1 or 0 <= item < len(family) for item in assignment):
                return assignment_text(assignment, family)
        if len(value) == 3 and isinstance(value[0], tuple):
            assignment, pair_tokens, simplex_tokens = value
            pieces = [assignment_text(assignment, family)]
            if pair_tokens:
                pieces.append(f"pair={pair_tokens}")
            if simplex_tokens:
                pieces.append(f"tri={simplex_tokens}")
            return " | ".join(pieces)
    return str(value)


def active_pair_token(update_kind: str, token_value: int) -> bool:
    if update_kind in {"toggle_mod2", "latch"}:
        return token_value == 1
    if update_kind == "capped_inc2":
        return token_value == 2
    if update_kind == "orientation":
        return token_value != 0
    raise ValueError(f"unknown pair update kind {update_kind}")


def edge_blocked_by_pair(
    edge_index: int,
    pair: PairDescriptor,
    token_value: int,
    update_kind: str,
    gate_kind: str,
) -> bool:
    if gate_kind == "block_lower_complete":
        return edge_index == pair.lower_edge and active_pair_token(update_kind, token_value)
    if gate_kind == "block_upper_complete":
        return edge_index == pair.upper_edge and active_pair_token(update_kind, token_value)
    if gate_kind == "block_oriented_complete":
        return (
            (edge_index == pair.lower_edge and token_value == 1)
            or (edge_index == pair.upper_edge and token_value == 2)
        )
    if gate_kind == "block_lower_token2":
        return edge_index == pair.lower_edge and token_value == 2
    raise ValueError(f"unknown pair gate kind {gate_kind}")


def edge_blocked_by_triangle(
    edge_index: int,
    triangle: TriangleDescriptor,
    token_value: int,
    gate_kind: str,
) -> bool:
    lowest_edge = min(triangle.edges)
    if gate_kind == "block_lowest_complete":
        return edge_index == lowest_edge and token_value == 1
    if gate_kind == "block_oriented_complete":
        if token_value == 0:
            return False
        local_index = triangle.edges.index(edge_index) + 1
        return token_value == local_index
    raise ValueError(f"unknown triangle gate kind {gate_kind}")


def pair_triggered(
    trigger_kind: str,
    pair: PairDescriptor,
    assignment: Sequence[int],
    event: Tuple[int, int],
) -> bool:
    variable, chosen_edge = event
    if chosen_edge not in (pair.lower_edge, pair.upper_edge):
        return False
    chosen_is_lower = chosen_edge == pair.lower_edge
    other_edge = pair.upper_edge if chosen_is_lower else pair.lower_edge
    other_live = edge_has_support(assignment, other_edge)
    other_exclusive_live = edge_has_support_on(
        assignment,
        other_edge,
        pair.upper_only if chosen_is_lower else pair.lower_only,
    )
    shared = variable in pair.shared
    exclusive = variable in (pair.lower_only if chosen_is_lower else pair.upper_only)
    both_live_before = edge_has_support(assignment, pair.lower_edge) and edge_has_support(assignment, pair.upper_edge)
    both_live_after = (
        edge_has_support(assignment, pair.lower_edge) or chosen_edge == pair.lower_edge
    ) and (
        edge_has_support(assignment, pair.upper_edge) or chosen_edge == pair.upper_edge
    )
    if trigger_kind == "shared_other_live":
        return shared and other_live
    if trigger_kind == "shared_other_exclusive_live":
        return shared and other_exclusive_live
    if trigger_kind == "exclusive_other_live":
        return exclusive and other_live
    if trigger_kind == "any_other_live":
        return other_live
    if trigger_kind == "pair_activates":
        return not both_live_before and both_live_after
    raise ValueError(f"unknown pair trigger {trigger_kind}")


def update_pair_token(
    token_value: int,
    update_kind: str,
    chosen_edge: int,
    pair: PairDescriptor,
) -> int:
    if update_kind == "toggle_mod2":
        return token_value ^ 1
    if update_kind == "latch":
        return 1
    if update_kind == "capped_inc2":
        return min(2, token_value + 1)
    if update_kind == "orientation":
        return 1 if chosen_edge == pair.lower_edge else 2
    raise ValueError(f"unknown pair update kind {update_kind}")


def triangle_triggered(
    trigger_kind: str,
    triangle: TriangleDescriptor,
    assignment: Sequence[int],
    event: Tuple[int, int],
) -> bool:
    variable, chosen_edge = event
    if chosen_edge not in triangle.edges:
        return False
    live_before = [edge_has_support(assignment, edge_index) for edge_index in triangle.edges]
    live_after = [live or edge_index == chosen_edge for live, edge_index in zip(live_before, triangle.edges)]
    if trigger_kind == "triangle_activates":
        return not all(live_before) and all(live_after)
    raise ValueError(f"unknown triangle trigger {trigger_kind}")


def update_triangle_token(
    token_value: int,
    update_kind: str,
    chosen_edge: int,
    triangle: TriangleDescriptor,
) -> int:
    if update_kind == "toggle_mod2":
        return token_value ^ 1
    if update_kind == "orientation":
        return triangle.edges.index(chosen_edge) + 1
    raise ValueError(f"unknown triangle update kind {update_kind}")


def broadcast_initial(context: FamilyContext) -> Tuple[int, ...]:
    return tuple(0 for _ in context.universe)


def broadcast_events(context: FamilyContext) -> Tuple[int, ...]:
    return context.universe


def broadcast_step(state: Tuple[int, ...], event: int, context: FamilyContext) -> Tuple[int, ...]:
    updated = list(state)
    updated[event - 1] = 1
    return tuple(updated)


def broadcast_output(state: Tuple[int, ...], context: FamilyContext) -> Family:
    return completed_edges_from_presence(state, context.family)


def broadcast_coordinate(state: Tuple[int, ...], context: FamilyContext) -> Tuple[int, ...]:
    return state


def broadcast_full_assignment(state: Tuple[int, ...], context: FamilyContext) -> Tuple[int, ...]:
    return state


def broadcast_token_summary(state: Tuple[int, ...], context: FamilyContext) -> Tuple[int, ...]:
    return state


def broadcast_incidence(state: Tuple[int, ...], context: FamilyContext) -> Tuple[int, ...]:
    return state


def broadcast_family_summary(state: Tuple[int, ...], context: FamilyContext) -> Tuple[int, ...]:
    return tuple(sum(state[item - 1] for item in edge) for edge in context.family)


def committed_segment_states(context: FamilyContext) -> Tuple[Tuple[int, ...], ...]:
    options = []
    for variable in context.universe:
        incident = tuple(edge_index for edge_index, edge in enumerate(context.family) if variable in edge)
        options.append((-1,) + incident)
    states: List[Tuple[int, ...]] = [tuple()]
    for option in options:
        if not states:
            states = [tuple((choice,)) for choice in option]
            continue
        states = [state + (choice,) for state in states for choice in option]
    return tuple(states)


def committed_compose(
    left: Tuple[int, ...],
    right: Tuple[int, ...],
    context: FamilyContext,
) -> Tuple[int, ...] | None:
    merged: List[int] = []
    for left_value, right_value in zip(left, right):
        if left_value >= 0 and right_value >= 0:
            return None
        merged.append(right_value if left_value == -1 else left_value)
    return tuple(merged)


def committed_output(state: Tuple[int, ...], context: FamilyContext) -> Family:
    return base_residual_profile(state, context.family)


def committed_coordinate(state: Tuple[int, ...], context: FamilyContext) -> Tuple[int, ...]:
    return assignment_presence(state)


def committed_full_assignment(state: Tuple[int, ...], context: FamilyContext) -> Tuple[int, ...]:
    return state


def committed_token_summary(state: Tuple[int, ...], context: FamilyContext) -> Tuple[int, ...]:
    return state


def committed_incidence(state: Tuple[int, ...], context: FamilyContext) -> Tuple[int, ...]:
    return state


def committed_family_summary(state: Tuple[int, ...], context: FamilyContext) -> Family:
    return base_residual_profile(state, context.family)


def token_initial(context: FamilyContext) -> Tuple[Tuple[int, ...], Tuple[int, ...], Tuple[int, ...]]:
    return (
        tuple(-1 for _ in context.universe),
        tuple(0 for _ in context.pairs),
        tuple(0 for _ in context.triangles),
    )


def token_events(context: FamilyContext) -> Tuple[Tuple[int, int], ...]:
    return context.assignment_events


def token_coordinate(state: Tuple[Tuple[int, ...], Tuple[int, ...], Tuple[int, ...]], context: FamilyContext) -> Tuple[int, ...]:
    return assignment_presence(state[0])


def token_full_assignment(state: Tuple[Tuple[int, ...], Tuple[int, ...], Tuple[int, ...]], context: FamilyContext) -> Tuple[int, ...]:
    return state[0]


def token_summary(state: Tuple[Tuple[int, ...], Tuple[int, ...], Tuple[int, ...]], context: FamilyContext) -> Hashable:
    assignment, pair_tokens, simplex_tokens = state
    if simplex_tokens:
        return assignment, pair_tokens, simplex_tokens
    return assignment, pair_tokens


def token_incidence(state: Tuple[Tuple[int, ...], Tuple[int, ...], Tuple[int, ...]], context: FamilyContext) -> Tuple[int, ...]:
    return state[0]


def token_family_summary(state: Tuple[Tuple[int, ...], Tuple[int, ...], Tuple[int, ...]], context: FamilyContext) -> Family:
    return base_residual_profile(state[0], context.family)


def make_pair_semantics(
    *,
    name: str,
    label: str,
    description: str,
    trigger_kind: str,
    update_kind: str,
    gate_kind: str,
    token_alphabet_size: int,
) -> SemanticDefinition:
    def step(
        state: Tuple[Tuple[int, ...], Tuple[int, ...], Tuple[int, ...]],
        event: Tuple[int, int],
        context: FamilyContext,
    ) -> Tuple[Tuple[int, ...], Tuple[int, ...], Tuple[int, ...]]:
        assignment, pair_tokens, simplex_tokens = state
        variable, chosen_edge = event
        if assignment[variable - 1] >= 0:
            return state
        updated_assignment = list(assignment)
        updated_tokens = list(pair_tokens)
        for pair in context.pairs:
            if pair_triggered(trigger_kind, pair, assignment, event):
                updated_tokens[pair.pair_index] = update_pair_token(
                    updated_tokens[pair.pair_index],
                    update_kind,
                    chosen_edge,
                    pair,
                )
        updated_assignment[variable - 1] = chosen_edge
        return tuple(updated_assignment), tuple(updated_tokens), simplex_tokens

    def output(
        state: Tuple[Tuple[int, ...], Tuple[int, ...], Tuple[int, ...]],
        context: FamilyContext,
    ) -> Family:
        assignment, pair_tokens, _ = state
        residuals: List[Tuple[int, ...]] = []
        for edge_index, edge in enumerate(context.family):
            live = True
            remaining: List[int] = []
            for variable in edge:
                value = assignment[variable - 1]
                if value == -1:
                    remaining.append(variable)
                elif value != edge_index:
                    live = False
                    break
            if not live:
                continue
            if not remaining:
                blocked = any(
                    edge_blocked_by_pair(
                        edge_index,
                        context.pairs[pair_index],
                        pair_tokens[pair_index],
                        update_kind,
                        gate_kind,
                    )
                    for pair_index in context.pair_indices_by_edge[edge_index]
                )
                if blocked:
                    continue
            residuals.append(tuple(remaining))
        return tuple(residuals)

    return SemanticDefinition(
        name=name,
        label=label,
        description=description,
        token_scope="pair",
        token_alphabet_size=token_alphabet_size,
        analysis_mode="automaton",
        initial_state=token_initial,
        events=token_events,
        step=step,
        output=output,
        coordinate_summary=token_coordinate,
        full_assignment_summary=token_full_assignment,
        token_summary=token_summary,
        incidence_summary=token_incidence,
        family_summary=token_family_summary,
    )


def make_simplex_semantics(
    *,
    name: str,
    label: str,
    description: str,
    trigger_kind: str,
    update_kind: str,
    gate_kind: str,
    token_alphabet_size: int,
) -> SemanticDefinition:
    def step(
        state: Tuple[Tuple[int, ...], Tuple[int, ...], Tuple[int, ...]],
        event: Tuple[int, int],
        context: FamilyContext,
    ) -> Tuple[Tuple[int, ...], Tuple[int, ...], Tuple[int, ...]]:
        assignment, pair_tokens, simplex_tokens = state
        variable, chosen_edge = event
        if assignment[variable - 1] >= 0:
            return state
        updated_assignment = list(assignment)
        updated_simplex = list(simplex_tokens)
        for triangle in context.triangles:
            if triangle_triggered(trigger_kind, triangle, assignment, event):
                updated_simplex[triangle.triangle_index] = update_triangle_token(
                    updated_simplex[triangle.triangle_index],
                    update_kind,
                    chosen_edge,
                    triangle,
                )
        updated_assignment[variable - 1] = chosen_edge
        return tuple(updated_assignment), pair_tokens, tuple(updated_simplex)

    def output(
        state: Tuple[Tuple[int, ...], Tuple[int, ...], Tuple[int, ...]],
        context: FamilyContext,
    ) -> Family:
        assignment, _, simplex_tokens = state
        residuals: List[Tuple[int, ...]] = []
        for edge_index, edge in enumerate(context.family):
            live = True
            remaining: List[int] = []
            for variable in edge:
                value = assignment[variable - 1]
                if value == -1:
                    remaining.append(variable)
                elif value != edge_index:
                    live = False
                    break
            if not live:
                continue
            if not remaining:
                blocked = any(
                    edge_blocked_by_triangle(
                        edge_index,
                        context.triangles[triangle_index],
                        simplex_tokens[triangle_index],
                        gate_kind,
                    )
                    for triangle_index in context.triangle_indices_by_edge[edge_index]
                )
                if blocked:
                    continue
            residuals.append(tuple(remaining))
        return tuple(residuals)

    return SemanticDefinition(
        name=name,
        label=label,
        description=description,
        token_scope="simplex",
        token_alphabet_size=token_alphabet_size,
        analysis_mode="automaton",
        initial_state=token_initial,
        events=token_events,
        step=step,
        output=output,
        coordinate_summary=token_coordinate,
        full_assignment_summary=token_full_assignment,
        token_summary=token_summary,
        incidence_summary=token_incidence,
        family_summary=token_family_summary,
    )


BROADCAST_CONTROL = SemanticDefinition(
    name="broadcast_control",
    label="Broadcast",
    description="Negative control: broadcast presence semantics; edge choice never enters the carrier.",
    token_scope="none",
    token_alphabet_size=1,
    analysis_mode="automaton",
    initial_state=broadcast_initial,
    events=broadcast_events,
    step=broadcast_step,
    output=broadcast_output,
    coordinate_summary=broadcast_coordinate,
    full_assignment_summary=broadcast_full_assignment,
    token_summary=broadcast_token_summary,
    incidence_summary=broadcast_incidence,
    family_summary=broadcast_family_summary,
)


COMMITTED_ALLOCATION = SemanticDefinition(
    name="committed_allocation",
    label="Committed Allocation",
    description="Positive control: variable-to-edge assignment with disjoint-domain segment composition on the V-hypergraph.",
    token_scope="none",
    token_alphabet_size=1,
    analysis_mode="segment_rows",
    initial_state=lambda context: tuple(-1 for _ in context.universe),
    events=lambda context: tuple(),
    step=lambda state, event, context: state,
    output=committed_output,
    coordinate_summary=committed_coordinate,
    full_assignment_summary=committed_full_assignment,
    token_summary=committed_token_summary,
    incidence_summary=committed_incidence,
    family_summary=committed_family_summary,
    segment_states=committed_segment_states,
    compose=committed_compose,
)


def generated_semantics() -> Tuple[SemanticDefinition, ...]:
    pair_specs = [
        (
            "pair_phase_shared_other_live_block_lower",
            "Pair Phase SL",
            "Pair phase mod 2: a shared claim into the lower edge toggles when the upper edge is already live; odd phase suppresses lower completion.",
            "shared_other_live",
            "toggle_mod2",
            "block_lower_complete",
            2,
        ),
        (
            "pair_phase_shared_other_live_block_upper",
            "Pair Phase SU",
            "Pair phase mod 2 with upper-edge suppression.",
            "shared_other_live",
            "toggle_mod2",
            "block_upper_complete",
            2,
        ),
        (
            "pair_phase_any_other_live_block_lower",
            "Pair Phase AL",
            "Pair phase mod 2: any claim into a pair edge toggles once the opposite edge is already live; odd phase suppresses lower completion.",
            "any_other_live",
            "toggle_mod2",
            "block_lower_complete",
            2,
        ),
        (
            "pair_phase_exclusive_other_live_block_lower",
            "Pair Phase XL",
            "Pair phase mod 2 triggered only by exclusive claims into a live pair.",
            "exclusive_other_live",
            "toggle_mod2",
            "block_lower_complete",
            2,
        ),
        (
            "braid_orientation_shared_other_live",
            "Braid Orient",
            "Orientation token records which pair edge received the decisive shared claim once the other edge is live; the oriented edge is blocked on completion.",
            "shared_other_live",
            "orientation",
            "block_oriented_complete",
            3,
        ),
        (
            "transport_debt_shared_other_live",
            "Debt Shared",
            "Capped debt token increments when a shared claim lands across a live overlap; level 2 debt blocks lower-edge completion.",
            "shared_other_live",
            "capped_inc2",
            "block_lower_token2",
            3,
        ),
        (
            "catalytic_pair_activation",
            "Catalytic Pair",
            "A latent pair catalyst latches when the overlap pair first becomes jointly live; active catalyst blocks lower-edge completion.",
            "pair_activates",
            "latch",
            "block_lower_complete",
            2,
        ),
    ]
    simplex_specs = [
        (
            "simplex_phase_triangle_activate",
            "Simplex Phase",
            "Triangle-phase mod 2 toggles when a nerve triangle first becomes jointly live; odd phase blocks the lowest edge completion.",
            "triangle_activates",
            "toggle_mod2",
            "block_lowest_complete",
            2,
        ),
        (
            "simplex_orientation_triangle_activate",
            "Simplex Orient",
            "Triangle orientation remembers which edge activated the live 2-simplex; that edge is blocked on completion.",
            "triangle_activates",
            "orientation",
            "block_oriented_complete",
            4,
        ),
    ]
    semantics: List[SemanticDefinition] = [BROADCAST_CONTROL, COMMITTED_ALLOCATION]
    semantics.extend(
        make_pair_semantics(
            name=name,
            label=label,
            description=description,
            trigger_kind=trigger_kind,
            update_kind=update_kind,
            gate_kind=gate_kind,
            token_alphabet_size=token_alphabet_size,
        )
        for name, label, description, trigger_kind, update_kind, gate_kind, token_alphabet_size in pair_specs
    )
    semantics.extend(
        make_simplex_semantics(
            name=name,
            label=label,
            description=description,
            trigger_kind=trigger_kind,
            update_kind=update_kind,
            gate_kind=gate_kind,
            token_alphabet_size=token_alphabet_size,
        )
        for name, label, description, trigger_kind, update_kind, gate_kind, token_alphabet_size in simplex_specs
    )
    return tuple(semantics)


SEMANTICS = generated_semantics()


def minimize_moore_machine(
    states: Sequence[Hashable],
    events: Sequence[Hashable],
    transitions: Dict[Hashable, Dict[Hashable, Hashable]],
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


def summary_exactness(
    summary_fn: Callable[[Hashable, FamilyContext], Hashable],
    states: Sequence[Hashable],
    context: FamilyContext,
    block_of: Dict[Hashable, int],
) -> Tuple[int, bool]:
    grouped: DefaultDict[Hashable, set] = defaultdict(set)
    for state in states:
        grouped[summary_fn(state, context)].add(block_of[state])
    return len(grouped), all(len(blocks) == 1 for blocks in grouped.values())


def row_exactness(
    summary_fn: Callable[[Hashable, FamilyContext], Hashable],
    states: Sequence[Hashable],
    context: FamilyContext,
    row_of: Dict[Hashable, Tuple[Hashable, ...]],
) -> Tuple[int, bool]:
    grouped: DefaultDict[Hashable, set] = defaultdict(set)
    for state in states:
        grouped[summary_fn(state, context)].add(row_of[state])
    return len(grouped), all(len(rows) == 1 for rows in grouped.values())


def shortest_distinguishing_suffix(
    left: Hashable,
    right: Hashable,
    events: Sequence[Hashable],
    transitions: Dict[Hashable, Dict[Hashable, Hashable]],
    outputs: Dict[Hashable, Hashable],
    *,
    require_non_empty: bool = False,
) -> Trace:
    queue = deque([(left, right, ())])
    visited = {(left, right)}
    while queue:
        current_left, current_right, trace = queue.popleft()
        if outputs[current_left] != outputs[current_right] and (trace or not require_non_empty):
            return trace
        for event in events:
            next_left = transitions[current_left][event]
            next_right = transitions[current_right][event]
            pair = (next_left, next_right)
            if pair in visited:
                continue
            visited.add(pair)
            queue.append((next_left, next_right, trace + (event,)))
    raise RuntimeError("No distinguishing suffix found")


def group_rank(
    states: Sequence[Hashable],
    block_of: Dict[Hashable, int],
    key_fn: Callable[[Hashable], Hashable],
) -> int:
    grouped: DefaultDict[Hashable, set] = defaultdict(set)
    for state in states:
        grouped[key_fn(state)].add(block_of[state])
    return max((len(blocks) for blocks in grouped.values()), default=1)


def extract_automaton_witness(
    states: Sequence[Hashable],
    context: FamilyContext,
    summary_fn: Callable[[Hashable, FamilyContext], Hashable],
    block_of: Dict[Hashable, int],
    outputs: Dict[Hashable, Hashable],
    transitions: Dict[Hashable, Dict[Hashable, Hashable]],
    shortest_trace: Dict[Hashable, Trace],
    events: Sequence[Hashable],
    *,
    require_same_output: bool = False,
    require_non_empty_suffix: bool = False,
) -> WitnessRecord | None:
    groups: DefaultDict[Hashable, List[Hashable]] = defaultdict(list)
    for state in states:
        groups[summary_fn(state, context)].append(state)
    candidates: List[Tuple[int, int, int, str, str, str, Hashable, Hashable, Trace]] = []
    for summary_value, fiber in groups.items():
        if len({block_of[state] for state in fiber}) <= 1:
            continue
        for left_index, left_state in enumerate(fiber):
            for right_state in fiber[left_index + 1 :]:
                if block_of[left_state] == block_of[right_state]:
                    continue
                if require_same_output and outputs[left_state] != outputs[right_state]:
                    continue
                suffix = shortest_distinguishing_suffix(
                    left_state,
                    right_state,
                    events,
                    transitions,
                    outputs,
                    require_non_empty=require_non_empty_suffix,
                )
                if require_non_empty_suffix and not suffix:
                    continue
                candidates.append(
                    (
                        len(shortest_trace[left_state]),
                        len(shortest_trace[right_state]),
                        len(suffix),
                        state_text(summary_fn(left_state, context), context.family),
                        state_text(left_state, context.family),
                        state_text(right_state, context.family),
                        left_state,
                        right_state,
                        suffix,
                    )
                )
    if not candidates:
        return None
    candidates.sort(key=lambda item: item[:6] + (trace_text(item[8], context.family),))
    left_state, right_state, suffix = candidates[0][6], candidates[0][7], candidates[0][8]
    future_left = left_state
    future_right = right_state
    for event in suffix:
        future_left = transitions[future_left][event]
        future_right = transitions[future_right][event]
    return WitnessRecord(
        left_trace=shortest_trace[left_state],
        right_trace=shortest_trace[right_state],
        suffix=suffix,
        summary_value=state_text(summary_fn(left_state, context), context.family),
        left_state=state_text(left_state, context.family),
        right_state=state_text(right_state, context.family),
        left_output_now=state_text(outputs[left_state], context.family),
        right_output_now=state_text(outputs[right_state], context.family),
        left_output_future=state_text(outputs[future_left], context.family),
        right_output_future=state_text(outputs[future_right], context.family),
        same_now=outputs[left_state] == outputs[right_state],
        non_empty_suffix=bool(suffix),
    )


def extract_segment_witness(
    states: Sequence[Hashable],
    context: FamilyContext,
    summary_fn: Callable[[Hashable, FamilyContext], Hashable],
    row_of: Dict[Hashable, Tuple[Hashable, ...]],
    block_of: Dict[Hashable, int],
    output_fn: Callable[[Hashable, FamilyContext], Hashable],
    state_for_suffix: Sequence[Hashable],
    compose_fn: Callable[[Hashable, Hashable, FamilyContext], Hashable | None],
    *,
    require_same_output: bool = False,
    require_non_empty_suffix: bool = False,
) -> WitnessRecord | None:
    groups: DefaultDict[Hashable, List[Hashable]] = defaultdict(list)
    for state in states:
        groups[summary_fn(state, context)].append(state)
    candidates: List[Tuple[int, int, int, str, str, str, Hashable, Hashable, Hashable]] = []
    for summary_value, fiber in groups.items():
        if len({block_of[state] for state in fiber}) <= 1:
            continue
        for left_index, left_state in enumerate(fiber):
            for right_state in fiber[left_index + 1 :]:
                if block_of[left_state] == block_of[right_state]:
                    continue
                if require_same_output and output_fn(left_state, context) != output_fn(right_state, context):
                    continue
                differing_suffixes = [
                    suffix
                    for suffix, left_row, right_row in zip(state_for_suffix, row_of[left_state], row_of[right_state])
                    if left_row != right_row and (not require_non_empty_suffix or summary_fn(suffix, context))
                ]
                if not differing_suffixes:
                    continue
                differing_suffixes.sort(
                    key=lambda suffix: (
                        0 if summary_fn(suffix, context) else 1,
                        state_text(suffix, context.family),
                    )
                )
                suffix = differing_suffixes[0]
                candidates.append(
                    (
                        len(str(left_state)),
                        len(str(right_state)),
                        len(str(suffix)),
                        state_text(summary_value, context.family),
                        state_text(left_state, context.family),
                        state_text(right_state, context.family),
                        left_state,
                        right_state,
                        suffix,
                    )
                )
    if not candidates:
        return None
    candidates.sort(key=lambda item: item[:6])
    left_state, right_state, suffix = candidates[0][6], candidates[0][7], candidates[0][8]
    future_left = compose_fn(left_state, suffix, context)
    future_right = compose_fn(right_state, suffix, context)
    return WitnessRecord(
        left_trace=(("segment", left_state),) if summary_fn(left_state, context) else (),
        right_trace=(("segment", right_state),) if summary_fn(right_state, context) else (),
        suffix=(("segment", suffix),) if summary_fn(suffix, context) else (),
        summary_value=state_text(summary_fn(left_state, context), context.family),
        left_state=state_text(left_state, context.family),
        right_state=state_text(right_state, context.family),
        left_output_now=state_text(output_fn(left_state, context), context.family),
        right_output_now=state_text(output_fn(right_state, context), context.family),
        left_output_future=state_text(("INVALID",), context.family) if future_left is None else state_text(output_fn(future_left, context), context.family),
        right_output_future=state_text(("INVALID",), context.family) if future_right is None else state_text(output_fn(future_right, context), context.family),
        same_now=output_fn(left_state, context) == output_fn(right_state, context),
        non_empty_suffix=bool(summary_fn(suffix, context)),
    )


def analyze_automaton(semantic: SemanticDefinition, context: FamilyContext) -> AnalysisRecord:
    events = semantic.events(context)
    initial = semantic.initial_state(context)
    queue = deque([initial])
    seen = {initial}
    shortest_trace: Dict[Hashable, Trace] = {initial: ()}
    transitions: Dict[Hashable, Dict[Hashable, Hashable]] = {}
    outputs: Dict[Hashable, Hashable] = {}

    while queue:
        state = queue.popleft()
        outputs[state] = semantic.output(state, context)
        row: Dict[Hashable, Hashable] = {}
        for event in events:
            next_state = semantic.step(state, event, context)
            row[event] = next_state
            if next_state not in seen:
                seen.add(next_state)
                shortest_trace[next_state] = shortest_trace[state] + (event,)
                queue.append(next_state)
        transitions[state] = row

    states = tuple(
        sorted(
            seen,
            key=lambda item: (
                len(shortest_trace[item]),
                shortest_trace[item],
                state_text(item, context.family),
            ),
        )
    )
    block_of = minimize_moore_machine(states, events, transitions, outputs)
    runtime_count = len(set(block_of.values()))
    coordinate_count, coordinate_exact = summary_exactness(semantic.coordinate_summary, states, context, block_of)
    assignment_count, full_assignment_exact = summary_exactness(semantic.full_assignment_summary, states, context, block_of)
    token_count, token_exact = summary_exactness(semantic.token_summary, states, context, block_of)
    incidence_count, incidence_exact = summary_exactness(semantic.incidence_summary, states, context, block_of)
    family_count, family_exact = summary_exactness(semantic.family_summary, states, context, block_of)

    coordinate_witness = extract_automaton_witness(
        states,
        context,
        semantic.coordinate_summary,
        block_of,
        outputs,
        transitions,
        shortest_trace,
        events,
    )
    assignment_witness = extract_automaton_witness(
        states,
        context,
        semantic.full_assignment_summary,
        block_of,
        outputs,
        transitions,
        shortest_trace,
        events,
    )
    hidden_future_witness = extract_automaton_witness(
        states,
        context,
        semantic.full_assignment_summary,
        block_of,
        outputs,
        transitions,
        shortest_trace,
        events,
        require_same_output=True,
        require_non_empty_suffix=True,
    )

    assignment_holonomy_rank = group_rank(
        states,
        block_of,
        key_fn=lambda state: semantic.full_assignment_summary(state, context),
    )
    hidden_future_rank = group_rank(
        states,
        block_of,
        key_fn=lambda state: (
            semantic.full_assignment_summary(state, context),
            outputs[state],
        ),
    )
    return AnalysisRecord(
        semantics=semantic.name,
        token_scope=semantic.token_scope,
        token_alphabet_size=semantic.token_alphabet_size,
        p=max(context.universe) if context.universe else 0,
        k=max(len(edge) for edge in context.family) if context.family else 0,
        family=context.family,
        reachable_state_count=len(states),
        runtime_quotient_count=runtime_count,
        coordinate_quotient_count=coordinate_count,
        full_assignment_quotient_count=assignment_count,
        token_quotient_count=token_count,
        incidence_quotient_count=incidence_count,
        family_quotient_count=family_count,
        coordinate_curvature_gap=log2_count(runtime_count) - log2_count(coordinate_count),
        assignment_curvature_gap=log2_count(runtime_count) - log2_count(assignment_count),
        coordinate_exact=coordinate_exact,
        full_assignment_exact=full_assignment_exact,
        token_exact=token_exact,
        incidence_exact=incidence_exact,
        family_exact=family_exact,
        assignment_holonomy_rank=assignment_holonomy_rank,
        hidden_future_rank=hidden_future_rank,
        coordinate_witness=coordinate_witness,
        full_assignment_witness=assignment_witness,
        hidden_future_witness=hidden_future_witness,
    )


def analyze_segment_rows(semantic: SemanticDefinition, context: FamilyContext) -> AnalysisRecord:
    if semantic.segment_states is None or semantic.compose is None:
        raise ValueError(f"{semantic.name} requires segment_states and compose")
    states = semantic.segment_states(context)
    row_of: Dict[Hashable, Tuple[Hashable, ...]] = {}
    for state in states:
        row: List[Hashable] = []
        for suffix in states:
            merged = semantic.compose(state, suffix, context)
            row.append(("INVALID",) if merged is None else semantic.output(merged, context))
        row_of[state] = tuple(row)
    runtime_blocks: Dict[Tuple[Hashable, ...], int] = {}
    block_of: Dict[Hashable, int] = {}
    for state in states:
        row = row_of[state]
        if row not in runtime_blocks:
            runtime_blocks[row] = len(runtime_blocks)
        block_of[state] = runtime_blocks[row]
    runtime_count = len(runtime_blocks)
    coordinate_count, coordinate_exact = row_exactness(semantic.coordinate_summary, states, context, row_of)
    assignment_count, full_assignment_exact = row_exactness(semantic.full_assignment_summary, states, context, row_of)
    token_count, token_exact = row_exactness(semantic.token_summary, states, context, row_of)
    incidence_count, incidence_exact = row_exactness(semantic.incidence_summary, states, context, row_of)
    family_count, family_exact = row_exactness(semantic.family_summary, states, context, row_of)
    coordinate_witness = extract_segment_witness(
        states,
        context,
        semantic.coordinate_summary,
        row_of,
        block_of,
        semantic.output,
        states,
        semantic.compose,
    )
    assignment_witness = extract_segment_witness(
        states,
        context,
        semantic.full_assignment_summary,
        row_of,
        block_of,
        semantic.output,
        states,
        semantic.compose,
    )
    hidden_future_witness = extract_segment_witness(
        states,
        context,
        semantic.full_assignment_summary,
        row_of,
        block_of,
        semantic.output,
        states,
        semantic.compose,
        require_same_output=True,
        require_non_empty_suffix=True,
    )
    assignment_holonomy_rank = group_rank(
        states,
        block_of,
        key_fn=lambda state: semantic.full_assignment_summary(state, context),
    )
    hidden_future_rank = group_rank(
        states,
        block_of,
        key_fn=lambda state: (
            semantic.full_assignment_summary(state, context),
            semantic.output(state, context),
        ),
    )
    return AnalysisRecord(
        semantics=semantic.name,
        token_scope=semantic.token_scope,
        token_alphabet_size=semantic.token_alphabet_size,
        p=max(context.universe) if context.universe else 0,
        k=max(len(edge) for edge in context.family) if context.family else 0,
        family=context.family,
        reachable_state_count=len(states),
        runtime_quotient_count=runtime_count,
        coordinate_quotient_count=coordinate_count,
        full_assignment_quotient_count=assignment_count,
        token_quotient_count=token_count,
        incidence_quotient_count=incidence_count,
        family_quotient_count=family_count,
        coordinate_curvature_gap=log2_count(runtime_count) - log2_count(coordinate_count),
        assignment_curvature_gap=log2_count(runtime_count) - log2_count(assignment_count),
        coordinate_exact=coordinate_exact,
        full_assignment_exact=full_assignment_exact,
        token_exact=token_exact,
        incidence_exact=incidence_exact,
        family_exact=family_exact,
        assignment_holonomy_rank=assignment_holonomy_rank,
        hidden_future_rank=hidden_future_rank,
        coordinate_witness=coordinate_witness,
        full_assignment_witness=assignment_witness,
        hidden_future_witness=hidden_future_witness,
    )


def analyze_family(semantic: SemanticDefinition, family: Family) -> AnalysisRecord:
    context = build_context(family)
    if semantic.analysis_mode == "segment_rows":
        return analyze_segment_rows(semantic, context)
    return analyze_automaton(semantic, context)


def witness_length(witness: WitnessRecord | None) -> int:
    if witness is None:
        return 0
    total = 0
    if witness.left_trace is not None:
        total += len(witness.left_trace)
    if witness.right_trace is not None:
        total += len(witness.right_trace)
    if witness.suffix is not None:
        total += len(witness.suffix)
    return total


def record_order_key(record: AnalysisRecord, witness_kind: str) -> Tuple[object, ...]:
    if witness_kind == "coordinate":
        chosen = record.coordinate_witness
    elif witness_kind == "assignment":
        chosen = record.full_assignment_witness
    elif witness_kind == "hidden":
        chosen = record.hidden_future_witness
    else:
        raise ValueError(f"unknown witness kind {witness_kind}")
    return (
        record.p,
        record.k,
        len(record.family),
        record.token_alphabet_size,
        record.reachable_state_count,
        witness_length(chosen),
        record.family,
        record.semantics,
    )


def record_to_json(record: AnalysisRecord) -> Dict[str, object]:
    def witness_to_json(witness: WitnessRecord | None) -> Dict[str, object] | None:
        if witness is None:
            return None
        return {
            "left_trace": None if witness.left_trace is None else list(witness.left_trace),
            "right_trace": None if witness.right_trace is None else list(witness.right_trace),
            "suffix": None if witness.suffix is None else list(witness.suffix),
            "summary_value": witness.summary_value,
            "left_state": witness.left_state,
            "right_state": witness.right_state,
            "left_output_now": witness.left_output_now,
            "right_output_now": witness.right_output_now,
            "left_output_future": witness.left_output_future,
            "right_output_future": witness.right_output_future,
            "same_now": witness.same_now,
            "non_empty_suffix": witness.non_empty_suffix,
        }

    return {
        "semantics": record.semantics,
        "token_scope": record.token_scope,
        "token_alphabet_size": record.token_alphabet_size,
        "p": record.p,
        "k": record.k,
        "family": [list(edge) for edge in record.family],
        "reachable_state_count": record.reachable_state_count,
        "runtime_quotient_count": record.runtime_quotient_count,
        "coordinate_quotient_count": record.coordinate_quotient_count,
        "full_assignment_quotient_count": record.full_assignment_quotient_count,
        "token_quotient_count": record.token_quotient_count,
        "incidence_quotient_count": record.incidence_quotient_count,
        "family_quotient_count": record.family_quotient_count,
        "coordinate_curvature_gap": record.coordinate_curvature_gap,
        "assignment_curvature_gap": record.assignment_curvature_gap,
        "coordinate_exact": record.coordinate_exact,
        "full_assignment_exact": record.full_assignment_exact,
        "token_exact": record.token_exact,
        "incidence_exact": record.incidence_exact,
        "family_exact": record.family_exact,
        "assignment_holonomy_rank": record.assignment_holonomy_rank,
        "hidden_future_rank": record.hidden_future_rank,
        "coordinate_witness": witness_to_json(record.coordinate_witness),
        "full_assignment_witness": witness_to_json(record.full_assignment_witness),
        "hidden_future_witness": witness_to_json(record.hidden_future_witness),
    }


def summary_to_json(summary: SemanticSummary) -> Dict[str, object]:
    return {
        "name": summary.name,
        "label": summary.label,
        "description": summary.description,
        "token_scope": summary.token_scope,
        "token_alphabet_size": summary.token_alphabet_size,
        "families_scanned": summary.families_scanned,
        "coordinate_split_count": summary.coordinate_split_count,
        "coordinate_gap_count": summary.coordinate_gap_count,
        "full_assignment_split_count": summary.full_assignment_split_count,
        "hidden_future_count": summary.hidden_future_count,
        "full_assignment_exact_on_scan": summary.full_assignment_exact_on_scan,
        "max_coordinate_curvature_gap": summary.max_coordinate_curvature_gap,
        "max_assignment_curvature_gap": summary.max_assignment_curvature_gap,
        "max_assignment_holonomy_rank": summary.max_assignment_holonomy_rank,
        "max_hidden_future_rank": summary.max_hidden_future_rank,
        "seed_record": None if summary.seed_record is None else record_to_json(summary.seed_record),
        "first_coordinate_split": None if summary.first_coordinate_split is None else record_to_json(summary.first_coordinate_split),
        "first_coordinate_gap": None if summary.first_coordinate_gap is None else record_to_json(summary.first_coordinate_gap),
        "first_full_assignment_split": None if summary.first_full_assignment_split is None else record_to_json(summary.first_full_assignment_split),
        "first_hidden_future_split": None if summary.first_hidden_future_split is None else record_to_json(summary.first_hidden_future_split),
    }


def build_report(
    summaries: Sequence[SemanticSummary],
    payload: Dict[str, object],
    note_path: Path | None,
    json_path: Path,
    svg_path: Path,
) -> str:
    overall_coordinate_split = payload["overall_first_coordinate_split"]
    overall_coordinate_gap = payload["overall_first_coordinate_gap"]
    overall_assignment_split = payload["overall_first_full_assignment_split"]
    overall_hidden_future = payload["overall_first_hidden_future_split"]
    lines = [
        "# Full Assignment Holonomy Search",
        "",
        "## Question",
        "",
        "This search asks for the first deterministic prefix-compositional semantics where raw committed assignment is no longer exact.",
        "The strongest witness is hidden future: two prefixes with the same full assignment and the same current output, but different futures under the same non-empty suffix.",
        "",
        "## Scan Setup",
        "",
        f"- Base scan: exact normalized full-union antichains on `[p]` with `p <= {max(BASE_P_SCAN)}` and `k <= {BASE_K_MAX}`.",
        f"- Expanded scan triggered: `{payload['scan']['expanded_scan_triggered']}`.",
        "- Controls: `broadcast_control` as the flat negative control and `committed_allocation` as the positive control for coordinate curvature.",
        "- Holonomy library: generated pairwise and simplex transport laws with tiny token alphabets.",
        "- Runtime quotient: exact continuation quotient; segment-row controls are analyzed by exact suffix rows, while tokenized laws are analyzed on reachable event-prefix automata.",
        "- Canonical `first` order: `(p, k, |A|, token alphabet, reachable states, witness length, family, semantics)` with witness-specific traces for coordinate, assignment, and hidden-future searches.",
        "- Tie handling: several pair laws hit the same seed family, but the overall winner is chosen by the full canonical order above rather than by family size alone.",
        "",
        "## Semantics Library",
        "",
    ]
    for summary in summaries:
        lines.append(
            f"- `{summary.name}` (`scope={summary.token_scope}`, `|Sigma|={summary.token_alphabet_size}`): {summary.description}"
        )
    lines.extend(
        [
            "",
            "## Summary Table",
            "",
            "| Semantics | Scope | `|Sigma|` | Seed counts `(runtime / coord / assign / token)` | First coordinate split | First `kappa_pi > 0` | First assignment split | First hidden future | Max assignment gap | Full assignment exact on scan |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for summary in summaries:
        seed = summary.seed_record
        seed_counts = "n/a"
        if seed is not None:
            seed_counts = f"{seed.runtime_quotient_count} / {seed.coordinate_quotient_count} / {seed.full_assignment_quotient_count} / {seed.token_quotient_count}"
        def label(record: AnalysisRecord | None) -> str:
            if record is None:
                return "none"
            return f"(p={record.p}, k={record.k}) {record.family}"
        lines.append(
            f"| `{summary.label}` | `{summary.token_scope}` | `{summary.token_alphabet_size}` | `{seed_counts}` | `{label(summary.first_coordinate_split)}` | `{label(summary.first_coordinate_gap)}` | `{label(summary.first_full_assignment_split)}` | `{label(summary.first_hidden_future_split)}` | `{summary.max_assignment_curvature_gap:.3f}` | `{summary.full_assignment_exact_on_scan}` |"
        )
    lines.extend(
        [
            "",
            "## Controls",
            "",
            "- `broadcast_control` stays flat: no coordinate split, no assignment split, and no hidden future on the scanned grid.",
            "- `committed_allocation` reproduces the known positive coordinate gap on `{{1,2},{1,3}}`, but still keeps full assignment exact on the scanned grid.",
            "",
            "## Boundary Results",
            "",
        ]
    )
    if overall_coordinate_split is None:
        lines.append("- No coordinate split was found.")
    else:
        record = overall_coordinate_split
        lines.append(
            f"- First coordinate split: `{record['semantics']}` on `{tuple(tuple(edge) for edge in record['family'])}` at `(p={record['p']}, k={record['k']})`."
        )
    if overall_coordinate_gap is None:
        lines.append("- No positive coordinate `kappa_pi` gap was found.")
    else:
        record = overall_coordinate_gap
        lines.append(
            f"- First positive coordinate `kappa_pi`: `{record['semantics']}` on `{tuple(tuple(edge) for edge in record['family'])}` with gap `{record['coordinate_curvature_gap']:.3f}` bits."
        )
    if overall_assignment_split is None:
        lines.append("- No full-assignment split was found on the scanned library.")
    else:
        record = overall_assignment_split
        lines.append(
            f"- First full-assignment split: `{record['semantics']}` on `{tuple(tuple(edge) for edge in record['family'])}` at `(p={record['p']}, k={record['k']})`, with assignment gap `{record['assignment_curvature_gap']:.3f}` bits."
        )
    if overall_hidden_future is None:
        lines.append("- No hidden-future witness was found on the scanned library.")
    else:
        record = overall_hidden_future
        lines.append(
            f"- First hidden-future split: `{record['semantics']}` on `{tuple(tuple(edge) for edge in record['family'])}` at `(p={record['p']}, k={record['k']})`."
        )
    lines.extend(["", "## First Full-Assignment Split", ""])
    if overall_assignment_split is None:
        strongest_negative = max(summaries, key=lambda summary: (summary.max_assignment_holonomy_rank, summary.max_assignment_curvature_gap))
        lines.extend(
            [
                "No semantics broke full assignment on the scanned library.",
                f"The strongest near-miss was `{strongest_negative.name}` with `max assignment holonomy rank = {strongest_negative.max_assignment_holonomy_rank}` and `max assignment gap = {strongest_negative.max_assignment_curvature_gap:.3f}` bits.",
            ]
        )
    else:
        record = overall_assignment_split
        summary = next(summary for summary in summaries if summary.name == record["semantics"])
        witness = record["full_assignment_witness"]
        lines.extend(
            [
                f"- semantics: `{summary.name}` (`scope={summary.token_scope}`, `|Sigma|={summary.token_alphabet_size}`)",
                f"- family: `{tuple(tuple(edge) for edge in record['family'])}`",
                f"- counts: runtime `{record['runtime_quotient_count']}`, coordinate `{record['coordinate_quotient_count']}`, assignment `{record['full_assignment_quotient_count']}`, token `{record['token_quotient_count']}`, family `{record['family_quotient_count']}`",
                f"- assignment holonomy rank: `{record['assignment_holonomy_rank']}`",
                f"- hidden future rank: `{record['hidden_future_rank']}`",
                f"- assignment gap: `{record['assignment_curvature_gap']:.3f}` bits, so exactness can fail before the count-level assignment gap turns positive",
                f"- same-assignment witness `u`: `{trace_text(tuple(witness['left_trace']) if witness and witness['left_trace'] else (), tuple(tuple(edge) for edge in record['family'])) if witness else '[]'}`",
                f"- same-assignment witness `v`: `{trace_text(tuple(witness['right_trace']) if witness and witness['right_trace'] else (), tuple(tuple(edge) for edge in record['family'])) if witness else '[]'}`",
                f"- suffix `w`: `{trace_text(tuple(witness['suffix']) if witness and witness['suffix'] else (), tuple(tuple(edge) for edge in record['family'])) if witness else '[]'}`",
                f"- outputs now: `{witness['left_output_now'] if witness else 'n/a'}` versus `{witness['right_output_now'] if witness else 'n/a'}`",
                f"- outputs after suffix: `{witness['left_output_future'] if witness else 'n/a'}` versus `{witness['right_output_future'] if witness else 'n/a'}`",
            ]
        )
    lines.extend(["", "## First Hidden-Future Split", ""])
    if overall_hidden_future is None:
        pairwise_positive = any(summary.token_scope == "pair" and summary.first_full_assignment_split is not None for summary in summaries)
        if pairwise_positive:
            lines.append("Pairwise token laws break full assignment, but none of the scanned semantics produced a same-now / future-separate hidden-future witness.")
        else:
            lines.append("No hidden-future split appeared on the scanned library.")
    else:
        record = overall_hidden_future
        summary = next(summary for summary in summaries if summary.name == record["semantics"])
        witness = record["hidden_future_witness"]
        lines.extend(
            [
                f"- semantics: `{summary.name}` (`scope={summary.token_scope}`, `|Sigma|={summary.token_alphabet_size}`)",
                f"- family: `{tuple(tuple(edge) for edge in record['family'])}`",
                f"- full assignment fiber: `{witness['summary_value'] if witness else 'n/a'}`",
                f"- left prefix `u`: `{trace_text(tuple(witness['left_trace']) if witness and witness['left_trace'] else (), tuple(tuple(edge) for edge in record['family'])) if witness else '[]'}`",
                f"- right prefix `v`: `{trace_text(tuple(witness['right_trace']) if witness and witness['right_trace'] else (), tuple(tuple(edge) for edge in record['family'])) if witness else '[]'}`",
                f"- non-empty suffix `w`: `{trace_text(tuple(witness['suffix']) if witness and witness['suffix'] else (), tuple(tuple(edge) for edge in record['family'])) if witness else '[]'}`",
                f"- shared current output: `{witness['left_output_now'] if witness else 'n/a'}`",
                f"- future outputs: `{witness['left_output_future'] if witness else 'n/a'}` versus `{witness['right_output_future'] if witness else 'n/a'}`",
            ]
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
        ]
    )
    if overall_assignment_split is None:
        lines.extend(
            [
                "No scanned semantics broke full assignment exactness.",
                "So even after adding local pairwise and simplex transport tokens, the current library still factors through committed incidence assignment.",
            ]
        )
    else:
        first_scope = overall_assignment_split["token_scope"]
        if first_scope == "pair":
            lines.extend(
                [
                    "Pairwise nerve holonomy is already enough.",
                    "The first full-assignment split appears on the seed V-hypergraph, so simplex transport is not necessary for the first runtime holonomy effect.",
                    "On the scanned library, the new exact runtime object is therefore assignment plus pair-transport token, not yet a fully global hypergraph state.",
                ]
            )
        else:
            lines.extend(
                [
                    "Pairwise token laws were not enough on the scanned library.",
                    "The first break required simplex transport, so 2-simplices are the first place where runtime holonomy enters beyond assignment.",
                ]
            )
    if overall_hidden_future is not None:
        lines.append("The stronger hidden-future witness shows the future can remember a local transport phase that the current output and the raw assignment both erase.")
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            f"- JSON: [{json_path.name}]({json_path.name})",
            f"- Figure: [{svg_path.name}]({svg_path.name})",
        ]
    )
    if note_path is not None:
        lines.append(f"- Note: [{note_path.name}](../../../docs/writing/experiments/holonomy/{note_path.name})")
    return "\n".join(lines) + "\n"


def render_svg(summaries: Sequence[SemanticSummary], payload: Dict[str, object]) -> str:
    width = 1600
    height = 920
    left = 48
    top = 56
    table_width = width - 2 * left
    row_height = 34
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<style>",
        "text { font-family: Menlo, Monaco, Consolas, monospace; font-size: 12px; fill: #1f2933; }",
        ".title { font-size: 18px; font-weight: 700; }",
        ".subtitle { fill: #52606d; }",
        ".header { font-weight: 700; fill: #102a43; }",
        ".panel { fill: #ffffff; stroke: #d9e2ec; stroke-width: 1; }",
        ".control { fill: #f4f7f9; }",
        ".pair { fill: #eef6ff; }",
        ".simplex { fill: #f7efff; }",
        ".winner { fill: #eefbf3; }",
        "</style>",
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#fbfbfd"/>',
        f'<text x="{left}" y="28" class="title">Full Assignment Holonomy Search</text>',
        f'<text x="{left}" y="46" class="subtitle">The search for the first runtime law where even raw assignment stops being exact.</text>',
        f'<rect x="{left}" y="{top}" width="{table_width}" height="352" class="panel"/>',
    ]
    columns = {
        "sem": left + 18,
        "scope": left + 190,
        "sigma": left + 270,
        "seed": left + 340,
        "assign": left + 530,
        "hidden": left + 820,
        "gap": left + 1090,
        "rank": left + 1200,
        "exact": left + 1320,
        "note": left + 1450,
    }
    head_y = top + 24
    for key, label in (
        ("sem", "semantics"),
        ("scope", "scope"),
        ("sigma", "|Sigma|"),
        ("seed", "seed runtime/assign/token"),
        ("assign", "first assignment split"),
        ("hidden", "first hidden future"),
        ("gap", "max assignment gap"),
        ("rank", "holonomy"),
        ("exact", "assign exact"),
        ("note", "status"),
    ):
        lines.append(f'<text x="{columns[key]}" y="{head_y}" class="header">{label}</text>')
    for index, summary in enumerate(summaries):
        y = head_y + 28 + index * row_height
        if summary.name in {"broadcast_control", "committed_allocation"}:
            row_class = "control"
        elif summary.first_full_assignment_split is not None:
            row_class = "winner" if summary.first_hidden_future_split is not None else "pair"
        elif summary.token_scope == "simplex":
            row_class = "simplex"
        else:
            row_class = "pair"
        lines.append(f'<rect x="{left + 8}" y="{y - 14}" width="{table_width - 16}" height="24" class="{row_class}"/>')
        seed = summary.seed_record
        seed_text = "n/a"
        if seed is not None:
            seed_text = f"{seed.runtime_quotient_count}/{seed.full_assignment_quotient_count}/{seed.token_quotient_count}"
        split_text = "none"
        if summary.first_full_assignment_split is not None:
            split = summary.first_full_assignment_split
            split_text = f"(p={split.p},k={split.k})"
        hidden_text = "none"
        if summary.first_hidden_future_split is not None:
            hidden = summary.first_hidden_future_split
            hidden_text = f"(p={hidden.p},k={hidden.k})"
        status = "flat"
        if summary.name == "committed_allocation":
            status = "coord control"
        elif summary.first_hidden_future_split is not None:
            status = "hidden future"
        elif summary.first_full_assignment_split is not None:
            status = "assignment split"
        lines.extend(
            [
                f'<text x="{columns["sem"]}" y="{y}">{summary.label}</text>',
                f'<text x="{columns["scope"]}" y="{y}">{summary.token_scope}</text>',
                f'<text x="{columns["sigma"]}" y="{y}">{summary.token_alphabet_size}</text>',
                f'<text x="{columns["seed"]}" y="{y}">{seed_text}</text>',
                f'<text x="{columns["assign"]}" y="{y}">{split_text}</text>',
                f'<text x="{columns["hidden"]}" y="{y}">{hidden_text}</text>',
                f'<text x="{columns["gap"]}" y="{y}">{summary.max_assignment_curvature_gap:.3f}</text>',
                f'<text x="{columns["rank"]}" y="{y}">{summary.max_assignment_holonomy_rank}/{summary.max_hidden_future_rank}</text>',
                f'<text x="{columns["exact"]}" y="{y}">{summary.full_assignment_exact_on_scan}</text>',
                f'<text x="{columns["note"]}" y="{y}">{status}</text>',
            ]
        )
    box_y = top + 380
    lines.append(f'<rect x="{left}" y="{box_y}" width="{table_width}" height="420" class="panel"/>')
    lines.append(f'<text x="{left + 16}" y="{box_y + 24}" class="header">Boundary statement</text>')
    overall_assignment_split = payload["overall_first_full_assignment_split"]
    overall_hidden_future = payload["overall_first_hidden_future_split"]
    if overall_assignment_split is None:
        lines.append(f'<text x="{left + 16}" y="{box_y + 52}">No full-assignment holonomy was found on the scanned library.</text>')
    else:
        lines.extend(
            [
                f'<text x="{left + 16}" y="{box_y + 52}">First assignment split: {overall_assignment_split["semantics"]} on {tuple(tuple(edge) for edge in overall_assignment_split["family"])}.</text>',
                f'<text x="{left + 16}" y="{box_y + 74}">Counts: runtime {overall_assignment_split["runtime_quotient_count"]}, coordinate {overall_assignment_split["coordinate_quotient_count"]}, assignment {overall_assignment_split["full_assignment_quotient_count"]}, token {overall_assignment_split["token_quotient_count"]}.</text>',
            ]
        )
        witness = overall_assignment_split["full_assignment_witness"]
        if witness is not None:
            lines.extend(
                [
                    f'<text x="{left + 16}" y="{box_y + 102}">u = {trace_text(tuple(witness["left_trace"]) if witness["left_trace"] else (), tuple(tuple(edge) for edge in overall_assignment_split["family"]))}</text>',
                    f'<text x="{left + 16}" y="{box_y + 124}">v = {trace_text(tuple(witness["right_trace"]) if witness["right_trace"] else (), tuple(tuple(edge) for edge in overall_assignment_split["family"]))}</text>',
                    f'<text x="{left + 16}" y="{box_y + 146}">w = {trace_text(tuple(witness["suffix"]) if witness["suffix"] else (), tuple(tuple(edge) for edge in overall_assignment_split["family"]))}</text>',
                    f'<text x="{left + 16}" y="{box_y + 168}">outputs now: {witness["left_output_now"]} vs {witness["right_output_now"]}</text>',
                    f'<text x="{left + 16}" y="{box_y + 190}">outputs after suffix: {witness["left_output_future"]} vs {witness["right_output_future"]}</text>',
                ]
            )
    if overall_hidden_future is None:
        lines.append(f'<text x="{left + 16}" y="{box_y + 236}">No hidden-future split was found.</text>')
    else:
        witness = overall_hidden_future["hidden_future_witness"]
        lines.extend(
            [
                f'<text x="{left + 16}" y="{box_y + 236}">First hidden future: {overall_hidden_future["semantics"]} on {tuple(tuple(edge) for edge in overall_hidden_future["family"])}.</text>',
                f'<text x="{left + 16}" y="{box_y + 258}">same assignment = {witness["summary_value"]}</text>',
                f'<text x="{left + 16}" y="{box_y + 280}">shared current output = {witness["left_output_now"]}</text>',
                f'<text x="{left + 16}" y="{box_y + 302}">future outputs after non-empty w: {witness["left_output_future"]} vs {witness["right_output_future"]}</text>',
            ]
        )
    lines.extend(
        [
            f'<text x="{left + 16}" y="{box_y + 344}">Controls: broadcast stays flat; committed allocation keeps assignment exact while reproducing positive coordinate curvature.</text>',
            f'<text x="{left + 16}" y="{box_y + 366}">If the first winner is pair-scoped, then pairwise nerve transport already suffices and simplex transport is not required for the first holonomy effect.</text>',
        ]
    )
    lines.append("</svg>")
    return "\n".join(lines)


def build_note(payload: Dict[str, object], summaries: Sequence[SemanticSummary]) -> str | None:
    overall_assignment_split = payload["overall_first_full_assignment_split"]
    overall_hidden_future = payload["overall_first_hidden_future_split"]
    if overall_assignment_split is None:
        return None
    summary = next(summary for summary in summaries if summary.name == overall_assignment_split["semantics"])
    scope_sentence = "pairwise nerve holonomy already suffices" if summary.token_scope == "pair" else "the first break requires simplex transport"
    lines = [
        "# Full Assignment Holonomy",
        "",
        "## Thesis",
        "",
        "The current search breaks the next boundary: raw committed assignment is no longer exact.",
        "",
        "## Exact Boundary",
        "",
        f"- First full-assignment split: `{overall_assignment_split['semantics']}` on `{tuple(tuple(edge) for edge in overall_assignment_split['family'])}`.",
        f"- Token scope: `{summary.token_scope}` with local alphabet size `{summary.token_alphabet_size}`.",
        f"- Counts: runtime `{overall_assignment_split['runtime_quotient_count']}`, assignment `{overall_assignment_split['full_assignment_quotient_count']}`, token `{overall_assignment_split['token_quotient_count']}`.",
        f"- Assignment gap: `{overall_assignment_split['assignment_curvature_gap']:.3f}` bits.",
        "",
        f"The key structural fact is that {scope_sentence}.",
    ]
    if overall_hidden_future is not None:
        lines.extend(
            [
                "",
                "## Hidden Future",
                "",
                f"- First hidden-future split: `{overall_hidden_future['semantics']}` on `{tuple(tuple(edge) for edge in overall_hidden_future['family'])}`.",
                "- So the future can remember a local transport state that both the raw assignment and the current readout erase.",
            ]
        )
    lines.extend(
        [
            "",
            "## Open Seam",
            "",
            "The next exact target is no longer whether assignment can fail. It is whether pair-token transport is already final, or whether there are deterministic local laws where even assignment plus pair transport fails and 2-simplex or higher holonomy becomes necessary.",
            "",
        ]
    )
    return "\n".join(lines)


def summarize_semantic(semantic: SemanticDefinition, records: Sequence[AnalysisRecord]) -> SemanticSummary:
    seed_record = None
    for family in SEED_FAMILIES.values():
        match = next((record for record in records if record.family == family), None)
        if match is not None:
            seed_record = match
            break
    coordinate_split = [record for record in records if not record.coordinate_exact]
    coordinate_gap = [record for record in records if record.coordinate_curvature_gap > 0]
    assignment_split = [record for record in records if not record.full_assignment_exact]
    hidden_future = [record for record in records if record.hidden_future_witness is not None]
    if coordinate_split:
        coordinate_split.sort(key=lambda record: record_order_key(record, "coordinate"))
    if coordinate_gap:
        coordinate_gap.sort(key=lambda record: record_order_key(record, "coordinate"))
    if assignment_split:
        assignment_split.sort(key=lambda record: record_order_key(record, "assignment"))
    if hidden_future:
        hidden_future.sort(key=lambda record: record_order_key(record, "hidden"))
    return SemanticSummary(
        name=semantic.name,
        label=semantic.label,
        description=semantic.description,
        token_scope=semantic.token_scope,
        token_alphabet_size=semantic.token_alphabet_size,
        families_scanned=len(records),
        coordinate_split_count=len(coordinate_split),
        coordinate_gap_count=len(coordinate_gap),
        full_assignment_split_count=len(assignment_split),
        hidden_future_count=len(hidden_future),
        full_assignment_exact_on_scan=all(record.full_assignment_exact for record in records),
        max_coordinate_curvature_gap=max(record.coordinate_curvature_gap for record in records),
        max_assignment_curvature_gap=max(record.assignment_curvature_gap for record in records),
        max_assignment_holonomy_rank=max(record.assignment_holonomy_rank for record in records),
        max_hidden_future_rank=max(record.hidden_future_rank for record in records),
        seed_record=seed_record,
        first_coordinate_split=coordinate_split[0] if coordinate_split else None,
        first_coordinate_gap=coordinate_gap[0] if coordinate_gap else None,
        first_full_assignment_split=assignment_split[0] if assignment_split else None,
        first_hidden_future_split=hidden_future[0] if hidden_future else None,
    )


def run_scan(
    semantics: Sequence[SemanticDefinition],
    *,
    p_scan: Sequence[int],
    k_max: int,
) -> Dict[str, List[AnalysisRecord]]:
    all_records: Dict[str, List[AnalysisRecord]] = {semantic.name: [] for semantic in semantics}
    for semantic in semantics:
        for p in p_scan:
            for k in range(1, min(k_max, p) + 1):
                for family in sorted_families(p, k):
                    all_records[semantic.name].append(analyze_family(semantic, family))
    return all_records


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    all_records = run_scan(SEMANTICS, p_scan=BASE_P_SCAN, k_max=BASE_K_MAX)
    summaries = [summarize_semantic(semantic, all_records[semantic.name]) for semantic in SEMANTICS]
    expanded_scan_triggered = not any(
        summary.first_full_assignment_split is not None for summary in summaries
    )
    if expanded_scan_triggered:
        promising = [
            semantic
            for semantic, summary in zip(SEMANTICS, summaries)
            if summary.max_assignment_holonomy_rank > 1 or summary.max_assignment_curvature_gap > 0
        ]
        expanded_records = run_scan(promising, p_scan=EXPANDED_P_SCAN, k_max=EXPANDED_K_MAX)
        for semantic in promising:
            all_records[semantic.name].extend(expanded_records[semantic.name])
        summaries = [summarize_semantic(semantic, all_records[semantic.name]) for semantic in SEMANTICS]

    overall_coordinate_split: AnalysisRecord | None = None
    overall_coordinate_gap: AnalysisRecord | None = None
    overall_assignment_split: AnalysisRecord | None = None
    overall_hidden_future: AnalysisRecord | None = None
    coordinate_candidates = [summary.first_coordinate_split for summary in summaries if summary.first_coordinate_split is not None]
    if coordinate_candidates:
        coordinate_candidates.sort(key=lambda record: record_order_key(record, "coordinate"))
        overall_coordinate_split = coordinate_candidates[0]
    gap_candidates = [summary.first_coordinate_gap for summary in summaries if summary.first_coordinate_gap is not None]
    if gap_candidates:
        gap_candidates.sort(key=lambda record: record_order_key(record, "coordinate"))
        overall_coordinate_gap = gap_candidates[0]
    assignment_candidates = [summary.first_full_assignment_split for summary in summaries if summary.first_full_assignment_split is not None]
    if assignment_candidates:
        assignment_candidates.sort(key=lambda record: record_order_key(record, "assignment"))
        overall_assignment_split = assignment_candidates[0]
    hidden_candidates = [summary.first_hidden_future_split for summary in summaries if summary.first_hidden_future_split is not None]
    if hidden_candidates:
        hidden_candidates.sort(key=lambda record: record_order_key(record, "hidden"))
        overall_hidden_future = hidden_candidates[0]

    json_path = RESULTS_DIR / "full_assignment_holonomy_search.json"
    report_path = RESULTS_DIR / "full_assignment_holonomy_search.md"
    svg_path = RESULTS_DIR / "full_assignment_holonomy_search.svg"
    note_path = DOCS_DIR / "full-assignment-holonomy.md"

    payload = {
        "scan": {
            "base_p_scan": list(BASE_P_SCAN),
            "base_k_max": BASE_K_MAX,
            "expanded_p_scan": list(EXPANDED_P_SCAN),
            "expanded_k_max": EXPANDED_K_MAX,
            "expanded_scan_triggered": expanded_scan_triggered,
            "seed_families": {name: [list(edge) for edge in family] for name, family in SEED_FAMILIES.items()},
            "semantics": [semantic.name for semantic in SEMANTICS],
        },
        "semantics": [summary_to_json(summary) for summary in summaries],
        "overall_first_coordinate_split": None if overall_coordinate_split is None else record_to_json(overall_coordinate_split),
        "overall_first_coordinate_gap": None if overall_coordinate_gap is None else record_to_json(overall_coordinate_gap),
        "overall_first_full_assignment_split": None if overall_assignment_split is None else record_to_json(overall_assignment_split),
        "overall_first_hidden_future_split": None if overall_hidden_future is None else record_to_json(overall_hidden_future),
    }
    json_path.write_text(json.dumps(payload, indent=2))
    note_text = build_note(payload, summaries)
    if note_text is not None:
        note_path.write_text(note_text)
    elif note_path.exists():
        note_path.unlink()
    report_path.write_text(build_report(summaries, payload, note_path if note_text is not None else None, json_path, svg_path))
    svg_path.write_text(render_svg(summaries, payload))

    print(f"Wrote {report_path}")
    print(f"Wrote {json_path}")
    print(f"Wrote {svg_path}")
    if note_text is not None:
        print(f"Wrote {note_path}")


if __name__ == "__main__":
    main()

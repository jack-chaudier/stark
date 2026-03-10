#!/usr/bin/env python3
"""Search for the first semantics where assignment plus pair transport is not exact.

The target boundary is stricter than full-assignment holonomy. We ask whether
pairwise nerve transport is already the final exact runtime object, or whether
there are deterministic prefix-compositional local laws where:

    assignment(u) == assignment(v)
    pair_summary(u) == pair_summary(v)
    but u and v are not continuation-equivalent.

The strongest witness is hidden future beyond pair transport:

    assignment(u) == assignment(v)
    pair_summary(u) == pair_summary(v)
    output(u) == output(v)
    and there exists a non-empty suffix w with output(u + w) != output(v + w).
"""

from __future__ import annotations

import json
from collections import defaultdict, deque
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from typing import Callable, DefaultDict, Dict, Hashable, Iterable, List, Sequence, Tuple

from runtime_collapse_boundary import enumerate_exact_antichains, log2_count

from full_assignment_holonomy_search import (
    BROADCAST_CONTROL as FULL_BROADCAST_CONTROL,
    COMMITTED_ALLOCATION as FULL_COMMITTED_ALLOCATION,
    SEMANTICS as FULL_HOLONOMY_SEMANTICS,
    Family,
    FamilyContext,
    PairDescriptor,
    Trace,
    TriangleDescriptor,
    WitnessRecord,
    assignment_presence,
    build_context,
    committed_compose,
    committed_output,
    committed_segment_states,
    edge_blocked_by_pair,
    edge_has_support,
    edge_has_support_on,
    event_text,
    family_overlap,
    family_union,
    minimize_moore_machine,
    pair_triggered,
    shortest_distinguishing_suffix,
    sorted_families,
    state_text,
    trace_text,
    update_pair_token,
)

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results"
DOCS_DIR = ROOT / "docs" / "writing"

BASE_P_SCAN = (2, 3, 4)
BASE_K_MAX = 3
EXPANDED_P_SCAN = (5,)
EXPANDED_K_MAX = 4
DENSE_P_SCAN = (6,)
DENSE_K_MAX = 4

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
SEED_FAMILY_ORDER = tuple(SEED_FAMILIES.values())

EXISTING_BY_NAME = {semantic.name: semantic for semantic in FULL_HOLONOMY_SEMANTICS}


@dataclass(frozen=True)
class PairBaseSpec:
    name: str
    label: str
    description: str
    trigger_kind: str
    update_kind: str
    gate_kind: str
    alphabet_size: int


@dataclass(frozen=True)
class SimplexSpec:
    name: str
    label: str
    description: str
    category: str
    trigger_kind: str
    update_kind: str
    gate_kind: str
    alphabet_size: int
    pair_feedback_kind: str = "none"


@dataclass(frozen=True)
class SemanticDefinition:
    name: str
    label: str
    description: str
    category: str
    pair_alphabet_size: int
    simplex_alphabet_size: int
    analysis_mode: str
    initial_state: Callable[[FamilyContext], Hashable]
    events: Callable[[FamilyContext], Tuple[Hashable, ...]]
    step: Callable[[Hashable, Hashable, FamilyContext], Hashable]
    output: Callable[[Hashable, FamilyContext], Hashable]
    assignment_summary: Callable[[Hashable, FamilyContext], Hashable]
    pair_summary: Callable[[Hashable, FamilyContext], Hashable]
    simplex_summary: Callable[[Hashable, FamilyContext], Hashable]
    full_state_summary: Callable[[Hashable, FamilyContext], Hashable]
    segment_states: Callable[[FamilyContext], Tuple[Hashable, ...]] | None = None
    compose: Callable[[Hashable, Hashable, FamilyContext], Hashable | None] | None = None


@dataclass(frozen=True)
class AnalysisRecord:
    semantics: str
    category: str
    pair_alphabet_size: int
    simplex_alphabet_size: int
    p: int
    k: int
    family: Family
    reachable_state_count: int
    runtime_quotient_count: int
    assignment_quotient_count: int
    pair_quotient_count: int
    simplex_quotient_count: int
    full_state_quotient_count: int
    output_quotient_count: int
    assignment_curvature_gap: float
    pair_curvature_gap: float
    simplex_curvature_gap: float
    assignment_exact: bool
    pair_exact: bool
    simplex_exact: bool
    full_state_exact: bool
    output_exact: bool
    assignment_holonomy_rank: int
    pair_holonomy_rank: int
    simplex_holonomy_rank: int
    hidden_future_rank: int
    hidden_future_beyond_pair_rank: int
    assignment_witness: WitnessRecord | None
    hidden_future_witness: WitnessRecord | None
    pair_witness: WitnessRecord | None
    hidden_future_beyond_pair_witness: WitnessRecord | None


@dataclass(frozen=True)
class SemanticSummary:
    name: str
    label: str
    description: str
    category: str
    pair_alphabet_size: int
    simplex_alphabet_size: int
    families_scanned: int
    seed_record: AnalysisRecord | None
    assignment_split_count: int
    hidden_future_count: int
    pair_split_count: int
    hidden_future_beyond_pair_count: int
    assignment_exact_on_scan: bool
    pair_exact_on_scan: bool
    simplex_exact_on_scan: bool
    max_assignment_curvature_gap: float
    max_pair_curvature_gap: float
    max_assignment_holonomy_rank: int
    max_pair_holonomy_rank: int
    max_simplex_holonomy_rank: int
    max_hidden_future_rank: int
    max_hidden_future_beyond_pair_rank: int
    first_assignment_split: AnalysisRecord | None
    first_hidden_future_split: AnalysisRecord | None
    first_pair_split: AnalysisRecord | None
    first_hidden_future_beyond_pair_split: AnalysisRecord | None


def format_family(family: Family) -> str:
    return "{" + ", ".join("{" + ",".join(str(item) for item in edge) + "}" for edge in family) + "}"


def empty_assignment(context: FamilyContext) -> Tuple[int, ...]:
    return tuple(-1 for _ in context.universe)


def token_initial(context: FamilyContext) -> Tuple[Tuple[int, ...], Tuple[int, ...], Tuple[int, ...]]:
    return (
        empty_assignment(context),
        tuple(0 for _ in context.pairs),
        tuple(0 for _ in context.triangles),
    )


def token_events(context: FamilyContext) -> Tuple[Tuple[int, int], ...]:
    return context.assignment_events


def broadcast_initial(context: FamilyContext) -> Tuple[int, ...]:
    return tuple(0 for _ in context.universe)


def broadcast_events(context: FamilyContext) -> Tuple[int, ...]:
    return context.universe


def broadcast_step(state: Tuple[int, ...], event: int, context: FamilyContext) -> Tuple[int, ...]:
    updated = list(state)
    updated[event - 1] = 1
    return tuple(updated)


def completed_edges_from_presence(presence: Sequence[int], family: Family) -> Family:
    return tuple(edge for edge in family if all(presence[item - 1] for item in edge))


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


def broadcast_output(state: Tuple[int, ...], context: FamilyContext) -> Family:
    return completed_edges_from_presence(state, context.family)


def broadcast_assignment(state: Tuple[int, ...], context: FamilyContext) -> Tuple[int, ...]:
    return state


def committed_assignment(state: Tuple[int, ...], context: FamilyContext) -> Tuple[int, ...]:
    return state


def pair_summary_from_state(
    state: Tuple[Tuple[int, ...], Tuple[int, ...], Tuple[int, ...]],
    context: FamilyContext,
) -> Tuple[Tuple[int, ...], Tuple[int, ...]]:
    assignment, pair_tokens, _ = state
    return assignment, pair_tokens


def simplex_summary_from_state(
    state: Tuple[Tuple[int, ...], Tuple[int, ...], Tuple[int, ...]],
    context: FamilyContext,
) -> Tuple[Tuple[int, ...], Tuple[int, ...], Tuple[int, ...]]:
    return state


def full_state_summary(state: Hashable, context: FamilyContext) -> Hashable:
    return state


def triangle_pair_indices(context: FamilyContext, triangle: TriangleDescriptor) -> Tuple[int, ...]:
    pair_lookup = {
        (pair.lower_edge, pair.upper_edge): pair.pair_index
        for pair in context.pairs
    }
    return tuple(
        pair_lookup[(left, right)]
        for left, right in combinations(triangle.edges, 2)
        if (left, right) in pair_lookup
    )


def active_pair_token(token_value: int) -> bool:
    return token_value != 0


def pair_feedback_allows(
    feedback_kind: str,
    pair: PairDescriptor,
    simplex_tokens: Sequence[int],
    context: FamilyContext,
) -> bool:
    if feedback_kind == "none":
        return True
    incident = [
        triangle.triangle_index
        for triangle in context.triangles
        if pair.lower_edge in triangle.edges and pair.upper_edge in triangle.edges
    ]
    active_count = sum(1 for index in incident if simplex_tokens[index] != 0)
    if feedback_kind == "freeze_if_simplex_active":
        return active_count == 0
    if feedback_kind == "parity_even_only":
        return active_count % 2 == 0
    raise ValueError(f"unknown pair feedback kind {feedback_kind}")


def triangle_triggered(
    trigger_kind: str,
    triangle: TriangleDescriptor,
    assignment: Sequence[int],
    pair_tokens: Sequence[int],
    simplex_tokens: Sequence[int],
    event: Tuple[int, int],
    context: FamilyContext,
) -> bool:
    _, chosen_edge = event
    if chosen_edge not in triangle.edges:
        return False
    live_before = [edge_has_support(assignment, edge_index) for edge_index in triangle.edges]
    live_after = [live or edge_index == chosen_edge for live, edge_index in zip(live_before, triangle.edges)]
    active_pairs = sum(
        1
        for pair_index in triangle_pair_indices(context, triangle)
        if active_pair_token(pair_tokens[pair_index])
    )
    simplex_active = simplex_tokens[triangle.triangle_index] != 0
    if trigger_kind == "two_live":
        return sum(live_before) == 1 and sum(live_after) == 2
    if trigger_kind == "three_live":
        return sum(live_before) == 2 and sum(live_after) == 3
    if trigger_kind == "second_or_third":
        return (sum(live_before), sum(live_after)) in {(1, 2), (2, 3)}
    if trigger_kind == "commutator_two_active":
        return sum(live_after) >= 2 and active_pairs >= 2 and not simplex_active
    if trigger_kind == "commutator_full_triangle":
        return sum(live_before) == 2 and sum(live_after) == 3 and active_pairs >= 2
    if trigger_kind == "triangle_debt":
        return sum(live_before) == 2 and sum(live_after) == 3 and active_pairs >= 1
    if trigger_kind == "triangle_feedback":
        return sum(live_after) >= 2 and active_pairs >= 1 and simplex_active
    raise ValueError(f"unknown simplex trigger {trigger_kind}")


def update_simplex_token(
    token_value: int,
    update_kind: str,
    chosen_edge: int,
    triangle: TriangleDescriptor,
) -> int:
    if update_kind == "toggle_mod2":
        return token_value ^ 1
    if update_kind == "orientation":
        return triangle.edges.index(chosen_edge) + 1
    if update_kind == "capped_inc2":
        return min(2, token_value + 1)
    raise ValueError(f"unknown simplex update kind {update_kind}")


def edge_blocked_by_simplex(
    edge_index: int,
    triangle: TriangleDescriptor,
    token_value: int,
    gate_kind: str,
) -> bool:
    if gate_kind == "block_none":
        return False
    if gate_kind == "block_lowest_complete":
        return edge_index == min(triangle.edges) and token_value == 1
    if gate_kind == "block_oriented_complete":
        if token_value == 0:
            return False
        return triangle.edges.index(edge_index) + 1 == token_value
    if gate_kind == "block_debt2_lowest":
        return edge_index == min(triangle.edges) and token_value == 2
    raise ValueError(f"unknown simplex gate kind {gate_kind}")


def make_pair_simplex_semantics(
    pair_base: PairBaseSpec,
    simplex_spec: SimplexSpec,
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
        updated_pairs = list(pair_tokens)
        updated_simplex = list(simplex_tokens)
        for pair in context.pairs:
            if not pair_feedback_allows(simplex_spec.pair_feedback_kind, pair, simplex_tokens, context):
                continue
            if pair_triggered(pair_base.trigger_kind, pair, assignment, event):
                updated_pairs[pair.pair_index] = update_pair_token(
                    updated_pairs[pair.pair_index],
                    pair_base.update_kind,
                    chosen_edge,
                    pair,
                )
        for triangle in context.triangles:
            if triangle_triggered(
                simplex_spec.trigger_kind,
                triangle,
                assignment,
                tuple(updated_pairs),
                simplex_tokens,
                event,
                context,
            ):
                updated_simplex[triangle.triangle_index] = update_simplex_token(
                    updated_simplex[triangle.triangle_index],
                    simplex_spec.update_kind,
                    chosen_edge,
                    triangle,
                )
        updated_assignment[variable - 1] = chosen_edge
        return tuple(updated_assignment), tuple(updated_pairs), tuple(updated_simplex)

    def output(
        state: Tuple[Tuple[int, ...], Tuple[int, ...], Tuple[int, ...]],
        context: FamilyContext,
    ) -> Family:
        assignment, pair_tokens, simplex_tokens = state
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
                pair_blocked = any(
                    edge_blocked_by_pair(
                        edge_index,
                        context.pairs[pair_index],
                        pair_tokens[pair_index],
                        pair_base.update_kind,
                        pair_base.gate_kind,
                    )
                    for pair_index in context.pair_indices_by_edge[edge_index]
                )
                simplex_blocked = any(
                    edge_blocked_by_simplex(
                        edge_index,
                        context.triangles[triangle_index],
                        simplex_tokens[triangle_index],
                        simplex_spec.gate_kind,
                    )
                    for triangle_index in context.triangle_indices_by_edge[edge_index]
                )
                if pair_blocked or simplex_blocked:
                    continue
            residuals.append(tuple(remaining))
        return tuple(residuals)

    return SemanticDefinition(
        name=f"{pair_base.name}__{simplex_spec.name}",
        label=f"{pair_base.label} + {simplex_spec.label}",
        description=f"{pair_base.description} {simplex_spec.description}",
        category=simplex_spec.category,
        pair_alphabet_size=pair_base.alphabet_size,
        simplex_alphabet_size=simplex_spec.alphabet_size,
        analysis_mode="automaton",
        initial_state=token_initial,
        events=token_events,
        step=step,
        output=output,
        assignment_summary=lambda state, context: state[0],
        pair_summary=pair_summary_from_state,
        simplex_summary=simplex_summary_from_state,
        full_state_summary=full_state_summary,
    )


def wrap_existing_semantics(name: str, category: str) -> SemanticDefinition:
    base = EXISTING_BY_NAME[name]
    pair_alphabet_size = base.token_alphabet_size if base.token_scope == "pair" else 1
    if base.token_scope == "pair":
        pair_summary = pair_summary_from_state
        simplex_summary = pair_summary_from_state
    else:
        pair_summary = base.full_assignment_summary
        simplex_summary = base.full_assignment_summary
    return SemanticDefinition(
        name=base.name,
        label=base.label,
        description=base.description,
        category=category,
        pair_alphabet_size=pair_alphabet_size,
        simplex_alphabet_size=1,
        analysis_mode=base.analysis_mode,
        initial_state=base.initial_state,
        events=base.events,
        step=base.step,
        output=base.output,
        assignment_summary=base.full_assignment_summary,
        pair_summary=pair_summary,
        simplex_summary=simplex_summary,
        full_state_summary=full_state_summary,
        segment_states=base.segment_states,
        compose=base.compose,
    )


PAIR_BASES = (
    PairBaseSpec(
        name="pair_phase_shared_other_live_block_lower",
        label="Shared Pair Phase",
        description="Pairwise shared-other-live phase toggles and suppresses lower completion.",
        trigger_kind="shared_other_live",
        update_kind="toggle_mod2",
        gate_kind="block_lower_complete",
        alphabet_size=2,
    ),
    PairBaseSpec(
        name="pair_phase_exclusive_other_live_block_lower",
        label="Exclusive Pair Phase",
        description="Exclusive-other-live pair phase toggles and suppresses lower completion.",
        trigger_kind="exclusive_other_live",
        update_kind="toggle_mod2",
        gate_kind="block_lower_complete",
        alphabet_size=2,
    ),
    PairBaseSpec(
        name="pair_phase_any_other_live_block_lower",
        label="Any-Live Pair Phase",
        description="Any-other-live pair phase toggles and suppresses lower completion.",
        trigger_kind="any_other_live",
        update_kind="toggle_mod2",
        gate_kind="block_lower_complete",
        alphabet_size=2,
    ),
)


SIMPLEX_SPECS = (
    SimplexSpec(
        name="simplex_orient_two_live",
        label="2-Live Orient",
        description="A triangle-orientation token records which edge created the second live edge of a 2-simplex and blocks that oriented edge on completion.",
        category="pair_plus_simplex",
        trigger_kind="two_live",
        update_kind="orientation",
        gate_kind="block_oriented_complete",
        alphabet_size=4,
    ),
    SimplexSpec(
        name="simplex_orient_three_live",
        label="3-Live Orient",
        description="A triangle-orientation token records which edge completed the live 2-simplex and blocks that oriented edge on completion.",
        category="pair_plus_simplex",
        trigger_kind="three_live",
        update_kind="orientation",
        gate_kind="block_oriented_complete",
        alphabet_size=4,
    ),
    SimplexSpec(
        name="simplex_orient_second_or_third",
        label="2/3-Live Orient",
        description="Triangle orientation updates on the second or third live edge and blocks the oriented edge on completion.",
        category="pair_plus_simplex",
        trigger_kind="second_or_third",
        update_kind="orientation",
        gate_kind="block_oriented_complete",
        alphabet_size=4,
    ),
    SimplexSpec(
        name="simplex_commutator_toggle",
        label="Commutator Toggle",
        description="A simplex phase toggles when two active pair phases meet inside a live triangle; odd phase blocks the lowest edge.",
        category="pair_plus_simplex",
        trigger_kind="commutator_two_active",
        update_kind="toggle_mod2",
        gate_kind="block_lowest_complete",
        alphabet_size=2,
    ),
    SimplexSpec(
        name="simplex_commutator_orient",
        label="Commutator Orient",
        description="A simplex orientation records which edge carries the pair commutator into a live triangle and blocks that oriented edge.",
        category="pair_plus_simplex",
        trigger_kind="commutator_full_triangle",
        update_kind="orientation",
        gate_kind="block_oriented_complete",
        alphabet_size=4,
    ),
    SimplexSpec(
        name="triangle_debt",
        label="Triangle Debt",
        description="Triangle-local debt accumulates when pair transport reaches a full triangle; debt level 2 blocks the lowest edge.",
        category="triangle_debt",
        trigger_kind="triangle_debt",
        update_kind="capped_inc2",
        gate_kind="block_debt2_lowest",
        alphabet_size=3,
    ),
    SimplexSpec(
        name="feedback_orient_freeze_pairs",
        label="Feedback Orient",
        description="Triangle orientation updates on the second or third live edge while active simplex tokens freeze further pair updates on incident overlaps.",
        category="higher_local_interaction",
        trigger_kind="second_or_third",
        update_kind="orientation",
        gate_kind="block_oriented_complete",
        alphabet_size=4,
        pair_feedback_kind="freeze_if_simplex_active",
    ),
    SimplexSpec(
        name="feedback_debt_parity",
        label="Feedback Debt",
        description="Triangle debt updates in the presence of pair transport while pair updates are parity-gated by incident simplex activity.",
        category="higher_local_interaction",
        trigger_kind="triangle_feedback",
        update_kind="capped_inc2",
        gate_kind="block_debt2_lowest",
        alphabet_size=3,
        pair_feedback_kind="parity_even_only",
    ),
)


def generated_semantics() -> Tuple[SemanticDefinition, ...]:
    semantics: List[SemanticDefinition] = [
        wrap_existing_semantics("broadcast_control", "control"),
        wrap_existing_semantics("committed_allocation", "control"),
        wrap_existing_semantics("pair_phase_exclusive_other_live_block_lower", "pair_only"),
        wrap_existing_semantics("pair_phase_shared_other_live_block_lower", "pair_only"),
        wrap_existing_semantics("pair_phase_any_other_live_block_lower", "pair_only"),
    ]
    generated_pair_base = PAIR_BASES[0]
    generated_simplex_specs = (
        SIMPLEX_SPECS[0],
        SIMPLEX_SPECS[1],
        SIMPLEX_SPECS[2],
        SIMPLEX_SPECS[3],
        SIMPLEX_SPECS[5],
        SIMPLEX_SPECS[6],
    )
    semantics.extend(
        make_pair_simplex_semantics(generated_pair_base, simplex_spec)
        for simplex_spec in generated_simplex_specs
    )
    return tuple(semantics)


SEMANTICS = generated_semantics()


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
    candidates: List[Tuple[object, ...]] = []
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
    empty_state: Hashable,
    *,
    require_same_output: bool = False,
    require_non_empty_suffix: bool = False,
) -> WitnessRecord | None:
    groups: DefaultDict[Hashable, List[Hashable]] = defaultdict(list)
    for state in states:
        groups[summary_fn(state, context)].append(state)
    candidates: List[Tuple[object, ...]] = []
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
                    if left_row != right_row and (not require_non_empty_suffix or suffix != empty_state)
                ]
                if not differing_suffixes:
                    continue
                differing_suffixes.sort(
                    key=lambda suffix: (
                        0 if suffix != empty_state else 1,
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
        left_trace=(("segment", left_state),) if left_state != empty_state else (),
        right_trace=(("segment", right_state),) if right_state != empty_state else (),
        suffix=(("segment", suffix),) if suffix != empty_state else (),
        summary_value=state_text(summary_fn(left_state, context), context.family),
        left_state=state_text(left_state, context.family),
        right_state=state_text(right_state, context.family),
        left_output_now=state_text(output_fn(left_state, context), context.family),
        right_output_now=state_text(output_fn(right_state, context), context.family),
        left_output_future=state_text(("INVALID",), context.family) if future_left is None else state_text(output_fn(future_left, context), context.family),
        right_output_future=state_text(("INVALID",), context.family) if future_right is None else state_text(output_fn(future_right, context), context.family),
        same_now=output_fn(left_state, context) == output_fn(right_state, context),
        non_empty_suffix=suffix != empty_state,
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
    assignment_count, assignment_exact = summary_exactness(semantic.assignment_summary, states, context, block_of)
    pair_count, pair_exact = summary_exactness(semantic.pair_summary, states, context, block_of)
    simplex_count, simplex_exact = summary_exactness(semantic.simplex_summary, states, context, block_of)
    full_state_count, full_state_exact = summary_exactness(semantic.full_state_summary, states, context, block_of)
    output_count, output_exact = summary_exactness(lambda state, _: outputs[state], states, context, block_of)

    assignment_witness = extract_automaton_witness(
        states,
        context,
        semantic.assignment_summary,
        block_of,
        outputs,
        transitions,
        shortest_trace,
        events,
    )
    hidden_future_witness = extract_automaton_witness(
        states,
        context,
        semantic.assignment_summary,
        block_of,
        outputs,
        transitions,
        shortest_trace,
        events,
        require_same_output=True,
        require_non_empty_suffix=True,
    )
    pair_witness = extract_automaton_witness(
        states,
        context,
        semantic.pair_summary,
        block_of,
        outputs,
        transitions,
        shortest_trace,
        events,
    )
    hidden_future_beyond_pair_witness = extract_automaton_witness(
        states,
        context,
        semantic.pair_summary,
        block_of,
        outputs,
        transitions,
        shortest_trace,
        events,
        require_same_output=True,
        require_non_empty_suffix=True,
    )

    return AnalysisRecord(
        semantics=semantic.name,
        category=semantic.category,
        pair_alphabet_size=semantic.pair_alphabet_size,
        simplex_alphabet_size=semantic.simplex_alphabet_size,
        p=max(context.universe) if context.universe else 0,
        k=max(len(edge) for edge in context.family) if context.family else 0,
        family=context.family,
        reachable_state_count=len(states),
        runtime_quotient_count=runtime_count,
        assignment_quotient_count=assignment_count,
        pair_quotient_count=pair_count,
        simplex_quotient_count=simplex_count,
        full_state_quotient_count=full_state_count,
        output_quotient_count=output_count,
        assignment_curvature_gap=log2_count(runtime_count) - log2_count(assignment_count),
        pair_curvature_gap=log2_count(runtime_count) - log2_count(pair_count),
        simplex_curvature_gap=log2_count(runtime_count) - log2_count(simplex_count),
        assignment_exact=assignment_exact,
        pair_exact=pair_exact,
        simplex_exact=simplex_exact,
        full_state_exact=full_state_exact,
        output_exact=output_exact,
        assignment_holonomy_rank=group_rank(states, block_of, key_fn=lambda state: semantic.assignment_summary(state, context)),
        pair_holonomy_rank=group_rank(states, block_of, key_fn=lambda state: semantic.pair_summary(state, context)),
        simplex_holonomy_rank=group_rank(states, block_of, key_fn=lambda state: semantic.simplex_summary(state, context)),
        hidden_future_rank=group_rank(states, block_of, key_fn=lambda state: (semantic.assignment_summary(state, context), outputs[state])),
        hidden_future_beyond_pair_rank=group_rank(states, block_of, key_fn=lambda state: (semantic.pair_summary(state, context), outputs[state])),
        assignment_witness=assignment_witness,
        hidden_future_witness=hidden_future_witness,
        pair_witness=pair_witness,
        hidden_future_beyond_pair_witness=hidden_future_beyond_pair_witness,
    )


def analyze_segment_rows(semantic: SemanticDefinition, context: FamilyContext) -> AnalysisRecord:
    if semantic.segment_states is None or semantic.compose is None:
        raise ValueError(f"{semantic.name} requires segment_states and compose")
    states = semantic.segment_states(context)
    empty_state = semantic.initial_state(context)
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
    assignment_count, assignment_exact = row_exactness(semantic.assignment_summary, states, context, row_of)
    pair_count, pair_exact = row_exactness(semantic.pair_summary, states, context, row_of)
    simplex_count, simplex_exact = row_exactness(semantic.simplex_summary, states, context, row_of)
    full_state_count, full_state_exact = row_exactness(semantic.full_state_summary, states, context, row_of)
    output_count, output_exact = row_exactness(lambda state, ctx: semantic.output(state, ctx), states, context, row_of)

    assignment_witness = extract_segment_witness(
        states,
        context,
        semantic.assignment_summary,
        row_of,
        block_of,
        semantic.output,
        states,
        semantic.compose,
        empty_state,
    )
    hidden_future_witness = extract_segment_witness(
        states,
        context,
        semantic.assignment_summary,
        row_of,
        block_of,
        semantic.output,
        states,
        semantic.compose,
        empty_state,
        require_same_output=True,
        require_non_empty_suffix=True,
    )
    pair_witness = extract_segment_witness(
        states,
        context,
        semantic.pair_summary,
        row_of,
        block_of,
        semantic.output,
        states,
        semantic.compose,
        empty_state,
    )
    hidden_future_beyond_pair_witness = extract_segment_witness(
        states,
        context,
        semantic.pair_summary,
        row_of,
        block_of,
        semantic.output,
        states,
        semantic.compose,
        empty_state,
        require_same_output=True,
        require_non_empty_suffix=True,
    )

    return AnalysisRecord(
        semantics=semantic.name,
        category=semantic.category,
        pair_alphabet_size=semantic.pair_alphabet_size,
        simplex_alphabet_size=semantic.simplex_alphabet_size,
        p=max(context.universe) if context.universe else 0,
        k=max(len(edge) for edge in context.family) if context.family else 0,
        family=context.family,
        reachable_state_count=len(states),
        runtime_quotient_count=runtime_count,
        assignment_quotient_count=assignment_count,
        pair_quotient_count=pair_count,
        simplex_quotient_count=simplex_count,
        full_state_quotient_count=full_state_count,
        output_quotient_count=output_count,
        assignment_curvature_gap=log2_count(runtime_count) - log2_count(assignment_count),
        pair_curvature_gap=log2_count(runtime_count) - log2_count(pair_count),
        simplex_curvature_gap=log2_count(runtime_count) - log2_count(simplex_count),
        assignment_exact=assignment_exact,
        pair_exact=pair_exact,
        simplex_exact=simplex_exact,
        full_state_exact=full_state_exact,
        output_exact=output_exact,
        assignment_holonomy_rank=group_rank(states, block_of, key_fn=lambda state: semantic.assignment_summary(state, context)),
        pair_holonomy_rank=group_rank(states, block_of, key_fn=lambda state: semantic.pair_summary(state, context)),
        simplex_holonomy_rank=group_rank(states, block_of, key_fn=lambda state: semantic.simplex_summary(state, context)),
        hidden_future_rank=group_rank(states, block_of, key_fn=lambda state: (semantic.assignment_summary(state, context), semantic.output(state, context))),
        hidden_future_beyond_pair_rank=group_rank(states, block_of, key_fn=lambda state: (semantic.pair_summary(state, context), semantic.output(state, context))),
        assignment_witness=assignment_witness,
        hidden_future_witness=hidden_future_witness,
        pair_witness=pair_witness,
        hidden_future_beyond_pair_witness=hidden_future_beyond_pair_witness,
    )


def analyze_family(semantic: SemanticDefinition, family: Family) -> AnalysisRecord:
    context = build_context(family)
    if semantic.analysis_mode == "segment_rows":
        return analyze_segment_rows(semantic, context)
    return analyze_automaton(semantic, context)


def record_order_key(record: AnalysisRecord, witness_kind: str) -> Tuple[object, ...]:
    if witness_kind == "assignment":
        chosen = record.assignment_witness
    elif witness_kind == "hidden_assignment":
        chosen = record.hidden_future_witness
    elif witness_kind == "pair":
        chosen = record.pair_witness
    elif witness_kind == "hidden_pair":
        chosen = record.hidden_future_beyond_pair_witness
    else:
        raise ValueError(f"unknown witness kind {witness_kind}")
    return (
        record.p,
        record.k,
        len(record.family),
        record.pair_alphabet_size,
        record.simplex_alphabet_size,
        record.reachable_state_count,
        witness_length(chosen),
        record.family,
        record.semantics,
    )


def summarize_semantic(semantic: SemanticDefinition, records: Sequence[AnalysisRecord]) -> SemanticSummary:
    seed_record = None
    for family in SEED_FAMILY_ORDER:
        match = next((record for record in records if record.family == family), None)
        if match is not None:
            seed_record = match
            break
    assignment_split = [record for record in records if not record.assignment_exact]
    hidden_future = [record for record in records if record.hidden_future_witness is not None]
    pair_split = [record for record in records if not record.pair_exact]
    hidden_beyond_pair = [record for record in records if record.hidden_future_beyond_pair_witness is not None]
    if assignment_split:
        assignment_split.sort(key=lambda record: record_order_key(record, "assignment"))
    if hidden_future:
        hidden_future.sort(key=lambda record: record_order_key(record, "hidden_assignment"))
    if pair_split:
        pair_split.sort(key=lambda record: record_order_key(record, "pair"))
    if hidden_beyond_pair:
        hidden_beyond_pair.sort(key=lambda record: record_order_key(record, "hidden_pair"))
    return SemanticSummary(
        name=semantic.name,
        label=semantic.label,
        description=semantic.description,
        category=semantic.category,
        pair_alphabet_size=semantic.pair_alphabet_size,
        simplex_alphabet_size=semantic.simplex_alphabet_size,
        families_scanned=len(records),
        seed_record=seed_record,
        assignment_split_count=len(assignment_split),
        hidden_future_count=len(hidden_future),
        pair_split_count=len(pair_split),
        hidden_future_beyond_pair_count=len(hidden_beyond_pair),
        assignment_exact_on_scan=all(record.assignment_exact for record in records),
        pair_exact_on_scan=all(record.pair_exact for record in records),
        simplex_exact_on_scan=all(record.simplex_exact for record in records),
        max_assignment_curvature_gap=max(record.assignment_curvature_gap for record in records),
        max_pair_curvature_gap=max(record.pair_curvature_gap for record in records),
        max_assignment_holonomy_rank=max(record.assignment_holonomy_rank for record in records),
        max_pair_holonomy_rank=max(record.pair_holonomy_rank for record in records),
        max_simplex_holonomy_rank=max(record.simplex_holonomy_rank for record in records),
        max_hidden_future_rank=max(record.hidden_future_rank for record in records),
        max_hidden_future_beyond_pair_rank=max(record.hidden_future_beyond_pair_rank for record in records),
        first_assignment_split=assignment_split[0] if assignment_split else None,
        first_hidden_future_split=hidden_future[0] if hidden_future else None,
        first_pair_split=pair_split[0] if pair_split else None,
        first_hidden_future_beyond_pair_split=hidden_beyond_pair[0] if hidden_beyond_pair else None,
    )


def dense_overlap_families(p: int, k: int) -> Tuple[Family, ...]:
    families = []
    for family in enumerate_exact_antichains(p, k):
        context = build_context(family)
        if len(context.triangles) == 0:
            continue
        if len(family) < 3:
            continue
        overlap_pairs = sum(1 for left, right in combinations(family, 2) if set(left) & set(right))
        if overlap_pairs < len(family) - 1:
            continue
        families.append(family)
    return tuple(
        sorted(
            families,
            key=lambda family: (
                len(family),
                tuple(sorted(len(edge) for edge in family)),
                sum(len(edge) for edge in family),
                family,
            ),
        )
    )


def run_scan(
    semantics: Sequence[SemanticDefinition],
    *,
    p_scan: Sequence[int],
    k_max: int,
    families_fn: Callable[[int, int], Sequence[Family]] = sorted_families,
) -> Dict[str, List[AnalysisRecord]]:
    all_records: Dict[str, List[AnalysisRecord]] = {semantic.name: [] for semantic in semantics}
    for semantic in semantics:
        for p in p_scan:
            for k in range(1, min(k_max, p) + 1):
                for family in families_fn(p, k):
                    all_records[semantic.name].append(analyze_family(semantic, family))
    return all_records


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


def record_to_json(record: AnalysisRecord) -> Dict[str, object]:
    return {
        "semantics": record.semantics,
        "category": record.category,
        "pair_alphabet_size": record.pair_alphabet_size,
        "simplex_alphabet_size": record.simplex_alphabet_size,
        "p": record.p,
        "k": record.k,
        "family": [list(edge) for edge in record.family],
        "reachable_state_count": record.reachable_state_count,
        "runtime_quotient_count": record.runtime_quotient_count,
        "assignment_quotient_count": record.assignment_quotient_count,
        "pair_quotient_count": record.pair_quotient_count,
        "simplex_quotient_count": record.simplex_quotient_count,
        "full_state_quotient_count": record.full_state_quotient_count,
        "output_quotient_count": record.output_quotient_count,
        "assignment_curvature_gap": record.assignment_curvature_gap,
        "pair_curvature_gap": record.pair_curvature_gap,
        "simplex_curvature_gap": record.simplex_curvature_gap,
        "assignment_exact": record.assignment_exact,
        "pair_exact": record.pair_exact,
        "simplex_exact": record.simplex_exact,
        "full_state_exact": record.full_state_exact,
        "output_exact": record.output_exact,
        "assignment_holonomy_rank": record.assignment_holonomy_rank,
        "pair_holonomy_rank": record.pair_holonomy_rank,
        "simplex_holonomy_rank": record.simplex_holonomy_rank,
        "hidden_future_rank": record.hidden_future_rank,
        "hidden_future_beyond_pair_rank": record.hidden_future_beyond_pair_rank,
        "assignment_witness": witness_to_json(record.assignment_witness),
        "hidden_future_witness": witness_to_json(record.hidden_future_witness),
        "pair_witness": witness_to_json(record.pair_witness),
        "hidden_future_beyond_pair_witness": witness_to_json(record.hidden_future_beyond_pair_witness),
    }


def summary_to_json(summary: SemanticSummary) -> Dict[str, object]:
    return {
        "name": summary.name,
        "label": summary.label,
        "description": summary.description,
        "category": summary.category,
        "pair_alphabet_size": summary.pair_alphabet_size,
        "simplex_alphabet_size": summary.simplex_alphabet_size,
        "families_scanned": summary.families_scanned,
        "assignment_split_count": summary.assignment_split_count,
        "hidden_future_count": summary.hidden_future_count,
        "pair_split_count": summary.pair_split_count,
        "hidden_future_beyond_pair_count": summary.hidden_future_beyond_pair_count,
        "assignment_exact_on_scan": summary.assignment_exact_on_scan,
        "pair_exact_on_scan": summary.pair_exact_on_scan,
        "simplex_exact_on_scan": summary.simplex_exact_on_scan,
        "max_assignment_curvature_gap": summary.max_assignment_curvature_gap,
        "max_pair_curvature_gap": summary.max_pair_curvature_gap,
        "max_assignment_holonomy_rank": summary.max_assignment_holonomy_rank,
        "max_pair_holonomy_rank": summary.max_pair_holonomy_rank,
        "max_simplex_holonomy_rank": summary.max_simplex_holonomy_rank,
        "max_hidden_future_rank": summary.max_hidden_future_rank,
        "max_hidden_future_beyond_pair_rank": summary.max_hidden_future_beyond_pair_rank,
        "seed_record": None if summary.seed_record is None else record_to_json(summary.seed_record),
        "first_assignment_split": None if summary.first_assignment_split is None else record_to_json(summary.first_assignment_split),
        "first_hidden_future_split": None if summary.first_hidden_future_split is None else record_to_json(summary.first_hidden_future_split),
        "first_pair_split": None if summary.first_pair_split is None else record_to_json(summary.first_pair_split),
        "first_hidden_future_beyond_pair_split": None if summary.first_hidden_future_beyond_pair_split is None else record_to_json(summary.first_hidden_future_beyond_pair_split),
    }


def build_report(
    summaries: Sequence[SemanticSummary],
    payload: Dict[str, object],
    note_path: Path | None,
    json_path: Path,
    svg_path: Path,
) -> str:
    overall_assignment = payload["overall_first_assignment_split"]
    overall_hidden_assignment = payload["overall_first_hidden_future_split"]
    overall_pair = payload["overall_first_pair_split"]
    overall_hidden_pair = payload["overall_first_hidden_future_beyond_pair_split"]
    lines = [
        "# Pair vs Simplex Holonomy Search",
        "",
        "## Question",
        "",
        "This search asks whether assignment plus pairwise nerve transport is already exact, or whether a deterministic local law can force runtime classes that survive inside a fixed assignment-plus-pair fiber.",
        "The strongest witness is hidden future beyond pair transport: two prefixes with the same assignment, the same pair summary, and the same current output, but different futures under the same non-empty suffix.",
        "",
        "## Scan Setup",
        "",
        f"- Base scan: exact normalized full-union antichains on `[p]` with `p <= {max(BASE_P_SCAN)}` and `k <= {BASE_K_MAX}`.",
        "- Expanded scan: not run in this base exact pass; this artifact fixes the boundary on the full normalized base grid first.",
        f"- Dense overlap expansion triggered: `{payload['scan']['dense_scan_triggered']}`.",
        "- Controls: `broadcast_control` stays flat, `committed_allocation` reproduces coordinate curvature while keeping assignment exact, and the pair-only laws test pairwise transport as the current exact object.",
        "- Local law library: pair-only controls, pair-plus-simplex orientation laws, pair-plus-simplex commutator laws, triangle debt laws, and higher local interaction laws with tiny deterministic alphabets.",
        "- Runtime quotient: exact continuation quotient; segment-row controls are analyzed by exact suffix rows, while tokenized laws are analyzed on reachable event-prefix automata.",
        "- Canonical `first` order: `(p, k, |A|, pair alphabet, simplex alphabet, reachable states, witness length, family, semantics)` with witness-specific traces for assignment, hidden-future, pair, and hidden-future-beyond-pair searches.",
        "",
        "## Semantics Library",
        "",
    ]
    for summary in summaries:
        lines.append(
            f"- `{summary.name}` (`category={summary.category}`, `|Sigma_pair|={summary.pair_alphabet_size}`, `|Sigma_simplex|={summary.simplex_alphabet_size}`): {summary.description}"
        )
    lines.extend(
        [
            "",
            "## Summary Table",
            "",
            "| Semantics | Category | `|Sigma_pair|` | `|Sigma_simplex|` | Seed counts `(runtime / assign / pair / simplex)` | First assignment split | First hidden future | First pair-insufficient split | First hidden-future-beyond-pair | Max pair gap | Pair exact on scan | Simplex exact on scan |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )

    def short_label(record: AnalysisRecord | None) -> str:
        if record is None:
            return "none"
        return f"(p={record.p}, k={record.k}) {record.family}"

    for summary in summaries:
        seed = summary.seed_record
        seed_counts = "n/a"
        if seed is not None:
            seed_counts = f"{seed.runtime_quotient_count} / {seed.assignment_quotient_count} / {seed.pair_quotient_count} / {seed.simplex_quotient_count}"
        lines.append(
            f"| `{summary.label}` | `{summary.category}` | `{summary.pair_alphabet_size}` | `{summary.simplex_alphabet_size}` | `{seed_counts}` | `{short_label(summary.first_assignment_split)}` | `{short_label(summary.first_hidden_future_split)}` | `{short_label(summary.first_pair_split)}` | `{short_label(summary.first_hidden_future_beyond_pair_split)}` | `{summary.max_pair_curvature_gap:.3f}` | `{summary.pair_exact_on_scan}` | `{summary.simplex_exact_on_scan}` |"
        )

    lines.extend(
        [
            "",
            "## Controls",
            "",
            "- `broadcast_control` stays flat: no assignment split, no pair split, and no hidden future on the scanned grid.",
            "- `committed_allocation` reproduces the known assignment-level control: coordinate collapse fails, but both raw assignment and assignment-plus-pair remain exact.",
            "- `pair_phase_exclusive_other_live_block_lower` and `pair_phase_shared_other_live_block_lower` provide the pairwise-holonomy controls: they break assignment exactness but keep assignment-plus-pair exact.",
            "",
            "## Boundary Results",
            "",
        ]
    )
    if overall_assignment is None:
        lines.append("- No assignment split was found.")
    else:
        record = overall_assignment
        lines.append(
            f"- First assignment split: `{record['semantics']}` on `{tuple(tuple(edge) for edge in record['family'])}` at `(p={record['p']}, k={record['k']})`."
        )
    if overall_hidden_assignment is None:
        lines.append("- No same-assignment hidden future was found.")
    else:
        record = overall_hidden_assignment
        lines.append(
            f"- First hidden future: `{record['semantics']}` on `{tuple(tuple(edge) for edge in record['family'])}` at `(p={record['p']}, k={record['k']})`."
        )
    if overall_pair is None:
        lines.append("- No pair-insufficient split was found on the scanned library.")
    else:
        record = overall_pair
        lines.append(
            f"- First pair-insufficient split: `{record['semantics']}` on `{tuple(tuple(edge) for edge in record['family'])}` at `(p={record['p']}, k={record['k']})`, with pair gap `{record['pair_curvature_gap']:.3f}` bits."
        )
    if overall_hidden_pair is None:
        lines.append("- No hidden-future-beyond-pair witness was found.")
    else:
        record = overall_hidden_pair
        lines.append(
            f"- First hidden-future-beyond-pair split: `{record['semantics']}` on `{tuple(tuple(edge) for edge in record['family'])}` at `(p={record['p']}, k={record['k']})`."
        )

    lines.extend(["", "## First Pair-Insufficient Split", ""])
    if overall_pair is None:
        strongest_negative = max(
            summaries,
            key=lambda summary: (
                summary.max_pair_holonomy_rank,
                summary.max_pair_curvature_gap,
                summary.max_hidden_future_beyond_pair_rank,
            ),
        )
        lines.extend(
            [
                "No semantics broke assignment-plus-pair exactness on the scanned library.",
                f"The strongest near-miss was `{strongest_negative.name}` with `max pair holonomy rank = {strongest_negative.max_pair_holonomy_rank}` and `max pair gap = {strongest_negative.max_pair_curvature_gap:.3f}` bits.",
                "On the tested local law library and scan range, assignment plus pairwise nerve transport is exact.",
            ]
        )
    else:
        record = overall_pair
        witness = record["pair_witness"]
        lines.extend(
            [
                f"- semantics: `{record['semantics']}` (`|Sigma_pair|={record['pair_alphabet_size']}`, `|Sigma_simplex|={record['simplex_alphabet_size']}`)",
                f"- family: `{tuple(tuple(edge) for edge in record['family'])}`",
                f"- counts: runtime `{record['runtime_quotient_count']}`, assignment `{record['assignment_quotient_count']}`, pair `{record['pair_quotient_count']}`, simplex `{record['simplex_quotient_count']}`, full state `{record['full_state_quotient_count']}`",
                f"- pair holonomy rank: `{record['pair_holonomy_rank']}`",
                f"- simplex holonomy rank: `{record['simplex_holonomy_rank']}`",
                f"- pair gap: `{record['pair_curvature_gap']:.3f}` bits",
                f"- same assignment-plus-pair witness `u`: `{trace_text(tuple(witness['left_trace']) if witness and witness['left_trace'] else (), tuple(tuple(edge) for edge in record['family'])) if witness else '[]'}`",
                f"- same assignment-plus-pair witness `v`: `{trace_text(tuple(witness['right_trace']) if witness and witness['right_trace'] else (), tuple(tuple(edge) for edge in record['family'])) if witness else '[]'}`",
                f"- suffix `w`: `{trace_text(tuple(witness['suffix']) if witness and witness['suffix'] else (), tuple(tuple(edge) for edge in record['family'])) if witness else '[]'}`",
                f"- pair fiber: `{witness['summary_value'] if witness else 'n/a'}`",
                f"- outputs now: `{witness['left_output_now'] if witness else 'n/a'}` versus `{witness['right_output_now'] if witness else 'n/a'}`",
                f"- outputs after suffix: `{witness['left_output_future'] if witness else 'n/a'}` versus `{witness['right_output_future'] if witness else 'n/a'}`",
            ]
        )

    lines.extend(["", "## First Hidden-Future-Beyond-Pair Split", ""])
    if overall_hidden_pair is None:
        if overall_pair is not None:
            lines.append("Assignment-plus-pair can fail, but none of the scanned semantics produced a same-now / future-separate witness beyond pair transport.")
        else:
            lines.append("No hidden-future-beyond-pair split appeared on the scanned library.")
    else:
        record = overall_hidden_pair
        witness = record["hidden_future_beyond_pair_witness"]
        lines.extend(
            [
                f"- semantics: `{record['semantics']}` (`|Sigma_pair|={record['pair_alphabet_size']}`, `|Sigma_simplex|={record['simplex_alphabet_size']}`)",
                f"- family: `{tuple(tuple(edge) for edge in record['family'])}`",
                f"- same assignment-plus-pair fiber: `{witness['summary_value'] if witness else 'n/a'}`",
                f"- left prefix `u`: `{trace_text(tuple(witness['left_trace']) if witness and witness['left_trace'] else (), tuple(tuple(edge) for edge in record['family'])) if witness else '[]'}`",
                f"- right prefix `v`: `{trace_text(tuple(witness['right_trace']) if witness and witness['right_trace'] else (), tuple(tuple(edge) for edge in record['family'])) if witness else '[]'}`",
                f"- shared current output: `{witness['left_output_now'] if witness else 'n/a'}`",
                f"- non-empty suffix `w`: `{trace_text(tuple(witness['suffix']) if witness and witness['suffix'] else (), tuple(tuple(edge) for edge in record['family'])) if witness else '[]'}`",
                f"- future outputs: `{witness['left_output_future'] if witness else 'n/a'}` versus `{witness['right_output_future'] if witness else 'n/a'}`",
            ]
        )

    lines.extend(["", "## Interpretation", ""])
    if overall_pair is None:
        lines.extend(
            [
                "On the tested local law library and scan range, assignment plus pairwise nerve transport is exact.",
                "The strongest near-misses still factor through pairwise transport, so 2-simplex tokens were not forced by the scanned deterministic local laws.",
            ]
        )
    else:
        lines.extend(
            [
                "Pairwise nerve transport is not final on the scanned local law library.",
                "The first counterexample already lives on the triangle family, so the next exact runtime object is assignment plus pair-plus-simplex transport rather than assignment plus pair transport alone.",
            ]
        )
    if overall_hidden_pair is not None:
        lines.append("The strongest witness is a hidden future beyond pair transport: the current output and the full pair fiber agree, but a non-empty suffix still separates the futures.")
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            f"- JSON: [{json_path.name}]({json_path})",
            f"- Figure: [{svg_path.name}]({svg_path})",
        ]
    )
    if note_path is not None:
        lines.append(f"- Note: [{note_path.name}]({note_path})")
    return "\n".join(lines) + "\n"


def render_svg(summaries: Sequence[SemanticSummary], payload: Dict[str, object]) -> str:
    width = 1680
    height = 960
    left = 44
    top = 54
    table_width = width - 2 * left
    row_height = 30
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
        f'<text x="{left}" y="28" class="title">Pair vs Simplex Holonomy Search</text>',
        f'<text x="{left}" y="46" class="subtitle">The search for the first deterministic law where assignment plus pair transport is no longer exact.</text>',
        f'<rect x="{left}" y="{top}" width="{table_width}" height="420" class="panel"/>',
    ]
    columns = {
        "sem": left + 18,
        "cat": left + 230,
        "pair": left + 340,
        "simplex": left + 410,
        "seed": left + 500,
        "pairsplit": left + 720,
        "hiddenpair": left + 980,
        "gap": left + 1260,
        "rank": left + 1360,
        "exact": left + 1470,
        "note": left + 1565,
    }
    head_y = top + 24
    for key, label in (
        ("sem", "semantics"),
        ("cat", "category"),
        ("pair", "|pair|"),
        ("simplex", "|simplex|"),
        ("seed", "seed runtime/assign/pair/simplex"),
        ("pairsplit", "first pair split"),
        ("hiddenpair", "first hidden beyond pair"),
        ("gap", "max pair gap"),
        ("rank", "pair/simplex"),
        ("exact", "pair exact"),
        ("note", "status"),
    ):
        lines.append(f'<text x="{columns[key]}" y="{head_y}" class="header">{label}</text>')
    for index, summary in enumerate(summaries):
        y = head_y + 28 + index * row_height
        if summary.category == "control":
            row_class = "control"
        elif summary.first_hidden_future_beyond_pair_split is not None:
            row_class = "winner"
        elif summary.first_pair_split is not None:
            row_class = "simplex"
        else:
            row_class = "pair"
        lines.append(f'<rect x="{left + 8}" y="{y - 14}" width="{table_width - 16}" height="22" class="{row_class}"/>')
        seed = summary.seed_record
        seed_text = "n/a"
        if seed is not None:
            seed_text = f"{seed.runtime_quotient_count}/{seed.assignment_quotient_count}/{seed.pair_quotient_count}/{seed.simplex_quotient_count}"
        pair_split = "none"
        if summary.first_pair_split is not None:
            pair_split = f"(p={summary.first_pair_split.p},k={summary.first_pair_split.k})"
        hidden_pair = "none"
        if summary.first_hidden_future_beyond_pair_split is not None:
            hidden_pair = f"(p={summary.first_hidden_future_beyond_pair_split.p},k={summary.first_hidden_future_beyond_pair_split.k})"
        status = "flat"
        if summary.first_hidden_future_beyond_pair_split is not None:
            status = "hidden future"
        elif summary.first_pair_split is not None:
            status = "pair split"
        elif summary.first_assignment_split is not None:
            status = "assignment only"
        lines.extend(
            [
                f'<text x="{columns["sem"]}" y="{y}">{summary.label}</text>',
                f'<text x="{columns["cat"]}" y="{y}">{summary.category}</text>',
                f'<text x="{columns["pair"]}" y="{y}">{summary.pair_alphabet_size}</text>',
                f'<text x="{columns["simplex"]}" y="{y}">{summary.simplex_alphabet_size}</text>',
                f'<text x="{columns["seed"]}" y="{y}">{seed_text}</text>',
                f'<text x="{columns["pairsplit"]}" y="{y}">{pair_split}</text>',
                f'<text x="{columns["hiddenpair"]}" y="{y}">{hidden_pair}</text>',
                f'<text x="{columns["gap"]}" y="{y}">{summary.max_pair_curvature_gap:.3f}</text>',
                f'<text x="{columns["rank"]}" y="{y}">{summary.max_pair_holonomy_rank}/{summary.max_simplex_holonomy_rank}</text>',
                f'<text x="{columns["exact"]}" y="{y}">{summary.pair_exact_on_scan}</text>',
                f'<text x="{columns["note"]}" y="{y}">{status}</text>',
            ]
        )
    box_y = top + 448
    lines.append(f'<rect x="{left}" y="{box_y}" width="{table_width}" height="388" class="panel"/>')
    lines.append(f'<text x="{left + 16}" y="{box_y + 24}" class="header">Boundary statement</text>')
    overall_pair = payload["overall_first_pair_split"]
    overall_hidden_pair = payload["overall_first_hidden_future_beyond_pair_split"]
    if overall_pair is None:
        lines.append(f'<text x="{left + 16}" y="{box_y + 54}">No pair-insufficient witness was found on the scanned library.</text>')
    else:
        lines.extend(
            [
                f'<text x="{left + 16}" y="{box_y + 54}">First pair split: {overall_pair["semantics"]} on {tuple(tuple(edge) for edge in overall_pair["family"])}.</text>',
                f'<text x="{left + 16}" y="{box_y + 76}">Counts: runtime {overall_pair["runtime_quotient_count"]}, assignment {overall_pair["assignment_quotient_count"]}, pair {overall_pair["pair_quotient_count"]}, simplex {overall_pair["simplex_quotient_count"]}.</text>',
            ]
        )
        witness = overall_pair["pair_witness"]
        if witness is not None:
            lines.extend(
                [
                    f'<text x="{left + 16}" y="{box_y + 104}">u = {trace_text(tuple(witness["left_trace"]) if witness["left_trace"] else (), tuple(tuple(edge) for edge in overall_pair["family"]))}</text>',
                    f'<text x="{left + 16}" y="{box_y + 126}">v = {trace_text(tuple(witness["right_trace"]) if witness["right_trace"] else (), tuple(tuple(edge) for edge in overall_pair["family"]))}</text>',
                    f'<text x="{left + 16}" y="{box_y + 148}">w = {trace_text(tuple(witness["suffix"]) if witness["suffix"] else (), tuple(tuple(edge) for edge in overall_pair["family"]))}</text>',
                    f'<text x="{left + 16}" y="{box_y + 170}">pair fiber = {witness["summary_value"]}</text>',
                    f'<text x="{left + 16}" y="{box_y + 192}">outputs now: {witness["left_output_now"]} vs {witness["right_output_now"]}</text>',
                ]
            )
    if overall_hidden_pair is None:
        lines.append(f'<text x="{left + 16}" y="{box_y + 236}">No hidden future beyond pair transport was found.</text>')
    else:
        witness = overall_hidden_pair["hidden_future_beyond_pair_witness"]
        lines.extend(
            [
                f'<text x="{left + 16}" y="{box_y + 236}">First hidden future beyond pair: {overall_hidden_pair["semantics"]} on {tuple(tuple(edge) for edge in overall_hidden_pair["family"])}.</text>',
                f'<text x="{left + 16}" y="{box_y + 258}">shared pair fiber = {witness["summary_value"]}</text>',
                f'<text x="{left + 16}" y="{box_y + 280}">shared current output = {witness["left_output_now"]}</text>',
                f'<text x="{left + 16}" y="{box_y + 302}">future outputs after non-empty w: {witness["left_output_future"]} vs {witness["right_output_future"]}</text>',
            ]
        )
    lines.extend(
        [
            f'<text x="{left + 16}" y="{box_y + 338}">Controls: broadcast stays flat; committed allocation keeps assignment and pair exact; pair-only laws break assignment but not pair summary.</text>',
            f'<text x="{left + 16}" y="{box_y + 360}">If the first winner is positive, the exact runtime object moves from assignment+pair transport to assignment+pair+simplex transport.</text>',
        ]
    )
    lines.append("</svg>")
    return "\n".join(lines)


def build_note(payload: Dict[str, object], summaries: Sequence[SemanticSummary]) -> str | None:
    overall_pair = payload["overall_first_pair_split"]
    overall_hidden_pair = payload["overall_first_hidden_future_beyond_pair_split"]
    if overall_pair is None:
        lines = [
            "# Pairwise Holonomy Sufficiency",
            "",
            "## Thesis",
            "",
            "On the tested local law library and scan range, assignment plus pairwise nerve transport is exact.",
            "",
            "## Boundary",
            "",
            "- No same-assignment-plus-pair continuation split appeared on the scanned families.",
            "- The strongest near-misses remained assignment-level only.",
            "",
            "## Open Seam",
            "",
            "The next exact target remains the first deterministic local law where even assignment plus pair transport fails and 2-simplex transport becomes necessary.",
            "",
        ]
        return "\n".join(lines)
    summary = next(summary for summary in summaries if summary.name == overall_pair["semantics"])
    lines = [
        "# Simplex Holonomy Boundary",
        "",
        "## Thesis",
        "",
        "This search crosses the next boundary: assignment plus pairwise nerve transport is no longer exact.",
        "",
        "## Exact Boundary",
        "",
        f"- First pair-insufficient split: `{overall_pair['semantics']}` on `{tuple(tuple(edge) for edge in overall_pair['family'])}`.",
        f"- Token sizes: `|Sigma_pair| = {summary.pair_alphabet_size}` and `|Sigma_simplex| = {summary.simplex_alphabet_size}`.",
        f"- Counts: runtime `{overall_pair['runtime_quotient_count']}`, pair `{overall_pair['pair_quotient_count']}`, simplex `{overall_pair['simplex_quotient_count']}`.",
        f"- Pair gap: `{overall_pair['pair_curvature_gap']:.3f}` bits.",
        "",
        "So the current exact runtime object on the scanned library is no longer assignment plus pair transport. It is assignment plus pair plus simplex transport.",
    ]
    if overall_hidden_pair is not None:
        lines.extend(
            [
                "",
                "## Hidden Future Beyond Pair",
                "",
                f"- First hidden-future-beyond-pair split: `{overall_hidden_pair['semantics']}` on `{tuple(tuple(edge) for edge in overall_hidden_pair['family'])}`.",
                "- The future can remember a simplex-local transport state that both the pair fiber and the current readout erase.",
            ]
        )
    lines.extend(
        [
            "",
            "## Open Seam",
            "",
            "The next exact target is no longer whether pair transport can fail. It is whether assignment plus pair plus simplex transport is already final, or whether a deterministic local law can force genuinely more global holonomy beyond the 2-simplex layer.",
            "",
        ]
    )
    return "\n".join(lines)


def select_promising_semantics(
    semantics: Sequence[SemanticDefinition],
    summaries: Sequence[SemanticSummary],
) -> Tuple[SemanticDefinition, ...]:
    keep_names: set[str] = set()
    pair_candidates = [summary.first_pair_split for summary in summaries if summary.first_pair_split is not None]
    if pair_candidates:
        pair_candidates.sort(key=lambda record: record_order_key(record, "pair"))
        keep_names.add(pair_candidates[0].semantics)
    hidden_candidates = [
        summary.first_hidden_future_beyond_pair_split
        for summary in summaries
        if summary.first_hidden_future_beyond_pair_split is not None
    ]
    if hidden_candidates:
        hidden_candidates.sort(key=lambda record: record_order_key(record, "hidden_pair"))
        keep_names.add(hidden_candidates[0].semantics)
    return tuple(semantic for semantic in semantics if semantic.name in keep_names)


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    all_records = run_scan(SEMANTICS, p_scan=BASE_P_SCAN, k_max=BASE_K_MAX)
    summaries = [summarize_semantic(semantic, all_records[semantic.name]) for semantic in SEMANTICS]

    promising: List[SemanticDefinition] = []
    dense_scan_triggered = False

    assignment_candidates = [summary.first_assignment_split for summary in summaries if summary.first_assignment_split is not None]
    if assignment_candidates:
        assignment_candidates.sort(key=lambda record: record_order_key(record, "assignment"))
    hidden_assignment_candidates = [summary.first_hidden_future_split for summary in summaries if summary.first_hidden_future_split is not None]
    if hidden_assignment_candidates:
        hidden_assignment_candidates.sort(key=lambda record: record_order_key(record, "hidden_assignment"))
    pair_candidates = [summary.first_pair_split for summary in summaries if summary.first_pair_split is not None]
    if pair_candidates:
        pair_candidates.sort(key=lambda record: record_order_key(record, "pair"))
    hidden_pair_candidates = [
        summary.first_hidden_future_beyond_pair_split
        for summary in summaries
        if summary.first_hidden_future_beyond_pair_split is not None
    ]
    if hidden_pair_candidates:
        hidden_pair_candidates.sort(key=lambda record: record_order_key(record, "hidden_pair"))

    json_path = RESULTS_DIR / "pair_vs_simplex_holonomy_search.json"
    report_path = RESULTS_DIR / "pair_vs_simplex_holonomy_search.md"
    svg_path = RESULTS_DIR / "pair_vs_simplex_holonomy_search.svg"
    positive_note_path = DOCS_DIR / "simplex-holonomy-boundary.md"
    negative_note_path = DOCS_DIR / "pairwise-holonomy-sufficiency.md"

    payload = {
        "scan": {
            "base_p_scan": list(BASE_P_SCAN),
            "base_k_max": BASE_K_MAX,
            "expanded_p_scan": list(EXPANDED_P_SCAN),
            "expanded_k_max": EXPANDED_K_MAX,
            "promising_semantics": [semantic.name for semantic in promising],
            "dense_p_scan": list(DENSE_P_SCAN),
            "dense_k_max": DENSE_K_MAX,
            "dense_scan_triggered": dense_scan_triggered,
            "seed_families": {name: [list(edge) for edge in family] for name, family in SEED_FAMILIES.items()},
            "semantics": [semantic.name for semantic in SEMANTICS],
            "canonical_first_order": [
                "p",
                "k",
                "family_count",
                "pair_alphabet_size",
                "simplex_alphabet_size",
                "reachable_state_count",
                "witness_length",
                "family",
                "semantics",
            ],
        },
        "semantics": [summary_to_json(summary) for summary in summaries],
        "records": {
            semantic.name: [record_to_json(record) for record in all_records[semantic.name]]
            for semantic in SEMANTICS
        },
        "overall_first_assignment_split": None if not assignment_candidates else record_to_json(assignment_candidates[0]),
        "overall_first_hidden_future_split": None if not hidden_assignment_candidates else record_to_json(hidden_assignment_candidates[0]),
        "overall_first_pair_split": None if not pair_candidates else record_to_json(pair_candidates[0]),
        "overall_first_hidden_future_beyond_pair_split": None if not hidden_pair_candidates else record_to_json(hidden_pair_candidates[0]),
    }
    json_path.write_text(json.dumps(payload, indent=2))

    note_text = build_note(payload, summaries)
    if pair_candidates:
        positive_note_path.write_text(note_text or "")
        if negative_note_path.exists():
            negative_note_path.unlink()
        note_path: Path | None = positive_note_path
    else:
        negative_note_path.write_text(note_text or "")
        if positive_note_path.exists():
            positive_note_path.unlink()
        note_path = negative_note_path

    report_path.write_text(build_report(summaries, payload, note_path, json_path, svg_path))
    svg_path.write_text(render_svg(summaries, payload))

    print(f"Wrote {report_path}")
    print(f"Wrote {json_path}")
    print(f"Wrote {svg_path}")
    if note_path is not None:
        print(f"Wrote {note_path}")


if __name__ == "__main__":
    main()

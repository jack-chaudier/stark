#!/usr/bin/env python3
"""Quick exact boundary push with a committed resource carrier.

This experiment changes the witness physics, not only the readout.

Carrier:
    each variable can be committed to at most one incident family edge.

Composition:
    segments compose only on disjoint variable domains; incompatible overlaps
    are marked `NA` in the continuation table rather than collapsed into a
    synthetic conflict state.

Question:
    when commitment moves into the carrier, does overlap become visible in the
    runtime quotient itself?
"""

from __future__ import annotations

import json
import math
import sys
from collections import defaultdict
from dataclasses import dataclass
from itertools import combinations, product
from pathlib import Path
from typing import DefaultDict, Dict, Iterable, List, Sequence, Tuple

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "README.md").exists())
SCRIPTS_ROOT = ROOT / "scripts"
for candidate in [SCRIPTS_ROOT] + sorted(path for path in SCRIPTS_ROOT.iterdir() if path.is_dir()):
    candidate_str = str(candidate)
    if candidate_str not in sys.path:
        sys.path.insert(0, candidate_str)

from runtime_collapse_boundary import enumerate_exact_antichains, log2_count

RESULTS_DIR = ROOT / "results" / "runtime-semantics" / "resource-carrier-boundary"

Family = Tuple[Tuple[int, ...], ...]
State = Tuple[int, ...]

P_SCAN = (2, 3, 4)
K_MAX = 3

REPRESENTATIVE_FAMILIES: Dict[str, Family] = {
    "disjoint_pair": ((1, 2), (3,)),
    "overlap_path": ((1, 2), (1, 3)),
    "triangle": ((1, 2), (1, 3), (2, 3)),
    "overlap_star": ((1, 2), (1, 3), (1, 4)),
}


@dataclass(frozen=True)
class FamilyRecord:
    p: int
    k: int
    family: Family
    overlap: bool
    raw_state_count: int
    raw_bits: float
    answer_row_count: int
    answer_bits: float
    variable_row_count: int
    variable_bits: float
    family_row_count: int
    family_bits: float
    family_gap_bits: float
    candidate_exactness: Dict[str, Dict[str, object]]
    counterexample: Dict[str, object] | None


@dataclass(frozen=True)
class GroupRecord:
    p: int
    k: int
    family_count: int
    overlap_family_count: int
    family_gap_count: int
    variable_rows_equal_2_to_p: bool
    family_gap_iff_overlap: bool
    min_family_bits: float
    max_family_bits: float
    max_gap_bits: float
    max_gap_family: Family


def family_union(family: Family) -> Tuple[int, ...]:
    return tuple(sorted(set().union(*map(set, family))))


def overlaps(family: Family) -> bool:
    sets = [set(edge) for edge in family]
    return any(left & right for left, right in combinations(sets, 2))


def incident_choices(family: Family, variable: int) -> Tuple[int, ...]:
    return tuple(index for index, edge in enumerate(family) if variable in edge)


def enumerate_resource_states(family: Family) -> Tuple[State, ...]:
    p = max(family_union(family))
    options = [(-1,) + incident_choices(family, variable) for variable in range(1, p + 1)]
    return tuple(tuple(choice) for choice in product(*options))


def compose_resource(left: State, right: State) -> State | None:
    merged: List[int] = []
    for left_value, right_value in zip(left, right):
        if left_value != -1 and right_value != -1:
            return None
        merged.append(right_value if left_value == -1 else left_value)
    return tuple(merged)


def variable_domain(state: State) -> Tuple[int, ...]:
    return tuple(index + 1 for index, value in enumerate(state) if value != -1)


def residual_profile(state: State, family: Family) -> Family:
    residuals: List[Tuple[int, ...]] = []
    for edge_index, edge in enumerate(family):
        live = True
        remaining: List[int] = []
        for variable in edge:
            assignment = state[variable - 1]
            if assignment == -1:
                remaining.append(variable)
            elif assignment != edge_index:
                live = False
                break
        if live:
            residuals.append(tuple(remaining))
    return tuple(residuals)


def answer_output(state: State, family: Family) -> str:
    profile = residual_profile(state, family)
    return "complete" if any(edge == () for edge in profile) else "incomplete"


def row_signatures(states: Sequence[State], family: Family, projection: str) -> Tuple[Tuple[object, ...], ...]:
    rows: List[Tuple[object, ...]] = []
    for left in states:
        row: List[object] = []
        for right in states:
            merged = compose_resource(left, right)
            if merged is None:
                row.append("NA")
                continue
            if projection == "answer":
                row.append(answer_output(merged, family))
            elif projection == "variable":
                row.append(variable_domain(merged))
            elif projection == "family":
                row.append(residual_profile(merged, family))
            else:
                raise ValueError(f"unknown projection {projection}")
        rows.append(tuple(row))
    return tuple(rows)


def edge_load_vector(state: State, family: Family) -> Tuple[int, ...]:
    return tuple(sum(1 for value in state if value == edge_index) for edge_index in range(len(family)))


def edge_load_multiset(state: State, family: Family) -> Tuple[int, ...]:
    return tuple(sorted(edge_load_vector(state, family)))


def candidate_exactness(states: Sequence[State], family: Family, family_rows: Sequence[Tuple[object, ...]]) -> Dict[str, Dict[str, object]]:
    def domain_only(state: State) -> Tuple[int, ...]:
        return variable_domain(state)

    def domain_size(state: State) -> int:
        return len(variable_domain(state))

    def loads(state: State) -> Tuple[int, ...]:
        return edge_load_vector(state, family)

    def load_multiset(state: State) -> Tuple[int, ...]:
        return edge_load_multiset(state, family)

    def residual(state: State) -> Family:
        return residual_profile(state, family)

    def full_assignment(state: State) -> State:
        return state

    candidates = {
        "domain_only": domain_only,
        "domain_size": domain_size,
        "edge_load_vector": loads,
        "edge_load_multiset": load_multiset,
        "residual_profile": residual,
        "full_assignment": full_assignment,
    }

    results: Dict[str, Dict[str, object]] = {}
    for name, summary_fn in candidates.items():
        grouped: DefaultDict[object, set] = defaultdict(set)
        for state, row in zip(states, family_rows):
            grouped[summary_fn(state)].add(row)
        mixed_classes = sum(1 for rows in grouped.values() if len(rows) > 1)
        results[name] = {
            "summary_count": len(grouped),
            "mixed_classes": mixed_classes,
            "exact": mixed_classes == 0,
        }
    return results


def assignment_to_text(state: State, family: Family) -> str:
    parts: List[str] = []
    for variable, value in enumerate(state, start=1):
        if value == -1:
            continue
        parts.append(f"{variable}->{family[value]}")
    return "{" + ", ".join(parts) + "}" if parts else "{}"


def find_counterexample(states: Sequence[State], family: Family, family_rows: Sequence[Tuple[object, ...]]) -> Dict[str, object] | None:
    groups: DefaultDict[Tuple[int, ...], List[int]] = defaultdict(list)
    for index, state in enumerate(states):
        groups[variable_domain(state)].append(index)

    for domain, indices in sorted(groups.items(), key=lambda item: (len(item[0]), item[0])):
        if len(indices) < 2:
            continue
        for left_offset, left_index in enumerate(indices):
            for right_index in indices[left_offset + 1 :]:
                if family_rows[left_index] == family_rows[right_index]:
                    continue
                differing = [
                    probe_index
                    for probe_index, (left_row, right_row) in enumerate(
                        zip(family_rows[left_index], family_rows[right_index])
                    )
                    if left_row != right_row
                ]
                distinguishing = next(
                    (
                        probe_index
                        for probe_index in differing
                        if assignment_to_text(states[probe_index], family) != "{}"
                    ),
                    differing[0],
                )
                return {
                    "shared_domain": list(domain),
                    "left_state": assignment_to_text(states[left_index], family),
                    "alternate_state": assignment_to_text(states[right_index], family),
                    "future_segment": assignment_to_text(states[distinguishing], family),
                    "left_future_family": family_rows[left_index][distinguishing],
                    "alternate_future_family": family_rows[right_index][distinguishing],
                }
    return None


def analyze_family(family: Family) -> FamilyRecord:
    p = max(family_union(family))
    k = max(len(edge) for edge in family)
    states = enumerate_resource_states(family)
    answer_rows = row_signatures(states, family, "answer")
    variable_rows = row_signatures(states, family, "variable")
    family_rows = row_signatures(states, family, "family")
    exactness = candidate_exactness(states, family, family_rows)
    return FamilyRecord(
        p=p,
        k=k,
        family=family,
        overlap=overlaps(family),
        raw_state_count=len(states),
        raw_bits=log2_count(len(states)),
        answer_row_count=len(set(answer_rows)),
        answer_bits=log2_count(len(set(answer_rows))),
        variable_row_count=len(set(variable_rows)),
        variable_bits=log2_count(len(set(variable_rows))),
        family_row_count=len(set(family_rows)),
        family_bits=log2_count(len(set(family_rows))),
        family_gap_bits=log2_count(len(set(family_rows))) - log2_count(len(set(variable_rows))),
        candidate_exactness=exactness,
        counterexample=find_counterexample(states, family, family_rows),
    )


def group_summary(records: Sequence[FamilyRecord], p: int, k: int) -> GroupRecord:
    overlap_records = [record for record in records if record.overlap]
    max_gap_record = max(records, key=lambda record: record.family_gap_bits)
    return GroupRecord(
        p=p,
        k=k,
        family_count=len(records),
        overlap_family_count=len(overlap_records),
        family_gap_count=sum(1 for record in records if record.family_row_count > record.variable_row_count),
        variable_rows_equal_2_to_p=all(record.variable_row_count == (1 << p) for record in records),
        family_gap_iff_overlap=all((record.family_row_count > record.variable_row_count) == record.overlap for record in records),
        min_family_bits=min(record.family_bits for record in records),
        max_family_bits=max(record.family_bits for record in records),
        max_gap_bits=max(record.family_gap_bits for record in records),
        max_gap_family=max_gap_record.family,
    )


def family_to_json(family: Family) -> List[List[int]]:
    return [list(edge) for edge in family]


def record_to_json(record: FamilyRecord) -> Dict[str, object]:
    return {
        "p": record.p,
        "k": record.k,
        "family": family_to_json(record.family),
        "overlap": record.overlap,
        "raw_state_count": record.raw_state_count,
        "raw_bits": record.raw_bits,
        "answer_row_count": record.answer_row_count,
        "answer_bits": record.answer_bits,
        "variable_row_count": record.variable_row_count,
        "variable_bits": record.variable_bits,
        "family_row_count": record.family_row_count,
        "family_bits": record.family_bits,
        "family_gap_bits": record.family_gap_bits,
        "candidate_exactness": record.candidate_exactness,
        "counterexample": record.counterexample,
    }


def group_to_json(group: GroupRecord) -> Dict[str, object]:
    return {
        "p": group.p,
        "k": group.k,
        "family_count": group.family_count,
        "overlap_family_count": group.overlap_family_count,
        "family_gap_count": group.family_gap_count,
        "variable_rows_equal_2_to_p": group.variable_rows_equal_2_to_p,
        "family_gap_iff_overlap": group.family_gap_iff_overlap,
        "min_family_bits": group.min_family_bits,
        "max_family_bits": group.max_family_bits,
        "max_gap_bits": group.max_gap_bits,
        "max_gap_family": family_to_json(group.max_gap_family),
    }


def format_family(family: Family) -> str:
    return "{" + ", ".join("{" + ",".join(str(item) for item in edge) + "}" for edge in family) + "}"


def render_svg(representatives: Sequence[Tuple[str, FamilyRecord]], groups: Sequence[GroupRecord], smallest: FamilyRecord) -> str:
    width = 1420
    height = 860
    left = 56
    top = 64
    panel_width = 640
    panel_height = 300
    max_bits = max(record.raw_bits for _, record in representatives) + 0.8

    def y(bits: float) -> float:
        usable = panel_height - 48
        return top + 22 + usable * (1 - bits / max_bits)

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<style>",
        "text { font-family: Menlo, Monaco, Consolas, monospace; font-size: 12px; fill: #1f2933; }",
        ".title { font-size: 18px; font-weight: 700; }",
        ".subtitle { fill: #52606d; }",
        ".panel { fill: #ffffff; stroke: #d9e2ec; stroke-width: 1; }",
        ".grid { stroke: #d9e2ec; stroke-width: 1; stroke-dasharray: 4 4; }",
        ".axis { stroke: #9fb3c8; stroke-width: 1; }",
        ".tablehead { font-weight: 700; fill: #102a43; }",
        ".overlap { fill: #eef6ff; }",
        ".disjoint { fill: #f4f7f9; }",
        "</style>",
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#fbfbfd"/>',
        f'<text x="{left}" y="28" class="title">Committed Resource Carrier Boundary</text>',
        f'<text x="{left}" y="48" class="subtitle">Changing the carrier makes overlap visible at runtime: on the scanned grid, family &gt; variable iff the family overlaps.</text>',
        f'<rect x="{left}" y="{top}" width="{panel_width}" height="{panel_height}" class="panel"/>',
        f'<text x="{left + 16}" y="{top + 22}" class="tablehead">Representative families: bits for raw assignment, variable quotient, and family quotient</text>',
    ]

    for tick in range(int(math.ceil(max_bits)) + 1):
        tick_y = y(float(tick))
        lines.append(f'<line x1="{left + 48}" y1="{tick_y:.2f}" x2="{left + panel_width - 22}" y2="{tick_y:.2f}" class="grid"/>')
        lines.append(f'<text x="{left + 14}" y="{tick_y + 4:.2f}">{tick}</text>')

    axis_bottom = top + panel_height - 26
    lines.append(f'<line x1="{left + 48}" y1="{axis_bottom}" x2="{left + panel_width - 22}" y2="{axis_bottom}" class="axis"/>')
    lines.append(f'<line x1="{left + 48}" y1="{top + 20}" x2="{left + 48}" y2="{axis_bottom}" class="axis"/>')

    colors = {
        "raw": "#8d99ae",
        "variable": "#22577a",
        "family": "#0b6e4f",
    }
    group_width = (panel_width - 110) / len(representatives)
    for index, (label, record) in enumerate(representatives):
        base_x = left + 70 + index * group_width
        bar_width = max(18.0, group_width / 5)
        values = {
            "raw": record.raw_bits,
            "variable": record.variable_bits,
            "family": record.family_bits,
        }
        for offset, channel in enumerate(("raw", "variable", "family")):
            bar_x = base_x + offset * (bar_width + 8)
            bar_y = y(values[channel])
            lines.append(
                f'<rect x="{bar_x:.2f}" y="{bar_y:.2f}" width="{bar_width:.2f}" height="{axis_bottom - bar_y:.2f}" fill="{colors[channel]}"/>'
            )
        lines.append(f'<text x="{base_x - 6:.2f}" y="{axis_bottom + 18}">{label}</text>')
        lines.append(f'<text x="{base_x - 6:.2f}" y="{axis_bottom + 32}">{record.variable_bits:.3f}/{record.family_bits:.3f}</text>')

    legend_x = left + panel_width - 160
    for row_index, (channel, label) in enumerate((("raw", "raw"), ("variable", "variable"), ("family", "family"))):
        legend_y = top + 52 + row_index * 18
        lines.append(f'<rect x="{legend_x}" y="{legend_y - 8}" width="10" height="10" fill="{colors[channel]}"/>')
        lines.append(f'<text x="{legend_x + 16}" y="{legend_y}">{label}</text>')

    table_x = left + panel_width + 28
    table_y = top
    table_width = width - table_x - 40
    table_height = 300
    lines.extend(
        [
            f'<rect x="{table_x}" y="{table_y}" width="{table_width}" height="{table_height}" class="panel"/>',
            f'<text x="{table_x + 16}" y="{table_y + 22}" class="tablehead">Scan summary on exact arbitrary antichains</text>',
            f'<text x="{table_x + 16}" y="{table_y + 42}" class="subtitle">Grid: full-union antichains with p ≤ 4 and k ≤ 3.</text>',
        ]
    )
    columns = {
        "group": table_x + 16,
        "count": table_x + 96,
        "overlap": table_x + 180,
        "gap": table_x + 290,
        "max": table_x + 380,
        "law": table_x + 500,
    }
    head_y = table_y + 72
    for key, title in (
        ("group", "group"),
        ("count", "families"),
        ("overlap", "overlap"),
        ("gap", "family>var"),
        ("max", "max gap"),
        ("law", "law"),
    ):
        lines.append(f'<text x="{columns[key]}" y="{head_y}" class="tablehead">{title}</text>')

    for row_index, group in enumerate(groups):
        y_row = head_y + 26 + row_index * 26
        row_class = "overlap" if group.family_gap_count else "disjoint"
        lines.append(f'<rect x="{table_x + 10}" y="{y_row - 14}" width="{table_width - 20}" height="20" class="{row_class}"/>')
        lines.append(f'<text x="{columns["group"]}" y="{y_row}">(p={group.p},k={group.k})</text>')
        lines.append(f'<text x="{columns["count"]}" y="{y_row}">{group.family_count}</text>')
        lines.append(f'<text x="{columns["overlap"]}" y="{y_row}">{group.overlap_family_count}</text>')
        lines.append(f'<text x="{columns["gap"]}" y="{y_row}">{group.family_gap_count}</text>')
        lines.append(f'<text x="{columns["max"]}" y="{y_row}">{group.max_gap_bits:.3f}</text>')
        lines.append(f'<text x="{columns["law"]}" y="{y_row}">overlap iff gap</text>' if group.family_gap_iff_overlap else f'<text x="{columns["law"]}" y="{y_row}">mixed</text>')

    box_y = top + panel_height + 28
    box_height = 360
    lines.extend(
        [
            f'<rect x="{left}" y="{box_y}" width="{width - 2 * left}" height="{box_height}" class="panel"/>',
            f'<text x="{left + 16}" y="{box_y + 22}" class="tablehead">Smallest overlap counterexample and current boundary</text>',
            f'<text x="{left + 16}" y="{box_y + 48}">Smallest family with a runtime family gap: {format_family(smallest.family)} at (p={smallest.p}, k={smallest.k}).</text>',
            f'<text x="{left + 16}" y="{box_y + 68}">Counts: raw={smallest.raw_state_count}, variable={smallest.variable_row_count}, family={smallest.family_row_count}; bits={smallest.raw_bits:.3f}/{smallest.variable_bits:.3f}/{smallest.family_bits:.3f}.</text>',
        ]
    )
    if smallest.counterexample is not None:
        lines.extend(
            [
                f'<text x="{left + 16}" y="{box_y + 98}">Same domain, different future family behavior:</text>',
                f'<text x="{left + 36}" y="{box_y + 122}">domain = {smallest.counterexample["shared_domain"]}</text>',
                f'<text x="{left + 36}" y="{box_y + 144}">left = {smallest.counterexample["left_state"]}</text>',
                f'<text x="{left + 36}" y="{box_y + 166}">alternate = {smallest.counterexample["alternate_state"]}</text>',
                f'<text x="{left + 36}" y="{box_y + 188}">future = {smallest.counterexample["future_segment"]}</text>',
                f'<text x="{left + 36}" y="{box_y + 210}">left future family = {smallest.counterexample["left_future_family"]}</text>',
                f'<text x="{left + 36}" y="{box_y + 232}">alternate future family = {smallest.counterexample["alternate_future_family"]}</text>',
            ]
        )
    lines.extend(
        [
            f'<text x="{left + 16}" y="{box_y + 270}">Tested summaries on this family:</text>',
            f'<text x="{left + 36}" y="{box_y + 292}">domain_only, edge_load_vector, edge_load_multiset, and residual_profile all fail.</text>',
            f'<text x="{left + 36}" y="{box_y + 314}">full_assignment is exact on the scan, so this quick push breaks the old coordinate law but does not yet force a genuinely global non-coordinate state.</text>',
        ]
    )

    lines.append("</svg>")
    return "\n".join(lines)


def build_markdown(records: Sequence[FamilyRecord], groups: Sequence[GroupRecord], representatives: Sequence[Tuple[str, FamilyRecord]], smallest: FamilyRecord, json_path: Path, svg_path: Path) -> str:
    lines = [
        "# Committed Resource Carrier Boundary",
        "",
        "## Question",
        "",
        "This quick experiment changes the witness carrier itself rather than only the readout.",
        "Each variable can be committed to at most one incident family edge, and segments compose only when their domains are disjoint.",
        "The question is whether overlap becomes computationally necessary at runtime the moment witness commitment moves into the carrier.",
        "",
        "## Setup",
        "",
        "- World: exact arbitrary full-union antichains on `[p]` with `p <= 4` and `k <= 3`.",
        "- Carrier state: a partial assignment `variable -> incident family edge`, with `-1` meaning uncommitted.",
        "- Composition: disjoint-domain union; incompatible overlaps are recorded as `NA` in continuation rows.",
        "- Variable channel: committed-variable domain.",
        "- Family channel: residual family profile, i.e. the live edges together with the variables they still need.",
        "- Answer channel: whether some edge is already complete after composition.",
        "",
        "## Main Exact Findings",
        "",
        f"1. The scan covers `{len(records)}` exact full-union antichains on `[p]` with `p <= 4` and `k <= 3`.",
        "   Raw carrier size is exact by construction: `|S_A| = product_v (deg_A(v) + 1)`.",
        f"2. The smallest runtime family gap appears immediately at `{format_family(smallest.family)}` with `(p={smallest.p}, k={smallest.k})`.",
        f"   Counts: raw `{smallest.raw_state_count}`, variable `{smallest.variable_row_count}`, family `{smallest.family_row_count}`.",
        f"   Bits: raw `{smallest.raw_bits:.3f}`, variable `{smallest.variable_bits:.3f}`, family `{smallest.family_bits:.3f}`.",
        "3. On the full scanned grid, the variable quotient still collapses exactly to `2^p`.",
        "4. On the full scanned grid, `family_row_count > variable_row_count` if and only if the family overlaps.",
        "5. The tested coarser summaries all fail on the smallest overlap example: `domain_only`, `edge_load_vector`, `edge_load_multiset`, and `residual_profile`.",
        "6. `full_assignment` is exact on the scan, so this carrier change breaks the old binary-completion coordinate law but does not yet force a genuinely global non-coordinate runtime state.",
        "",
        "## Smallest Counterexample",
        "",
        f"- Family: `{format_family(smallest.family)}`",
        f"- Shared domain: `{smallest.counterexample['shared_domain'] if smallest.counterexample else None}`",
        f"- Left state: `{smallest.counterexample['left_state'] if smallest.counterexample else None}`",
        f"- Alternate state: `{smallest.counterexample['alternate_state'] if smallest.counterexample else None}`",
        f"- Future segment: `{smallest.counterexample['future_segment'] if smallest.counterexample else None}`",
        f"- Left future family: `{smallest.counterexample['left_future_family'] if smallest.counterexample else None}`",
        f"- Alternate future family: `{smallest.counterexample['alternate_future_family'] if smallest.counterexample else None}`",
        "",
        "This is the first place where the old domain-only coordinate summary fails because a shared witness has already been committed to different overlapping families.",
        "",
        "## Representative Families",
        "",
        "| Label | Family | Overlap | Raw states | Variable rows | Family rows | Bits (raw / variable / family) |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]

    for label, record in representatives:
        lines.append(
            f"| `{label}` | `{format_family(record.family)}` | `{record.overlap}` | `{record.raw_state_count}` | `{record.variable_row_count}` | `{record.family_row_count}` | `{record.raw_bits:.3f} / {record.variable_bits:.3f} / {record.family_bits:.3f}` |"
        )

    lines.extend(
        [
            "",
            "## Group Scan Summary",
            "",
            "| Group | Families | Overlap families | Family > variable | Variable rows = 2^p | Gap iff overlap | Max family gap (bits) |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for group in groups:
        lines.append(
            f"| `(p={group.p}, k={group.k})` | `{group.family_count}` | `{group.overlap_family_count}` | `{group.family_gap_count}` | `{group.variable_rows_equal_2_to_p}` | `{group.family_gap_iff_overlap}` | `{group.max_gap_bits:.3f}` |"
        )

    lines.extend(
        [
            "",
            "## Candidate Exactness On The Smallest Overlap Example",
            "",
            "| Candidate summary | Summary count | Mixed classes | Exact |",
            "| --- | --- | --- | --- |",
        ]
    )
    for name, stats in smallest.candidate_exactness.items():
        lines.append(
            f"| `{name}` | `{stats['summary_count']}` | `{stats['mixed_classes']}` | `{stats['exact']}` |"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "This experiment is a real boundary push.",
            "Under binary completion, overlap changed the contract but not the fixed-carrier runtime quotient.",
            "Under committed allocation, overlap becomes visible in the runtime family quotient itself.",
            "The old `2^p` variable collapse survives, but it is no longer sufficient whenever the family overlaps.",
            "",
            "The boundary is still honest:",
            "",
            "- overlap is now computationally active at runtime,",
            "- the old coordinate law is broken,",
            "- but the tested exact runtime state is still captured by the full assignment carrier rather than by a genuinely global hypergraph-only state.",
            "",
            "So this quick push does not yet prove the final runtime-hypergraph theorem.",
            "It does show that changing the carrier is enough to make overlap matter at runtime immediately.",
            "",
            "## Artifacts",
            "",
            f"- JSON: [{json_path.name}]({json_path.name})",
            f"- Figure: [{svg_path.name}]({svg_path.name})",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    all_records: List[FamilyRecord] = []
    grouped: Dict[Tuple[int, int], List[FamilyRecord]] = {}
    for p in P_SCAN:
        for k in range(1, min(K_MAX, p) + 1):
            families = enumerate_exact_antichains(p, k)
            if not families:
                continue
            records = [analyze_family(family) for family in families]
            grouped[(p, k)] = records
            all_records.extend(records)

    groups = [group_summary(grouped[key], *key) for key in sorted(grouped)]
    smallest = min(
        (record for record in all_records if record.family_row_count > record.variable_row_count),
        key=lambda record: (record.p, record.k, len(record.family), record.family),
    )
    representatives = [
        (label, analyze_family(family))
        for label, family in REPRESENTATIVE_FAMILIES.items()
    ]

    json_path = RESULTS_DIR / "resource_carrier_boundary.json"
    svg_path = RESULTS_DIR / "resource_carrier_boundary.svg"
    report_path = RESULTS_DIR / "resource_carrier_boundary.md"

    payload = {
        "scan": {
            "p_scan": list(P_SCAN),
            "k_max": K_MAX,
            "family_count": len(all_records),
            "smallest_counterexample": record_to_json(smallest),
            "group_summaries": [group_to_json(group) for group in groups],
        },
        "representatives": {
            label: record_to_json(record)
            for label, record in representatives
        },
        "observed_laws": {
            "variable_rows_equal_2_to_p_on_scan": all(group.variable_rows_equal_2_to_p for group in groups),
            "family_gap_iff_overlap_on_scan": all(group.family_gap_iff_overlap for group in groups),
        },
    }
    json_path.write_text(json.dumps(payload, indent=2))
    svg_path.write_text(render_svg(representatives, groups, smallest))
    report_path.write_text(build_markdown(all_records, groups, representatives, smallest, json_path, svg_path))
    print(f"Wrote {report_path}")
    print(f"Wrote {json_path}")
    print(f"Wrote {svg_path}")


if __name__ == "__main__":
    main()

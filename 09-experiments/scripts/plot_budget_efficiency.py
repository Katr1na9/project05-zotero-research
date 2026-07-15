#!/usr/bin/env python3
"""Generate the frozen C07-C09 budget-efficiency paper figure and table."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt


DISPLAY = {
    "coverage_greedy": "Coverage",
    "cmi_proxy": "CMI proxy",
    "project05_m1": "M1",
    "project05_m2": "M2",
    "project05_m3a_gap_compat": "M3a",
    "oracle_optimal": "Oracle",
}
COLORS = {
    "coverage_greedy": "#009E73",
    "cmi_proxy": "#56B4E9",
    "project05_m1": "#CC79A7",
    "project05_m2": "#0072B2",
    "project05_m3a_gap_compat": "#D55E00",
    "oracle_optimal": "#222222",
}
MARKERS = {
    "coverage_greedy": "s",
    "cmi_proxy": "D",
    "project05_m1": "v",
    "project05_m2": "o",
    "project05_m3a_gap_compat": "^",
    "oracle_optimal": "X",
}


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def success_rate(rows: list[dict[str, str]]) -> float:
    if not rows:
        return 0.0
    return sum(int(row["reached_target"]) for row in rows) / len(rows)


def _rate(rows: list[dict[str, str]], field: str) -> float:
    if not rows:
        return 0.0
    return sum(int(row[field]) for row in rows) / len(rows)


def write_table(path: Path, rows: list[dict[str, str]]) -> None:
    grouped: dict[tuple[str, float], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        if row["budget_offset"] == "":
            continue
        offset = float(row["budget_offset"])
        if offset in (0.0, 1.0, 2.0):
            grouped[(row["planner"], offset)].append(row)

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "planner",
                "budget_offset",
                "condition_count",
                "success_rate",
                "premature_stop_rate",
                "ceiling_violation_rate",
            ],
        )
        writer.writeheader()
        for planner in DISPLAY:
            for offset in (0.0, 1.0, 2.0):
                group = grouped[(planner, offset)]
                writer.writerow(
                    {
                        "planner": planner,
                        "budget_offset": offset,
                        "condition_count": len(group),
                        "success_rate": f"{success_rate(group):.4f}",
                        "premature_stop_rate": f"{_rate(group, 'premature_stop'):.4f}",
                        "ceiling_violation_rate": f"{_rate(group, 'ceiling_violation'):.4f}",
                    }
                )


def make_figure(rows: list[dict[str, str]], output_stem: Path) -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9,
            "axes.labelsize": 10,
            "axes.titlesize": 10,
            "legend.fontsize": 8,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "axes.linewidth": 0.8,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.15), constrained_layout=True)

    tight: dict[tuple[str, float], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        if row["budget_offset"] != "":
            offset = float(row["budget_offset"])
            if offset in (0.0, 1.0, 2.0):
                tight[(row["planner"], offset)].append(row)

    ax = axes[0]
    for planner in DISPLAY:
        values = [success_rate(tight[(planner, offset)]) for offset in (0.0, 1.0, 2.0)]
        ax.plot(
            (0, 1, 2),
            values,
            label=DISPLAY[planner],
            color=COLORS[planner],
            marker=MARKERS[planner],
            linewidth=1.6,
            markersize=4.5,
            linestyle="--" if planner == "oracle_optimal" else "-",
        )
    ax.set_title("a  Pooled tight-budget performance", loc="left", fontweight="bold")
    ax.set_xlabel("Budget above Oracle minimum, C* + k")
    ax.set_ylabel("Target success rate")
    ax.set_xticks((0, 1, 2))
    ax.set_ylim(-0.02, 1.04)
    ax.grid(axis="y", color="#D9D9D9", linewidth=0.6)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(ncol=2, frameon=False, loc="lower right")

    selected = ["cmi_proxy", "project05_m1", "project05_m2", "project05_m3a_gap_compat"]
    case_ids = sorted({row["case_id"] for row in rows})
    case_labels = [case_id.split("-", 1)[0] for case_id in case_ids]
    by_case: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        if row["budget_offset"] != "" and float(row["budget_offset"]) == 0.0:
            by_case[(row["case_id"], row["planner"])].append(row)

    ax = axes[1]
    width = 0.19
    base = list(range(len(case_ids)))
    for index, planner in enumerate(selected):
        positions = [x + (index - 1.5) * width for x in base]
        values = [success_rate(by_case[(case_id, planner)]) for case_id in case_ids]
        ax.bar(
            positions,
            values,
            width=width,
            label=DISPLAY[planner],
            color=COLORS[planner],
            edgecolor="white",
            linewidth=0.5,
        )
    ax.set_title("b  Case-level success at C*", loc="left", fontweight="bold")
    ax.set_xlabel("Held-out attack case")
    ax.set_ylabel("Target success rate")
    ax.set_xticks(base, case_labels)
    ax.set_ylim(0, 1.04)
    ax.grid(axis="y", color="#D9D9D9", linewidth=0.6)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(ncol=2, frameon=False, loc="upper center", bbox_to_anchor=(0.5, 0.98))

    fig.suptitle(
        "Frozen Oracle-relative budget evaluation (3 independent cases; 135 paired conditions)",
        fontsize=10,
    )
    output_stem.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_stem.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(output_stem.with_suffix(".png"), dpi=300, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--output-stem", type=Path, required=True)
    parser.add_argument("--table", type=Path, required=True)
    args = parser.parse_args()
    rows = read_rows(args.results)
    write_table(args.table, rows)
    make_figure(rows, args.output_stem)


if __name__ == "__main__":
    main()

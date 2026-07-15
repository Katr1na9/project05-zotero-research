from __future__ import annotations

import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = ROOT / "08-writing" / "figures" / "main-v0.4"

COLORS = {
    "m2": "#0F4D92",
    "xgboost": "#42949E",
    "m3a": "#B64342",
    "logistic": "#9A4D8E",
    "coverage": "#9B9B9B",
    "cmi": "#B4C0E4",
    "m1": "#7884B4",
    "oracle": "#272727",
    "depth2": "#8BCF8B",
    "one_step": "#E9A6A1",
    "afa_myopic": "#E69F00",
    "afa_rollout": "#009E73",
    "public": "#DDEAF6",
    "hidden": "#F5DAD7",
    "state": "#DDF3DE",
    "neutral": "#F1F1F1",
}


def configure_style() -> None:
    mpl.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
            "svg.fonttype": "none",
            "svg.hashsalt": "project05-paper-main-v0.3",
            "pdf.fonttype": 42,
            "font.size": 7,
            "axes.titlesize": 8,
            "axes.labelsize": 7,
            "xtick.labelsize": 6.5,
            "ytick.labelsize": 6.5,
            "legend.fontsize": 6.5,
            "axes.spines.right": False,
            "axes.spines.top": False,
            "axes.linewidth": 0.8,
            "legend.frameon": False,
        }
    )


def save_figure(fig: plt.Figure, stem: str) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    base = OUTPUT_DIR / stem
    svg_path = base.with_suffix(".svg")
    fig.savefig(
        svg_path,
        bbox_inches="tight",
        metadata={"Date": "2026-07-11"},
    )
    svg_text = svg_path.read_text(encoding="utf-8")
    svg_path.write_text(
        "\n".join(line.rstrip() for line in svg_text.splitlines()) + "\n",
        encoding="utf-8",
    )
    fig.savefig(base.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(base.with_suffix(".png"), dpi=300, bbox_inches="tight")
    fig.savefig(base.with_suffix(".tiff"), dpi=600, bbox_inches="tight")
    plt.close(fig)


def add_box(
    ax: plt.Axes,
    xy: tuple[float, float],
    width: float,
    height: float,
    text: str,
    facecolor: str,
    edgecolor: str = "#4D4D4D",
    fontsize: float = 7,
) -> FancyBboxPatch:
    box = FancyBboxPatch(
        xy,
        width,
        height,
        boxstyle="round,pad=0.012,rounding_size=0.012",
        linewidth=0.8,
        facecolor=facecolor,
        edgecolor=edgecolor,
    )
    ax.add_patch(box)
    ax.text(
        xy[0] + width / 2,
        xy[1] + height / 2,
        text,
        ha="center",
        va="center",
        fontsize=fontsize,
        linespacing=1.2,
    )
    return box


def add_arrow(
    ax: plt.Axes,
    start: tuple[float, float],
    end: tuple[float, float],
    color: str = "#4D4D4D",
    style: str = "-|>",
    connectionstyle: str = "arc3",
) -> None:
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle=style,
            mutation_scale=8,
            linewidth=0.9,
            color=color,
            connectionstyle=connectionstyle,
        )
    )


def make_method_figure() -> None:
    fig = plt.figure(figsize=(7.2, 4.25), constrained_layout=False)
    gs = fig.add_gridspec(2, 1, height_ratios=[1.2, 1.0], hspace=0.22)

    ax = fig.add_subplot(gs[0])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.text(0.0, 0.98, "a", fontweight="bold", fontsize=9, va="top")

    boxes = [
        (0.03, "Partial CTI-to-local\nevidence alignment", COLORS["neutral"]),
        (0.23, "Evidence-gap state\ncoverage\ncritical gaps\ngranularity | budget", COLORS["state"]),
        (0.46, "Cost-constrained\naction planner", COLORS["public"]),
        (0.65, "Acquisition-channel\nexecution", "#F7E7C6"),
        (0.84, "Support-limited\nresult or STOP", "#E8E0F0"),
    ]
    width = 0.145
    height = 0.36
    for x, label, color in boxes:
        add_box(ax, (x, 0.43), width, height, label, color)
    for x0, x1 in zip([0.03, 0.23, 0.46, 0.65], [0.23, 0.46, 0.65, 0.84]):
        add_arrow(ax, (x0 + width, 0.61), (x1, 0.61))
    add_arrow(
        ax,
        (0.73, 0.42),
        (0.30, 0.41),
        color=COLORS["m2"],
        connectionstyle="arc3,rad=-0.24",
    )
    ax.text(
        0.51,
        0.16,
        "new claims + zero-yield feedback update the state",
        ha="center",
        va="center",
        color=COLORS["m2"],
        fontsize=6.5,
    )
    ax.text(
        0.50,
        0.89,
        "Target reached | budget exhausted | target unreachable",
        ha="center",
        va="center",
        fontsize=6.5,
        color="#4D4D4D",
    )

    ax2 = fig.add_subplot(gs[1])
    ax2.set_xlim(0, 1)
    ax2.set_ylim(0, 1)
    ax2.axis("off")
    ax2.text(0.0, 0.98, "b", fontweight="bold", fontsize=9, va="top")
    ax2.axvline(0.52, ymin=0.12, ymax=0.88, color="#767676", lw=1.0, ls="--")
    ax2.text(0.25, 0.91, "Planner-visible public information", ha="center", fontweight="bold")
    ax2.text(0.76, 0.91, "Executor / Oracle-only hidden information", ha="center", fontweight="bold")

    add_box(ax2, (0.05, 0.52), 0.19, 0.22, "intended CTI nodes", COLORS["public"])
    add_box(ax2, (0.27, 0.52), 0.19, 0.22, "channel + cost", COLORS["public"])
    add_box(ax2, (0.05, 0.20), 0.19, 0.22, "current gaps + budget", COLORS["state"])
    add_box(ax2, (0.27, 0.20), 0.19, 0.22, "past execution feedback", COLORS["state"])

    add_box(ax2, (0.58, 0.52), 0.17, 0.22, "recoverable claims", COLORS["hidden"])
    add_box(ax2, (0.78, 0.52), 0.17, 0.22, "realized channel state", COLORS["hidden"])
    add_box(ax2, (0.68, 0.20), 0.17, 0.22, "Oracle path", COLORS["hidden"])

    ax2.text(
        0.52,
        0.08,
        "Information boundary: intended nodes are annotated independently of realized recovery",
        ha="center",
        va="center",
        fontsize=6.5,
        color="#4D4D4D",
    )
    save_figure(fig, "fig1_method_and_information_boundary")


def aggregate_policy_results(path: Path) -> pd.DataFrame:
    data = pd.read_csv(path)
    data["reached_target"] = pd.to_numeric(data["reached_target"], errors="coerce").fillna(0)
    data["cost_to_target"] = pd.to_numeric(data["cost_to_target"], errors="coerce")
    data["zero_yield_actions"] = pd.to_numeric(data["zero_yield_actions"], errors="coerce").fillna(0)
    rows = []
    for planner, group in data.groupby("planner"):
        success = float(group["reached_target"].mean())
        successful = group[group["reached_target"] == 1]
        mean_cost = (
            float(successful["cost_to_target"].mean())
            if len(successful)
            else float("nan")
        )
        rows.append(
            {
                "planner": planner,
                "success": success,
                "mean_cost": mean_cost,
                "zero_yield": float(group["zero_yield_actions"].mean()),
                "episodes": int(len(group)),
                "cases": int(group["case_id"].nunique()),
            }
        )
    return pd.DataFrame(rows)


def add_real_depth2_result(policy: pd.DataFrame, summary_path: Path) -> pd.DataFrame:
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    depth2 = summary["overall_by_planner"]["project05_depth2_public"]
    row = pd.DataFrame(
        [
            {
                "planner": "project05_depth2_public",
                "success": float(depth2["success_rate"]),
                "mean_cost": float(depth2["mean_cost_to_target"]),
                "zero_yield": float(depth2["mean_zero_yield_actions"]),
                "episodes": int(depth2["repeated_run_count"]),
                "cases": int(depth2["independent_case_count"]),
            }
        ]
    )
    return pd.concat([policy, row], ignore_index=True)


def load_revision_figure_data() -> dict:
    afa_path = (
        ROOT
        / "09-experiments"
        / "results"
        / "afa_voi_c07_c10_v0.1"
        / "afa_voi_policy_summary.json"
    )
    sensitivity_root = ROOT / "09-experiments" / "results" / "m2_sensitivity_v0.1"
    afa_summary = json.loads(afa_path.read_text(encoding="utf-8"))[
        "overall_by_planner"
    ]
    afa = {
        planner: {
            "success": float(afa_summary[planner]["success_rate"]),
            "mean_cost": float(afa_summary[planner]["mean_cost_to_target"]),
        }
        for planner in (
            "oracle_optimal",
            "project05_m2",
            "afa_voi_myopic",
            "afa_voi_rollout_h3",
        )
    }

    weight_comparison = json.loads(
        (sensitivity_root / "m2_weight_comparison.json").read_text(encoding="utf-8")
    )
    weight_groups: dict[tuple[float, float], int] = {}
    for result in weight_comparison.values():
        key = (
            float(result["first_action_agreement_rate"]),
            float(result["mean_cost_difference_vs_base"]),
        )
        weight_groups[key] = weight_groups.get(key, 0) + 1

    dev = json.loads(
        (sensitivity_root / "coverage_semantics_dev_summary.json").read_text(
            encoding="utf-8"
        )
    )
    semantics = {
        name: {
            planner: float(dev[f"{name}_default"][planner]["success_rate"])
            for planner in ("project05_m2", "oracle_optimal")
        }
        for name in ("OR", "AND")
    }
    return {"afa": afa, "weight_groups": weight_groups, "semantics": semantics}


def make_results_figure() -> None:
    budget_path = ROOT / "08-writing" / "table-budget-efficiency-c07-c09.csv"
    policy_path = (
        ROOT
        / "09-experiments"
        / "results"
        / "xgboost_c01_c06_train_c07_c10_test"
        / "xgboost_policy_results.csv"
    )
    gate_path = (
        ROOT
        / "09-experiments"
        / "results"
        / "nonmyopic_dqn_gate_v0.1"
        / "nonmyopic_gate_summary.json"
    )
    real_depth2_path = (
        ROOT
        / "09-experiments"
        / "results"
        / "nonmyopic_real_v0.1"
        / "nonmyopic_policy_summary.json"
    )

    budget = pd.read_csv(budget_path)
    policy = add_real_depth2_result(
        aggregate_policy_results(policy_path), real_depth2_path
    )
    gate = json.loads(gate_path.read_text(encoding="utf-8"))

    fig = plt.figure(figsize=(7.2, 4.65), constrained_layout=False)
    gs = fig.add_gridspec(2, 2, width_ratios=[1.28, 1.0], height_ratios=[1.0, 1.0], hspace=0.48, wspace=0.36)
    ax_a = fig.add_subplot(gs[:, 0])
    ax_b = fig.add_subplot(gs[0, 1])
    ax_c = fig.add_subplot(gs[1, 1])

    planner_style = {
        "project05_m2": ("M2", COLORS["m2"], "o", "-"),
        "project05_m3a_gap_compat": ("M3a", COLORS["m3a"], "s", "-"),
        "coverage_greedy": ("Coverage", COLORS["coverage"], "^", "--"),
        "cmi_proxy": ("CMI proxy", COLORS["cmi"], "D", "--"),
        "project05_m1": ("M1", COLORS["m1"], "v", "--"),
        "oracle_optimal": ("Oracle", COLORS["oracle"], "P", ":"),
    }
    for planner, (label, color, marker, linestyle) in planner_style.items():
        subset = budget[budget["planner"] == planner].sort_values("budget_offset")
        if subset.empty:
            continue
        ax_a.plot(
            subset["budget_offset"],
            subset["success_rate"],
            label=label,
            color=color,
            marker=marker,
            linestyle=linestyle,
            linewidth=1.7 if planner in {"project05_m2", "project05_m3a_gap_compat"} else 1.1,
            markersize=4.2,
        )
    ax_a.set_xticks([0, 1, 2], [r"$C^*$", r"$C^*+1$", r"$C^*+2$"])
    ax_a.set_ylim(0.18, 1.04)
    ax_a.set_ylabel("Success rate")
    ax_a.set_xlabel("Budget relative to Oracle minimum")
    ax_a.set_title("Tight-budget performance (C07-C09)", loc="left", pad=7)
    ax_a.legend(loc="lower right", ncol=2, handlelength=2.0, columnspacing=0.9)
    ax_a.text(
        0.02,
        0.79,
        "3 independent cases; 135 repeated mask conditions",
        transform=ax_a.transAxes,
        fontsize=6,
        color="#4D4D4D",
    )

    policy_map = {
        "oracle_optimal": ("Oracle", COLORS["oracle"], "P"),
        "project05_m2": ("M2", COLORS["m2"], "o"),
        "project05_depth2_public": ("Depth-2 public", COLORS["depth2"], "X"),
        "project05_xgboost_policy": ("XGBoost", COLORS["xgboost"], "s"),
        "project05_m3b_policy": ("Logistic", COLORS["logistic"], "D"),
        "project05_m3a_gap_compat": ("M3a", COLORS["m3a"], "^"),
        "coverage_greedy": ("Coverage", COLORS["coverage"], "v"),
    }
    label_offsets = {
        "Oracle": (4, 3),
        "M2": (4, -14),
        "Depth-2 public": (-60, 9),
        "XGBoost": (5, 9),
        "Logistic": (4, -9),
        "M3a": (4, 3),
        "Coverage": (-43, 3),
    }
    for _, row in policy.iterrows():
        if row["planner"] not in policy_map:
            continue
        label, color, marker = policy_map[row["planner"]]
        size = 32 + 24 * row["zero_yield"]
        ax_b.scatter(
            row["mean_cost"],
            row["success"],
            s=size,
            color=color,
            marker=marker,
            edgecolor="white",
            linewidth=0.7,
            zorder=3,
        )
        dx, dy = label_offsets[label]
        ax_b.annotate(label, (row["mean_cost"], row["success"]), xytext=(dx, dy), textcoords="offset points", fontsize=6.1)
    ax_b.set_xlim(3.65, 6.18)
    ax_b.set_ylim(0.87, 1.015)
    ax_b.set_xlabel("Mean cost on successful episodes")
    ax_b.set_ylabel("Success rate")
    ax_b.set_title("Sequential holdout results (C07-C10)", loc="left", pad=7)
    ax_b.text(
        0.02,
        0.04,
        "4 independent cases; marker size = zero-yield",
        transform=ax_b.transAxes,
        fontsize=5.8,
        color="#4D4D4D",
    )

    gate_order = ["one_step_gain_cost", "project05_m2", "depth2_m2", "dp_oracle"]
    gate_labels = ["One-step", "M2", "Depth-2", "DP"]
    gate_colors = [COLORS["one_step"], COLORS["m2"], COLORS["depth2"], COLORS["oracle"]]
    gate_values = [gate["overall_by_planner"][name]["success_rate"] for name in gate_order]
    bars = ax_c.bar(np.arange(4), gate_values, color=gate_colors, edgecolor="white", linewidth=0.6, width=0.72)
    for bar, value in zip(bars, gate_values):
        ax_c.text(bar.get_x() + bar.get_width() / 2, value + 0.025, f"{value:.2f}", ha="center", va="bottom", fontsize=6.2)
    ax_c.set_xticks(np.arange(4), gate_labels)
    ax_c.set_ylim(0, 0.86)
    ax_c.set_ylabel("Success rate")
    ax_c.set_title("Controlled nonmyopic diagnostic", loc="left", pad=7)
    ax_c.text(
        0.02,
        0.94,
        "Gate A: PASS   Gate B: FAIL",
        transform=ax_c.transAxes,
        fontsize=6.4,
        fontweight="bold",
        color="#272727",
        va="top",
    )
    ax_c.text(
        0.02,
        0.80,
        "192 independent environments; 10 seeds each",
        transform=ax_c.transAxes,
        fontsize=5.8,
        color="#4D4D4D",
        va="top",
    )

    for label, ax in zip(["a", "b", "c"], [ax_a, ax_b, ax_c]):
        ax.text(-0.14, 1.07, label, transform=ax.transAxes, fontweight="bold", fontsize=9, va="top")

    save_figure(fig, "fig2_holdout_and_nonmyopic_results")


def make_revision_figure() -> None:
    data = load_revision_figure_data()
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.55), constrained_layout=False)
    fig.subplots_adjust(left=0.075, right=0.99, bottom=0.24, top=0.83, wspace=0.48)
    ax_a, ax_b, ax_c = axes

    planners = [
        ("oracle_optimal", "Oracle", COLORS["oracle"]),
        ("project05_m2", "M2", COLORS["m2"]),
        ("afa_voi_myopic", "AFA-M", COLORS["afa_myopic"]),
        ("afa_voi_rollout_h3", "AFA-H3", COLORS["afa_rollout"]),
    ]
    costs = [data["afa"][planner]["mean_cost"] for planner, _, _ in planners]
    bars = ax_a.bar(
        np.arange(len(planners)),
        costs,
        color=[color for _, _, color in planners],
        width=0.72,
        edgecolor="white",
        linewidth=0.6,
    )
    for bar, value in zip(bars, costs):
        ax_a.text(
            bar.get_x() + bar.get_width() / 2,
            value + 0.08,
            f"{value:.2f}",
            ha="center",
            va="bottom",
            fontsize=6.2,
        )
    ax_a.set_xticks(np.arange(len(planners)), [label for _, label, _ in planners])
    ax_a.set_ylim(0, 5.55)
    ax_a.set_ylabel("Mean cost on successful episodes")
    ax_a.set_xlabel("All strategies: success = 1.00; n cases = 4")
    ax_a.set_title("AFA adapters on C07-C10", loc="left", pad=7)

    for (agreement, cost_delta), count in sorted(data["weight_groups"].items()):
        ax_b.scatter(
            agreement,
            cost_delta,
            s=42 + 8 * count,
            color=COLORS["m2"],
            alpha=0.78,
            edgecolor="white",
            linewidth=0.7,
        )
        ax_b.annotate(
            f"{count} variants",
            (agreement, cost_delta),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=6.0,
        )
    ax_b.axhline(0, color="#9B9B9B", linewidth=0.8, linestyle="--")
    ax_b.set_xlim(0.84, 1.025)
    ax_b.set_ylim(-0.004, 0.032)
    ax_b.set_xlabel("First-action agreement with M2")
    ax_b.set_ylabel(r"Mean cost difference ($\Delta$)")
    ax_b.set_title("One-weight sensitivity", loc="left", pad=7)
    ax_b.text(
        0.02,
        0.91,
        "16 preregistered ±25% variants",
        transform=ax_b.transAxes,
        fontsize=5.6,
        color="#4D4D4D",
        va="top",
    )

    methods = ["project05_m2", "oracle_optimal"]
    method_labels = ["M2", "Oracle"]
    x = np.arange(len(methods))
    width = 0.34
    for index, (semantics, color) in enumerate(
        (("OR", COLORS["m2"]), ("AND", COLORS["afa_myopic"]))
    ):
        values = [data["semantics"][semantics][method] for method in methods]
        offset = (-0.5 if index == 0 else 0.5) * width
        bars = ax_c.bar(
            x + offset,
            values,
            width,
            label=semantics,
            color=color,
            edgecolor="white",
            linewidth=0.6,
        )
        for bar, value in zip(bars, values):
            ax_c.text(
                bar.get_x() + bar.get_width() / 2,
                value + 0.025,
                f"{value:.2f}",
                ha="center",
                va="bottom",
                fontsize=5.8,
            )
    ax_c.set_xticks(x, method_labels)
    ax_c.set_ylim(0, 1.12)
    ax_c.set_ylabel("Success rate")
    ax_c.set_xlabel("Development only; holdout OR = AND")
    ax_c.set_title("Coverage semantics (C01-C06)", loc="left", pad=7)
    ax_c.legend(loc="lower right", ncol=2, handlelength=1.2)

    for label, ax in zip(("a", "b", "c"), axes):
        ax.text(
            -0.18,
            1.11,
            label,
            transform=ax.transAxes,
            fontweight="bold",
            fontsize=9,
            va="top",
        )
    save_figure(fig, "fig3_afa_and_sensitivity")


def main() -> None:
    configure_style()
    make_method_figure()
    make_results_figure()
    make_revision_figure()


if __name__ == "__main__":
    main()

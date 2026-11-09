from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "analysis"
FIGURES = ROOT / "figures"
FIGURES.mkdir(exist_ok=True)

FACTOR_ORDER = [
    "Aggressive tone",
    "Polite tone",
    "Role framing",
    "JSON wrapper",
    "XML wrapper",
]


def read_rows(filename: str) -> list[dict[str, str]]:
    path = ANALYSIS / filename
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def save_pipeline() -> None:
    fig, ax = plt.subplots(figsize=(5.8, 4.4))
    ax.set_axis_off()
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    boxes = [
        ("Task sources\n50 code tasks + 50 math tasks", 0.78),
        ("Prompt matrix\n18 variants: 3 tones x 2 roles x 3 wrappers", 0.61),
        ("Model execution\n6 local Ollama models + 2 API models", 0.44),
        ("Extraction and evaluation\nPython tests / numeric final answers", 0.27),
        ("Analysis\npass@1, tokens, duration\ncompliance, failures", 0.10),
    ]

    x = 0.18
    width = 0.64
    height = 0.11
    for label, y in boxes:
        box = FancyBboxPatch(
            (x, y),
            width,
            height,
            boxstyle="round,pad=0.02,rounding_size=0.025",
            linewidth=1.25,
            edgecolor="#263238",
            facecolor="#eef3f7",
        )
        ax.add_patch(box)
        ax.text(x + width / 2, y + height / 2, label, ha="center", va="center", fontsize=9.6, color="#111827")

    for (_, y1), (_, y2) in zip(boxes[:-1], boxes[1:]):
        arrow = FancyArrowPatch(
            (x + width / 2, y1 - 0.012),
            (x + width / 2, y2 + height + 0.012),
            arrowstyle="-|>",
            mutation_scale=12,
            linewidth=1.2,
            color="#455a64",
        )
        ax.add_patch(arrow)

    ax.text(
        0.5,
        0.02,
        "Each base task is evaluated under every prompt variant; empty responses and errors remain in the factorial dataset.",
        ha="center",
        va="center",
        fontsize=8.4,
        color="#374151",
    )

    fig.savefig(FIGURES / "experimental_pipeline.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def save_model_performance() -> None:
    rows = read_rows("manuscript_model_performance.csv")
    group_order = ["Local code", "Local math", "API Python", "API math"]
    colors = {
        "Local code": "#2f6f9f",
        "Local math": "#8f5f21",
        "API Python": "#2b7a5b",
        "API math": "#7a4f9f",
    }

    fig, axes = plt.subplots(4, 1, figsize=(5.8, 7.8), sharex=True)
    for ax, group_name in zip(axes, group_order):
        group_rows = [row for row in rows if row["task_group"] == group_name]
        group_rows.sort(key=lambda row: float(row["pass_rate_pct"]), reverse=True)
        labels = [row["model_label"] for row in group_rows]
        values = [float(row["pass_rate_pct"]) for row in group_rows]
        positions = range(len(group_rows))

        ax.barh(positions, values, color=colors[group_name], alpha=0.88)
        ax.set_yticks(positions)
        ax.set_yticklabels(labels, fontsize=8.6)
        ax.invert_yaxis()
        ax.set_title(group_name, fontsize=10.5, loc="left", fontweight="bold")
        ax.set_xlim(0, 100)
        ax.grid(axis="x", linestyle=":", linewidth=0.8, alpha=0.45)
        ax.set_axisbelow(True)
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.tick_params(axis="y", length=0)

        for pos, value in zip(positions, values):
            ax.text(value + 1.2, pos, f"{value:.1f}%", va="center", fontsize=8.2, color="#111827")

    axes[-1].set_xlabel("Pass rate", fontsize=9)
    fig.suptitle("Model pass rates by task kind", fontsize=12, fontweight="bold", y=0.995)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(FIGURES / "model_performance_by_task.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


BEHAVIOR_OUTCOME = {
    "log(tokens)": "log_completion_tokens",
    "log(duration)": "log_duration",
    "result_only": "result_only",
}


def _behavior_bars(fig, axes, metric_order, metric_labels, colors, xlabel, xlim):
    rows = read_rows("mixed_effects_behavior.csv")
    lookup = {
        (row["stratum"], row["outcome"], row["contrast"]): row for row in rows
    }
    group_order = ["Local code", "Local math"]
    y_positions = list(range(len(FACTOR_ORDER)))
    bar_height = 0.8 / max(len(metric_order), 1) / 1.25
    offsets = [
        (i - (len(metric_order) - 1) / 2) * bar_height * 1.25
        for i in range(len(metric_order))
    ]

    for ax, group_name in zip(axes, group_order):
        for metric, offset in zip(metric_order, offsets):
            label = metric_labels[metric]
            outcome = BEHAVIOR_OUTCOME[metric]
            values, lo_err, hi_err = [], [], []
            for factor_label in FACTOR_ORDER:
                row = lookup[(group_name, outcome, factor_label)]
                value = float(row["effect_approx"])
                lo = float(row["ci_lo"])
                hi = float(row["ci_hi"])
                values.append(value)
                lo_err.append(value - lo)
                hi_err.append(hi - value)
            positions = [y + offset for y in y_positions]
            ax.barh(positions, values, height=bar_height, color=colors[label], alpha=0.88, label=label)
            ax.errorbar(
                values,
                positions,
                xerr=[lo_err, hi_err],
                fmt="none",
                ecolor="#374151",
                elinewidth=0.9,
                capsize=2.2,
                capthick=0.9,
                zorder=4,
            )
            for pos, value, lo_e, hi_e in zip(positions, values, lo_err, hi_err):
                if value >= 0:
                    x, ha = value + hi_e + 0.45, "left"
                else:
                    x, ha = value - lo_e - 0.45, "right"
                ax.text(x, pos, f"{value:+.1f}", va="center", ha=ha, fontsize=6.9, color="#111827")

        ax.axvline(0, color="#111827", linewidth=0.8)
        ax.set_yticks(y_positions)
        ax.set_yticklabels(FACTOR_ORDER, fontsize=8.8)
        ax.invert_yaxis()
        ax.set_title(f"{group_name}", fontsize=10.5, loc="left", fontweight="bold")
        ax.grid(axis="x", linestyle=":", linewidth=0.8, alpha=0.45)
        ax.set_axisbelow(True)
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.tick_params(axis="y", length=0)

    axes[-1].set_xlim(*xlim)
    axes[-1].set_xlabel(xlabel, fontsize=8.8)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 0.955), fontsize=8, frameon=False, ncol=len(metric_order))
    fig.tight_layout(rect=(0, 0, 1, 0.91))


def save_behavior_effects_tokens_duration() -> None:
    """Figure 3a: token and duration effects, both in percent."""
    fig, axes = plt.subplots(2, 1, figsize=(6.4, 5.6), sharex=True)
    _behavior_bars(
        fig,
        axes,
        ["log(tokens)", "log(duration)"],
        {"log(tokens)": "Token effect (%)", "log(duration)": "Duration effect (%)"},
        {"Token effect (%)": "#2f6f9f", "Duration effect (%)": "#8f5f21"},
        "Effect on completion tokens / duration, percent",
        (-28, 19),
    )
    fig.savefig(FIGURES / "behavior_effects_tokens_duration.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def save_behavior_effects_compliance() -> None:
    """Figure 3b: result-only compliance effects, in percentage points."""
    fig, axes = plt.subplots(2, 1, figsize=(6.4, 4.4), sharex=True)
    _behavior_bars(
        fig,
        axes,
        ["result_only"],
        {"result_only": "Result-only effect (pp)"},
        {"Result-only effect (pp)": "#7a4f9f"},
        "Effect on result-only compliance, percentage points",
        (-10.5, 10.5),
    )
    fig.savefig(FIGURES / "behavior_effects_compliance.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def save_mediation_controls() -> None:
    rows = read_rows("manuscript_mediation_decomposition.csv")
    group_order = ["Local code", "Local math"]

    fig, axes = plt.subplots(2, 1, figsize=(6.2, 5.9), sharex=True)
    y_positions = list(range(len(FACTOR_ORDER)))

    for ax, group_name in zip(axes, group_order):
        total = []
        controlled = []
        for factor_label in FACTOR_ORDER:
            row = [item for item in rows if item["task_group"] == group_name and item["factor_label"] == factor_label][0]
            total.append(float(row["total_pp"]))
            controlled.append(float(row["+all3_pp"]))

        for y, before, after in zip(y_positions, total, controlled):
            ax.plot([before, after], [y, y], color="#9ca3af", linewidth=1.5, zorder=1)

        ax.scatter(total, y_positions, color="#2f6f9f", s=34, label="Total effect", zorder=2)
        ax.scatter(controlled, y_positions, color="#8f5f21", s=34, label="After behavior controls", zorder=3)
        ax.axvline(0, color="#111827", linewidth=0.8)
        ax.set_yticks(y_positions)
        ax.set_yticklabels(FACTOR_ORDER, fontsize=8.8)
        ax.invert_yaxis()
        ax.set_title(group_name, fontsize=10.5, loc="left", fontweight="bold")
        ax.grid(axis="x", linestyle=":", linewidth=0.8, alpha=0.45)
        ax.set_axisbelow(True)
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.tick_params(axis="y", length=0)

    axes[-1].set_xlim(-5, 3)
    axes[-1].set_xlabel("Pass-rate effect, percentage points", fontsize=8.8)
    fig.suptitle(
        "Prompt-factor correctness effects before and after behavioral controls",
        fontsize=11.0,
        fontweight="bold",
        y=0.995,
    )
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 0.948), fontsize=8, frameon=False, ncol=2)
    fig.tight_layout(rect=(0, 0, 1, 0.90))
    fig.savefig(FIGURES / "mediation_controls.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    save_pipeline()
    save_model_performance()
    save_behavior_effects_tokens_duration()
    save_behavior_effects_compliance()
    save_mediation_controls()

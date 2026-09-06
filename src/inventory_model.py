"""Stochastic (s, S) inventory model with simulation and Markov-chain analysis.

The model describes a single-product retailer with periodic review, zero supplier
lead time, lost sales, and discrete independent daily demand.  The program is
deliberately self-contained: it runs with only NumPy and pandas and exports all
tables and figures used by the GitHub report.

Run from the repository root:
    python3 src/inventory_model.py
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, replace
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "outputs"
FIGURE_DIR = OUTPUT_DIR / "figures"


@dataclass(frozen=True)
class Policy:
    """An (s, S) policy: order to S whenever opening inventory is at most s."""

    reorder_point: int
    order_up_to: int

    def validate(self) -> None:
        if self.reorder_point < 0:
            raise ValueError("The reorder point must be non-negative.")
        if self.order_up_to <= self.reorder_point:
            raise ValueError("The order-up-to level must be strictly larger than s.")


@dataclass(frozen=True)
class CostParameters:
    """Daily inventory cost assumptions, measured in arbitrary currency units."""

    order_fixed_cost: float = 30.0
    order_unit_cost: float = 2.0
    holding_cost: float = 1.0
    shortage_cost: float = 8.0

    def validate(self) -> None:
        if any(value < 0 for value in asdict(self).values()):
            raise ValueError("All cost parameters must be non-negative.")


@dataclass(frozen=True)
class DemandScenario:
    """A finite discrete demand distribution for a single day."""

    name: str
    values: tuple[int, ...]
    probabilities: tuple[float, ...]

    def arrays(self) -> tuple[np.ndarray, np.ndarray]:
        values = np.asarray(self.values, dtype=int)
        probabilities = np.asarray(self.probabilities, dtype=float)
        if len(values) == 0 or len(values) != len(probabilities):
            raise ValueError("Demand values and probabilities must have equal non-zero length.")
        if np.any(values < 0) or np.any(probabilities < 0):
            raise ValueError("Demand values and probabilities must be non-negative.")
        if not np.isclose(probabilities.sum(), 1.0):
            raise ValueError("Demand probabilities must sum to one.")
        return values, probabilities


BASELINE_DEMAND = DemandScenario(
    name="baseline_discrete_demand",
    values=(0, 1, 2, 3, 4, 5, 6),
    probabilities=(0.05, 0.10, 0.20, 0.25, 0.20, 0.12, 0.08),
)
BASELINE_COSTS = CostParameters()


def replenish(opening_inventory: int, policy: Policy) -> tuple[int, int]:
    """Return available inventory and order quantity after the policy decision."""

    if opening_inventory <= policy.reorder_point:
        order_quantity = policy.order_up_to - opening_inventory
        return policy.order_up_to, order_quantity
    return opening_inventory, 0


def daily_outcome(
    opening_inventory: int,
    demand: int,
    policy: Policy,
    costs: CostParameters,
) -> dict[str, float]:
    """Calculate one period of inventory movement and all cost components."""

    available_inventory, order_quantity = replenish(opening_inventory, policy)
    sales = min(available_inventory, demand)
    shortage = max(demand - available_inventory, 0)
    ending_inventory = available_inventory - sales
    order_cost = (
        costs.order_fixed_cost + costs.order_unit_cost * order_quantity
        if order_quantity > 0
        else 0.0
    )
    holding_cost = costs.holding_cost * ending_inventory
    shortage_cost = costs.shortage_cost * shortage

    return {
        "available_inventory": available_inventory,
        "order_quantity": order_quantity,
        "sales": sales,
        "ending_inventory": ending_inventory,
        "shortage": shortage,
        "order_cost": order_cost,
        "holding_cost": holding_cost,
        "shortage_cost": shortage_cost,
        "total_cost": order_cost + holding_cost + shortage_cost,
    }


def simulate_policy(
    policy: Policy,
    periods: int = 365,
    starting_inventory: int | None = None,
    demand_scenario: DemandScenario = BASELINE_DEMAND,
    costs: CostParameters = BASELINE_COSTS,
    seed: int = 42,
) -> pd.DataFrame:
    """Simulate daily operations under an (s, S) policy with a fixed random seed."""

    policy.validate()
    costs.validate()
    demand_values, demand_probabilities = demand_scenario.arrays()
    if periods <= 0:
        raise ValueError("The number of periods must be positive.")

    inventory = policy.order_up_to if starting_inventory is None else starting_inventory
    if inventory < 0:
        raise ValueError("Starting inventory must be non-negative.")

    rng = np.random.default_rng(seed)
    records: list[dict[str, float]] = []
    for day in range(1, periods + 1):
        opening_inventory = inventory
        demand = int(rng.choice(demand_values, p=demand_probabilities))
        outcome = daily_outcome(opening_inventory, demand, policy, costs)
        inventory = int(outcome["ending_inventory"])
        records.append({"day": day, "opening_inventory": opening_inventory, "demand": demand, **outcome})

    return pd.DataFrame.from_records(records)


def trace_metrics(trace: pd.DataFrame) -> dict[str, float]:
    """Summarise one simulation trace using business-facing performance metrics."""

    return {
        "average_daily_cost": float(trace["total_cost"].mean()),
        "stockout_rate": float((trace["shortage"] > 0).mean()),
        "fill_rate": float(trace["sales"].sum() / trace["demand"].sum()) if trace["demand"].sum() else 1.0,
        "average_ending_inventory": float(trace["ending_inventory"].mean()),
        "average_order_quantity": float(trace["order_quantity"].mean()),
        "order_frequency": float((trace["order_quantity"] > 0).mean()),
    }


def build_transition_matrix(policy: Policy, demand_scenario: DemandScenario = BASELINE_DEMAND) -> np.ndarray:
    """Build the Markov transition matrix for opening inventory states 0, ..., S.

    With a fixed policy, tomorrow's opening inventory depends only on today's
    opening inventory and the random demand realization.  The state process is
    therefore a finite Markov chain.
    """

    policy.validate()
    demand_values, demand_probabilities = demand_scenario.arrays()
    transition = np.zeros((policy.order_up_to + 1, policy.order_up_to + 1))

    for state in range(policy.order_up_to + 1):
        available_inventory, _ = replenish(state, policy)
        for demand, probability in zip(demand_values, demand_probabilities, strict=True):
            next_state = max(available_inventory - int(demand), 0)
            transition[state, next_state] += probability

    return transition


def stationary_distribution(
    transition: np.ndarray,
    tolerance: float = 1e-14,
    max_iterations: int = 100_000,
) -> np.ndarray:
    """Find the stationary state probabilities by power iteration."""

    if transition.ndim != 2 or transition.shape[0] != transition.shape[1]:
        raise ValueError("The transition matrix must be square.")
    if not np.allclose(transition.sum(axis=1), 1.0):
        raise ValueError("Each transition-matrix row must sum to one.")

    distribution = np.full(transition.shape[0], 1 / transition.shape[0])
    for _ in range(max_iterations):
        next_distribution = distribution @ transition
        if np.max(np.abs(next_distribution - distribution)) < tolerance:
            return next_distribution
        distribution = next_distribution
    raise RuntimeError("Stationary distribution did not converge.")


def markov_policy_metrics(
    policy: Policy,
    demand_scenario: DemandScenario = BASELINE_DEMAND,
    costs: CostParameters = BASELINE_COSTS,
) -> dict[str, float]:
    """Compute exact long-run metrics from the finite Markov-chain model."""

    policy.validate()
    costs.validate()
    demand_values, demand_probabilities = demand_scenario.arrays()
    distribution = stationary_distribution(build_transition_matrix(policy, demand_scenario))

    expected_cost = 0.0
    expected_stockout = 0.0
    expected_demand = 0.0
    expected_sales = 0.0
    expected_ending_inventory = 0.0
    expected_order_quantity = 0.0
    expected_order_frequency = 0.0

    for state, state_probability in enumerate(distribution):
        available_inventory, order_quantity = replenish(state, policy)
        order_cost = (
            costs.order_fixed_cost + costs.order_unit_cost * order_quantity
            if order_quantity > 0
            else 0.0
        )
        expected_order_quantity += state_probability * order_quantity
        expected_order_frequency += state_probability * float(order_quantity > 0)

        for demand, demand_probability in zip(demand_values, demand_probabilities, strict=True):
            sales = min(available_inventory, int(demand))
            shortage = max(int(demand) - available_inventory, 0)
            ending_inventory = available_inventory - sales
            probability = state_probability * demand_probability
            expected_cost += probability * (
                order_cost + costs.holding_cost * ending_inventory + costs.shortage_cost * shortage
            )
            expected_stockout += probability * float(shortage > 0)
            expected_demand += probability * demand
            expected_sales += probability * sales
            expected_ending_inventory += probability * ending_inventory

    return {
        "average_daily_cost": expected_cost,
        "stockout_rate": expected_stockout,
        "fill_rate": expected_sales / expected_demand if expected_demand else 1.0,
        "average_ending_inventory": expected_ending_inventory,
        "average_order_quantity": expected_order_quantity,
        "order_frequency": expected_order_frequency,
    }


def _mean_and_interval(values: list[float]) -> tuple[float, float, float]:
    """Return a Monte Carlo mean and approximate 95 percent confidence interval."""

    array = np.asarray(values, dtype=float)
    mean = float(array.mean())
    if len(array) < 2:
        return mean, mean, mean
    half_width = 1.96 * float(array.std(ddof=1)) / np.sqrt(len(array))
    return mean, mean - half_width, mean + half_width


def evaluate_policies(
    policies: list[Policy],
    replications: int = 200,
    periods: int = 365,
    demand_scenario: DemandScenario = BASELINE_DEMAND,
    costs: CostParameters = BASELINE_COSTS,
    seed: int = 42,
) -> pd.DataFrame:
    """Compare policies using exact Markov metrics and repeated simulations.

    The same replication seeds are used for every policy.  This common-random-
    numbers design reduces noise when comparing alternatives.
    """

    if replications <= 0:
        raise ValueError("The number of replications must be positive.")

    rows: list[dict[str, float]] = []
    for policy in policies:
        exact = markov_policy_metrics(policy, demand_scenario, costs)
        replication_metrics = [
            trace_metrics(
                simulate_policy(
                    policy=policy,
                    periods=periods,
                    demand_scenario=demand_scenario,
                    costs=costs,
                    seed=seed + replication,
                )
            )
            for replication in range(replications)
        ]
        simulation_cost, cost_ci_low, cost_ci_high = _mean_and_interval(
            [metrics["average_daily_cost"] for metrics in replication_metrics]
        )
        simulation_stockout, stockout_ci_low, stockout_ci_high = _mean_and_interval(
            [metrics["stockout_rate"] for metrics in replication_metrics]
        )

        rows.append(
            {
                "s": policy.reorder_point,
                "S": policy.order_up_to,
                "average_daily_cost": exact["average_daily_cost"],
                "stockout_rate": exact["stockout_rate"],
                "fill_rate": exact["fill_rate"],
                "average_ending_inventory": exact["average_ending_inventory"],
                "average_order_quantity": exact["average_order_quantity"],
                "order_frequency": exact["order_frequency"],
                "simulation_average_daily_cost": simulation_cost,
                "simulation_cost_95_ci_low": cost_ci_low,
                "simulation_cost_95_ci_high": cost_ci_high,
                "simulation_stockout_rate": simulation_stockout,
                "simulation_stockout_95_ci_low": stockout_ci_low,
                "simulation_stockout_95_ci_high": stockout_ci_high,
                "simulation_fill_rate": float(np.mean([metrics["fill_rate"] for metrics in replication_metrics])),
                "simulation_average_ending_inventory": float(
                    np.mean([metrics["average_ending_inventory"] for metrics in replication_metrics])
                ),
                "simulation_average_order_quantity": float(
                    np.mean([metrics["average_order_quantity"] for metrics in replication_metrics])
                ),
                "absolute_cost_gap": abs(simulation_cost - exact["average_daily_cost"]),
            }
        )

    return pd.DataFrame(rows).sort_values("average_daily_cost", ignore_index=True)


def policy_grid(minimum_s: int = 1, maximum_s: int = 6, maximum_S: int = 12) -> list[Policy]:
    """Create the feasible policy set used in the baseline experiment."""

    return [
        Policy(reorder_point=s, order_up_to=S)
        for s in range(minimum_s, maximum_s + 1)
        for S in range(s + 2, maximum_S + 1)
    ]


def sensitivity_analysis(
    policies: list[Policy],
    holding_costs: tuple[float, ...] = (0.5, 1.0, 2.0),
    shortage_costs: tuple[float, ...] = (4.0, 8.0, 16.0),
    base_costs: CostParameters = BASELINE_COSTS,
) -> pd.DataFrame:
    """Find the best policy when holding and shortage penalties change."""

    rows: list[dict[str, float]] = []
    for holding_cost in holding_costs:
        for shortage_cost in shortage_costs:
            costs = replace(base_costs, holding_cost=holding_cost, shortage_cost=shortage_cost)
            results = [
                {"s": policy.reorder_point, "S": policy.order_up_to, **markov_policy_metrics(policy, costs=costs)}
                for policy in policies
            ]
            best = min(results, key=lambda result: result["average_daily_cost"])
            rows.append(
                {
                    "holding_cost": holding_cost,
                    "shortage_cost": shortage_cost,
                    "best_s": best["s"],
                    "best_S": best["S"],
                    "best_average_daily_cost": best["average_daily_cost"],
                    "best_stockout_rate": best["stockout_rate"],
                    "best_fill_rate": best["fill_rate"],
                    "best_average_ending_inventory": best["average_ending_inventory"],
                }
            )
    return pd.DataFrame(rows).sort_values(["holding_cost", "shortage_cost"], ignore_index=True)


def _scale(value: float, source_min: float, source_max: float, target_min: float, target_max: float) -> float:
    if np.isclose(source_max, source_min):
        return (target_min + target_max) / 2
    ratio = (value - source_min) / (source_max - source_min)
    return target_min + ratio * (target_max - target_min)


def _write_svg(path: Path, body: str, width: int = 920, height: int = 520) -> None:
    """Write a dependency-free SVG figure with a consistent visual style."""

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<rect width="100%" height="100%" fill="#fbfaf7"/>
<style>
text {{ font-family: Arial, sans-serif; fill: #243044; }}
.title {{ font-size: 22px; font-weight: 700; }}
.label {{ font-size: 13px; }}
.tick {{ font-size: 11px; fill: #607086; }}
.annotation {{ font-size: 12px; fill: #344256; }}
</style>
{body}
</svg>
"""
    path.write_text(svg, encoding="utf-8")


def plot_inventory_path(example: pd.DataFrame) -> None:
    """Plot daily demand bars and ending inventory for a representative trace."""

    width, height = 920, 520
    left, right, top, bottom = 70, 40, 70, 70
    x_min, x_max = float(example["day"].min()), float(example["day"].max())
    y_max = float(max(example["ending_inventory"].max(), example["demand"].max())) + 1
    points: list[str] = []
    bars: list[str] = []

    for _, row in example.iterrows():
        x = _scale(float(row["day"]), x_min, x_max, left, width - right)
        inventory_y = _scale(float(row["ending_inventory"]), 0, y_max, height - bottom, top)
        demand_y = _scale(float(row["demand"]), 0, y_max, height - bottom, top)
        points.append(f"{x:.1f},{inventory_y:.1f}")
        bars.append(
            f'<rect x="{x - 3:.1f}" y="{demand_y:.1f}" width="6" height="{height - bottom - demand_y:.1f}" fill="#d8aa4f" opacity="0.32"/>'
        )

    body = f"""
<text x="{left}" y="36" class="title">Inventory Level and Daily Demand Under Baseline Policy (3, 8)</text>
<line x1="{left}" y1="{height-bottom}" x2="{width-right}" y2="{height-bottom}" stroke="#9aa7b8"/>
<line x1="{left}" y1="{top}" x2="{left}" y2="{height-bottom}" stroke="#9aa7b8"/>
{''.join(bars)}
<polyline points="{' '.join(points)}" fill="none" stroke="#334155" stroke-width="3"/>
<text x="{width / 2 - 22}" y="{height - 24}" class="label">Day</text>
<text x="16" y="{height / 2}" class="label" transform="rotate(-90 16,{height / 2})">Units</text>
<rect x="{width - 250}" y="72" width="14" height="14" fill="#d8aa4f" opacity="0.32"/>
<text x="{width - 228}" y="84" class="tick">Daily demand</text>
<line x1="{width - 250}" y1="106" x2="{width - 236}" y2="106" stroke="#334155" stroke-width="3"/>
<text x="{width - 228}" y="110" class="tick">Ending inventory</text>
"""
    _write_svg(FIGURE_DIR / "inventory_path.svg", body, width, height)


def plot_policy_comparison(summary: pd.DataFrame) -> None:
    """Plot exact long-run daily cost for every tested (s, S) combination."""

    width, height = 920, 560
    left, top, cell_width, cell_height = 90, 80, 58, 46
    pivot = summary.pivot(index="s", columns="S", values="average_daily_cost")
    minimum_cost = float(pivot.min().min())
    maximum_cost = float(pivot.max().max())
    best = summary.iloc[0]
    cells: list[str] = []

    for row_index, s in enumerate(pivot.index):
        for column_index, S in enumerate(pivot.columns):
            value = pivot.loc[s, S]
            x = left + column_index * cell_width
            y = top + row_index * cell_height
            if pd.isna(value):
                fill, label = "#f1f5f9", ""
            else:
                intensity = _scale(float(value), minimum_cost, maximum_cost, 35, 88)
                fill, label = f"hsl(210, 45%, {intensity:.0f}%)", f"{value:.1f}"
            border = "#d8aa4f" if int(s) == int(best["s"]) and int(S) == int(best["S"]) else "none"
            border_width = "3" if border != "none" else "0"
            cells.append(
                f'<rect x="{x}" y="{y}" width="{cell_width - 2}" height="{cell_height - 2}" fill="{fill}" stroke="{border}" stroke-width="{border_width}"/>'
            )
            if label:
                cells.append(f'<text x="{x + 10}" y="{y + 28}" class="tick">{label}</text>')

    x_labels = "".join(
        f'<text x="{left + index * cell_width + 18}" y="{top - 12}" class="tick">{column}</text>'
        for index, column in enumerate(pivot.columns)
    )
    y_labels = "".join(
        f'<text x="{left - 28}" y="{top + index * cell_height + 28}" class="tick">{row}</text>'
        for index, row in enumerate(pivot.index)
    )
    body = f"""
<text x="{left}" y="38" class="title">Exact Long-Run Average Daily Cost Across (s, S) Policies</text>
<text x="{left + 250}" y="532" class="label">Order-up-to level S</text>
<text x="26" y="285" class="label" transform="rotate(-90 26,285)">Reorder point s</text>
{x_labels}
{y_labels}
{''.join(cells)}
<text x="650" y="96" class="annotation">Gold outline: recommended policy ({int(best['s'])}, {int(best['S'])}).</text>
<text x="650" y="118" class="annotation">Darker cells indicate lower cost.</text>
<text x="650" y="140" class="annotation">Blank cells are infeasible where S is not larger than s.</text>
"""
    _write_svg(FIGURE_DIR / "policy_cost_heatmap.svg", body, width, height)


def plot_tradeoff(summary: pd.DataFrame) -> None:
    """Plot the service-level versus inventory-holding trade-off across policies."""

    width, height = 820, 560
    left, right, top, bottom = 80, 60, 70, 75
    x_min, x_max = float(summary["average_ending_inventory"].min()), float(summary["average_ending_inventory"].max())
    y_min, y_max = float(summary["stockout_rate"].min()), float(summary["stockout_rate"].max())
    cost_min, cost_max = float(summary["average_daily_cost"].min()), float(summary["average_daily_cost"].max())
    best = summary.iloc[0]
    circles: list[str] = []

    for _, row in summary.iterrows():
        x = _scale(float(row["average_ending_inventory"]), x_min, x_max, left, width - right)
        y = _scale(float(row["stockout_rate"]), y_min, y_max, height - bottom, top)
        lightness = _scale(float(row["average_daily_cost"]), cost_min, cost_max, 35, 75)
        radius = 8 if int(row["s"]) == int(best["s"]) and int(row["S"]) == int(best["S"]) else 6
        stroke = "#d8aa4f" if radius == 8 else "none"
        circles.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radius}" fill="hsl(18, 70%, {lightness:.0f}%)" stroke="{stroke}" stroke-width="3" opacity="0.85"/>'
        )

    body = f"""
<text x="{left}" y="38" class="title">Trade-off Between Inventory Holding and Stockout Risk</text>
<line x1="{left}" y1="{height-bottom}" x2="{width-right}" y2="{height-bottom}" stroke="#9aa7b8"/>
<line x1="{left}" y1="{top}" x2="{left}" y2="{height-bottom}" stroke="#9aa7b8"/>
{''.join(circles)}
<text x="{width / 2 - 80}" y="{height - 26}" class="label">Average ending inventory</text>
<text x="18" y="{height / 2}" class="label" transform="rotate(-90 18,{height / 2})">Stockout rate</text>
<text x="510" y="92" class="annotation">Darker points indicate lower cost.</text>
<text x="510" y="114" class="annotation">Gold outline: recommended policy.</text>
"""
    _write_svg(FIGURE_DIR / "inventory_stockout_tradeoff.svg", body, width, height)


def plot_sensitivity(sensitivity: pd.DataFrame) -> None:
    """Plot the optimal policy under each holding-cost and shortage-cost setting."""

    width, height = 820, 420
    left, top, cell_width, cell_height = 180, 90, 150, 72
    holding_costs = sorted(sensitivity["holding_cost"].unique())
    shortage_costs = sorted(sensitivity["shortage_cost"].unique())
    cells: list[str] = []

    for row_index, holding_cost in enumerate(holding_costs):
        for column_index, shortage_cost in enumerate(shortage_costs):
            row = sensitivity.loc[
                (sensitivity["holding_cost"] == holding_cost)
                & (sensitivity["shortage_cost"] == shortage_cost)
            ].iloc[0]
            x, y = left + column_index * cell_width, top + row_index * cell_height
            fill = "#e9eff6" if float(row["best_stockout_rate"]) > 0.02 else "#eef3e8"
            cells.append(f'<rect x="{x}" y="{y}" width="{cell_width - 8}" height="{cell_height - 8}" fill="{fill}" stroke="#c7d2df"/>')
            cells.append(f'<text x="{x + 14}" y="{y + 27}" class="annotation">Policy ({int(row["best_s"])}, {int(row["best_S"])})</text>')
            cells.append(f'<text x="{x + 14}" y="{y + 47}" class="tick">Cost {row["best_average_daily_cost"]:.2f} | Stockout {row["best_stockout_rate"]:.1%}</text>')

    x_labels = "".join(
        f'<text x="{left + index * cell_width + 20}" y="{top - 18}" class="annotation">Shortage cost = {cost:g}</text>'
        for index, cost in enumerate(shortage_costs)
    )
    y_labels = "".join(
        f'<text x="{left - 152}" y="{top + index * cell_height + 36}" class="annotation">Holding cost = {cost:g}</text>'
        for index, cost in enumerate(holding_costs)
    )
    body = f"""
<text x="{left}" y="38" class="title">Sensitivity of the Recommended Policy to Cost Assumptions</text>
{x_labels}
{y_labels}
{''.join(cells)}
<text x="{left}" y="370" class="tick">Each cell reports the lowest-cost policy in the baseline policy grid.</text>
"""
    _write_svg(FIGURE_DIR / "cost_sensitivity.svg", body, width, height)


def write_run_summary(summary: pd.DataFrame, sensitivity: pd.DataFrame, periods: int, replications: int) -> None:
    """Write a concise, GitHub-renderable interpretation of the latest run."""

    best = summary.iloc[0]
    closest_service_policy = summary.loc[summary["stockout_rate"].idxmin()]
    sensitivity_lines = "\n".join(
        f"| {row.holding_cost:g} | {row.shortage_cost:g} | ({int(row.best_s)}, {int(row.best_S)}) | {row.best_average_daily_cost:.2f} | {row.best_stockout_rate:.2%} |"
        for row in sensitivity.itertuples(index=False)
    )
    content = f"""# Analysis Run Summary

This file is generated by `python3 src/inventory_model.py`. It records the exact Markov-chain result and the Monte Carlo validation used in the report.

## Baseline Recommendation

The lowest-cost policy in the tested grid is **({int(best['s'])}, {int(best['S'])})**.

| Metric | Exact Markov result | Monte Carlo validation |
| --- | ---: | ---: |
| Average daily cost | {best['average_daily_cost']:.2f} | {best['simulation_average_daily_cost']:.2f} |
| 95% CI for simulated cost | - | [{best['simulation_cost_95_ci_low']:.2f}, {best['simulation_cost_95_ci_high']:.2f}] |
| Stockout rate | {best['stockout_rate']:.2%} | {best['simulation_stockout_rate']:.2%} |
| Fill rate | {best['fill_rate']:.2%} | {best['simulation_fill_rate']:.2%} |
| Average ending inventory | {best['average_ending_inventory']:.2f} | {best['simulation_average_ending_inventory']:.2f} |

The simulation uses {replications} independent replications of {periods} days each. Its average-cost estimate differs from the Markov result by {best['absolute_cost_gap']:.3f} currency units per day, providing a direct reproducibility check.

The lowest-stockout policy in the tested grid is ({int(closest_service_policy['s'])}, {int(closest_service_policy['S'])}); it has a {closest_service_policy['stockout_rate']:.2%} stockout rate but a higher average daily cost of {closest_service_policy['average_daily_cost']:.2f}. This makes the cost-service trade-off explicit rather than treating the low-cost choice as universally best.

## Cost Sensitivity

| Holding cost | Shortage cost | Best policy | Average daily cost | Stockout rate |
| ---: | ---: | --- | ---: | ---: |
{sensitivity_lines}

"""
    (OUTPUT_DIR / "analysis_summary.md").write_text(content, encoding="utf-8")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the stochastic (s, S) inventory analysis.")
    parser.add_argument("--periods", type=int, default=365, help="Days in each simulation replication.")
    parser.add_argument("--replications", type=int, default=200, help="Monte Carlo replications per policy.")
    parser.add_argument("--seed", type=int, default=42, help="Base random seed for reproducibility.")
    return parser.parse_args()


def main() -> None:
    """Run the complete baseline experiment and export all project artefacts."""

    arguments = parse_arguments()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)

    baseline_policy = Policy(reorder_point=3, order_up_to=8)
    baseline_trace = simulate_policy(policy=baseline_policy, periods=90, seed=7)
    policies = policy_grid()
    summary = evaluate_policies(
        policies,
        replications=arguments.replications,
        periods=arguments.periods,
        seed=arguments.seed,
    )
    sensitivity = sensitivity_analysis(policies)

    baseline_trace.to_csv(OUTPUT_DIR / "baseline_simulation_trace.csv", index=False)
    summary.to_csv(OUTPUT_DIR / "policy_evaluation_summary.csv", index=False)
    sensitivity.to_csv(OUTPUT_DIR / "cost_sensitivity_summary.csv", index=False)
    assumptions = {
        "demand_scenario": asdict(BASELINE_DEMAND),
        "cost_parameters": asdict(BASELINE_COSTS),
        "inventory_system": {
            "review_period": "daily",
            "lead_time": 0,
            "shortage_treatment": "lost sales",
            "number_of_products": 1,
        },
        "simulation": {
            "periods_per_replication": arguments.periods,
            "replications_per_policy": arguments.replications,
            "base_seed": arguments.seed,
            "comparison_design": "common random numbers across policies",
        },
    }
    (OUTPUT_DIR / "model_assumptions.json").write_text(json.dumps(assumptions, indent=2), encoding="utf-8")

    plot_inventory_path(baseline_trace)
    plot_policy_comparison(summary)
    plot_tradeoff(summary)
    plot_sensitivity(sensitivity)
    write_run_summary(summary, sensitivity, arguments.periods, arguments.replications)

    best = summary.iloc[0]
    print("Baseline analysis complete")
    print(f"Recommended policy: s = {int(best['s'])}, S = {int(best['S'])}")
    print(f"Exact average daily cost: {best['average_daily_cost']:.2f}")
    print(f"Exact stockout rate: {best['stockout_rate']:.2%}")
    print(f"Simulation average daily cost: {best['simulation_average_daily_cost']:.2f}")
    print(f"Results written to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()

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
SERVICE_FILL_RATE_TARGET = 0.97
POLICY_GRID_MIN_REORDER_POINT = 0
POLICY_GRID_MAX_REORDER_POINT = 8
POLICY_GRID_MAX_ORDER_UP_TO = 24
CASE_STUDY = {
    "business": "illustrative ecommerce fulfilment centre",
    "product_scope": "one generic non-perishable SKU",
    "category_status": "category-neutral by design",
    "replenishment_source": "nearby central warehouse",
    "data_status": "illustrative scenario; not calibrated to company data",
}


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
    name="baseline_mixed",
    values=(0, 1, 2, 3, 4, 5, 6),
    probabilities=(0.05, 0.10, 0.20, 0.25, 0.20, 0.12, 0.08),
)
DEMAND_SCENARIOS = {
    BASELINE_DEMAND.name: BASELINE_DEMAND,
    "steady": DemandScenario(
        name="steady",
        values=(0, 1, 2, 3, 4, 5, 6),
        probabilities=(0.01, 0.04, 0.20, 0.50, 0.20, 0.04, 0.01),
    ),
    "volatile": DemandScenario(
        name="volatile",
        values=(0, 1, 2, 3, 4, 5, 6),
        probabilities=(0.20, 0.10, 0.10, 0.20, 0.10, 0.10, 0.20),
    ),
    "promotion_peak": DemandScenario(
        name="promotion_peak",
        values=(0, 1, 2, 3, 4, 5, 6, 7, 8),
        probabilities=(0.01, 0.03, 0.06, 0.12, 0.20, 0.23, 0.18, 0.11, 0.06),
    ),
}
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
    warmup_periods: int = 0,
    starting_inventory: int | None = None,
    demand_scenario: DemandScenario = BASELINE_DEMAND,
    costs: CostParameters = BASELINE_COSTS,
    seed: int = 42,
) -> pd.DataFrame:
    """Simulate measured operations after an optional unreported warm-up period."""

    policy.validate()
    costs.validate()
    demand_values, demand_probabilities = demand_scenario.arrays()
    if periods <= 0:
        raise ValueError("The number of periods must be positive.")
    if warmup_periods < 0:
        raise ValueError("The number of warm-up periods must be non-negative.")

    inventory = policy.order_up_to if starting_inventory is None else starting_inventory
    if inventory < 0:
        raise ValueError("Starting inventory must be non-negative.")

    rng = np.random.default_rng(seed)
    records: list[dict[str, float]] = []
    for simulation_day in range(1, periods + warmup_periods + 1):
        opening_inventory = inventory
        demand = int(rng.choice(demand_values, p=demand_probabilities))
        outcome = daily_outcome(opening_inventory, demand, policy, costs)
        inventory = int(outcome["ending_inventory"])
        if simulation_day > warmup_periods:
            measured_day = simulation_day - warmup_periods
            records.append(
                {"day": measured_day, "opening_inventory": opening_inventory, "demand": demand, **outcome}
            )

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
    """Compute stationary long-run metrics for the finite Markov-chain model."""

    policy.validate()
    costs.validate()
    demand_values, demand_probabilities = demand_scenario.arrays()
    distribution = stationary_distribution(build_transition_matrix(policy, demand_scenario))

    expected_cost = 0.0
    expected_fixed_order_cost = 0.0
    expected_unit_order_cost = 0.0
    expected_holding_cost = 0.0
    expected_shortage_cost = 0.0
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
        expected_fixed_order_cost += (
            state_probability * costs.order_fixed_cost * float(order_quantity > 0)
        )
        expected_unit_order_cost += state_probability * costs.order_unit_cost * order_quantity
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
            expected_holding_cost += probability * costs.holding_cost * ending_inventory
            expected_shortage_cost += probability * costs.shortage_cost * shortage
            expected_stockout += probability * float(shortage > 0)
            expected_demand += probability * demand
            expected_sales += probability * sales
            expected_ending_inventory += probability * ending_inventory

    return {
        "average_daily_cost": expected_cost,
        "average_fixed_order_cost": expected_fixed_order_cost,
        "average_unit_order_cost": expected_unit_order_cost,
        "average_holding_cost": expected_holding_cost,
        "average_shortage_cost": expected_shortage_cost,
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
    warmup_periods: int = 365,
    demand_scenario: DemandScenario = BASELINE_DEMAND,
    costs: CostParameters = BASELINE_COSTS,
    seed: int = 42,
) -> pd.DataFrame:
    """Compare policies using stationary Markov metrics and repeated simulations.

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
                    warmup_periods=warmup_periods,
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
                "average_fixed_order_cost": exact["average_fixed_order_cost"],
                "average_unit_order_cost": exact["average_unit_order_cost"],
                "average_holding_cost": exact["average_holding_cost"],
                "average_shortage_cost": exact["average_shortage_cost"],
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


def policy_grid(
    minimum_s: int = POLICY_GRID_MIN_REORDER_POINT,
    maximum_s: int = POLICY_GRID_MAX_REORDER_POINT,
    maximum_S: int = POLICY_GRID_MAX_ORDER_UP_TO,
) -> list[Policy]:
    """Create the feasible policy set used in the baseline experiment."""

    return [
        Policy(reorder_point=s, order_up_to=S)
        for s in range(minimum_s, maximum_s + 1)
        for S in range(s + 1, maximum_S + 1)
    ]


def audit_policy_search_boundaries(
    selected_policies: pd.DataFrame,
    maximum_s: int = POLICY_GRID_MAX_REORDER_POINT,
    maximum_S: int = POLICY_GRID_MAX_ORDER_UP_TO,
) -> pd.DataFrame:
    """Verify that no reported choice is created by an artificial upper limit."""

    required_columns = {"analysis", "s", "S"}
    missing_columns = required_columns.difference(selected_policies.columns)
    if missing_columns:
        raise ValueError(f"Boundary audit is missing columns: {sorted(missing_columns)}")
    audited = selected_policies.copy()
    audited["distance_to_max_s"] = maximum_s - audited["s"]
    audited["distance_to_max_S"] = maximum_S - audited["S"]
    audited["touches_upper_boundary"] = (
        (audited["s"] >= maximum_s) | (audited["S"] >= maximum_S)
    )
    boundary_rows = audited.loc[audited["touches_upper_boundary"]]
    if not boundary_rows.empty:
        analyses = ", ".join(boundary_rows["analysis"].astype(str))
        raise ValueError(
            "Selected policy touches an artificial upper boundary; expand the grid before "
            f"publishing: {analyses}."
        )
    return audited


def select_policy(summary: pd.DataFrame, minimum_fill_rate: float | None = None) -> pd.Series:
    """Select the lowest-cost policy, optionally subject to a fill-rate target."""

    required_columns = {"average_daily_cost", "stockout_rate", "fill_rate", "s", "S"}
    missing_columns = required_columns.difference(summary.columns)
    if missing_columns:
        raise ValueError(f"Policy summary is missing columns: {sorted(missing_columns)}")
    if minimum_fill_rate is not None and not 0 <= minimum_fill_rate <= 1:
        raise ValueError("The minimum fill rate must be between zero and one.")

    feasible = summary
    if minimum_fill_rate is not None:
        feasible = summary.loc[summary["fill_rate"] >= minimum_fill_rate]
    if feasible.empty:
        raise ValueError("No policy satisfies the requested fill-rate constraint.")
    return feasible.sort_values(["average_daily_cost", "stockout_rate", "s", "S"]).iloc[0]


def pareto_frontier(summary: pd.DataFrame) -> pd.DataFrame:
    """Return policies not dominated on both expected cost and stockout rate."""

    required_columns = {"average_daily_cost", "stockout_rate"}
    missing_columns = required_columns.difference(summary.columns)
    if missing_columns:
        raise ValueError(f"Policy summary is missing columns: {sorted(missing_columns)}")

    frontier_indices: list[int] = []
    for index, candidate in summary.iterrows():
        no_more_costly = summary["average_daily_cost"] <= candidate["average_daily_cost"]
        no_more_stockouts = summary["stockout_rate"] <= candidate["stockout_rate"]
        strictly_better = (
            (summary["average_daily_cost"] < candidate["average_daily_cost"])
            | (summary["stockout_rate"] < candidate["stockout_rate"])
        )
        if not bool((no_more_costly & no_more_stockouts & strictly_better).any()):
            frontier_indices.append(index)

    return summary.loc[frontier_indices].sort_values(
        ["average_daily_cost", "stockout_rate"], ignore_index=True
    )


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


def demand_scenario_analysis(
    policies: list[Policy],
    scenarios: dict[str, DemandScenario] = DEMAND_SCENARIOS,
    replications: int = 200,
    periods: int = 365,
    warmup_periods: int = 365,
    costs: CostParameters = BASELINE_COSTS,
    seed: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Compare policy optima across demand distributions and validate each by simulation."""

    if not policies:
        raise ValueError("At least one policy is required.")
    if not scenarios:
        raise ValueError("At least one demand scenario is required.")

    scenario_rows: list[dict[str, float | str]] = []
    policy_rows: list[dict[str, float | str]] = []
    for scenario_index, (scenario_name, scenario) in enumerate(scenarios.items()):
        values, probabilities = scenario.arrays()
        demand_mean = float(np.dot(values, probabilities))
        demand_variance = float(np.dot((values - demand_mean) ** 2, probabilities))

        current_rows = [
            {
                "scenario": scenario_name,
                "s": policy.reorder_point,
                "S": policy.order_up_to,
                **markov_policy_metrics(policy, demand_scenario=scenario, costs=costs),
            }
            for policy in policies
        ]
        policy_rows.extend(current_rows)
        current_results = pd.DataFrame(current_rows)
        best = select_policy(current_results)
        service_feasible = current_results.loc[
            current_results["fill_rate"] >= SERVICE_FILL_RATE_TARGET
        ]
        service_best = (
            select_policy(current_results, minimum_fill_rate=SERVICE_FILL_RATE_TARGET)
            if not service_feasible.empty
            else None
        )
        best_policy = Policy(int(best["s"]), int(best["S"]))
        validation = evaluate_policies(
            [best_policy],
            replications=replications,
            periods=periods,
            warmup_periods=warmup_periods,
            demand_scenario=scenario,
            costs=costs,
            seed=seed + scenario_index * 10_000,
        ).iloc[0]
        scenario_rows.append(
            {
                "scenario": scenario_name,
                "demand_mean": demand_mean,
                "demand_variance": demand_variance,
                "best_s": int(best["s"]),
                "best_S": int(best["S"]),
                "exact_average_daily_cost": float(best["average_daily_cost"]),
                "exact_stockout_rate": float(best["stockout_rate"]),
                "exact_fill_rate": float(best["fill_rate"]),
                "exact_average_ending_inventory": float(best["average_ending_inventory"]),
                "service_s": int(service_best["s"]) if service_best is not None else np.nan,
                "service_S": int(service_best["S"]) if service_best is not None else np.nan,
                "service_average_daily_cost": (
                    float(service_best["average_daily_cost"]) if service_best is not None else np.nan
                ),
                "service_fill_rate": (
                    float(service_best["fill_rate"]) if service_best is not None else np.nan
                ),
                "simulation_average_daily_cost": float(validation["simulation_average_daily_cost"]),
                "simulation_cost_95_ci_low": float(validation["simulation_cost_95_ci_low"]),
                "simulation_cost_95_ci_high": float(validation["simulation_cost_95_ci_high"]),
                "absolute_cost_gap": float(validation["absolute_cost_gap"]),
            }
        )

    scenario_summary = pd.DataFrame(scenario_rows)
    policy_results = pd.DataFrame(policy_rows).sort_values(
        ["scenario", "average_daily_cost", "stockout_rate", "s", "S"],
        ignore_index=True,
    )
    return scenario_summary, policy_results


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


def write_stable_csv(frame: pd.DataFrame, path: Path) -> None:
    """Write published tables with cross-platform-stable floating-point text."""
    frame.to_csv(path, index=False, float_format="%.10f", lineterminator="\n")


def plot_inventory_path(example: pd.DataFrame, policy: Policy) -> None:
    """Plot daily demand bars and ending inventory for a representative trace."""

    width, height = 920, 520
    left, right, top, bottom = 70, 40, 70, 70
    x_min, x_max = float(example["day"].min()), float(example["day"].max())
    y_max = float(max(example["ending_inventory"].max(), example["demand"].max())) + 1
    points: list[str] = []
    bars: list[str] = []
    x_ticks: list[str] = []
    y_ticks: list[str] = []

    for _, row in example.iterrows():
        x = _scale(float(row["day"]), x_min, x_max, left, width - right)
        inventory_y = _scale(float(row["ending_inventory"]), 0, y_max, height - bottom, top)
        demand_y = _scale(float(row["demand"]), 0, y_max, height - bottom, top)
        points.append(f"{x:.1f},{inventory_y:.1f}")
        bars.append(
            f'<rect x="{x - 3:.1f}" y="{demand_y:.1f}" width="6" height="{height - bottom - demand_y:.1f}" fill="#d8aa4f" opacity="0.32"/>'
        )

    for value in np.linspace(x_min, x_max, 7):
        x = _scale(float(value), x_min, x_max, left, width - right)
        x_ticks.append(f'<line x1="{x:.1f}" y1="{height-bottom}" x2="{x:.1f}" y2="{height-bottom+6}" stroke="#7b8797"/>')
        x_ticks.append(f'<text x="{x-8:.1f}" y="{height-bottom+22}" class="tick">{value:.0f}</text>')
    for value in range(0, int(y_max) + 1, 2):
        y = _scale(float(value), 0, y_max, height - bottom, top)
        y_ticks.append(f'<line x1="{left}" y1="{y:.1f}" x2="{width-right}" y2="{y:.1f}" stroke="#dfe4ea"/>')
        y_ticks.append(f'<text x="{left-26}" y="{y+4:.1f}" class="tick">{value}</text>')

    body = f"""
<text x="{left}" y="36" class="title">Inventory and Demand Under Cost-Optimal Policy ({policy.reorder_point}, {policy.order_up_to})</text>
{''.join(y_ticks)}
<line x1="{left}" y1="{height-bottom}" x2="{width-right}" y2="{height-bottom}" stroke="#9aa7b8"/>
<line x1="{left}" y1="{top}" x2="{left}" y2="{height-bottom}" stroke="#9aa7b8"/>
{''.join(x_ticks)}
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
    """Plot stationary long-run daily cost for every tested (s, S) combination."""

    pivot = summary.pivot(index="s", columns="S", values="average_daily_cost")
    left, top, cell_width, cell_height = 90, 80, 40, 36
    width = left + len(pivot.columns) * cell_width + 70
    height = top + len(pivot.index) * cell_height + 105
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
                cells.append(f'<text x="{x + 6}" y="{y + 23}" class="tick">{label}</text>')

    x_labels = "".join(
        f'<text x="{left + index * cell_width + 11}" y="{top - 12}" class="tick">{column}</text>'
        for index, column in enumerate(pivot.columns)
    )
    y_labels = "".join(
        f'<text x="{left - 28}" y="{top + index * cell_height + 23}" class="tick">{row}</text>'
        for index, row in enumerate(pivot.index)
    )
    body = f"""
<text x="{left}" y="38" class="title">Stationary Long-Run Average Daily Cost Across (s, S) Policies</text>
<text x="{width / 2 - 60}" y="{height - 55}" class="label">Order-up-to level S</text>
<text x="26" y="{height / 2}" class="label" transform="rotate(-90 26,{height / 2})">Reorder point s</text>
{x_labels}
{y_labels}
{''.join(cells)}
<text x="{left}" y="{height - 28}" class="annotation">Gold outline: cost-optimal policy ({int(best['s'])}, {int(best['S'])}). Darker cells indicate lower cost.</text>
<text x="{left}" y="{height - 9}" class="tick">Blank cells are infeasible because an (s, S) policy requires S &gt; s.</text>
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
    x_ticks: list[str] = []
    y_ticks: list[str] = []

    for _, row in summary.iterrows():
        x = _scale(float(row["average_ending_inventory"]), x_min, x_max, left, width - right)
        y = _scale(float(row["stockout_rate"]), y_min, y_max, height - bottom, top)
        lightness = _scale(float(row["average_daily_cost"]), cost_min, cost_max, 35, 75)
        radius = 8 if int(row["s"]) == int(best["s"]) and int(row["S"]) == int(best["S"]) else 6
        stroke = "#d8aa4f" if radius == 8 else "none"
        circles.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radius}" fill="hsl(18, 70%, {lightness:.0f}%)" stroke="{stroke}" stroke-width="3" opacity="0.85"/>'
        )

    for value in np.linspace(x_min, x_max, 6):
        x = _scale(float(value), x_min, x_max, left, width - right)
        x_ticks.append(f'<line x1="{x:.1f}" y1="{height-bottom}" x2="{x:.1f}" y2="{height-bottom+6}" stroke="#7b8797"/>')
        x_ticks.append(f'<text x="{x-10:.1f}" y="{height-bottom+24}" class="tick">{value:.1f}</text>')
    for value in np.linspace(y_min, y_max, 6):
        y = _scale(float(value), y_min, y_max, height - bottom, top)
        y_ticks.append(f'<line x1="{left-6}" y1="{y:.1f}" x2="{left}" y2="{y:.1f}" stroke="#7b8797"/>')
        y_ticks.append(f'<text x="{left-48}" y="{y+4:.1f}" class="tick">{value:.0%}</text>')

    body = f"""
<text x="{left}" y="38" class="title">Trade-off Between Inventory Holding and Stockout Risk</text>
{''.join(y_ticks)}
<line x1="{left}" y1="{height-bottom}" x2="{width-right}" y2="{height-bottom}" stroke="#9aa7b8"/>
<line x1="{left}" y1="{top}" x2="{left}" y2="{height-bottom}" stroke="#9aa7b8"/>
{''.join(x_ticks)}
{''.join(circles)}
<text x="{width / 2 - 80}" y="{height - 26}" class="label">Average ending inventory</text>
<text x="18" y="{height / 2}" class="label" transform="rotate(-90 18,{height / 2})">Stockout rate</text>
<text x="510" y="92" class="annotation">Darker points indicate lower cost.</text>
<text x="510" y="114" class="annotation">Gold outline: recommended policy.</text>
"""
    _write_svg(FIGURE_DIR / "inventory_stockout_tradeoff.svg", body, width, height)


def plot_service_frontier(
    summary: pd.DataFrame,
    frontier: pd.DataFrame,
    cost_optimum: pd.Series,
    service_policy: pd.Series,
) -> None:
    """Plot the non-dominated cost-stockout frontier and two decision rules."""

    width, height = 900, 560
    left, right, top, bottom = 90, 55, 75, 85
    x_min = float(summary["average_daily_cost"].min()) - 0.3
    x_max = float(summary["average_daily_cost"].max()) + 0.3
    y_min = 0.0
    y_max = float(summary["stockout_rate"].max()) * 1.08

    def coordinates(row: pd.Series) -> tuple[float, float]:
        return (
            _scale(float(row["average_daily_cost"]), x_min, x_max, left, width - right),
            _scale(float(row["stockout_rate"]), y_min, y_max, height - bottom, top),
        )

    all_points = "".join(
        f'<circle cx="{coordinates(row)[0]:.1f}" cy="{coordinates(row)[1]:.1f}" r="4" fill="#a8b3c2" opacity="0.55"/>'
        for _, row in summary.iterrows()
    )
    ordered_frontier = frontier.sort_values("average_daily_cost")
    frontier_points = " ".join(
        f"{coordinates(row)[0]:.1f},{coordinates(row)[1]:.1f}"
        for _, row in ordered_frontier.iterrows()
    )
    cost_x, cost_y = coordinates(cost_optimum)
    service_x, service_y = coordinates(service_policy)

    x_ticks: list[str] = []
    y_ticks: list[str] = []
    for value in np.linspace(x_min, x_max, 6):
        x = _scale(float(value), x_min, x_max, left, width - right)
        x_ticks.append(f'<line x1="{x:.1f}" y1="{height-bottom}" x2="{x:.1f}" y2="{height-bottom+6}" stroke="#7b8797"/>')
        x_ticks.append(f'<text x="{x-13:.1f}" y="{height-bottom+24}" class="tick">{value:.1f}</text>')
    for value in np.linspace(y_min, y_max, 6):
        y = _scale(float(value), y_min, y_max, height - bottom, top)
        y_ticks.append(f'<line x1="{left-6}" y1="{y:.1f}" x2="{left}" y2="{y:.1f}" stroke="#7b8797"/>')
        y_ticks.append(f'<text x="{left-48}" y="{y+4:.1f}" class="tick">{value:.0%}</text>')

    body = f"""
<text x="{left}" y="38" class="title">Cost-Service Pareto Frontier</text>
<text x="{left}" y="59" class="tick">Every point is a tested (s, S) policy; the line joins non-dominated choices.</text>
<line x1="{left}" y1="{height-bottom}" x2="{width-right}" y2="{height-bottom}" stroke="#7b8797"/>
<line x1="{left}" y1="{top}" x2="{left}" y2="{height-bottom}" stroke="#7b8797"/>
{''.join(x_ticks)}
{''.join(y_ticks)}
{all_points}
<polyline points="{frontier_points}" fill="none" stroke="#117c75" stroke-width="3"/>
<circle cx="{cost_x:.1f}" cy="{cost_y:.1f}" r="8" fill="#d7a43b" stroke="#243044" stroke-width="2"/>
<circle cx="{service_x:.1f}" cy="{service_y:.1f}" r="8" fill="#d95d4f" stroke="#243044" stroke-width="2"/>
<text x="{cost_x+12:.1f}" y="{cost_y-8:.1f}" class="annotation">Cost optimum ({int(cost_optimum['s'])}, {int(cost_optimum['S'])})</text>
<text x="{service_x+12:.1f}" y="{service_y+20:.1f}" class="annotation">97% fill-rate choice ({int(service_policy['s'])}, {int(service_policy['S'])})</text>
<text x="{width/2-95}" y="{height-28}" class="label">Expected daily cost</text>
<text x="20" y="{height/2}" class="label" transform="rotate(-90 20,{height/2})">Stockout probability</text>
"""
    _write_svg(FIGURE_DIR / "cost_service_frontier.svg", body, width, height)


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


def plot_demand_scenario_comparison(scenarios: pd.DataFrame) -> None:
    """Compare the cost-optimal policy and service outcome across demand distributions."""

    width, height = 920, 520
    top, row_height = 116, 82
    bar_left, bar_width = 390, 220
    service_left, service_width = 700, 155
    maximum_cost = float(scenarios["exact_average_daily_cost"].max())
    colours = ("#117c75", "#d7a43b", "#d95d4f", "#526b8b")
    rows: list[str] = []

    for index, row in enumerate(scenarios.itertuples(index=False)):
        y = top + index * row_height
        cost_width = _scale(float(row.exact_average_daily_cost), 0, maximum_cost, 0, bar_width)
        fill_x = _scale(float(row.exact_fill_rate), 0.70, 1.0, service_left, service_left + service_width)
        label = str(row.scenario).replace("_", " ").title()
        colour = colours[index % len(colours)]
        service_policy = (
            f"({int(row.service_s)}, {int(row.service_S)})"
            if not pd.isna(row.service_s)
            else "Not feasible"
        )
        rows.extend(
            [
                f'<text x="56" y="{y + 8}" class="annotation">{label}</text>',
                f'<text x="56" y="{y + 29}" class="tick">E[D] {row.demand_mean:.2f} | Var(D) {row.demand_variance:.2f}</text>',
                f'<text x="240" y="{y + 8}" class="annotation">Cost ({int(row.best_s)}, {int(row.best_S)})</text>',
                f'<text x="240" y="{y + 29}" class="tick">97% {service_policy}</text>',
                f'<rect x="{bar_left}" y="{y - 10}" width="{cost_width:.1f}" height="27" fill="{colour}" opacity="0.85"/>',
                f'<text x="{bar_left + cost_width + 8:.1f}" y="{y + 8}" class="annotation">{row.exact_average_daily_cost:.2f}</text>',
                f'<line x1="{service_left}" y1="{y + 3}" x2="{service_left + service_width}" y2="{y + 3}" stroke="#d6dde5" stroke-width="3"/>',
                f'<circle cx="{fill_x:.1f}" cy="{y + 3}" r="7" fill="{colour}"/>',
                f'<text x="{fill_x - 17:.1f}" y="{y + 29}" class="tick">{row.exact_fill_rate:.1%}</text>',
            ]
        )

    body = f"""
<text x="56" y="38" class="title">Demand-Distribution Stress Test</text>
<text x="56" y="62" class="tick">Costs and the {len(policy_grid())}-policy search grid are held constant; each selected policy is checked by simulation.</text>
<text x="56" y="91" class="label">Demand scenario</text>
<text x="240" y="91" class="label">Selected policies</text>
<text x="{bar_left}" y="91" class="label">Expected daily cost</text>
<text x="{service_left}" y="91" class="label">Fill rate</text>
{''.join(rows)}
<text x="{service_left}" y="{height - 31}" class="tick">70%</text>
<text x="{service_left + service_width - 25}" y="{height - 31}" class="tick">100%</text>
"""
    _write_svg(FIGURE_DIR / "demand_scenario_comparison.svg", body, width, height)


def write_run_summary(
    summary: pd.DataFrame,
    sensitivity: pd.DataFrame,
    demand_scenarios: pd.DataFrame,
    cost_optimum: pd.Series,
    service_policy: pd.Series,
    search_audit: pd.DataFrame,
    periods: int,
    replications: int,
    warmup_periods: int,
) -> None:
    """Write a concise, GitHub-renderable interpretation of the latest run."""

    closest_service_policy = summary.loc[summary["stockout_rate"].idxmin()]
    incremental_cost = service_policy["average_daily_cost"] - cost_optimum["average_daily_cost"]
    incremental_cost_rate = incremental_cost / cost_optimum["average_daily_cost"]
    exact_inside_interval = (
        cost_optimum["simulation_cost_95_ci_low"]
        <= cost_optimum["average_daily_cost"]
        <= cost_optimum["simulation_cost_95_ci_high"]
    )
    maximum_selected_s = int(search_audit["s"].max())
    maximum_selected_S = int(search_audit["S"].max())
    sensitivity_lines = "\n".join(
        f"| {row.holding_cost:g} | {row.shortage_cost:g} | ({int(row.best_s)}, {int(row.best_S)}) | {row.best_average_daily_cost:.2f} | {row.best_stockout_rate:.2%} |"
        for row in sensitivity.itertuples(index=False)
    )
    demand_scenario_lines = "\n".join(
        f"| {row.scenario.replace('_', ' ').title()} | {row.demand_mean:.2f} | {row.demand_variance:.2f} | ({int(row.best_s)}, {int(row.best_S)}) | ({int(row.service_s)}, {int(row.service_S)}) | {row.exact_average_daily_cost:.2f} | {row.exact_fill_rate:.2%} |"
        for row in demand_scenarios.itertuples(index=False)
    )
    content = f"""# Analysis Run Summary

This file is generated by `python3 src/inventory_model.py`. It records the stationary Markov-chain result, warm-up-adjusted Monte Carlo validation, and decision rules used in the report.

## Case and Decision Question

The illustrative case is an ecommerce fulfilment centre replenishing one generic non-perishable SKU from a nearby central warehouse. The product category is intentionally unspecified. The inputs are transparent teaching assumptions, not company observations.

The program answers two different questions: which tested policy has the lowest expected cost, and which has the lowest cost while achieving at least a {SERVICE_FILL_RATE_TARGET:.0%} fill rate?

The finite search contains {len(summary)} policies with `s` from {POLICY_GRID_MIN_REORDER_POINT} to {POLICY_GRID_MAX_REORDER_POINT} and `S` up to {POLICY_GRID_MAX_ORDER_UP_TO}. Across the baseline, demand-distribution, service, and cost-sensitivity decisions, the largest selected values are `s={maximum_selected_s}` and `S={maximum_selected_S}`. Neither reaches an artificial upper boundary, so the published grid has margins of {POLICY_GRID_MAX_REORDER_POINT - maximum_selected_s} and {POLICY_GRID_MAX_ORDER_UP_TO - maximum_selected_S} units respectively. This is a finite-grid adequacy check, not a proof over every unbounded integer policy.

## Cost-Optimal Policy

The lowest-cost policy in the tested grid is **({int(cost_optimum['s'])}, {int(cost_optimum['S'])})**.

| Metric | Stationary Markov result | Monte Carlo validation |
| --- | ---: | ---: |
| Average daily cost | {cost_optimum['average_daily_cost']:.2f} | {cost_optimum['simulation_average_daily_cost']:.2f} |
| 95% CI for simulated cost | - | [{cost_optimum['simulation_cost_95_ci_low']:.2f}, {cost_optimum['simulation_cost_95_ci_high']:.2f}] |
| Stockout rate | {cost_optimum['stockout_rate']:.2%} | {cost_optimum['simulation_stockout_rate']:.2%} |
| Fill rate | {cost_optimum['fill_rate']:.2%} | {cost_optimum['simulation_fill_rate']:.2%} |
| Average ending inventory | {cost_optimum['average_ending_inventory']:.2f} | {cost_optimum['simulation_average_ending_inventory']:.2f} |

Each simulation replication discards {warmup_periods} warm-up days before measuring {periods} days. Across {replications} replications, the numerically evaluated stationary Markov cost {'falls inside' if exact_inside_interval else 'does not fall inside'} the simulated 95% interval. The absolute difference between the two estimates is {cost_optimum['absolute_cost_gap']:.3f} currency units per day.

The lowest-stockout policy in the tested grid is ({int(closest_service_policy['s'])}, {int(closest_service_policy['S'])}); it has a {closest_service_policy['stockout_rate']:.2%} stockout rate but a higher average daily cost of {closest_service_policy['average_daily_cost']:.2f}. This makes the cost-service trade-off explicit rather than treating the low-cost choice as universally best.

## Service-Constrained Policy

Among policies with a fill rate of at least {SERVICE_FILL_RATE_TARGET:.0%}, the lowest-cost choice is **({int(service_policy['s'])}, {int(service_policy['S'])})**. Its stationary daily cost is {service_policy['average_daily_cost']:.2f}, fill rate is {service_policy['fill_rate']:.2%}, and stockout rate is {service_policy['stockout_rate']:.2%}.

Compared with the unconstrained minimum, this choice costs {incremental_cost:.2f} more per day ({incremental_cost_rate:.2%}) while reducing the stockout rate by {(cost_optimum['stockout_rate'] - service_policy['stockout_rate']) * 100:.2f} percentage points. This recommendation applies only when the illustrative 97% target is adopted; the threshold is not an industry benchmark.

## Demand-Distribution Sensitivity

| Scenario | Mean demand | Demand variance | Cost optimum | 97% choice | Expected daily cost | Fill rate |
| --- | ---: | ---: | --- | --- | ---: | ---: |
{demand_scenario_lines}

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
    parser.add_argument(
        "--warmup-periods",
        type=int,
        default=365,
        help="Unreported simulation days discarded before each measured replication.",
    )
    parser.add_argument("--seed", type=int, default=42, help="Base random seed for reproducibility.")
    return parser.parse_args()


def main() -> None:
    """Run the complete baseline experiment and export all project artefacts."""

    arguments = parse_arguments()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)

    policies = policy_grid()
    summary = evaluate_policies(
        policies,
        replications=arguments.replications,
        periods=arguments.periods,
        warmup_periods=arguments.warmup_periods,
        seed=arguments.seed,
    )
    sensitivity = sensitivity_analysis(policies)
    demand_scenarios, demand_policy_results = demand_scenario_analysis(
        policies,
        replications=arguments.replications,
        periods=arguments.periods,
        warmup_periods=arguments.warmup_periods,
        seed=arguments.seed,
    )
    cost_optimum = select_policy(summary)
    service_policy = select_policy(summary, minimum_fill_rate=SERVICE_FILL_RATE_TARGET)
    frontier = pareto_frontier(summary)
    recommended_policy = Policy(int(cost_optimum["s"]), int(cost_optimum["S"]))
    baseline_trace = simulate_policy(
        policy=recommended_policy,
        periods=90,
        warmup_periods=arguments.warmup_periods,
        seed=7,
    )
    incremental_cost = service_policy["average_daily_cost"] - cost_optimum["average_daily_cost"]
    decision_summary = pd.DataFrame(
        [
            {
                "decision_rule": "minimum expected daily cost",
                "minimum_fill_rate": 0.0,
                **cost_optimum.to_dict(),
                "incremental_cost_vs_unconstrained": 0.0,
            },
            {
                "decision_rule": f"minimum cost with fill rate >= {SERVICE_FILL_RATE_TARGET:.0%}",
                "minimum_fill_rate": SERVICE_FILL_RATE_TARGET,
                **service_policy.to_dict(),
                "incremental_cost_vs_unconstrained": incremental_cost,
            },
        ]
    )
    audit_rows: list[dict[str, float | str]] = [
        {
            "analysis": "baseline cost optimum",
            "scenario": "baseline_mixed",
            "s": int(cost_optimum["s"]),
            "S": int(cost_optimum["S"]),
        },
        {
            "analysis": "baseline 97% fill-rate choice",
            "scenario": "baseline_mixed",
            "s": int(service_policy["s"]),
            "S": int(service_policy["S"]),
        },
    ]
    audit_rows.extend(
        {
            "analysis": "cost sensitivity optimum",
            "scenario": f"holding={row.holding_cost:g}; shortage={row.shortage_cost:g}",
            "s": int(row.best_s),
            "S": int(row.best_S),
        }
        for row in sensitivity.itertuples(index=False)
    )
    for row in demand_scenarios.itertuples(index=False):
        audit_rows.append(
            {
                "analysis": "demand-scenario cost optimum",
                "scenario": row.scenario,
                "s": int(row.best_s),
                "S": int(row.best_S),
            }
        )
        if not pd.isna(row.service_s):
            audit_rows.append(
                {
                    "analysis": "demand-scenario 97% fill-rate choice",
                    "scenario": row.scenario,
                    "s": int(row.service_s),
                    "S": int(row.service_S),
                }
            )
    search_audit = audit_policy_search_boundaries(pd.DataFrame(audit_rows))

    write_stable_csv(baseline_trace, OUTPUT_DIR / "baseline_simulation_trace.csv")
    write_stable_csv(summary, OUTPUT_DIR / "policy_evaluation_summary.csv")
    write_stable_csv(sensitivity, OUTPUT_DIR / "cost_sensitivity_summary.csv")
    write_stable_csv(demand_scenarios, OUTPUT_DIR / "demand_scenario_summary.csv")
    write_stable_csv(demand_policy_results, OUTPUT_DIR / "demand_scenario_policy_evaluation.csv")
    write_stable_csv(decision_summary, OUTPUT_DIR / "service_level_policy_summary.csv")
    write_stable_csv(frontier, OUTPUT_DIR / "policy_pareto_frontier.csv")
    write_stable_csv(search_audit, OUTPUT_DIR / "search_boundary_audit.csv")
    assumptions = {
        "case_study": CASE_STUDY,
        "demand_scenarios": {
            name: asdict(scenario) for name, scenario in DEMAND_SCENARIOS.items()
        },
        "cost_parameters": asdict(BASELINE_COSTS),
        "inventory_system": {
            "review_period": "daily",
            "lead_time": 0,
            "shortage_treatment": "lost sales",
            "number_of_products": 1,
        },
        "simulation": {
            "periods_per_replication": arguments.periods,
            "warmup_periods_per_replication": arguments.warmup_periods,
            "replications_per_policy": arguments.replications,
            "base_seed": arguments.seed,
            "comparison_design": "common random numbers across policies",
        },
        "optimisation": {
            "method": "exhaustive enumeration over a finite policy grid",
            "objective": "minimise numerically evaluated stationary long-run expected daily cost",
            "reorder_points": list(
                range(POLICY_GRID_MIN_REORDER_POINT, POLICY_GRID_MAX_REORDER_POINT + 1)
            ),
            "order_up_to_rule": (
                f"S ranges from s + 1 through {POLICY_GRID_MAX_ORDER_UP_TO}"
            ),
            "tested_policy_count": len(policies),
            "service_fill_rate_target": SERVICE_FILL_RATE_TARGET,
            "search_boundary_audit": {
                "rule": "no selected policy may touch either artificial upper boundary",
                "maximum_selected_reorder_point": int(search_audit["s"].max()),
                "maximum_selected_order_up_to": int(search_audit["S"].max()),
                "reorder_point_upper_margin": int(search_audit["distance_to_max_s"].min()),
                "order_up_to_upper_margin": int(search_audit["distance_to_max_S"].min()),
                "natural_reorder_point_lower_bound": POLICY_GRID_MIN_REORDER_POINT,
                "status": "passed",
            },
        },
    }
    (OUTPUT_DIR / "model_assumptions.json").write_text(json.dumps(assumptions, indent=2), encoding="utf-8")

    plot_inventory_path(baseline_trace, recommended_policy)
    plot_policy_comparison(summary)
    plot_tradeoff(summary)
    plot_service_frontier(summary, frontier, cost_optimum, service_policy)
    plot_sensitivity(sensitivity)
    plot_demand_scenario_comparison(demand_scenarios)
    write_run_summary(
        summary,
        sensitivity,
        demand_scenarios,
        cost_optimum,
        service_policy,
        search_audit,
        arguments.periods,
        arguments.replications,
        arguments.warmup_periods,
    )

    print("Baseline analysis complete")
    print(f"Cost-optimal policy: s = {int(cost_optimum['s'])}, S = {int(cost_optimum['S'])}")
    print(f"Stationary average daily cost: {cost_optimum['average_daily_cost']:.2f}")
    print(f"Stationary stockout rate: {cost_optimum['stockout_rate']:.2%}")
    print(f"Simulation average daily cost: {cost_optimum['simulation_average_daily_cost']:.2f}")
    print(
        f"Service-constrained policy: s = {int(service_policy['s'])}, "
        f"S = {int(service_policy['S'])} at {service_policy['fill_rate']:.2%} fill rate"
    )
    print(f"Results written to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()

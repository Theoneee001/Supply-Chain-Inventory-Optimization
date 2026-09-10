"""Regression tests for the stochastic inventory model."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import inventory_model as inventory  # noqa: E402

from inventory_model import (  # noqa: E402
    CostParameters,
    DemandScenario,
    Policy,
    build_transition_matrix,
    evaluate_policies,
    markov_policy_metrics,
    pareto_frontier,
    plot_service_frontier,
    policy_grid,
    select_policy,
    simulate_policy,
    stationary_distribution,
)


class InventoryModelTests(unittest.TestCase):
    @staticmethod
    def exact_policy_summary() -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    "s": policy.reorder_point,
                    "S": policy.order_up_to,
                    **markov_policy_metrics(policy),
                }
                for policy in policy_grid()
            ]
        )

    def test_transition_matrix_rows_sum_to_one(self) -> None:
        transition = build_transition_matrix(Policy(1, 12))
        self.assertEqual(transition.shape, (13, 13))
        np.testing.assert_allclose(transition.sum(axis=1), np.ones(13))
        self.assertTrue(np.all(transition >= 0))

    def test_stationary_distribution_is_a_probability_vector(self) -> None:
        distribution = stationary_distribution(build_transition_matrix(Policy(2, 10)))
        self.assertAlmostEqual(float(distribution.sum()), 1.0, places=12)
        self.assertTrue(np.all(distribution >= 0))

    def test_simulation_is_reproducible_for_a_fixed_seed(self) -> None:
        first = simulate_policy(Policy(3, 8), periods=40, seed=19)
        second = simulate_policy(Policy(3, 8), periods=40, seed=19)
        self.assertTrue(first.equals(second))

    def test_published_csv_rounds_insignificant_platform_noise(self) -> None:
        first = pd.DataFrame({"metric": [1.234567890123]})
        second = pd.DataFrame({"metric": [1.234567890124]})
        with tempfile.TemporaryDirectory() as temporary_directory:
            first_path = Path(temporary_directory) / "first.csv"
            second_path = Path(temporary_directory) / "second.csv"
            inventory.write_stable_csv(first, first_path)
            inventory.write_stable_csv(second, second_path)
            self.assertEqual(first_path.read_bytes(), second_path.read_bytes())

    def test_simulation_discards_warmup_and_renumbers_measured_days(self) -> None:
        trace = simulate_policy(Policy(1, 12), periods=10, warmup_periods=20, seed=19)
        self.assertEqual(len(trace), 10)
        self.assertEqual(trace["day"].tolist(), list(range(1, 11)))

    def test_negative_warmup_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            simulate_policy(Policy(1, 12), periods=10, warmup_periods=-1)

    def test_warmup_simulation_interval_contains_exact_baseline_cost(self) -> None:
        policy = Policy(1, 12)
        result = evaluate_policies(
            [policy],
            replications=200,
            periods=365,
            warmup_periods=500,
            seed=42,
        ).iloc[0]
        exact_cost = markov_policy_metrics(policy)["average_daily_cost"]
        self.assertLessEqual(result["simulation_cost_95_ci_low"], exact_cost)
        self.assertGreaterEqual(result["simulation_cost_95_ci_high"], exact_cost)

    def test_zero_demand_trace_has_known_cost(self) -> None:
        no_demand = DemandScenario("no_demand", (0,), (1.0,))
        policy = Policy(1, 5)
        costs = CostParameters(order_fixed_cost=30, order_unit_cost=2, holding_cost=1, shortage_cost=8)
        trace = simulate_policy(
            policy,
            periods=8,
            starting_inventory=5,
            demand_scenario=no_demand,
            costs=costs,
        )
        self.assertTrue((trace["ending_inventory"] == 5).all())
        self.assertTrue((trace["total_cost"] == 5.0).all())

    def test_markov_result_agrees_with_a_long_random_trace(self) -> None:
        simple_demand = DemandScenario("zero_or_one", (0, 1), (0.5, 0.5))
        policy = Policy(1, 5)
        costs = CostParameters(order_fixed_cost=10, order_unit_cost=1, holding_cost=1, shortage_cost=5)
        exact = markov_policy_metrics(policy, demand_scenario=simple_demand, costs=costs)
        trace = simulate_policy(
            policy,
            periods=25_000,
            demand_scenario=simple_demand,
            costs=costs,
            seed=7,
        )
        self.assertAlmostEqual(float(trace["total_cost"].mean()), exact["average_daily_cost"], delta=0.2)

    def test_invalid_policy_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            simulate_policy(Policy(4, 4), periods=10)

    def test_policy_selection_supports_a_fill_rate_constraint(self) -> None:
        summary = self.exact_policy_summary()
        unconstrained = select_policy(summary)
        service_constrained = select_policy(summary, minimum_fill_rate=0.97)
        self.assertEqual((int(unconstrained["s"]), int(unconstrained["S"])), (1, 12))
        self.assertEqual((int(service_constrained["s"]), int(service_constrained["S"])), (2, 12))

    def test_policy_selection_rejects_an_infeasible_fill_rate(self) -> None:
        with self.assertRaises(ValueError):
            select_policy(self.exact_policy_summary(), minimum_fill_rate=1.01)

    def test_policy_selection_reports_a_missing_tie_break_column(self) -> None:
        incomplete_summary = self.exact_policy_summary().drop(columns="stockout_rate")
        with self.assertRaisesRegex(ValueError, "stockout_rate"):
            select_policy(incomplete_summary)

    def test_pareto_frontier_removes_cost_and_stockout_dominated_rows(self) -> None:
        summary = pd.DataFrame(
            [
                {"s": 1, "S": 8, "average_daily_cost": 10.0, "stockout_rate": 0.20},
                {"s": 2, "S": 8, "average_daily_cost": 11.0, "stockout_rate": 0.10},
                {"s": 3, "S": 8, "average_daily_cost": 12.0, "stockout_rate": 0.15},
                {"s": 1, "S": 7, "average_daily_cost": 9.0, "stockout_rate": 0.25},
            ]
        )
        frontier = pareto_frontier(summary)
        policies = {(int(row.s), int(row.S)) for row in frontier.itertuples()}
        self.assertEqual(policies, {(1, 7), (1, 8), (2, 8)})

    def test_service_frontier_figure_marks_both_decision_rules(self) -> None:
        summary = self.exact_policy_summary()
        frontier = pareto_frontier(summary)
        cost_optimum = select_policy(summary)
        service_policy = select_policy(summary, minimum_fill_rate=0.97)
        with tempfile.TemporaryDirectory() as temporary_directory:
            with patch("inventory_model.FIGURE_DIR", Path(temporary_directory)):
                plot_service_frontier(summary, frontier, cost_optimum, service_policy)
            figure = Path(temporary_directory, "cost_service_frontier.svg").read_text(encoding="utf-8")
        self.assertIn("Cost optimum (1, 12)", figure)
        self.assertIn("97% fill-rate choice (2, 12)", figure)

    def test_declared_demand_scenarios_are_valid_and_distinct(self) -> None:
        scenarios = getattr(inventory, "DEMAND_SCENARIOS", None)
        self.assertIsNotNone(scenarios, "DEMAND_SCENARIOS must be declared")
        if scenarios is None:
            return

        self.assertEqual(
            set(scenarios),
            {"baseline_mixed", "steady", "volatile", "promotion_peak"},
        )
        moments: set[tuple[float, float]] = set()
        for scenario in scenarios.values():
            values, probabilities = scenario.arrays()
            mean = float(np.dot(values, probabilities))
            variance = float(np.dot((values - mean) ** 2, probabilities))
            moments.add((round(mean, 6), round(variance, 6)))
        self.assertEqual(len(moments), 4)

    def test_demand_scenario_analysis_evaluates_each_policy_and_selects_its_minimum(self) -> None:
        analyse = getattr(inventory, "demand_scenario_analysis", None)
        scenarios = getattr(inventory, "DEMAND_SCENARIOS", None)
        self.assertIsNotNone(analyse, "demand_scenario_analysis must be implemented")
        self.assertIsNotNone(scenarios, "DEMAND_SCENARIOS must be declared")
        if analyse is None or scenarios is None:
            return

        policies = [Policy(1, 6), Policy(2, 7)]
        scenario_summary, policy_results = analyse(
            policies,
            scenarios=scenarios,
            replications=4,
            periods=20,
            warmup_periods=10,
            seed=9,
        )

        self.assertEqual(len(scenario_summary), 4)
        self.assertEqual(len(policy_results), 8)
        self.assertEqual(set(scenario_summary["scenario"]), set(scenarios))
        service_columns = {"service_s", "service_S", "service_fill_rate"}
        self.assertTrue(
            service_columns.issubset(scenario_summary.columns),
            "Scenario summary must report the illustrative 97% service choice",
        )
        if not service_columns.issubset(scenario_summary.columns):
            return
        for row in scenario_summary.itertuples(index=False):
            candidates = policy_results.loc[policy_results["scenario"] == row.scenario]
            minimum = candidates.sort_values(
                ["average_daily_cost", "stockout_rate", "s", "S"]
            ).iloc[0]
            self.assertEqual((row.best_s, row.best_S), (minimum["s"], minimum["S"]))
            self.assertAlmostEqual(row.exact_average_daily_cost, minimum["average_daily_cost"])
            self.assertLessEqual(row.simulation_cost_95_ci_low, row.simulation_average_daily_cost)
            self.assertGreaterEqual(row.simulation_cost_95_ci_high, row.simulation_average_daily_cost)

            service_feasible = candidates.loc[candidates["fill_rate"] >= 0.97].sort_values(
                ["average_daily_cost", "stockout_rate", "s", "S"]
            )
            if service_feasible.empty:
                self.assertTrue(pd.isna(row.service_s))
                self.assertTrue(pd.isna(row.service_S))
            else:
                service_minimum = service_feasible.iloc[0]
                self.assertEqual(
                    (row.service_s, row.service_S),
                    (service_minimum["s"], service_minimum["S"]),
                )
                self.assertGreaterEqual(row.service_fill_rate, 0.97)


if __name__ == "__main__":
    unittest.main(verbosity=2)

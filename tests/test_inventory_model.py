"""Regression tests for the stochastic inventory model."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from inventory_model import (  # noqa: E402
    CostParameters,
    DemandScenario,
    Policy,
    build_transition_matrix,
    markov_policy_metrics,
    simulate_policy,
    stationary_distribution,
)


class InventoryModelTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main(verbosity=2)

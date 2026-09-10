"""Build and execute the narrative Jupyter notebook from tested project code."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import nbformat
from nbclient import NotebookClient


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_PATH = ROOT / "notebooks" / "supply_chain_inventory_optimization.ipynb"
NOTEBOOK_PYTHON_VERSION = "3.12"
STATIONARY_RESIDUAL_PREFIX = "Stationary residual ||pi P - pi||_inf: "


def markdown(source: str) -> nbformat.NotebookNode:
    return nbformat.v4.new_markdown_cell(dedent(source).strip())


def code(source: str) -> nbformat.NotebookNode:
    return nbformat.v4.new_code_cell(dedent(source).strip())


def stabilise_notebook(notebook: nbformat.NotebookNode) -> None:
    """Remove runtime-specific noise from the published notebook."""
    notebook.metadata.setdefault("language_info", {})["version"] = NOTEBOOK_PYTHON_VERSION
    for cell in notebook.cells:
        cell.metadata.pop("execution", None)
        for output in cell.get("outputs", []):
            if output.get("output_type") != "stream":
                continue
            lines = []
            for line in str(output.get("text", "")).splitlines(keepends=True):
                if line.startswith(STATIONARY_RESIDUAL_PREFIX):
                    suffix = "\n" if line.endswith("\n") else ""
                    value = float(line[len(STATIONARY_RESIDUAL_PREFIX) :].strip())
                    line = f"{STATIONARY_RESIDUAL_PREFIX}{value:.2e}{suffix}"
                lines.append(line)
            output["text"] = "".join(lines)


def build_notebook() -> nbformat.NotebookNode:
    cells = [
        markdown(
            """
            # Stochastic Inventory Optimisation for Ecommerce

            ## A Markov-chain and Monte Carlo study of one category-neutral SKU

            This notebook follows the full argument behind the GitHub report. The case is an illustrative ecommerce fulfilment centre replenishing one generic non-perishable SKU from a nearby central warehouse. The category is intentionally unspecified, and the inputs are not company observations.

            **Question:** Which `(s, S)` policy minimises stationary long-run expected daily cost, how does the answer respond to different demand distributions, and which policy is cheapest under an illustrative 97% fill-rate target?
            """
        ),
        markdown(
            """
            ## Mathematical route

            The analysis uses undergraduate ideas from discrete probability, linear algebra, stochastic processes, statistics, and finite optimisation:

            1. represent inventory as a finite Markov chain;
            2. calculate its stationary distribution;
            3. weight state-demand costs by stationary probabilities;
            4. enumerate 180 feasible policies and audit the artificial upper boundaries;
            5. check the implementation with warm-up-adjusted Monte Carlo simulation;
            6. impose an illustrative 97% fill-rate constraint and inspect the cost-service Pareto frontier;
            7. repeat the optimisation under four different demand distributions.
            """
        ),
        code(
            """
            from pathlib import Path
            import sys

            import numpy as np
            import pandas as pd
            from IPython.display import SVG, display

            ROOT = Path.cwd()
            if ROOT.name == "notebooks":
                ROOT = ROOT.parent
            sys.path.insert(0, str(ROOT / "src"))

            from inventory_model import (
                BASELINE_COSTS,
                BASELINE_DEMAND,
                CASE_STUDY,
                POLICY_GRID_MAX_ORDER_UP_TO,
                POLICY_GRID_MAX_REORDER_POINT,
                POLICY_GRID_MIN_REORDER_POINT,
                SERVICE_FILL_RATE_TARGET,
                Policy,
                build_transition_matrix,
                markov_policy_metrics,
                pareto_frontier,
                select_policy,
                simulate_policy,
                stationary_distribution,
            )

            pd.set_option("display.max_columns", 30)
            CASE_STUDY
            """
        ),
        markdown(
            """
            ## 1. Assumptions

            The model reviews stock daily, assumes same-day transfer from the central warehouse, and treats unmet demand as lost sales. These choices make the first model finite and inspectable. They are modelling assumptions, not facts about every ecommerce operation.
            """
        ),
        code(
            """
            demand = pd.DataFrame(
                {
                    "daily_demand": BASELINE_DEMAND.values,
                    "probability": BASELINE_DEMAND.probabilities,
                }
            )
            demand["weighted_demand"] = demand["daily_demand"] * demand["probability"]
            expected_demand = demand["weighted_demand"].sum()
            demand_variance = (
                ((demand["daily_demand"] - expected_demand) ** 2) * demand["probability"]
            ).sum()
            demand_display = demand.copy()
            demand_display["probability"] = demand_display["probability"].map("{:.0%}".format)
            demand_display["weighted_demand"] = demand_display["weighted_demand"].map("{:.3f}".format)
            display(demand_display)
            print(f"E[D] = {expected_demand:.2f} units; Var(D) = {demand_variance:.4f}")

            pd.DataFrame(
                {
                    "parameter": ["Fixed order cost K", "Unit order cost c", "Holding cost h", "Shortage cost p"],
                    "value": [
                        BASELINE_COSTS.order_fixed_cost,
                        BASELINE_COSTS.order_unit_cost,
                        BASELINE_COSTS.holding_cost,
                        BASELINE_COSTS.shortage_cost,
                    ],
                }
            )
            """
        ),
        markdown(
            """
            ## 2. State transition and one-day cost

            For opening inventory `I_t`, the policy replenishes to `S` whenever `I_t <= s`. After demand `D_t`, the next state is

            ```text
            I_(t+1) = max(I_t + Q_t - D_t, 0).
            ```

            Daily cost combines the order setup charge, unit purchasing cost, ending-inventory holding cost, and shortage penalty. Under a fixed policy, the next state depends only on the current state and the new demand draw, so the process has the Markov property.
            """
        ),
        code(
            """
            published_decisions = pd.read_csv(ROOT / "outputs" / "service_level_policy_summary.csv")
            published_cost_choice = published_decisions.loc[
                published_decisions["minimum_fill_rate"] == 0
            ].iloc[0]
            cost_policy = Policy(int(published_cost_choice["s"]), int(published_cost_choice["S"]))
            transition = build_transition_matrix(cost_policy)
            stationary = stationary_distribution(transition)

            print("Transition shape:", transition.shape)
            print("Maximum row-sum error:", np.abs(transition.sum(axis=1) - 1).max())
            print("Stationary residual ||pi P - pi||_inf:", np.abs(stationary @ transition - stationary).max())

            stationary_table = pd.DataFrame(
                {"opening_inventory": np.arange(len(stationary)), "stationary_probability": stationary}
            )
            stationary_display = stationary_table.copy()
            stationary_display["stationary_probability"] = stationary_display["stationary_probability"].map("{:.2%}".format)
            display(stationary_display)
            """
        ),
        markdown(
            """
            ## 3. Stationary long-run result

            The stationary distribution gives the long-run proportion of days spent in each state. Weighting expected one-day outcomes by these probabilities produces deterministic finite-model metrics, evaluated numerically to a tolerance of `1e-14`.
            """
        ),
        code(
            """
            exact_metrics = pd.Series(markov_policy_metrics(cost_policy), name="exact_result")
            exact_metrics.to_frame().round(4)
            """
        ),
        markdown(
            """
            ## 4. Independent Monte Carlo check

            The saved experiment uses 200 replications. Each replication discards 365 warm-up days before measuring the next 365 days. The warm-up prevents the chosen full-stock initial state from biasing a short measurement window.
            """
        ),
        code(
            """
            decisions = pd.read_csv(ROOT / "outputs" / "service_level_policy_summary.csv")
            validation_columns = [
                "decision_rule",
                "s",
                "S",
                "average_daily_cost",
                "simulation_average_daily_cost",
                "simulation_cost_95_ci_low",
                "simulation_cost_95_ci_high",
                "stockout_rate",
                "fill_rate",
            ]
            validation = decisions[validation_columns].copy()
            for column in [
                "average_daily_cost",
                "simulation_average_daily_cost",
                "simulation_cost_95_ci_low",
                "simulation_cost_95_ci_high",
            ]:
                validation[column] = validation[column].map("{:.4f}".format)
            for column in ["stockout_rate", "fill_rate"]:
                validation[column] = validation[column].map("{:.2%}".format)
            validation
            """
        ),
        code(
            """
            trace = simulate_policy(cost_policy, periods=20, warmup_periods=365, seed=7)
            display(trace.head(10))
            display(SVG(filename=str(ROOT / "outputs" / "figures" / "inventory_path.svg")))
            """
        ),
        markdown(
            """
            ## 5. Exhaustive policy search

            The feasible grid contains 180 policies: `s` ranges from 0 to 8, and `S` ranges from `s + 1` to 24. This includes every integer pair satisfying the standard requirement `S > s` inside the rectangle. Reorder point zero is the natural physical lower bound. The program rejects publication if any selected baseline, demand, service, or cost-sensitivity policy touches either artificial upper bound. The largest selected values are `s=3` and `S=21`, leaving margins of 5 and 3 units. Thus `(0, 14)` is the exact minimum **within an audited finite grid**, not a claim over every possible business environment.
            """
        ),
        code(
            """
            evaluation = pd.read_csv(ROOT / "outputs" / "policy_evaluation_summary.csv")
            columns = ["s", "S", "average_daily_cost", "stockout_rate", "fill_rate", "average_ending_inventory"]
            top_policies = evaluation.loc[:9, columns].copy()
            top_policies["average_daily_cost"] = top_policies["average_daily_cost"].map("{:.2f}".format)
            top_policies["stockout_rate"] = top_policies["stockout_rate"].map("{:.2%}".format)
            top_policies["fill_rate"] = top_policies["fill_rate"].map("{:.2%}".format)
            top_policies["average_ending_inventory"] = top_policies["average_ending_inventory"].map("{:.2f}".format)
            display(top_policies)
            cost_components = evaluation.loc[
                (evaluation["s"] == cost_policy.reorder_point)
                & (evaluation["S"] == cost_policy.order_up_to),
                [
                    "average_fixed_order_cost",
                    "average_unit_order_cost",
                    "average_holding_cost",
                    "average_shortage_cost",
                    "average_daily_cost",
                ],
            ].T
            cost_components.columns = ["cost per day"]
            display(cost_components.round(4))
            boundary_audit = pd.read_csv(ROOT / "outputs" / "search_boundary_audit.csv")
            display(boundary_audit)
            display(SVG(filename=str(ROOT / "outputs" / "figures" / "policy_cost_heatmap.svg")))
            """
        ),
        markdown(
            """
            ## 6. Service constraint and Pareto frontier

            Cost alone selects `(0, 14)`, with a fill rate of `90.60%`. If the fulfilment centre adopts an illustrative target of at least `97%`, the feasible policy set changes and `(2, 15)` becomes the minimum-cost choice. It costs `0.3585` more per day (`1.84%`) and lowers stockout probability by `9.40` percentage points. The threshold is a scenario input, not an industry benchmark.
            """
        ),
        code(
            """
            exact_summary = evaluation[["s", "S", "average_daily_cost", "stockout_rate", "fill_rate"]]
            selected_cost = select_policy(exact_summary)
            selected_service = select_policy(exact_summary, minimum_fill_rate=SERVICE_FILL_RATE_TARGET)
            frontier = pareto_frontier(exact_summary)

            print("Cost optimum:", (int(selected_cost["s"]), int(selected_cost["S"])))
            print("97% fill-rate choice:", (int(selected_service["s"]), int(selected_service["S"])))
            frontier_display = frontier.copy()
            frontier_display["average_daily_cost"] = frontier_display["average_daily_cost"].map("{:.2f}".format)
            frontier_display["stockout_rate"] = frontier_display["stockout_rate"].map("{:.2%}".format)
            frontier_display["fill_rate"] = frontier_display["fill_rate"].map("{:.2%}".format)
            display(frontier_display)
            display(SVG(filename=str(ROOT / "outputs" / "figures" / "cost_service_frontier.svg")))
            """
        ),
        markdown(
            """
            ## 7. Sensitivity analysis

            The recommendation should move when the economics move. Increasing shortage cost makes earlier replenishment worthwhile; increasing holding cost supports a leaner stock target.
            """
        ),
        code(
            """
            sensitivity = pd.read_csv(ROOT / "outputs" / "cost_sensitivity_summary.csv")
            sensitivity_display = sensitivity.copy()
            sensitivity_display["best_average_daily_cost"] = sensitivity_display["best_average_daily_cost"].map("{:.2f}".format)
            sensitivity_display["best_stockout_rate"] = sensitivity_display["best_stockout_rate"].map("{:.2%}".format)
            sensitivity_display["best_fill_rate"] = sensitivity_display["best_fill_rate"].map("{:.2%}".format)
            sensitivity_display["best_average_ending_inventory"] = sensitivity_display["best_average_ending_inventory"].map("{:.2f}".format)
            display(sensitivity_display)
            display(SVG(filename=str(ROOT / "outputs" / "figures" / "cost_sensitivity.svg")))
            """
        ),
        markdown(
            """
            ## 8. Demand-distribution sensitivity

            The execution manual asks for optimisation under different demand distributions. Four scenarios separate changes in average demand from changes in variability. Cost-only choices are `(0, 14)` for baseline and steady demand, `(1, 14)` under volatile demand, and `(2, 18)` during the promotion peak. The 97% choices are `(2, 15)`, `(1, 16)`, `(3, 16)`, and `(3, 18)` respectively. A fresh 180-policy enumeration produces every row.
            """
        ),
        code(
            """
            demand_scenarios = pd.read_csv(ROOT / "outputs" / "demand_scenario_summary.csv")
            demand_display = demand_scenarios[
                [
                    "scenario",
                    "demand_mean",
                    "demand_variance",
                    "best_s",
                    "best_S",
                    "service_s",
                    "service_S",
                    "exact_average_daily_cost",
                    "exact_fill_rate",
                    "simulation_average_daily_cost",
                ]
            ].copy()
            demand_display["exact_average_daily_cost"] = demand_display["exact_average_daily_cost"].map("{:.2f}".format)
            demand_display["simulation_average_daily_cost"] = demand_display["simulation_average_daily_cost"].map("{:.2f}".format)
            demand_display["exact_fill_rate"] = demand_display["exact_fill_rate"].map("{:.2%}".format)
            display(demand_display)
            display(SVG(filename=str(ROOT / "outputs" / "figures" / "demand_scenario_comparison.svg")))
            """
        ),
        markdown(
            """
            ## Conclusion and limits

            The mathematical answer depends on the question. `(0, 14)` has the lowest stationary expected cost in the audited baseline grid. `(2, 15)` is the least-cost policy that meets the illustrative 97% fill-rate target under baseline demand. The cost gap between `(0, 14)` and `(1, 14)` is only about `0.0031` per day, so the exact ranking is sensitive to input calibration even though it is numerically well defined here. Distribution stress tests show that both the reorder point and target respond to variance and upward demand shifts.

            The inputs are illustrative, demand is independent across days, lead time is treated as zero, shortages are lost sales, and only one SKU is modelled. A next empirical version should estimate demand from licensed transaction data and add positive lead time. AI supported review, debugging, prose editing, and visual QA; all numerical claims shown here come from executable code and tested outputs.
            """
        ),
    ]

    notebook = nbformat.v4.new_notebook(cells=cells)
    for index, cell in enumerate(notebook.cells, start=1):
        cell["id"] = f"inventory-{index:02d}"
    notebook.metadata["kernelspec"] = {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3",
    }
    notebook.metadata["language_info"] = {
        "name": "python",
        "version": NOTEBOOK_PYTHON_VERSION,
    }
    return notebook


def main() -> None:
    notebook = build_notebook()
    client = NotebookClient(
        notebook,
        timeout=240,
        kernel_name="python3",
        resources={"metadata": {"path": str(ROOT)}},
    )
    client.execute()
    stabilise_notebook(notebook)
    nbformat.write(notebook, NOTEBOOK_PATH)
    print(f"Executed notebook written to {NOTEBOOK_PATH}")


if __name__ == "__main__":
    main()

"""Validate regenerated project artifacts using cross-platform invariants."""

from __future__ import annotations

import json
import re
import sys
from dataclasses import replace
from pathlib import Path

import nbformat
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"
sys.path.insert(0, str(ROOT / "src"))

from inventory_model import (  # noqa: E402
    BASELINE_COSTS,
    BASELINE_DEMAND,
    DEMAND_SCENARIOS,
    SERVICE_FILL_RATE_TARGET,
    build_transition_matrix,
    markov_policy_metrics,
    policy_grid,
    select_policy,
    stationary_distribution,
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def require_complete_policy_grid(
    scenario_policies: pd.DataFrame,
    expected_scenarios: set[str],
    baseline_policies: pd.DataFrame,
) -> None:
    """Require every scenario to contain the same unique policy grid."""
    expected_grid = {
        (int(row.s), int(row.S)) for row in baseline_policies[["s", "S"]].itertuples(index=False)
    }
    for scenario in expected_scenarios:
        rows = scenario_policies.loc[scenario_policies["scenario"] == scenario, ["s", "S"]]
        observed = [(int(row.s), int(row.S)) for row in rows.itertuples(index=False)]
        require(
            len(observed) == len(expected_grid)
            and len(set(observed)) == len(observed)
            and set(observed) == expected_grid,
            f"Demand scenario {scenario} does not contain the complete unique policy grid.",
        )


def verify_tables() -> None:
    policies = pd.read_csv(OUTPUTS / "policy_evaluation_summary.csv")
    require(len(policies) == 180, "Expected 180 policies in the baseline grid.")
    require(not policies.isna().any().any(), "Policy results contain missing values.")
    require(not policies.duplicated(["s", "S"]).any(), "Policy results contain duplicates.")

    optimum = policies.sort_values(["average_daily_cost", "stockout_rate", "s", "S"]).iloc[0]
    require((int(optimum["s"]), int(optimum["S"])) == (0, 14), "Unexpected cost optimum.")
    require(abs(float(optimum["average_daily_cost"]) - 19.4352369768) < 1e-8, "Exact cost changed.")
    component_columns = [
        "average_fixed_order_cost",
        "average_unit_order_cost",
        "average_holding_cost",
        "average_shortage_cost",
    ]
    require(
        (policies[component_columns].sum(axis=1) - policies["average_daily_cost"]).abs().max()
        < 1e-8,
        "Published cost components do not reconcile to total expected cost.",
    )
    require(
        float(optimum["simulation_cost_95_ci_low"])
        <= float(optimum["average_daily_cost"])
        <= float(optimum["simulation_cost_95_ci_high"]),
        "Exact cost falls outside the simulation interval.",
    )

    decisions = pd.read_csv(OUTPUTS / "service_level_policy_summary.csv")
    require(len(decisions) == 2, "Expected two published decision rules.")
    service_choice = decisions.loc[decisions["minimum_fill_rate"] == 0.97]
    require(len(service_choice) == 1, "The 97 percent service decision is missing.")
    service_choice = service_choice.iloc[0]
    require((int(service_choice["s"]), int(service_choice["S"])) == (2, 15), "Unexpected service choice.")
    require(float(service_choice["fill_rate"]) >= 0.97, "Service choice misses its fill-rate target.")

    frontier = pd.read_csv(OUTPUTS / "policy_pareto_frontier.csv")
    sensitivity = pd.read_csv(OUTPUTS / "cost_sensitivity_summary.csv")
    require(len(frontier) == 25, "Expected 25 non-dominated policies.")
    require(len(sensitivity) == 9, "Expected nine cost-sensitivity scenarios.")

    demand_summary = pd.read_csv(OUTPUTS / "demand_scenario_summary.csv")
    demand_policies = pd.read_csv(OUTPUTS / "demand_scenario_policy_evaluation.csv")
    expected_scenarios = {"baseline_mixed", "steady", "volatile", "promotion_peak"}
    require(set(demand_summary["scenario"]) == expected_scenarios, "Demand scenarios are incomplete.")
    require(len(demand_policies) == 720, "Expected 180 policies for each of four demand scenarios.")
    require_complete_policy_grid(demand_policies, expected_scenarios, policies)
    for row in demand_summary.itertuples(index=False):
        candidates = demand_policies.loc[demand_policies["scenario"] == row.scenario]
        optimum = candidates.sort_values(["average_daily_cost", "stockout_rate", "s", "S"]).iloc[0]
        require(
            (int(row.best_s), int(row.best_S)) == (int(optimum["s"]), int(optimum["S"])),
            f"Incorrect cost optimum for demand scenario {row.scenario}.",
        )
        for summary_value, policy_value, metric in (
            (row.exact_average_daily_cost, optimum["average_daily_cost"], "cost"),
            (row.exact_stockout_rate, optimum["stockout_rate"], "stockout rate"),
            (row.exact_fill_rate, optimum["fill_rate"], "fill rate"),
            (row.exact_average_ending_inventory, optimum["average_ending_inventory"], "inventory"),
        ):
            require(
                abs(float(summary_value) - float(policy_value)) < 1e-10,
                f"Scenario summary {metric} disagrees with policy evidence for {row.scenario}.",
            )
        service = candidates.loc[candidates["fill_rate"] >= 0.97].sort_values(
            ["average_daily_cost", "stockout_rate", "s", "S"]
        ).iloc[0]
        require(
            (int(row.service_s), int(row.service_S)) == (int(service["s"]), int(service["S"])),
            f"Incorrect service choice for demand scenario {row.scenario}.",
        )
        require(
            abs(float(row.service_average_daily_cost) - float(service["average_daily_cost"])) < 1e-10
            and abs(float(row.service_fill_rate) - float(service["fill_rate"])) < 1e-10,
            f"Service metrics disagree with policy evidence for {row.scenario}.",
        )
        require(
            float(row.simulation_cost_95_ci_low)
            <= float(row.exact_average_daily_cost)
            <= float(row.simulation_cost_95_ci_high),
            f"Stationary cost falls outside the simulation interval for {row.scenario}.",
        )

    boundary_audit = pd.read_csv(OUTPUTS / "search_boundary_audit.csv")
    require(len(boundary_audit) == 19, "Expected 19 published boundary-audit decisions.")
    require(
        not boundary_audit["touches_upper_boundary"].astype(str).str.lower().eq("true").any(),
        "A published decision touches an artificial upper search boundary.",
    )
    require(
        int(boundary_audit["distance_to_max_s"].min()) == 5
        and int(boundary_audit["distance_to_max_S"].min()) == 3,
        "Search-boundary margins changed unexpectedly.",
    )


def verify_configuration_and_figures() -> None:
    assumptions = json.loads((OUTPUTS / "model_assumptions.json").read_text(encoding="utf-8"))
    require(
        assumptions["case_study"]["category_status"] == "category-neutral by design",
        "The case must remain category-neutral.",
    )
    require(len(assumptions["demand_scenarios"]) == 4, "Expected four declared demand distributions.")
    require(assumptions["optimisation"]["tested_policy_count"] == 180, "Policy count changed.")
    require(assumptions["optimisation"]["service_fill_rate_target"] == 0.97, "Service target changed.")
    require(
        assumptions["optimisation"]["search_boundary_audit"]["status"] == "passed",
        "Search-boundary audit is not recorded as passed.",
    )

    figure_names = {
        "cost_sensitivity.svg",
        "cost_service_frontier.svg",
        "demand_scenario_comparison.svg",
        "inventory_path.svg",
        "inventory_stockout_tradeoff.svg",
        "policy_cost_heatmap.svg",
    }
    for name in figure_names:
        figure = OUTPUTS / "figures" / name
        require(figure.exists() and figure.stat().st_size > 1_000, f"Figure is missing or empty: {name}")


def verify_mathematical_cross_checks() -> None:
    """Compare solvers and confirm published choices in a larger exact grid."""

    maximum_distribution_gap = 0.0
    maximum_row_sum_error = 0.0
    maximum_stationary_residual = 0.0
    for scenario in DEMAND_SCENARIOS.values():
        for policy in policy_grid():
            transition = build_transition_matrix(policy, scenario)
            equations = transition.T - np.eye(transition.shape[0])
            target = np.zeros(transition.shape[0])
            equations[-1, :] = 1.0
            target[-1] = 1.0
            linear_solution = np.linalg.solve(equations, target)
            iterative_solution = stationary_distribution(transition)
            maximum_distribution_gap = max(
                maximum_distribution_gap,
                float(np.max(np.abs(linear_solution - iterative_solution))),
            )
            maximum_row_sum_error = max(
                maximum_row_sum_error,
                float(np.max(np.abs(transition.sum(axis=1) - 1))),
            )
            maximum_stationary_residual = max(
                maximum_stationary_residual,
                float(np.max(np.abs(iterative_solution @ transition - iterative_solution))),
            )
    require(maximum_row_sum_error < 1e-12, "Transition rows fail the independent sum check.")
    require(maximum_stationary_residual < 1e-10, "Stationary residual is unexpectedly large.")
    require(
        maximum_distribution_gap < 1e-10,
        "Power iteration disagrees with the independent linear-system solution.",
    )

    expanded_policies = policy_grid(minimum_s=0, maximum_s=12, maximum_S=40)

    def exact_frame(demand=BASELINE_DEMAND, costs=BASELINE_COSTS) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    "s": policy.reorder_point,
                    "S": policy.order_up_to,
                    **markov_policy_metrics(policy, demand, costs),
                }
                for policy in expanded_policies
            ]
        )

    expanded_rows: list[dict[str, str | int]] = []
    baseline = exact_frame()
    for analysis, target_fill_rate in (
        ("baseline cost optimum", None),
        ("baseline 97% fill-rate choice", SERVICE_FILL_RATE_TARGET),
    ):
        choice = select_policy(baseline, target_fill_rate)
        expanded_rows.append(
            {
                "analysis": analysis,
                "scenario": "baseline_mixed",
                "s": int(choice["s"]),
                "S": int(choice["S"]),
            }
        )
    for holding_cost in (0.5, 1.0, 2.0):
        for shortage_cost in (4.0, 8.0, 16.0):
            costs = replace(
                BASELINE_COSTS,
                holding_cost=holding_cost,
                shortage_cost=shortage_cost,
            )
            choice = select_policy(exact_frame(costs=costs))
            expanded_rows.append(
                {
                    "analysis": "cost sensitivity optimum",
                    "scenario": f"holding={holding_cost:g}; shortage={shortage_cost:g}",
                    "s": int(choice["s"]),
                    "S": int(choice["S"]),
                }
            )
    for scenario_name, scenario in DEMAND_SCENARIOS.items():
        results = exact_frame(demand=scenario)
        for analysis, target_fill_rate in (
            ("demand-scenario cost optimum", None),
            ("demand-scenario 97% fill-rate choice", SERVICE_FILL_RATE_TARGET),
        ):
            choice = select_policy(results, target_fill_rate)
            expanded_rows.append(
                {
                    "analysis": analysis,
                    "scenario": scenario_name,
                    "s": int(choice["s"]),
                    "S": int(choice["S"]),
                }
            )

    published = pd.read_csv(OUTPUTS / "search_boundary_audit.csv")
    columns = ["analysis", "scenario", "s", "S"]
    published_records = {
        (str(row.analysis), str(row.scenario), int(row.s), int(row.S))
        for row in published[columns].itertuples(index=False)
    }
    expanded_records = {
        (str(row["analysis"]), str(row["scenario"]), int(row["s"]), int(row["S"]))
        for row in expanded_rows
    }
    require(
        published_records == expanded_records,
        "A published decision changes in the expanded 442-policy verification grid.",
    )


def verify_notebook_and_report() -> None:
    notebook_path = ROOT / "notebooks" / "supply_chain_inventory_optimization.ipynb"
    notebook = nbformat.read(notebook_path, as_version=4)
    code_cells = [cell for cell in notebook.cells if cell.cell_type == "code"]
    require(len(code_cells) == 10, "Expected ten notebook code cells.")
    require(all(cell.execution_count is not None for cell in code_cells), "Notebook has unexecuted code cells.")
    require(
        not any(output.output_type == "error" for cell in code_cells for output in cell.get("outputs", [])),
        "Notebook contains an execution error.",
    )
    notebook_text = json.dumps(notebook)
    for evidence in ("promotion_peak", "service_s", "97.70%", "search_boundary_audit.csv"):
        require(evidence in notebook_text, f"Notebook is missing executed scenario evidence: {evidence}")

    report_source = (ROOT / "report" / "final_report.md").read_text(encoding="utf-8")
    for evidence in (
        "19.4352",
        "19.4512",
        "97.70%",
        "(2, 15)",
        "180",
        "boundary audit",
        "category-neutral",
        "promotion peak",
    ):
        require(evidence in report_source, f"Report is missing evidence: {evidence}")
    require(
        "generic non-perishable SKU" in report_source and "category-neutral" in report_source,
        "Report must describe the case as a generic, category-neutral SKU.",
    )

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    readme_lower = readme.lower()
    for evidence in ("category-neutral", "720", "promotion peak", "(3, 18)", "97%"):
        require(evidence in readme_lower, f"README is missing scenario evidence: {evidence}")

    application_materials = (ROOT / "docs" / "application_materials.md").read_text(
        encoding="utf-8"
    )
    ps_match = re.search(
        r"## Personal Statement Material \(\d+ words\)\n\n(.*?)\n\n## Interview",
        application_materials,
        flags=re.DOTALL,
    )
    require(ps_match is not None, "Personal-statement material is missing.")
    ps_word_count = len(
        re.findall(
            r"[A-Za-z]+(?:['-][A-Za-z]+)*|[0-9]+(?:\.[0-9]+)?%?",
            ps_match.group(1) if ps_match else "",
        )
    )
    require(
        150 <= ps_word_count <= 200,
        f"Personal-statement material is {ps_word_count} words, outside 150-200.",
    )

    prose_lines: list[str] = []
    in_code = False
    for line in report_source.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code = not in_code
            continue
        if in_code or not stripped or stripped.startswith(("#", "|", "![")):
            continue
        prose_lines.append(stripped)
    word_count = len(
        re.findall(r"[A-Za-z]+(?:['-][A-Za-z]+)*|[0-9]+(?:\.[0-9]+)?%?", " ".join(prose_lines))
    )
    require(3_000 <= word_count <= 5_000, f"Report prose word count is {word_count}, outside 3,000-5,000.")
    report_pdf = ROOT / "report" / "final_report.pdf"
    require(report_pdf.exists() and report_pdf.stat().st_size > 50_000, "PDF report is missing or unexpectedly small.")


def main() -> None:
    verify_tables()
    verify_configuration_and_figures()
    verify_mathematical_cross_checks()
    verify_notebook_and_report()
    print("Artifact verification passed: policies, decisions, figures, notebook, and report are consistent.")


if __name__ == "__main__":
    main()

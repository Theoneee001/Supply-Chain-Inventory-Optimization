"""Validate regenerated project artifacts using cross-platform invariants."""

from __future__ import annotations

import json
import re
from pathlib import Path

import nbformat
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"


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
    require(len(policies) == 45, "Expected 45 policies in the baseline grid.")
    require(not policies.isna().any().any(), "Policy results contain missing values.")
    require(not policies.duplicated(["s", "S"]).any(), "Policy results contain duplicates.")

    optimum = policies.sort_values(["average_daily_cost", "stockout_rate", "s", "S"]).iloc[0]
    require((int(optimum["s"]), int(optimum["S"])) == (1, 12), "Unexpected cost optimum.")
    require(abs(float(optimum["average_daily_cost"]) - 19.6568008768) < 1e-8, "Exact cost changed.")
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
    require((int(service_choice["s"]), int(service_choice["S"])) == (2, 12), "Unexpected service choice.")
    require(float(service_choice["fill_rate"]) >= 0.97, "Service choice misses its fill-rate target.")

    frontier = pd.read_csv(OUTPUTS / "policy_pareto_frontier.csv")
    sensitivity = pd.read_csv(OUTPUTS / "cost_sensitivity_summary.csv")
    require(len(frontier) == 5, "Expected five non-dominated policies.")
    require(len(sensitivity) == 9, "Expected nine cost-sensitivity scenarios.")

    demand_summary = pd.read_csv(OUTPUTS / "demand_scenario_summary.csv")
    demand_policies = pd.read_csv(OUTPUTS / "demand_scenario_policy_evaluation.csv")
    expected_scenarios = {"baseline_mixed", "steady", "volatile", "promotion_peak"}
    require(set(demand_summary["scenario"]) == expected_scenarios, "Demand scenarios are incomplete.")
    require(len(demand_policies) == 180, "Expected 45 policies for each of four demand scenarios.")
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


def verify_configuration_and_figures() -> None:
    assumptions = json.loads((OUTPUTS / "model_assumptions.json").read_text(encoding="utf-8"))
    require(
        assumptions["case_study"]["category_status"] == "category-neutral by design",
        "The case must remain category-neutral.",
    )
    require(len(assumptions["demand_scenarios"]) == 4, "Expected four declared demand distributions.")
    require(assumptions["optimisation"]["tested_policy_count"] == 45, "Policy count changed.")
    require(assumptions["optimisation"]["service_fill_rate_target"] == 0.97, "Service target changed.")

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
    for evidence in ("promotion_peak", "service_s", "97.09%"):
        require(evidence in notebook_text, f"Notebook is missing executed scenario evidence: {evidence}")

    report_source = (ROOT / "report" / "final_report.md").read_text(encoding="utf-8")
    for evidence in (
        "19.6568",
        "19.6571",
        "97.09%",
        "(2, 12)",
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
    for evidence in ("category-neutral", "180", "promotion peak", "(4, 12)", "97%"):
        require(evidence in readme_lower, f"README is missing scenario evidence: {evidence}")

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
    verify_notebook_and_report()
    print("Artifact verification passed: policies, decisions, figures, notebook, and report are consistent.")


if __name__ == "__main__":
    main()

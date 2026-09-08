"""Validate regenerated project artifacts using cross-platform invariants."""

from __future__ import annotations

import json
from pathlib import Path

import nbformat
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


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


def verify_configuration_and_figures() -> None:
    assumptions = json.loads((OUTPUTS / "model_assumptions.json").read_text(encoding="utf-8"))
    require(assumptions["case_study"]["sku"] == "standard USB-C charging cable", "SKU scope changed.")
    require(assumptions["optimisation"]["tested_policy_count"] == 45, "Policy count changed.")
    require(assumptions["optimisation"]["service_fill_rate_target"] == 0.97, "Service target changed.")

    figure_names = {
        "cost_sensitivity.svg",
        "cost_service_frontier.svg",
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
    require(len(code_cells) == 9, "Expected nine notebook code cells.")
    require(all(cell.execution_count is not None for cell in code_cells), "Notebook has unexecuted code cells.")
    require(
        not any(output.output_type == "error" for cell in code_cells for output in cell.get("outputs", [])),
        "Notebook contains an execution error.",
    )

    report_source = (ROOT / "report" / "final_report.md").read_text(encoding="utf-8")
    for evidence in ("19.6568", "19.6571", "97.09%", "(2, 12)", "USB-C"):
        require(evidence in report_source, f"Report is missing evidence: {evidence}")
    report_pdf = ROOT / "report" / "final_report.pdf"
    require(report_pdf.exists() and report_pdf.stat().st_size > 50_000, "PDF report is missing or unexpectedly small.")


def main() -> None:
    verify_tables()
    verify_configuration_and_figures()
    verify_notebook_and_report()
    print("Artifact verification passed: policies, decisions, figures, notebook, and report are consistent.")


if __name__ == "__main__":
    main()

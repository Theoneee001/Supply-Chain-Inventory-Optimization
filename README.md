# Stochastic Inventory Optimisation for Ecommerce

## A Markov-chain and Monte Carlo study of one category-neutral SKU

This project asks a practical question: **when should an ecommerce fulfilment centre reorder a non-perishable SKU, and how much should it replenish?** The SKU is intentionally category-neutral because no real product category or retailer dataset is being claimed.

I model the decision with an `(s, S)` policy, calculate stationary long-run performance through a finite Markov chain, and independently check the implementation with warm-up-adjusted Monte Carlo simulation. The project draws on my University of Manchester mathematics training and combines probability, linear algebra, statistics, numerical computation, Python engineering, and business interpretation.

> **Scope:** This is a transparent teaching case, not a claim about a named retailer. Demand probabilities and cost values are illustrative. Real data can replace them without changing the analytical workflow.

## Decision Summary

There is no single "best" policy until the business states its objective.

| Decision rule | Policy | Stationary daily cost | Stockout rate | Fill rate |
| --- | ---: | ---: | ---: | ---: |
| Minimum expected cost in the audited grid | `(0, 14)` | `19.4352` | `14.10%` | `90.60%` |
| Minimum cost subject to fill rate >= `97%` | `(2, 15)` | `19.7937` | `4.70%` | `97.70%` |

Choosing `(2, 15)` costs `0.3585` more per day, a `1.84%` increase, while reducing the stockout rate by `9.40` percentage points. I would use `(0, 14)` only when the stated objective is expected cost alone. If the illustrative 97% fill-rate target is adopted, `(2, 15)` is the defensible baseline recommendation. The target is a decision scenario, not an industry benchmark.

![Cost-service Pareto frontier](outputs/figures/cost_service_frontier.svg)

## What "Optimal" Means Here

The program evaluates all 180 feasible policies in a declared finite grid:

- reorder point `s` ranges from its natural lower bound `0` to `8`;
- order-up-to level `S` ranges from `s + 1` to `24`, so every integer pair with `S > s` is included;
- the stationary long-run expected daily cost scores each policy;
- an optional fill-rate constraint removes policies that do not meet the service target;
- the program chooses the lowest-cost remaining policy;
- a boundary audit stops publication if any reported selection reaches `s=8` or `S=24`.

The word *optimal* therefore means **lowest expected cost among the tested policies under the stated demand and cost assumptions**. Across 19 baseline, service, demand, and cost-sensitivity selections, the largest chosen values are `s=3` and `S=21`, leaving clear margins below both artificial upper limits. It does not mean that `(0, 14)` is universally correct for every product or retailer.

## Mathematical Model

At the beginning of day `t`, the fulfilment centre observes opening inventory `I_t`. If `I_t <= s`, it replenishes from a nearby central warehouse up to `S`. Demand then occurs, and the model records unmet demand as lost sales.

```text
If I_t <= s:  Q_t = S - I_t
If I_t > s:   Q_t = 0

A_t = I_t + Q_t
Sales_t = min(A_t, D_t)
Shortage_t = max(D_t - A_t, 0)
I_(t+1) = A_t - Sales_t

Cost_t = K * 1{Q_t > 0} + c * Q_t + h * I_(t+1) + p * Shortage_t
```

Under a fixed policy, tomorrow's inventory depends only on today's inventory and a new demand draw. The states `0, 1, ..., S` therefore form a finite Markov chain. If `P` is its transition matrix and `pi` its stationary distribution, then

```text
pi = pi P,    sum_i pi_i = 1.
```

The stationary long-run cost is the stationary-probability-weighted expected one-day cost. Power iteration evaluates the finite model to a tolerance of `1e-14`. This connects an operational decision to undergraduate ideas from discrete probability, matrices, stochastic processes, expectation, convergence, and optimisation. The full derivation is in [docs/mathematical_appendix.md](docs/mathematical_appendix.md).

## Validation Against Simulation

The Markov calculation is deterministic for the stated finite model up to the declared numerical tolerance. Monte Carlo simulation independently checks the code.

Every policy receives the same demand-path seeds through a common-random-numbers design. Each replication discards `365` warm-up days before measuring the next `365` days, which removes the finite-horizon bias caused by always starting at full inventory. The experiment uses `200` replications per policy.

| Validation metric for `(0, 14)` | Result |
| --- | ---: |
| Stationary Markov cost | `19.4352` |
| Simulated mean cost | `19.4512` |
| Simulated 95% interval | `[19.4020, 19.5004]` |
| Absolute difference | `0.0160` |

The stationary value falls inside the simulated interval. The expected total also reconciles to four visible components: fixed ordering `6.0768`, unit ordering `5.6717`, holding `5.3335`, and shortage `2.3532`. The publication verifier independently solves all 720 stationary systems as linear equations and repeats all 19 decisions on a larger 442-policy grid (`s <= 12`, `S <= 40`). Regression tests protect the interval check and cost identity. The runner-up `(1, 14)` is only `0.0031` per day more expensive, so the ranking is exact for these inputs but should be recalibrated with real data.

## Four Demand Distributions

The execution manual calls for optimisation under different demand distributions. The model repeats the complete 180-policy search under baseline mixed, steady, volatile, and promotion-peak demand, producing `720` auditable scenario-policy rows. Steady and volatile demand both average `3.00` units per day, but their variances are `0.90` and `4.60`. This separates average demand from tail risk.

| Scenario | Mean | Variance | Cost optimum | 97% service choice | Cost-optimum fill rate |
| --- | ---: | ---: | --- | --- | ---: |
| Baseline mixed | 3.13 | 2.43 | `(0, 14)` | `(2, 15)` | 90.60% |
| Steady | 3.00 | 0.90 | `(0, 14)` | `(1, 16)` | 92.38% |
| Volatile | 3.00 | 4.60 | `(1, 14)` | `(3, 16)` | 92.72% |
| Promotion peak | 4.79 | 3.07 | `(2, 18)` | `(3, 18)` | 95.49% |

Both cost and service choices respond to the demand distribution. Each cost optimum is independently checked with 200 warm-up-adjusted Monte Carlo replications.

![Demand-distribution stress test](outputs/figures/demand_scenario_comparison.svg)

## Visual Evidence

### Complete policy search

The gold outline marks the unconstrained cost minimum. Blank cells violate the standard requirement `S > s`.

![Stationary cost heatmap](outputs/figures/policy_cost_heatmap.svg)

### Steady-state operating trace

This chart shows a 90-day trace after the warm-up period under `(0, 14)`. Inventory falls with demand and returns to `14` when opening stock reaches zero.

![Inventory and demand trace](outputs/figures/inventory_path.svg)

### Inventory and stockout trade-off

More inventory usually reduces stockout risk, but it does not automatically minimise total cost.

![Inventory and stockout trade-off](outputs/figures/inventory_stockout_tradeoff.svg)

### Sensitivity to cost assumptions

Higher shortage cost moves the trigger upward; higher holding cost favours a lower stock target.

![Cost sensitivity](outputs/figures/cost_sensitivity.svg)

## Evidence Map

| Claim | Evidence |
| --- | --- |
| Stationary policy ranking | [outputs/policy_evaluation_summary.csv](outputs/policy_evaluation_summary.csv) |
| Two decision rules | [outputs/service_level_policy_summary.csv](outputs/service_level_policy_summary.csv) |
| Non-dominated choices | [outputs/policy_pareto_frontier.csv](outputs/policy_pareto_frontier.csv) |
| Nine cost scenarios | [outputs/cost_sensitivity_summary.csv](outputs/cost_sensitivity_summary.csv) |
| Four demand distributions | [outputs/demand_scenario_summary.csv](outputs/demand_scenario_summary.csv) and [outputs/demand_scenario_policy_evaluation.csv](outputs/demand_scenario_policy_evaluation.csv) |
| Search-space stopping rule | [outputs/search_boundary_audit.csv](outputs/search_boundary_audit.csv) |
| Demand and cost settings | [outputs/model_assumptions.json](outputs/model_assumptions.json) |
| Generated interpretation | [outputs/analysis_summary.md](outputs/analysis_summary.md) |
| Complete academic discussion | [report/final_report.md](report/final_report.md) and `report/final_report.pdf` |
| Mathematical derivation | [docs/mathematical_appendix.md](docs/mathematical_appendix.md) |
| Executable analysis | [notebooks/supply_chain_inventory_optimization.ipynb](notebooks/supply_chain_inventory_optimization.ipynb) |
| Regression tests | [tests/test_inventory_model.py](tests/test_inventory_model.py), [tests/test_notebook_builder.py](tests/test_notebook_builder.py), [tests/test_report_builder.py](tests/test_report_builder.py), and [tests/test_verify_artifacts.py](tests/test_verify_artifacts.py) |
| Responsible AI record | [docs/ai_workflow.md](docs/ai_workflow.md) |

## Repository Structure

```text
.
├── .github/workflows/reproducibility.yml
├── data/README.md
├── docs/
│   ├── ai_workflow.md
│   ├── application_materials.md
│   ├── deliverables_checklist.md
│   └── mathematical_appendix.md
├── notebooks/supply_chain_inventory_optimization.ipynb
├── outputs/
│   ├── figures/
│   ├── model_assumptions.json
│   └── generated result tables
├── report/
│   ├── final_report.md
│   └── final_report.pdf
├── scripts/
│   ├── build_notebook.py
│   ├── build_report_pdf.py
│   └── verify_artifacts.py
├── src/inventory_model.py
├── tests/
│   ├── test_inventory_model.py
│   ├── test_report_builder.py
│   └── test_verify_artifacts.py
├── LICENSE
├── requirements.txt
└── requirements-lock.txt
```

## Reproduce the Project

```bash
git clone https://github.com/Theoneee001/Supply-Chain-Inventory-Optimization.git
cd Supply-Chain-Inventory-Optimization
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements-lock.txt
python3 -m unittest discover -s tests -v
python3 src/inventory_model.py
python3 scripts/build_notebook.py
python3 scripts/build_report_pdf.py
python3 scripts/verify_artifacts.py
```

Optional controls:

```bash
python3 src/inventory_model.py \
  --periods 730 \
  --warmup-periods 730 \
  --replications 500 \
  --seed 42
```

The lock file reproduces the tested environment; `requirements.txt` records broader compatible version ranges for reuse. The model run regenerates the CSV, JSON, Markdown, and SVG outputs. The remaining commands execute the notebook, rebuild the PDF, and check that the published decisions still agree across files. GitHub Actions runs the same sequence after every push.

## Limits and Next Research Step

The current model assumes independent daily demand, zero replenishment lead time, lost sales, and one SKU. A nearby central warehouse supplies the same-day transfer, but this remains a simplification. A stronger empirical extension would estimate demand from an openly licensed transaction dataset, model positive lead time and seasonality, and compare the resulting policy against the current controlled baseline.

## AI Assistance and Authorship

AI supported structured brainstorming, code review, edge-case discovery, prose editing, and visual QA. It did not supply private data or replace the mathematical decision. Python regenerates every reported result; the stationary Markov calculation, independent simulations, and regression tests check the output. The author remains responsible for the case definition, assumptions, mathematics, implementation choices, interpretation, and final presentation.

## Licence

The [MIT License](LICENSE) covers the code and documentation. The full report lists the academic references.

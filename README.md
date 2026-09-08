# Stochastic Inventory Optimisation for Ecommerce

## A Markov-chain and Monte Carlo study of one USB-C charging cable SKU

This project asks a practical question: **when should a UK ecommerce fulfilment centre reorder a fast-moving USB-C charging cable, and how much should it replenish?**

I model the decision with an `(s, S)` policy, calculate exact long-run performance through a finite Markov chain, and independently check the implementation with warm-up-adjusted Monte Carlo simulation. The project combines probability, linear algebra, statistics, numerical computation, Python engineering, and business interpretation.

> **Scope:** This is a transparent teaching case, not a claim about a named retailer. Demand probabilities and cost values are illustrative. Real data can replace them without changing the analytical workflow.

## Decision Summary

There is no single "best" policy until the business states its objective.

| Decision rule | Policy | Exact daily cost | Stockout rate | Fill rate |
| --- | ---: | ---: | ---: | ---: |
| Minimum expected cost in the tested grid | `(1, 12)` | `19.66` | `10.69%` | `93.91%` |
| Minimum cost subject to fill rate >= `97%` | `(2, 12)` | `20.11` | `5.93%` | `97.09%` |

Choosing `(2, 12)` costs `0.46` more per day, a `2.32%` increase, while reducing the stockout rate by `4.75` percentage points. I would use `(1, 12)` when the stated objective is cost alone. If a 97% fill-rate promise is binding, `(2, 12)` is the defensible recommendation.

![Cost-service Pareto frontier](outputs/figures/cost_service_frontier.svg)

## What "Optimal" Means Here

The program evaluates all 45 feasible policies in a declared finite grid:

- reorder point `s` ranges from `1` to `6`;
- order-up-to level `S` ranges from `s + 2` to `12`;
- the exact long-run expected daily cost scores each policy;
- an optional fill-rate constraint removes policies that do not meet the service target;
- the program chooses the lowest-cost remaining policy.

The word *optimal* therefore means **lowest expected cost among the tested policies under the stated demand and cost assumptions**. It does not mean that `(1, 12)` is universally correct for every product or retailer.

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

The exact long-run cost is the stationary-probability-weighted expected one-day cost. This connects an operational decision to undergraduate ideas from discrete probability, matrices, stochastic processes, expectation, convergence, and optimisation. The full derivation is in [docs/mathematical_appendix.md](docs/mathematical_appendix.md).

## Validation, Not Just Simulation

The Markov calculation is exact for the stated finite model. Monte Carlo simulation independently checks the code.

Every policy receives the same demand-path seeds through a common-random-numbers design. Each replication discards `365` warm-up days before measuring the next `365` days, which removes the finite-horizon bias caused by always starting at full inventory. The experiment uses `200` replications per policy.

| Validation metric for `(1, 12)` | Result |
| --- | ---: |
| Exact Markov cost | `19.6568` |
| Simulated mean cost | `19.6571` |
| Simulated 95% interval | `[19.6053, 19.7089]` |
| Absolute difference | `0.0003` |

The exact value falls inside the simulated interval. A regression test protects this result from future changes.

## Visual Evidence

### Complete policy search

The gold outline marks the unconstrained cost minimum. The rule `S >= s + 2` excludes blank cells.

![Exact cost heatmap](outputs/figures/policy_cost_heatmap.svg)

### Steady-state operating trace

This chart shows a 90-day trace after the warm-up period under `(1, 12)`. Inventory falls with demand and returns to `12` once stock reaches the reorder trigger.

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
| Exact policy ranking | [outputs/policy_evaluation_summary.csv](outputs/policy_evaluation_summary.csv) |
| Two decision rules | [outputs/service_level_policy_summary.csv](outputs/service_level_policy_summary.csv) |
| Non-dominated choices | [outputs/policy_pareto_frontier.csv](outputs/policy_pareto_frontier.csv) |
| Nine cost scenarios | [outputs/cost_sensitivity_summary.csv](outputs/cost_sensitivity_summary.csv) |
| Demand and cost settings | [outputs/model_assumptions.json](outputs/model_assumptions.json) |
| Generated interpretation | [outputs/analysis_summary.md](outputs/analysis_summary.md) |
| Complete academic discussion | [report/final_report.md](report/final_report.md) and `report/final_report.pdf` |
| Mathematical derivation | [docs/mathematical_appendix.md](docs/mathematical_appendix.md) |
| Executable analysis | [notebooks/supply_chain_inventory_optimization.ipynb](notebooks/supply_chain_inventory_optimization.ipynb) |
| Model tests | [tests/test_inventory_model.py](tests/test_inventory_model.py) |
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
├── tests/test_inventory_model.py
├── LICENSE
└── requirements.txt
```

## Reproduce the Project

```bash
git clone https://github.com/Theoneee001/Supply-Chain-Inventory-Optimization.git
cd Supply-Chain-Inventory-Optimization
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
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

The model run regenerates the CSV, JSON, Markdown, and SVG outputs. The remaining commands execute the notebook, rebuild the PDF, and check that the published decisions still agree across files. GitHub Actions runs the same sequence after every push.

## Limits and Next Research Step

The current model assumes independent daily demand, zero replenishment lead time, lost sales, and one SKU. A nearby central warehouse supplies the same-day transfer, but this remains a simplification. A stronger empirical extension would estimate demand from an openly licensed transaction dataset, model positive lead time and seasonality, and compare the resulting policy against the current controlled baseline.

## AI Assistance and Authorship

AI supported structured brainstorming, code review, edge-case discovery, prose editing, and visual QA. It did not supply private data or replace the mathematical decision. Python regenerates every reported result; an exact Markov calculation and regression tests check the output. The author remains responsible for the case definition, assumptions, mathematics, implementation choices, interpretation, and final presentation.

## Licence

The [MIT License](LICENSE) covers the code and documentation. The full report lists the academic references.

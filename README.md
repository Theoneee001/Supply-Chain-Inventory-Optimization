# Supply Chain Inventory Optimization with Stochastic Demand

An applied stochastic-process project that turns uncertain daily demand into an interpretable inventory decision rule. The repository combines a finite Markov chain, Monte Carlo simulation, visual analytics, and a business-facing interpretation of the results.

**Research question:** How should a single-product retailer choose a reorder point `s` and an order-up-to level `S` when daily demand is random and ordering, holding, and stockout costs all matter?

The project is designed as an academic portfolio artefact for operations management, business analytics, information systems, and digital transformation applications. It demonstrates an end-to-end workflow: mathematical model, reproducible Python implementation, experiment design, validation, visualisation, and managerial insight.

## Executive Result

For the baseline demand and cost assumptions, the recommended policy in the tested grid is **(s, S) = (1, 12)**.

| Metric | Markov-chain result | Monte Carlo validation |
| --- | ---: | ---: |
| Average daily cost | 19.66 | 19.59 |
| Simulated 95% cost interval | - | [19.54, 19.64] |
| Stockout rate | 10.69% | 10.60% |
| Fill rate | 93.91% | 93.98% |
| Average ending inventory | 4.71 units | 4.71 units |

The simulation consists of 200 independent replications of 365 days for each policy. Its estimate is within `0.069` cost units per day of the exact Markov-chain result. This agreement is an internal validation check, not merely a convenient numerical coincidence.

The recommendation is cost-optimal under the stated assumptions, not automatically service-optimal. For example, policy `(5, 12)` reduces the stockout rate to `0.00%`, but increases average daily cost to `23.76`. The appropriate final decision depends on the retailer's service-level target.

## Visual Results

### Baseline inventory dynamics

![Inventory level and daily demand](outputs/figures/inventory_path.svg)

### Cost comparison across policies

![Policy cost heatmap](outputs/figures/policy_cost_heatmap.svg)

### Inventory-service trade-off

![Inventory and stockout trade-off](outputs/figures/inventory_stockout_tradeoff.svg)

### Sensitivity to holding and shortage costs

![Cost sensitivity](outputs/figures/cost_sensitivity.svg)

## Model

The retailer reviews inventory at the beginning of each day. If opening inventory `I_t` is at or below `s`, it immediately orders enough units to reach `S`; demand then occurs during the day. Unsatisfied demand is treated as a lost sale.

```text
If I_t <= s:  Q_t = S - I_t
If I_t > s:   Q_t = 0

A_t = I_t + Q_t
Sales_t = min(A_t, D_t)
Shortage_t = max(D_t - A_t, 0)
I_(t+1) = A_t - Sales_t

Cost_t = K * 1{Q_t > 0} + c * Q_t + h * I_(t+1) + p * Shortage_t
```

Under a fixed policy, the next inventory state depends only on the current inventory state and the current random demand draw. The inventory process is therefore a finite Markov chain with states `0, 1, ..., S`. The code calculates its stationary distribution for exact long-run metrics, then independently estimates the same metrics using Monte Carlo simulation.

### Baseline assumptions

| Item | Assumption |
| --- | --- |
| Product scope | One non-perishable product |
| Review interval | Daily |
| Supplier lead time | Zero days |
| Demand | Discrete, independent daily random variable over 0-6 units |
| Shortage treatment | Lost sales, not backorders |
| Fixed order cost `K` | 30 |
| Unit order cost `c` | 2 |
| Holding cost `h` | 1 per end-of-day unit |
| Shortage penalty `p` | 8 per unsatisfied unit |

The full machine-readable configuration is available in [outputs/model_assumptions.json](outputs/model_assumptions.json). These are stylised parameters for a transparent baseline experiment; they do not claim to represent a real company.

## Repository Guide

```text
.
├── .github/workflows/reproducibility.yml  # Automated test and reproduction check
├── data/                                  # Data assumptions and future data guidance
├── docs/                                  # Delivery checklist, application notes, September plan
├── notebooks/                             # Narrative notebook for interactive exploration
├── outputs/                               # Generated tables, figures, and result summary
├── report/                                # Complete English research report
├── src/inventory_model.py                 # Full model, simulation, Markov analysis, and figures
├── tests/test_inventory_model.py          # Regression tests
├── requirements.txt
└── README.md
```

Start with [report/final_report.md](report/final_report.md) for the full academic discussion, then inspect [outputs/analysis_summary.md](outputs/analysis_summary.md) for the current generated results. The complete executable implementation is [src/inventory_model.py](src/inventory_model.py).

## Reproduce the Analysis

### 1. Clone and create an environment

```bash
git clone https://github.com/Theoneee001/Supply-Chain-Inventory-Optimization.git
cd Supply-Chain-Inventory-Optimization
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

On Windows PowerShell, activate the environment with `.venv\\Scripts\\Activate.ps1`.

### 2. Run automated checks

```bash
python3 -m unittest discover -s tests -v
```

The test suite checks probability-matrix validity, stationary-distribution validity, fixed-seed reproducibility, a known zero-demand case, and policy-input validation.

### 3. Generate all outputs

```bash
python3 src/inventory_model.py
```

This command regenerates:

| File | Content |
| --- | --- |
| `outputs/baseline_simulation_trace.csv` | 90-day illustrative operational trace |
| `outputs/policy_evaluation_summary.csv` | Exact and simulated metrics for every policy |
| `outputs/cost_sensitivity_summary.csv` | Best policy under nine cost scenarios |
| `outputs/model_assumptions.json` | Experiment assumptions in machine-readable form |
| `outputs/analysis_summary.md` | GitHub-ready interpretation of the latest run |
| `outputs/figures/*.svg` | Four labelled, vector-quality figures |

Optional command-line controls are available when testing a faster or larger experiment:

```bash
python3 src/inventory_model.py --periods 730 --replications 500 --seed 42
```

## Results and Interpretation

The baseline fixed order cost makes frequent small orders expensive. In the tested policy grid, `(1, 12)` accepts a modest stockout risk in exchange for larger, less frequent replenishment batches. When shortage cost doubles from `8` to `16`, the selected policy becomes `(2, 12)`, improving the stockout rate from `10.69%` to `5.93%`. When holding cost doubles from `1` to `2`, the model shifts to leaner policies such as `(1, 10)`.

This sensitivity check is deliberately included because a recommendation without an assumption check is fragile. The model should be used to structure a manager's decision, not to hide the judgement embedded in cost parameters.

## Limitations and Next Extension

This first version has four intentional limits: demand is independent across days, replenishment is instantaneous, shortages are lost sales, and the system contains one product. A substantive second version can add a public demand dataset, non-zero supplier lead time, seasonality, service-level constraints, or multiple products with capacity constraints.

## AI Assistance and Authorship

AI assistance was used to support code review, explanation drafting, and figure refinement. The author remains responsible for the problem framing, assumptions, modelling choices, interpretation, and final submission. This repository documents the logic and generated outputs so that the work can be reviewed, reproduced, and discussed transparently.

## Publication Notes

No proprietary company or personal transaction data is included in this repository. Generated output files are committed alongside the code so that readers can inspect the current baseline result before reproducing it locally.

# Application Materials

## CV Version A: Mathematics and Analytics

- Built a finite-state inventory optimisation model in Python, using Markov-chain stationary distributions to calculate exact long-run cost and service metrics across 45 `(s, S)` policies.
- Corrected finite-horizon simulation bias with a 365-day warm-up and validated the exact cost of `19.6568` against 200 Monte Carlo replications (`19.6571`, 95% CI `[19.6053, 19.7089]`).
- Formulated a service-constrained decision rule that selected `(2, 12)` at a `97.09%` fill rate, reducing stockout probability by `4.75` percentage points for a `2.32%` cost increase.

## CV Version B: Programming and Digital Transformation

- Developed a reproducible Python decision-support workflow with modular data classes, exhaustive policy search, sensitivity analysis, Pareto filtering, 14 regression tests, an executed Jupyter Notebook, and GitHub Actions CI.
- Converted an informal replenishment rule into auditable CSV, JSON, SVG, Markdown, and PDF outputs, with responsible AI documentation and file-level evidence for every published result.

## Personal Statement Material (180 words)

My undergraduate mathematics training at the University of Manchester taught me to be careful about the gap between a result and the assumptions that produce it. I applied that habit in a supply-chain project for an illustrative ecommerce fulfilment centre replenishing one USB-C charging cable SKU. I represented an `(s, S)` inventory policy as a finite Markov chain, calculated its stationary distribution, and used Python to evaluate 45 policies under uncertain daily demand. I then checked the exact result with 200 Monte Carlo replications. During validation, I found that the original simulation window retained a small initial-state bias; adding a warm-up period brought the simulated mean of `19.6571` into close agreement with the exact value of `19.6568`. The project also changed how I think about optimisation. The lowest-cost policy achieved only a `93.91%` fill rate, so I added a `97%` service constraint. The resulting policy cost `2.32%` more but cut stockout probability by `4.75` percentage points. This work showed me how probability, linear algebra, statistics, programming, and responsible AI assistance can support a decision without hiding the judgement behind it.

## Interview Explanation: 60 Seconds

I used ideas from my mathematics degree at Manchester to build a Python inventory model for an illustrative ecommerce fulfilment centre selling one USB-C charging cable SKU. Under an `(s, S)` rule, stock is replenished to `S` when it reaches `s`. For each of 45 policies, I constructed a finite Markov chain and calculated the exact long-run cost from its stationary distribution. I then used 200 Monte Carlo replications as an independent check. That comparison exposed a small initial-state bias in my first simulation design, so I added a 365-day warm-up and protected the correction with tests. The unconstrained cost minimum was `(1, 12)`, but its fill rate was only `93.91%`. With a `97%` fill-rate constraint, `(2, 12)` became the best feasible policy. It cost `2.32%` more and reduced stockout probability by `4.75` percentage points. The project demonstrates how I combine mathematical reasoning, programming, AI-assisted review, and business judgement.

## Interview Explanation: 3 Minutes

I wanted a project that used undergraduate mathematics for a decision that a business could actually discuss. I chose inventory replenishment for an illustrative UK ecommerce fulfilment centre holding one standard USB-C charging cable SKU. The centre checks stock daily and uses an `(s, S)` policy: if opening inventory is at or below `s`, it orders enough to reach `S`. The central problem is a trade-off between fixed ordering cost, unit purchasing cost, holding cost, and the cost of unmet demand.

Mathematically, once a policy is fixed, tomorrow's opening inventory depends only on today's inventory and a new demand draw. That gives a finite Markov chain with states from zero to `S`. I built the transition matrix in Python and found its stationary distribution by power iteration. Weighting each state-demand cost by the stationary probabilities gives an exact long-run expected cost. I then evaluated every policy in a 45-member grid, so the reported optimum is global within that declared feasible set rather than the output of an unexplained heuristic.

I also built an independent Monte Carlo check with 200 replications. This led to one of the most useful parts of the project. My original simulated interval did not quite contain the exact Markov value. Instead of changing the wording, I traced the discrepancy to the fact that each one-year run started at full inventory. A 365-day warm-up removed that transient effect. The final simulated mean is `19.6571`, the exact value is `19.6568`, and the exact result lies within the 95% simulation interval. I added regression tests so the issue cannot quietly return.

The unconstrained minimum is `(1, 12)`, with a daily cost of `19.66` and a `93.91%` fill rate. That service level may be too low for a product advertised as readily available, so I formulated a second problem: minimise cost subject to a fill rate of at least `97%`. The answer is `(2, 12)`. It costs `0.46` more per day, or `2.32%`, while reducing stockout probability from `10.69%` to `5.93%`.

AI helped me review code, spot inconsistencies, refine explanations, and inspect figures, but I did not treat it as mathematical evidence. Every published number comes from generated outputs, and the repository includes 14 tests, an executed notebook, a formal report, and CI. The main lesson for me was that good analytics does not merely produce a minimum. It makes the assumptions, validation, and cost of alternative decisions visible.

## GitHub or LinkedIn Project Summary

Built a reproducible stochastic inventory optimisation project for an illustrative ecommerce USB-C cable SKU. The model combines finite Markov chains, stationary distributions, Monte Carlo validation, exhaustive policy search, sensitivity analysis, and a cost-service Pareto frontier. The unconstrained policy `(1, 12)` minimises expected cost, while `(2, 12)` is the lowest-cost choice meeting a `97%` fill-rate target. Python tests, an executed notebook, generated figures, a PDF report, GitHub Actions, and a transparent AI-use record make the full analysis auditable.

## Evidence to Keep Beside Any Application Claim

| Claim | Repository evidence |
| --- | --- |
| 45 policies evaluated | `outputs/policy_evaluation_summary.csv` |
| Exact and simulated values agree | `outputs/service_level_policy_summary.csv` and regression tests |
| 97% service constraint | `src/inventory_model.py` and `outputs/service_level_policy_summary.csv` |
| 14 regression tests | `tests/test_inventory_model.py` |
| Responsible AI use | `docs/ai_workflow.md` |
| Mathematical depth | `docs/mathematical_appendix.md` |

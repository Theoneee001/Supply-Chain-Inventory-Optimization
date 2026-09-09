# Application Materials

## CV Version A: Mathematics and Analytics

- Built a finite-state inventory optimisation model in Python, using Markov-chain stationary distributions to calculate long-run cost and service metrics for 180 policy-demand combinations.
- Isolated the effect of demand variance by comparing steady and volatile distributions with the same mean, then validated each selected cost optimum with 200 warm-up-adjusted Monte Carlo replications.
- Formulated an illustrative 97% service constraint whose minimum-cost reorder point rose from `2` under baseline demand to `3` under volatile demand and `4` during a promotion peak.

## CV Version B: Programming and Digital Transformation

- Developed a reproducible Python decision-support workflow with modular data classes, exhaustive policy search, two forms of sensitivity analysis, Pareto filtering, 19 regression tests, an executed Jupyter Notebook, and GitHub Actions CI.
- Converted an informal replenishment rule into auditable CSV, JSON, SVG, Markdown, and PDF outputs, including six vector figures, pinned dependencies, responsible AI documentation, and file-level evidence for every published result.

## Personal Statement Material (180 words)

My undergraduate mathematics training at the University of Manchester taught me to separate a result from the assumptions behind it. I applied that habit to a category-neutral inventory project for an illustrative ecommerce fulfilment centre. I represented an `(s, S)` replenishment policy as a finite Markov chain and used Python to evaluate 45 policies under four demand distributions. Power iteration produced stationary cost and service metrics to a declared numerical tolerance, while 200 Monte Carlo replications checked each selected cost optimum. During validation, I found that my first simulation retained initial-state bias. Adding a 365-day warm-up brought the simulated baseline cost of `19.6571` into agreement with the stationary value of `19.6568`. The analysis also showed why optimisation needs a business objective. The cost minimum `(1, 12)` remained stable across the tested distributions, but the policy required to meet an illustrative `97%` fill-rate target moved from `(2, 12)` under baseline demand to `(3, 12)` under volatile demand and `(4, 12)` during a promotion peak. This project demonstrates how I use probability, linear algebra, statistics, programming, and responsible AI assistance to turn an uncertain operational question into an auditable decision.

## Interview Explanation: 60 Seconds

I used my Manchester mathematics training to build a Python inventory model for a category-neutral ecommerce SKU. For each `(s, S)` policy, I constructed a finite Markov chain and calculated long-run cost and service from its stationary distribution. I evaluated all 45 policies under four demand distributions, then checked each selected cost optimum with 200 Monte Carlo replications. The cost minimum remained `(1, 12)`, but service changed sharply: steady and volatile demand had the same mean, yet their fill rates were `96.01%` and `92.18%`. Under an illustrative `97%` target, the best trigger rose from `2` under baseline demand to `3` under volatile demand and `4` during a promotion peak. The project shows how I combine probability, programming, validation, and business judgement without pretending that an assumed service target is a universal rule.

## Interview Explanation: 3 Minutes

I wanted a project that used undergraduate mathematics for a decision that a business could actually discuss. I chose inventory replenishment for an illustrative ecommerce fulfilment centre holding one generic non-perishable SKU. The category is intentionally unspecified because the model is not calibrated to a real product. The centre checks stock daily and uses an `(s, S)` policy: if opening inventory is at or below `s`, it orders enough to reach `S`. The central problem is a trade-off between fixed ordering cost, unit purchasing cost, holding cost, and the cost of unmet demand.

Mathematically, once a policy is fixed, tomorrow's opening inventory depends only on today's inventory and a new demand draw. That gives a finite Markov chain with states from zero to `S`. I built the transition matrix in Python and found its stationary distribution by power iteration to a tolerance of `1e-14`. Weighting each state-demand cost by the stationary probabilities gives the long-run expected cost for the stated finite model. I then evaluated every policy in a 45-member grid, so the reported optimum is global within that declared feasible set rather than the output of an unexplained heuristic.

I also built an independent Monte Carlo check with 200 replications. This led to one of the most useful parts of the project. My original simulated interval did not quite contain the stationary Markov value. Instead of changing the wording, I traced the discrepancy to the fact that each one-year run started at full inventory. A 365-day warm-up removed that transient effect. The final simulated mean is `19.6571`, the stationary value is `19.6568`, and the result lies within the 95% simulation interval. I added regression tests so the issue cannot quietly return.

The unconstrained baseline minimum is `(1, 12)`, with a daily cost of `19.66` and a `93.91%` fill rate. I then formulated a second problem: minimise cost subject to an illustrative fill rate of at least `97%`. Under baseline demand the answer is `(2, 12)`. It costs `0.46` more per day, or `2.32%`, while reducing stockout probability from `10.69%` to `5.93%`.

Finally, I changed the demand distribution while holding costs fixed. The cost optimum remained stable, but service did not. Steady and volatile demand both averaged three units per day, yet the cost-optimal fill rate fell from `96.01%` to `92.18%`. To meet the same illustrative 97% target, the reorder point had to rise from `2` under baseline demand to `3` under volatile demand and `4` during a promotion peak. This is a practical example of why variance matters, not only the mean.

AI helped me review code, spot inconsistencies, refine explanations, and inspect figures, but I did not treat it as mathematical evidence. Every published number comes from generated outputs, and the repository includes 19 tests, an executed notebook, a formal report, and CI. The main lesson for me was that good analytics does not merely produce a minimum. It makes the assumptions, validation, and cost of alternative decisions visible.

## GitHub or LinkedIn Project Summary

Built a reproducible stochastic inventory optimisation project for a category-neutral ecommerce SKU. The model combines finite Markov chains, stationary distributions, Monte Carlo validation, exhaustive search across 180 policy-demand combinations, cost and demand sensitivity, and a Pareto frontier. The cost optimum remains `(1, 12)` across four distributions, while the minimum-cost policy meeting an illustrative `97%` target moves from `(2, 12)` under baseline demand to `(4, 12)` during a promotion peak. Seventeen tests, an executed notebook, six vector figures, a PDF report, pinned dependencies, GitHub Actions, and a transparent AI-use record make the analysis auditable.

## Evidence to Keep Beside Any Application Claim

| Claim | Repository evidence |
| --- | --- |
| 45 policies evaluated | `outputs/policy_evaluation_summary.csv` |
| Four demand distributions and 180 combinations | `outputs/demand_scenario_policy_evaluation.csv` |
| Stationary and simulated values agree | `outputs/service_level_policy_summary.csv` and regression tests |
| 97% service constraint | `src/inventory_model.py` and `outputs/service_level_policy_summary.csv` |
| 19 regression tests | `tests/test_inventory_model.py`, `tests/test_report_builder.py`, and `tests/test_verify_artifacts.py` |
| Responsible AI use | `docs/ai_workflow.md` |
| Mathematical depth | `docs/mathematical_appendix.md` |

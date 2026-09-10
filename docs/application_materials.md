# Application Materials

## CV Version A: Mathematics and Analytics

- Built a finite-state inventory optimisation model in Python, using Markov-chain stationary distributions to calculate long-run cost and service metrics for 720 policy-demand combinations.
- Isolated the effect of demand variance by comparing steady and volatile distributions with the same mean, then validated each selected cost optimum with 200 warm-up-adjusted Monte Carlo replications.
- Formulated an illustrative 97% service constraint and showed how the minimum-cost policy moves from `(2, 15)` under baseline demand to `(3, 16)` under volatile demand and `(3, 18)` during a promotion peak.

## CV Version B: Programming and Digital Transformation

- Developed a reproducible Python decision-support workflow with modular data classes, exhaustive policy search, two forms of sensitivity analysis, Pareto filtering, an automated regression suite, an executed Jupyter Notebook, and GitHub Actions CI.
- Converted an informal replenishment rule into auditable CSV, JSON, SVG, Markdown, and PDF outputs, including six vector figures, a machine-enforced boundary audit, pinned dependencies, responsible AI documentation, and file-level evidence for every published result.

## Personal Statement Material (182 words)

My undergraduate mathematics training at the University of Manchester taught me to separate a result from the assumptions behind it. I applied that habit to a category-neutral inventory project for an illustrative ecommerce fulfilment centre. I represented an `(s, S)` replenishment policy as a finite Markov chain and used Python to evaluate 180 policies under four demand distributions, producing 720 auditable combinations. Power iteration generated stationary cost and service measures, while 200 warm-up-adjusted Monte Carlo replications checked each selected cost optimum. Review also exposed a weakness in my first search: its answer sat on the upper boundary. I expanded the grid and wrote an automated audit that stops publication whenever a selected policy reaches an artificial limit. The corrected baseline cost minimum is `(0, 14)`, while `(2, 15)` is the least-cost policy meeting an illustrative `97%` fill-rate target. Their daily costs are `19.4352` and `19.7937`, showing that a modest cost increase can materially improve service. The project demonstrates how I combine probability, linear algebra, statistics, programming, critical validation, and responsible AI assistance to turn an uncertain operational question into an inspectable decision.

## Interview Explanation: 60 Seconds

I used my Manchester mathematics training to build a Python inventory model for a category-neutral ecommerce SKU. For each `(s, S)` policy, I constructed a finite Markov chain and calculated long-run cost and service from its stationary distribution. I evaluated 180 policies under four demand distributions, then checked each selected cost optimum with 200 Monte Carlo replications. I also corrected an early boundary problem by expanding the grid and making publication fail if a selected policy reaches an artificial upper limit. The baseline cost minimum is `(0, 14)`, while `(2, 15)` is the least-cost policy meeting an illustrative `97%` fill-rate target. The project shows how I combine probability, programming, validation, and business judgement without treating an assumed service target as a universal rule.

## Interview Explanation: 3 Minutes

I wanted a project that used undergraduate mathematics for a decision that a business could actually discuss. I chose inventory replenishment for an illustrative ecommerce fulfilment centre holding one generic non-perishable SKU. The category is intentionally unspecified because the model is not calibrated to a real product. The centre checks stock daily and uses an `(s, S)` policy: if opening inventory is at or below `s`, it orders enough to reach `S`. The central problem is a trade-off between fixed ordering cost, unit purchasing cost, holding cost, and the cost of unmet demand.

Mathematically, once a policy is fixed, tomorrow's opening inventory depends only on today's inventory and a new demand draw. That gives a finite Markov chain with states from zero to `S`. I built the transition matrix in Python and found its stationary distribution by power iteration to a tolerance of `1e-14`. Weighting each state-demand cost by the stationary probabilities gives the long-run expected cost for the stated finite model. I evaluated every policy in a 180-member grid. A boundary audit covers 19 selected decisions; the largest values are `s=3` and `S=21`, below limits `8` and `24`. The reported optimum is therefore global within an audited feasible set rather than the output of an unexplained heuristic.

I also built an independent Monte Carlo check with 200 replications. My original simulated interval did not quite contain the stationary Markov value. Instead of changing the wording, I traced the discrepancy to each one-year run starting at full inventory. A 365-day warm-up removed that transient effect. The final simulated mean is `19.4512`, the stationary value is `19.4352`, and the latter lies within the 95% simulation interval `[19.4020, 19.5004]`. I added regression tests so the issue cannot quietly return.

The unconstrained baseline minimum is `(0, 14)`, with a daily cost of `19.4352` and a `90.60%` fill rate. I then formulated a second problem: minimise cost subject to an illustrative fill rate of at least `97%`. Under baseline demand the answer is `(2, 15)`. It costs `0.3585` more per day, or `1.84%`, while reducing stockout probability from `14.10%` to `4.70%`. I also expose the four cost components so readers can see exactly why the total changes.

Finally, I changed the demand distribution while holding costs fixed. Steady and volatile demand both average three units per day, yet their cost choices differ: `(0, 14)` and `(1, 14)`. During the promotion peak, the cost optimum moves to `(2, 18)`. To meet the same illustrative 97% target, the choices become `(1, 16)`, `(3, 16)`, and `(3, 18)` across the steady, volatile, and peak cases. This is a practical example of why the shape of a distribution matters as well as its mean.

AI helped me review code, spot inconsistencies, refine explanations, and inspect figures, but I did not treat it as mathematical evidence. Every published number comes from generated outputs, and the repository includes automated tests, an executed notebook, a formal report, and CI. The main lesson for me was that good analytics does not merely produce a minimum. It makes assumptions, search limits, validation, and the cost of alternative decisions visible.

## GitHub or LinkedIn Project Summary

Built a reproducible stochastic inventory optimisation project for a category-neutral ecommerce SKU. The model combines finite Markov chains, stationary distributions, Monte Carlo validation, exhaustive search across 720 policy-demand combinations, cost and demand sensitivity, and a Pareto frontier. The baseline cost optimum is `(0, 14)`, while the minimum-cost policy meeting an illustrative `97%` target is `(2, 15)`. An automated boundary audit, regression suite, executed notebook, six vector figures, PDF report, pinned dependencies, GitHub Actions, and transparent AI-use record make the analysis auditable.

## Evidence to Keep Beside Any Application Claim

| Claim | Repository evidence |
| --- | --- |
| 180 policies evaluated | `outputs/policy_evaluation_summary.csv` |
| Four demand distributions and 720 combinations | `outputs/demand_scenario_policy_evaluation.csv` |
| Stationary and simulated values agree | `outputs/service_level_policy_summary.csv` and regression tests |
| 97% service constraint | `src/inventory_model.py` and `outputs/service_level_policy_summary.csv` |
| No selected policy touches the search ceiling | `outputs/search_boundary_audit.csv` |
| Automated regression suite | `tests/test_inventory_model.py`, `tests/test_notebook_builder.py`, `tests/test_report_builder.py`, and `tests/test_verify_artifacts.py` |
| Responsible AI use | `docs/ai_workflow.md` |
| Mathematical depth | `docs/mathematical_appendix.md` |

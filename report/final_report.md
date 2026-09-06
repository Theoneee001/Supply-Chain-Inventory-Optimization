# Supply Chain Inventory Optimization with Stochastic Demand

## An (s, S) Policy Study Using Markov Chains and Monte Carlo Simulation

**Project type:** Applied stochastic-process and operations analytics project  
**Implementation:** Python, NumPy, pandas, SVG visualisation  
**Repository:** See the root [README](../README.md) for reproducibility instructions and generated outputs.

## Abstract

Inventory decisions are difficult because a retailer must commit resources before knowing future customer demand. Excess stock creates holding cost and ties up capital, while insufficient stock produces lost sales and can weaken service reliability. This report develops a transparent, reproducible model for a single-product retailer facing uncertain daily demand. The retailer follows an `(s, S)` replenishment policy: whenever opening inventory is at or below a reorder point `s`, an order is placed to raise stock to `S`. Daily demand is represented by a discrete random variable, and the model includes fixed ordering cost, unit ordering cost, end-of-day holding cost, and shortage penalty.

The study combines two methods. First, it represents the inventory level under a fixed policy as a finite Markov chain and calculates exact long-run performance from the stationary distribution. Second, it performs repeated Monte Carlo simulations to validate the analytical result and provide an interpretable day-by-day operational trace. The baseline experiment compares 45 feasible policies, using 200 independent replications of 365 days per policy. Under the stated baseline assumptions, policy `(1, 12)` has the lowest exact average daily cost, `19.66`. Its simulated estimate is `19.59`, with a 95% interval of `[19.54, 19.64]`, which provides a close implementation check. The policy has a `10.69%` stockout rate and a `93.91%` fill rate.

The result is not presented as a universal recommendation. A sensitivity analysis shows that higher shortage penalties justify a higher reorder point, while higher holding costs justify leaner stock targets. The contribution of the project is therefore practical as well as mathematical: it shows how stochastic modelling can turn operational uncertainty into an explicit, auditable decision process.

## 1. Introduction

Inventory management sits at the boundary between quantitative reasoning and everyday business judgment. A retailer must decide how much stock to carry even though demand, supplier performance, customer behaviour, and storage constraints are imperfectly known. The resulting trade-off is familiar: holding too much stock raises storage cost and may leave capital trapped in slow-moving goods; holding too little stock risks stockouts, missed transactions, and an inconsistent customer experience. The correct decision is rarely obvious because these costs interact.

This project studies a deliberately focused version of that problem. The setting is a retailer with one non-perishable product, daily review of stock, immediate replenishment, and random demand. The goal is to identify a replenishment rule that balances cost and service performance over the long run. Rather than starting from a large black-box prediction system, the analysis begins with an interpretable policy that a manager can explain: if inventory falls to or below a threshold, replenish it to a specified target. This is called an `(s, S)` policy.

The topic has both theoretical and applied significance. Classical inventory research established the importance of threshold policies in stochastic settings with fixed ordering costs. Arrow, Harris, and Marschak framed early inventory decisions as optimisation under uncertainty [1]. Scarf later showed the central role of `(s, S)` policies in dynamic inventory problems [2], and Iglehart studied their long-run behaviour in infinite-horizon settings [3]. The present project does not claim a new theorem. Its aim is different: to make this body of mathematical thinking visible in a complete analytical workflow that includes code, simulation, figures, validation, and business interpretation.

For an academic and professional portfolio, that workflow matters. It demonstrates applied probability, state-based reasoning, programming discipline, visual communication, and the ability to translate a mathematical result into operational terms. The project is especially relevant to operations management, business analytics, digital transformation, and information-systems contexts, where decision makers need models that are rigorous enough to trust but simple enough to discuss.

The report addresses four questions:

1. How can an `(s, S)` replenishment policy be expressed as a stochastic state-transition model?
2. Which policy minimises long-run average cost in a baseline grid of alternatives?
3. Does a Monte Carlo implementation agree with the exact Markov-chain calculation?
4. How does the recommendation change when holding cost or shortage cost changes?

The answer is intentionally conditional. A policy is good only relative to a stated demand distribution, cost structure, and service expectation. Making those assumptions explicit is a feature of the model, not a weakness.

## 2. Background and Project Positioning

An inventory policy is a rule for deciding when and how much to order. In a periodic-review system, the firm checks stock at regular intervals and chooses an action based on its current inventory position. The `(s, S)` policy used here has two parameters. The reorder point `s` is the trigger level, and `S` is the post-order target. When stock is low, the firm makes one replenishment decision rather than continuously adjusting quantity. This is operationally attractive because it converts a complex uncertainty problem into a simple rule that can be communicated to a planner.

The policy is particularly meaningful when there is a fixed cost each time an order is placed. If every order requires administrative effort, transport coordination, or a minimum processing cost, frequent small replenishments can be inefficient. On the other hand, ordering large quantities too early increases the time that products remain in storage. This creates the central cost-service tension examined in the project.

The mathematical literature provides the motivation for this structure, but it does not remove the need for implementation choices. A real retailer may have seasonal demand, uncertain lead time, multiple products, supplier constraints, or backorders. This report restricts attention to a single product and independent daily demand in order to make the state process observable and reproducible. It uses the language of a Markov chain because, under a fixed policy, tomorrow's inventory state is determined by today's state and a new demand realisation; earlier history affects tomorrow only through the current state. This property makes long-run calculation possible.

The analytical design also avoids a common portfolio problem: producing code that generates a number but does not explain why the number is credible. The model computes results in two independent ways. The Markov method calculates the long-run distribution over inventory states. The simulation method draws random demand paths and averages observed outcomes over repeated experiments. Agreement between them is a meaningful check on the implementation. Simulation is a standard tool for studying systems with uncertainty, but its quality depends on a clear experiment design, fixed seeds, appropriate replications, and transparent outputs [4].

## 3. Problem Definition and Assumptions

Consider one retailer selling a single non-perishable product. Time is divided into days, indexed by `t = 1, 2, ...`. At the beginning of each day, the retailer observes inventory and, if necessary, places an order. The order is assumed to arrive immediately. Customer demand occurs after the decision. Sales cannot exceed the units available, and demand that cannot be served is recorded as a lost sale rather than a backorder.

The model is intentionally stylised. Its purpose is to compare policies under controlled assumptions, not to represent a named company. The baseline daily demand distribution is shown below.

| Daily demand `d` | 0 | 1 | 2 | 3 | 4 | 5 | 6 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Probability `P(D_t = d)` | 0.05 | 0.10 | 0.20 | 0.25 | 0.20 | 0.12 | 0.08 |

The distribution has an expected demand of `3.12` units per day. It gives substantial probability mass to moderate demand while retaining an upper tail that can create shortages. Demand draws are independent and identically distributed in the baseline model. This assumption is restrictive, but it allows the contribution of the inventory policy to be isolated before adding seasonality or other operational features.

The baseline cost parameters are also set for explanation rather than calibrated from a proprietary dataset.

| Parameter | Interpretation | Value |
| --- | --- | ---: |
| `K` | Fixed cost whenever an order is placed | 30 |
| `c` | Cost per replenished unit | 2 |
| `h` | Holding cost per unit of ending inventory | 1 |
| `p` | Penalty per unit of unsatisfied demand | 8 |

The fixed cost makes ordering frequency important. The shortage penalty is positive because unfilled demand is operationally undesirable, but it is not so large that the model will necessarily eliminate all stockouts. This is useful for analysis because it exposes a genuine trade-off. If the goal were simply zero shortage at any cost, the problem would be trivial and less representative of practical decision making.

The baseline policy grid includes reorder points from `1` to `6` and order-up-to levels from `s + 2` to `12`. This creates 45 feasible alternatives. The grid is finite by design. It is wide enough to include low-stock and high-stock approaches while keeping the experiment transparent and quick to reproduce.

## 4. Mathematical Formulation

Let `I_t` be opening inventory at the start of day `t`, before any order is placed. Let `D_t` be random demand during that day. For a given policy `(s, S)`, the order quantity is

```text
Q_t = S - I_t,  if I_t <= s
Q_t = 0,        if I_t > s.
```

Available inventory after the replenishment decision is

```text
A_t = I_t + Q_t.
```

Demand is served up to the available stock level. The sales, shortage, and end-of-day inventory equations are

```text
Sales_t = min(A_t, D_t)
Shortage_t = max(D_t - A_t, 0)
I_(t+1) = A_t - Sales_t.
```

The daily cost combines four components:

```text
Cost_t = K * 1{Q_t > 0} + c * Q_t + h * I_(t+1) + p * Shortage_t.
```

The indicator `1{Q_t > 0}` equals one when the retailer orders and zero otherwise. The objective is to minimise long-run expected daily cost. In this project, performance is reported through five complementary metrics: average daily cost, stockout rate, fill rate, average ending inventory, and average order quantity. The stockout rate is the proportion of days on which some demand cannot be filled. The fill rate is the proportion of requested units that are sold. Reporting both prevents the analysis from reducing service quality to a single number.

For a fixed `(s, S)` policy, possible opening states are `0, 1, ..., S`. Let `P_ij` represent the probability of moving from opening inventory state `i` to state `j` in one day. After applying the policy, the available stock is either `S` or `i`, and the next state is `max(A_t - D_t, 0)`. Therefore, each transition probability is obtained by summing the probabilities of demand values that lead to the same next state. The resulting matrix `P` has non-negative elements and every row sums to one.

If `pi` is a stationary distribution, it satisfies

```text
pi = pi P,  with sum_i pi_i = 1.
```

The expected long-run cost is then the stationary-probability-weighted expected cost across all states and demand outcomes. In the code, `pi` is calculated by power iteration until the maximum change between iterations is smaller than `1e-14`. The model uses a finite state space, so this approach is practical and easy to audit. It also makes an important bridge between probability theory and business analytics: a long-run operational decision can be evaluated from recurring state transitions.

## 5. Implementation and Experimental Design

The implementation is contained in [`src/inventory_model.py`](../src/inventory_model.py). It uses only Python's standard library, NumPy, and pandas. This limited dependency set lowers the barrier to reproducing the work and helps the code run cleanly in VS Code, a terminal, or a GitHub Actions workflow.

The program is organised around several small, testable components. `Policy`, `CostParameters`, and `DemandScenario` are immutable data classes that make assumptions explicit. `daily_outcome` computes one period of ordering, sales, inventory, shortage, and cost. `simulate_policy` creates a complete daily trace for a given random seed. `build_transition_matrix` constructs the Markov matrix implied by a policy. `stationary_distribution` calculates the long-run state probabilities, while `markov_policy_metrics` converts those probabilities into business metrics. Finally, `evaluate_policies` combines exact and simulated results for every policy in the grid.

The Monte Carlo design uses 200 independent replications of 365 days for every policy. A replication is a fresh demand path generated from a deterministic seed. Policy `j` uses the same set of demand-path seeds as policy `k`; this is a common-random-numbers design. It makes comparisons more stable because observed differences are less likely to result only from one policy receiving an unusually easy or difficult sequence of demand. The script calculates an approximate 95% confidence interval for the simulated mean cost from the replication-level average costs.

The project exports all material needed to inspect or reuse the analysis:

| Output | Role in the project |
| --- | --- |
| `baseline_simulation_trace.csv` | A 90-day, row-by-row illustration of the operating logic |
| `policy_evaluation_summary.csv` | Exact and simulated metrics for all 45 policies |
| `cost_sensitivity_summary.csv` | Selected policy under nine alternative cost combinations |
| `model_assumptions.json` | Machine-readable model, cost, and simulation settings |
| `analysis_summary.md` | Generated results narrative used by the GitHub homepage |
| Four SVG figures | Vector-quality plots that render cleanly on GitHub |

The repository also includes a standard-library regression test suite. It checks that transition-matrix rows sum to one, stationary probabilities form a valid distribution, equal seeds reproduce equal simulation traces, a zero-demand scenario has a known cost, and invalid policies fail clearly. A GitHub Actions workflow installs dependencies, runs these tests, and regenerates the analysis on each push or pull request. This is a useful practical safeguard: it demonstrates that reproducibility is part of the project design rather than an afterthought.

## 6. Baseline Results

The lowest-cost policy in the tested baseline grid is `(s, S) = (1, 12)`. The exact Markov-chain average daily cost is `19.66`. The simulation estimate is `19.59`, and its 95% interval is `[19.54, 19.64]`. The small gap of `0.069` cost units per day is expected because a finite simulation estimates, rather than directly computes, the long-run mean. More importantly, the exact value lies close to the simulated interval, so the two approaches tell the same operational story.

| Metric | Exact Markov calculation | Monte Carlo estimate |
| --- | ---: | ---: |
| Average daily cost | 19.66 | 19.59 |
| Stockout rate | 10.69% | 10.60% |
| Fill rate | 93.91% | 93.98% |
| Average ending inventory | 4.71 | 4.71 |
| Average daily order quantity | 2.94 | 2.93 |

The next-best policies are close in cost, which is useful information. It indicates that a manager has room to trade a small amount of cost for better service. For example, `(2, 12)` has an exact average cost of `20.11`, only `0.46` higher than the minimum, but its stockout rate is `5.93%`, roughly half of the baseline recommendation's rate. A cost-minimising firm may choose `(1, 12)`; a firm that strongly values availability may find `(2, 12)` more appropriate. The model does not eliminate management judgment. It makes that judgment numerically explicit.

| Policy `(s, S)` | Average daily cost | Stockout rate | Fill rate | Average ending inventory |
| --- | ---: | ---: | ---: | ---: |
| `(1, 12)` | 19.66 | 10.69% | 93.91% | 4.71 |
| `(1, 11)` | 19.93 | 11.61% | 93.38% | 4.23 |
| `(2, 12)` | 20.11 | 5.93% | 97.09% | 5.11 |
| `(1, 10)` | 20.34 | 12.61% | 92.83% | 3.74 |
| `(2, 11)` | 20.46 | 6.43% | 96.86% | 4.62 |

The inventory trace provides a concrete view of the process. Stock is gradually depleted by daily demand, then jumps back to the target when the trigger level is reached. This pattern illustrates why the policy is not equivalent to holding a constant level of stock: it cycles through states and incurs ordering and holding costs at different times.

![Baseline inventory path](../outputs/figures/inventory_path.svg)

The heatmap compares the exact average daily cost across all tested policies. Darker cells are lower-cost outcomes, and the gold outline marks `(1, 12)`. Moving `S` too low creates shortages and repeated costly replenishment. Moving `s` or `S` too high protects service but accumulates holding cost. The best result sits between these extremes.

![Cost heatmap](../outputs/figures/policy_cost_heatmap.svg)

The final baseline figure makes the service-cost tension visible. Policies with more average inventory usually have lower stockout rates, but they do not necessarily have lower total cost. A decision process that looked only at stockout rate would choose a high-inventory policy; a process that looked only at cost might accept more service risk than the business wants. The plot creates a shared reference point for discussing that trade-off.

![Inventory and stockout trade-off](../outputs/figures/inventory_stockout_tradeoff.svg)

## 7. Sensitivity Analysis

A useful policy should remain interpretable when assumptions move. The project therefore varies holding cost over `{0.5, 1, 2}` and shortage cost over `{4, 8, 16}` while keeping all other baseline settings constant. For each of the nine scenarios, the program evaluates the same 45-policy grid through the Markov-chain calculation and selects the lowest-cost option.

| Holding cost | Shortage cost | Best policy | Average daily cost | Stockout rate |
| ---: | ---: | --- | ---: | ---: |
| 0.5 | 4 | `(1, 12)` | 16.54 | 10.69% |
| 0.5 | 8 | `(1, 12)` | 17.30 | 10.69% |
| 0.5 | 16 | `(2, 12)` | 18.29 | 5.93% |
| 1.0 | 4 | `(1, 12)` | 18.89 | 10.69% |
| 1.0 | 8 | `(1, 12)` | 19.66 | 10.69% |
| 1.0 | 16 | `(2, 12)` | 20.84 | 5.93% |
| 2.0 | 4 | `(1, 10)` | 23.19 | 12.61% |
| 2.0 | 8 | `(1, 10)` | 24.08 | 12.61% |
| 2.0 | 16 | `(1, 11)` | 25.81 | 11.61% |

Two patterns are clear. First, when shortage cost rises from `8` to `16` while holding cost remains low or moderate, the optimal policy raises the reorder point from `1` to `2`. The retailer begins replenishing sooner because a missed sale is more expensive. Second, when holding cost doubles to `2`, the model moves toward lower order-up-to levels such as `10` or `11`. Keeping stock lean becomes worth the somewhat higher shortage risk.

![Cost sensitivity](../outputs/figures/cost_sensitivity.svg)

The sensitivity table changes the interpretation of the baseline result. `(1, 12)` is not a claim that every retailer should wait until inventory reaches one unit. It is evidence that this policy is robust within some low-to-moderate holding-cost and shortage-cost settings. If a retailer's true shortage cost includes reputation damage or costly expedited fulfilment, a different policy may be preferable. Conversely, if product storage is expensive, perishable, or space-constrained, a lower target may be justified.

## 8. Business Interpretation

The project yields three business-facing insights. First, fixed ordering cost creates an economy of scale in replenishment. Ordering only when stock is low and refilling to a relatively high level avoids repeated setup costs. This is why the baseline model prefers `(1, 12)` over policies with small replenishment batches. The conclusion is not simply "hold more inventory"; the chosen policy holds enough inventory to reduce the frequency of orders while still limiting average end-of-day stock.

Second, cost optimisation and service optimisation should be separated. The lowest-cost policy has a stockout rate above ten percent, which may be unacceptable for a premium product, a critical spare part, or a retailer with a strict customer promise. The near-optimal policy `(2, 12)` is a useful alternative because it reduces stockout risk to below six percent for a relatively small cost increase. This provides a concrete starting point for a service-level conversation. A manager can state a required fill-rate target, then choose from policy options that meet it instead of treating the numerical minimum as a final answer.

Third, the value of the model lies in its repeatability. The parameters can be revised as the business learns more about demand, supplier lead time, storage costs, or customer behaviour. The code produces a new recommendation and a comparable set of outputs every time. In an operational setting, that repeatability supports a simple decision-support process: collect data, update assumptions, run the model, review the cost-service trade-off, and document the decision.

This type of process is relevant to digital transformation because it turns an informal operational rule into a transparent analytical asset. It does not require a large machine-learning system to be useful. A well-specified stochastic model can make uncertainty, assumptions, and trade-offs visible enough for a team to challenge and improve them.

## 9. Limitations, Ethics, and Next Steps

Several limits should be kept visible. Daily demand is independent in the baseline model, whereas real demand often shows weekday effects, promotions, weather sensitivity, trends, and seasonality. Supplier lead time is zero, so the model does not capture demand arriving while a replenishment order is in transit. Shortages are treated as lost sales, although some businesses backorder demand and incur a different cost pattern. The project also models one product and therefore ignores shared storage capacity, budget limits, substitution between products, and supplier minimum-order requirements.

These limitations are appropriate for a first portfolio project because they keep the model inspectable. They also define a credible development path. The next version could use an openly licensed retail-demand dataset to estimate the discrete demand distribution instead of specifying it manually. It could add a positive lead time by expanding the state to include outstanding orders. A service-level constraint, such as a minimum 97% fill rate, could be imposed before selecting the lowest-cost policy. Finally, a multi-product extension could consider capacity and budget constraints.

There is also an ethical and practical requirement to avoid false precision. The baseline values are illustrative, so it would be misleading to describe `19.66` as a prediction of a real company's cost. The number is an internally consistent result under stated assumptions. In a real deployment, cost parameters should be reviewed with finance and operations teams, demand data should be checked for bias or data-quality problems, and human decision makers should remain accountable for implementation choices.

## 10. Conclusion

This project develops a complete, reproducible inventory-optimisation study for a retailer facing stochastic demand. It formulates an `(s, S)` replenishment rule, represents the resulting inventory process as a finite Markov chain, calculates exact long-run metrics, and validates them with repeated Monte Carlo simulation. The baseline experiment selects policy `(1, 12)` as the lowest-cost option in the tested grid, with an exact average daily cost of `19.66`, a stockout rate of `10.69%`, and a fill rate of `93.91%`.

The central lesson is not that one pair of thresholds is universally correct. It is that uncertainty can be converted into a structured decision problem with assumptions, outputs, checks, and managerial trade-offs that others can inspect. The project therefore demonstrates a practical connection between mathematical modelling, Python programming, visual analysis, and supply-chain decision making.

## Reproducibility and AI Assistance Statement

The full implementation, inputs, generated outputs, test suite, and GitHub Actions workflow are included in this repository. Run `python3 -m unittest discover -s tests -v` to verify core model behaviour and `python3 src/inventory_model.py` to regenerate all baseline outputs. AI assistance was used for code review, explanation drafting, and visual refinement. The author is responsible for the project framing, assumptions, modelling choices, interpretation, and final presentation.

## References

1. Arrow, K. J., Harris, T., & Marschak, J. (1951). Optimal inventory policy. *Econometrica, 19*(3), 250-272. https://doi.org/10.2307/1906813
2. Scarf, H. (1960). The optimality of `(S, s)` policies in the dynamic inventory problem. In K. J. Arrow, S. Karlin, & P. Suppes (Eds.), *Mathematical Methods in the Social Sciences* (pp. 196-202). Stanford University Press. https://statistics.stanford.edu/technical-reports/optimality-ss-policies-dynamic-inventory-problem
3. Iglehart, D. L. (1963). Optimality of `(s, S)` policies in the infinite horizon dynamic inventory problem. *Management Science, 9*(2), 259-267. https://doi.org/10.1287/mnsc.9.2.259
4. Law, A. M. (2015). *Simulation Modeling and Analysis* (5th ed.). McGraw-Hill Education.

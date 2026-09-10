# Stochastic Inventory Optimisation for Ecommerce

## A Markov-Chain and Monte Carlo Study of One Category-Neutral SKU

**Project type:** Applied stochastic-process and operations analytics project  
**Implementation:** Python, NumPy, pandas, SVG visualisation  
**Repository:** See the root [README](../README.md) for reproducibility instructions and generated outputs.

## Abstract

Retailers must decide how much inventory to hold before they know what customers will buy. Too much stock raises holding costs and ties up capital; too little leads to lost sales and unreliable service. This report examines that trade-off for an illustrative ecommerce fulfilment centre replenishing one generic non-perishable SKU from a nearby central warehouse. The product category is intentionally unspecified so that the analysis tests the replenishment logic rather than relying on an invented commercial identity. The centre uses an `(s, S)` policy: when opening inventory is at or below reorder point `s`, it places an order that raises stock to `S`. Demand is modelled as a discrete random variable, and daily cost includes fixed ordering, unit purchasing, end-of-day holding, and shortage components.

Two methods are used. A finite Markov chain gives the stationary long-run performance of each fixed policy, evaluated numerically to a tolerance of `1e-14`. Repeated Monte Carlo simulation then checks that calculation. The baseline experiment compares 180 feasible policies, using 200 independent replications that discard 365 warm-up days before measuring 365 days. Under the baseline assumptions, `(0, 14)` has the lowest stationary average daily cost: `19.4352`. Its simulated mean is `19.4512`, with a 95% interval of `[19.4020, 19.5004]`; the stationary result lies inside that interval. The policy has a `14.10%` stockout rate and a `90.60%` fill rate.

The cost minimum is not automatically the best management choice. When an illustrative `97%` fill-rate constraint is imposed, `(2, 15)` becomes the lowest-cost feasible policy. It costs `19.7937` per day, only `0.3585` or `1.84%` more than the unconstrained minimum, while reducing the stockout rate to `4.70%`. Four demand distributions add a second stress test: their cost optima range from `(0, 14)` to `(2, 18)`, while their 97% choices range from `(1, 16)` to `(3, 18)`. A separate boundary audit covers all baseline, service, demand, and cost-sensitivity choices. The largest selected values are `s=3` and `S=21`, below the artificial limits of `8` and `24`. The value of the work lies in this explicit decision process: assumptions, calculations, boundary checks, and operational trade-offs remain open to inspection.

## 1. Introduction

Inventory management sits at the boundary between quantitative reasoning and everyday business judgment. A retailer must decide how much stock to carry even though demand, supplier performance, customer behaviour, and storage constraints are imperfectly known. The resulting trade-off is familiar: holding too much stock raises storage cost and may leave capital trapped in slow-moving goods; holding too little stock risks stockouts, missed transactions, and an inconsistent customer experience. The correct decision is rarely obvious because these costs interact.

The analysis deliberately keeps the setting narrow: one generic non-perishable SKU, a daily stock review, same-day transfer from a nearby central warehouse, and random demand. Its goal is to find a replenishment rule that balances long-run cost with service performance. There is no black-box prediction system here. Instead, the retailer follows a rule that a manager can explain in one sentence: when inventory reaches a threshold, replenish it to a chosen target. This is an `(s, S)` policy.

Threshold policies have a long history in inventory research, particularly when every order incurs a fixed cost. Arrow, Harris, and Marschak framed early inventory decisions as optimisation under uncertainty [1]. Scarf established the central place of `(s, S)` policies in inventory problems that unfold over time [2], and Iglehart studied their long-run behaviour in infinite-horizon settings [3]. This report does not claim a new theorem. It takes those mathematical ideas and works through a complete application, from code and simulation to figures, validation, and business interpretation.

That full workflow is the point of the project. It draws on my undergraduate mathematics training at the University of Manchester through probability, linear algebra, statistics, stochastic processes, and numerical reasoning, then turns those ideas into tested Python. This combination matters in operations management, business analytics, digital transformation, and information systems, where a model must be rigorous enough to examine and simple enough to discuss with decision makers.

The report addresses six questions:

1. How can an `(s, S)` replenishment policy be expressed as a stochastic state-transition model?
2. Which policy minimises long-run average cost in a baseline grid of alternatives?
3. Does a Monte Carlo implementation agree with the stationary Markov-chain calculation?
4. How does the recommendation change when holding cost or shortage cost changes?
5. How does a `97%` fill-rate requirement change the decision?
6. How do steady, volatile, baseline, and promotion-peak demand distributions change cost and service decisions?

Any answer must remain conditional. A policy is only as good as the demand distribution, cost structure, and service expectation used to evaluate it. Stating those assumptions plainly allows the result to be challenged and recalculated.

## 2. Background and Project Positioning

An inventory policy specifies when to order and how much to buy. In a periodic-review system, the firm checks stock at regular intervals and acts on its current inventory position. The `(s, S)` policy has two parameters: `s`, the reorder trigger, and `S`, the post-order target. Once stock is low enough, the firm places a single replenishment order instead of adjusting quantity continuously. For a planner, the appeal is practical. A complicated uncertainty problem becomes a rule that is easy to communicate and apply.

The policy becomes especially relevant when each order carries a fixed cost. Administrative work, transport coordination, or minimum processing charges make frequent small orders expensive. Yet ordering a large quantity too early leaves products in storage for longer. The analysis focuses on this tension between ordering less often and carrying more stock.

The literature motivates the policy, but the implementation still depends on modelling choices. A real retailer may face seasonal demand, uncertain lead time, supplier constraints, backorders, and interactions across many products. Here, the scope is limited to one product with independent daily demand so that the state process remains observable and reproducible. Under a fixed policy, tomorrow's inventory depends on today's inventory and a new demand realisation. Earlier events matter only through the current state. That is the Markov property, and it makes a stationary long-run calculation possible.

Code can produce a convincing-looking number even when the logic is wrong, so the result is calculated in two independent ways. The Markov method derives the long-run distribution of inventory states. The simulation method draws random demand paths and averages the outcomes across repeated experiments. When the two results agree, confidence in the implementation improves. That agreement is not automatic: a credible simulation still needs a clear experiment design, fixed seeds, enough replications, and outputs that can be inspected [4].

## 3. Problem Definition and Assumptions

Consider an illustrative ecommerce fulfilment centre holding one generic non-perishable SKU. Time is divided into days, indexed by `t = 1, 2, ...`. At the beginning of each day, the centre observes inventory and, if necessary, requests a transfer from a nearby central warehouse. The transfer is assumed to arrive before that day's demand. Customer demand then occurs, sales cannot exceed available units, and unmet demand is recorded as a lost sale rather than a backorder.

The category-neutral setting is intentionally stylised. It does not represent a named company, and the demand and cost inputs are not estimated from retailer records. The purpose is to make the mathematics and code auditable before an empirical extension. The baseline daily demand distribution is shown below.

| Daily demand `d` | 0 | 1 | 2 | 3 | 4 | 5 | 6 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Probability `P(D_t = d)` | 0.05 | 0.10 | 0.20 | 0.25 | 0.20 | 0.12 | 0.08 |

The distribution has an expected demand of `3.13` units per day. It gives substantial probability mass to moderate demand while retaining an upper tail that can create shortages. Demand draws are independent and identically distributed in the baseline model. This assumption is restrictive, but it allows the contribution of the inventory policy to be isolated before adding seasonality or other operational features.

The baseline cost parameters are also set for explanation rather than calibrated from a proprietary dataset.

| Parameter | Interpretation | Value |
| --- | --- | ---: |
| `K` | Fixed cost whenever an order is placed | 30 |
| `c` | Cost per replenished unit | 2 |
| `h` | Holding cost per unit of ending inventory | 1 |
| `p` | Penalty per unit of unsatisfied demand | 8 |

Because each order has a fixed cost, ordering frequency matters. Unfilled demand also carries a penalty, but the value is not high enough to force the model to eliminate every stockout. This creates a genuine trade-off. If zero shortage were required regardless of cost, there would be little left to optimise.

The baseline grid uses reorder points from `0` to `8` and order-up-to levels from `s + 1` to `24`, giving 180 feasible alternatives. This includes every integer pair satisfying `S > s` inside the declared rectangle. Zero is the natural physical lower bound for the reorder point. The upper limits are computational choices, so they need a stopping rule: no selected baseline, service, demand-scenario, or cost-sensitivity policy may touch either artificial upper boundary. Across all 19 audited selections, the largest reorder point is `3` and the largest order-up-to level is `21`, leaving margins of `5` and `3` units. The reported optimum is therefore the best policy in an audited finite grid, not a proof over every possible value of `s` and `S`.

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

The indicator `1{Q_t > 0}` equals one when the retailer orders and zero otherwise. The objective is to minimise long-run expected daily cost. Five metrics describe performance: average daily cost, stockout rate, fill rate, average ending inventory, and average order quantity. Stockout rate measures the share of days with unfilled demand; fill rate measures the share of requested units that are sold. Both are reported because they describe different aspects of service quality.

For a fixed `(s, S)` policy, possible opening states are `0, 1, ..., S`. Let `P_ij` represent the probability of moving from opening inventory state `i` to state `j` in one day. After applying the policy, the available stock is either `S` or `i`, and the next state is `max(A_t - D_t, 0)`. Therefore, each transition probability is obtained by summing the probabilities of demand values that lead to the same next state. The resulting matrix `P` has non-negative elements and every row sums to one.

If `pi` is a stationary distribution, it satisfies

```text
pi = pi P,  with sum_i pi_i = 1.
```

The long-run cost is the expected cost across all states and demand outcomes, weighted by the stationary probability of each state. In the code, `pi` is calculated by power iteration until the maximum change between iterations falls below `1e-14`. The reported stationary metrics are therefore deterministic numerical evaluations of the stated finite model up to that tolerance, rather than symbolic closed-form values. Because the state space is finite, the calculation is fast and easy to inspect. The practical meaning is straightforward: recurring state transitions can be used to evaluate a long-run operating policy.

The optimisation itself is exhaustive. The program calculates `C(s,S)` for every policy in the 180-member feasible set, then returns the row with the lowest stationary expected cost. A second decision rule first removes policies with fill rate below an illustrative `97%` target and minimises cost over the remaining set. This is a constrained finite optimisation problem:

```text
minimise C(s,S)
subject to FillRate(s,S) >= 0.97.
```

The generated Pareto frontier adds another check. A policy is removed when another policy is no more expensive, has no higher stockout rate, and is strictly better on at least one of those measures. Full derivations are provided in [`docs/mathematical_appendix.md`](../docs/mathematical_appendix.md).

## 5. Implementation and Experimental Design

The implementation is contained in [`src/inventory_model.py`](../src/inventory_model.py). It relies only on Python's standard library, NumPy, and pandas. With so few dependencies, the analysis can be reproduced in VS Code, a terminal, or a GitHub Actions workflow without a complicated setup.

The program is split into small components that can be tested separately. `Policy`, `CostParameters`, and `DemandScenario` are immutable data classes, so the main assumptions remain explicit. `daily_outcome` calculates one period of ordering, sales, ending inventory, shortage, and cost. `simulate_policy` builds a full daily trace for a chosen random seed. `build_transition_matrix` constructs the Markov matrix implied by a policy, `stationary_distribution` calculates the long-run state probabilities, and `markov_policy_metrics` translates those probabilities into business measures. `evaluate_policies` then brings the stationary and simulated results together for every policy in the grid.

For every policy, the Monte Carlo experiment runs 200 independent replications. Each replication first runs for 365 warm-up days, which are discarded, and then records the following 365 days. The warm-up matters because starting every replication at full inventory otherwise leaves a small transient bias in a one-year measurement window. Each replication uses a deterministic seed, and policy `j` receives the same demand path as policy `k`. This common-random-numbers design makes comparisons less sensitive to one option receiving an unusually easy or difficult sequence. The script uses replication-level average costs to calculate an approximate 95% confidence interval for the simulated mean.

The project exports all material needed to inspect or reuse the analysis:

| Output | Role in the project |
| --- | --- |
| `baseline_simulation_trace.csv` | A 90-day, row-by-row illustration of the operating logic |
| `policy_evaluation_summary.csv` | Stationary, simulated, and cost-component metrics for all 180 policies |
| `service_level_policy_summary.csv` | Unconstrained and 97% fill-rate decision rules |
| `policy_pareto_frontier.csv` | Policies not dominated on cost and stockout rate |
| `cost_sensitivity_summary.csv` | Selected policy under nine alternative cost combinations |
| `demand_scenario_summary.csv` | Cost and 97% service choices under four demand distributions |
| `demand_scenario_policy_evaluation.csv` | Stationary metrics for all 720 scenario-policy combinations |
| `search_boundary_audit.csv` | Machine-readable evidence that 19 selected policies avoid the artificial upper limits |
| `model_assumptions.json` | Machine-readable model, cost, and simulation settings |
| `analysis_summary.md` | Generated results narrative used by the GitHub homepage |
| Six SVG figures | Vector-quality plots that render cleanly on GitHub |

The repository includes a regression test suite built with Python's standard library. The tests cover transition-matrix validity, stationary probabilities, fixed-seed reproducibility, a known zero-demand case, invalid policies, warm-up handling, confidence-interval agreement, the illustrative `97%` service constraint, four demand distributions, Pareto dominance, and PDF table-header visibility. On every push or pull request, GitHub Actions installs pinned dependencies, runs the tests, regenerates the analysis, executes the notebook, and rebuilds the PDF. Reproducibility is checked by the workflow rather than left as a promise in the report.

### 5.1 Reliability controls and scope of the claim

Four checks support the published numbers. First, each transition-matrix row must sum to one and each stationary vector must be non-negative, sum to one, and satisfy `pi P = pi` to the numerical tolerance. Second, the four reported cost components must add back to total expected cost; this identity is enforced by a regression test. Third, repeated simulation uses the same random-number streams across policies, discards the initial transient, and reports confidence intervals from replication-level means. Fourth, the boundary audit prevents a search limit from silently becoming the answer. If any selected policy reaches `s=8` or `S=24`, the generation script raises an error and publication stops.

The publication verifier adds two independent numerical checks. It solves all 720 stationary systems directly as constrained linear equations and compares those distributions with power iteration. It also repeats all 19 published decisions on a larger 442-policy grid with `s <= 12` and `S <= 40`; none changes. These checks establish internal correctness for the stated finite model. They do not establish external validity for a real retailer because the demand probabilities and costs are illustrative rather than estimated. They also do not turn Monte Carlo agreement into a proof: the stationary Markov calculation supplies the exact finite-model ranking up to numerical tolerance, while simulation acts as an independent implementation check. Finally, the two cheapest baseline policies are very close. `(0, 14)` costs `19.4352` and `(1, 14)` costs `19.4384`, a gap of only `0.0031` per day. The ordering is numerically clear under the declared inputs, but a small empirical recalibration could reverse it. That sensitivity is part of the result, not a defect to hide.

## 6. Baseline Results

Within the tested baseline grid, `(s, S) = (0, 14)` has the lowest stationary expected cost: `19.4352` per day. Operationally, the centre waits until opening inventory is zero and then replenishes to 14 units. After warm-up, simulation gives `19.4512`, with a 95% interval of `[19.4020, 19.5004]`. The difference between the estimates is `0.0160` cost units per day, and the stationary value lies inside the simulated interval. The analytical and computational methods therefore agree at the precision expected from this Monte Carlo experiment.

| Metric | Stationary Markov calculation | Monte Carlo estimate |
| --- | ---: | ---: |
| Average daily cost | 19.44 | 19.45 |
| Stockout rate | 14.10% | 14.21% |
| Fill rate | 90.60% | 90.65% |
| Average ending inventory | 5.33 | 5.34 |
| Average daily order quantity | 2.84 | 2.84 |

The value `19.4352` is the sum of four stationary expectations. The fixed-order component is `6.0768`, the unit-order component is `5.6717`, holding cost is `5.3335`, and shortage cost is `2.3532`. For `(2, 15)`, those components become `6.4961`, `6.1161`, `6.6059`, and `0.5756`. Replenishing earlier and to a slightly higher target therefore raises ordering and holding costs but removes most of the shortage penalty. This decomposition explains why the constrained choice costs only slightly more overall.

Several alternatives sit close to the minimum, and that matters more than a winner-takes-all ranking suggests. Policy `(1, 14)` costs `19.4384`, only `0.0031` above `(0, 14)`, while improving fill rate from `90.60%` to `94.76%`. Policy `(2, 15)` costs `19.7937`, only `0.3585` or `1.84%` above the minimum, while its `4.70%` stockout rate is about one-third of the cost minimum's `14.10%`. Its `97.70%` fill rate makes it the least-cost policy that satisfies the declared `97%` service constraint. A firm focused strictly on the modelled objective may choose `(0, 14)`; one with a binding availability promise should choose `(2, 15)` under these assumptions.

| Policy `(s, S)` | Average daily cost | Stockout rate | Fill rate | Average ending inventory |
| --- | ---: | ---: | ---: | ---: |
| `(0, 14)` | 19.44 | 14.10% | 90.60% | 5.33 |
| `(1, 14)` | 19.44 | 9.21% | 94.76% | 5.70 |
| `(0, 15)` | 19.44 | 13.25% | 91.17% | 5.82 |
| `(1, 15)` | 19.45 | 8.60% | 95.11% | 6.19 |
| `(2, 15)` | 19.79 | 4.70% | 97.70% | 6.61 |

The inventory trace shows what the rule looks like in operation. Daily demand gradually draws stock down. Once inventory reaches the trigger, replenishment moves it back to the target. Inventory therefore cycles through a set of states rather than staying constant, and ordering and holding costs arise at different points in that cycle.

![Baseline inventory path](../outputs/figures/inventory_path.svg)

The heatmap compares stationary average daily cost across all 180 policies. Darker cells indicate lower cost, and the gold outline marks `(0, 14)`. If `S` is too low, shortages and repeated replenishment become expensive. If `s` or `S` is too high, service improves but holding cost accumulates. Crucially, the minimum is ten units below the artificial `S=24` ceiling, unlike the earlier narrow-grid result that sat at its boundary.

![Cost heatmap](../outputs/figures/policy_cost_heatmap.svg)

The final baseline figure puts cost and service on the same page. Policies with more average inventory usually have lower stockout rates, but not necessarily lower total cost. Looking only at stockouts would push the decision toward high inventory. Looking only at cost could accept more service risk than the business wants. The plot makes the compromise visible.

![Inventory and stockout trade-off](../outputs/figures/inventory_stockout_tradeoff.svg)

The Pareto frontier sharpens that comparison by removing policies that are simultaneously no cheaper and no better on stockouts. The gold point is the cost optimum, while the red point is the lowest-cost policy meeting the `97%` fill-rate requirement.

![Cost-service Pareto frontier](../outputs/figures/cost_service_frontier.svg)

## 7. Sensitivity Analysis

### 7.1 Cost parameters

A recommendation is more informative when readers can see how it changes with the assumptions. The sensitivity analysis varies holding cost over `{0.5, 1, 2}` and shortage cost over `{4, 8, 16}`, with all other baseline settings held constant. For each of the nine scenarios, the program applies the Markov-chain calculation to the same 180-policy grid and selects the lowest-cost option.

| Holding cost | Shortage cost | Best policy | Average daily cost | Stockout rate |
| ---: | ---: | --- | ---: | ---: |
| 0.5 | 4 | `(0, 19)` | 15.18 | 10.66% |
| 0.5 | 8 | `(1, 20)` | 15.88 | 6.50% |
| 0.5 | 16 | `(2, 21)` | 16.36 | 3.32% |
| 1.0 | 4 | `(0, 13)` | 18.24 | 15.10% |
| 1.0 | 8 | `(0, 14)` | 19.44 | 14.10% |
| 1.0 | 16 | `(2, 15)` | 20.37 | 4.70% |
| 2.0 | 4 | `(0, 9)` | 22.02 | 20.77% |
| 2.0 | 8 | `(0, 10)` | 23.67 | 19.01% |
| 2.0 | 16 | `(1, 11)` | 25.81 | 11.61% |

The results move in the expected direction. When shortage cost rises while holding cost remains low, the selected policy moves from `(0, 19)` through `(1, 20)` to `(2, 21)`. The retailer orders sooner and carries a higher target because a missed sale is now more expensive. When holding cost doubles to `2`, the selected order-up-to level falls to `9`, `10`, or `11`. In those scenarios, leaner stock is worth the additional shortage risk. The largest selected target is `21`, which still leaves three units below the tested ceiling and therefore passes the stopping rule.

![Cost sensitivity](../outputs/figures/cost_sensitivity.svg)

The table also limits what can be claimed about `(0, 14)`. It does not mean that every retailer should wait until stock is exhausted. It is the baseline cost answer for one illustrative parameter set, and the recommendation changes across the sensitivity grid. If shortage cost includes reputational damage or expensive emergency fulfilment, ordering earlier is sensible. If the product is costly to store, perishable, or space-intensive, a lower target fits better.

### 7.2 Demand distributions

Cost sensitivity does not answer the whole question because two demand processes can have similar means and very different tail risk. The model therefore repeats the 180-policy search under four discrete distributions. Baseline mixed demand preserves the original assumptions. Steady demand concentrates probability near three units. Volatile demand keeps mean demand at `3.00` but shifts more probability into the tails. Promotion-peak demand raises the mean to `4.79` and extends possible daily demand to eight units. Costs, lead time, and the policy grid remain unchanged, so the comparison isolates the effect of changing demand.

| Demand scenario | `E[D]` | `Var(D)` | Cost optimum | Daily cost |
| --- | ---: | ---: | --- | ---: |
| Baseline mixed | 3.13 | 2.43 | `(0, 14)` | 19.44 |
| Steady | 3.00 | 0.90 | `(0, 14)` | 18.58 |
| Volatile | 3.00 | 4.60 | `(1, 14)` | 19.37 |
| Promotion peak | 4.79 | 3.07 | `(2, 18)` | 25.72 |

The cost-only optimum changes across the four scenarios. Each row comes from a fresh enumeration of all 180 policies rather than from carrying the baseline answer forward. Steady demand retains `(0, 14)`, volatility moves the reorder point to one, and the promotion peak raises both thresholds to `(2, 18)`. At the same mean demand of `3.00`, the steady cost optimum has a `92.38%` fill rate while the volatile optimum has `92.72%`; similar aggregate service is achieved through different policies because the demand tails differ. Variance changes both state occupancy and the value of ordering earlier even when average demand does not.

| Demand scenario | Cost-optimum fill rate | Lowest-cost 97% policy | Constrained fill rate |
| --- | ---: | --- | ---: |
| Baseline mixed | 90.60% | `(2, 15)` | 97.70% |
| Steady | 92.38% | `(1, 16)` | 97.04% |
| Volatile | 92.72% | `(3, 16)` | 98.31% |
| Promotion peak | 95.49% | `(3, 18)` | 97.55% |

The illustrative service target exposes a clearer policy response. Greater volatility requires an earlier trigger than steady demand, while promotion-peak demand needs a target of 18 units. This does not prove that 97% is the right target for a real retailer. It shows how a declared service requirement changes the feasible set and how the demand distribution changes the least-cost policy within that set. For each scenario, 200 warm-up-adjusted Monte Carlo replications independently check the selected cost optimum; every stationary cost lies inside its simulated 95% interval.

![Demand-distribution comparison](../outputs/figures/demand_scenario_comparison.svg)

## 8. Business Interpretation

The first business lesson concerns order frequency. A fixed ordering cost creates an economy of scale, so ordering only when stock is low and replenishing to a relatively high target avoids repeated setup charges. That is why the baseline cost calculation favours `(0, 14)` over policies with smaller batches. The result should not be reduced to "wait for a stockout." It follows because the assumed shortage penalty is modest relative to the fixed setup cost; a business with stronger availability commitments should use the constrained decision instead.

Cost and service also need separate attention. The lowest-cost baseline policy has a `14.10%` stockout rate, which may be difficult to defend when availability matters. Policy `(2, 15)` is the minimum-cost solution after the illustrative `97%` fill-rate constraint is imposed. The extra `0.3585` per day, or `1.84%`, buys a `9.40` percentage-point reduction in stockout probability and raises fill rate by `7.10` percentage points. Under more volatile or promotion-peak demand, the same target changes both thresholds. The numerical minimum becomes an input to management judgement rather than a substitute for it.

Finally, the analysis can be rerun. As the business learns more about demand, lead time, storage costs, or customer behaviour, those inputs can be revised. The code will produce a new recommendation in the same output format. In practice, the process is simple: collect data, update assumptions, run the model, review the cost-service trade-off, and record the decision.

This is a modest but useful form of digital transformation. An informal stocking rule becomes a documented analytical process that a team can inspect and revise. It does not need a large machine-learning system. A well-specified stochastic model is enough to make uncertainty and trade-offs visible.

## 9. Limitations, Ethics, and Next Steps

The model has several important limits. Baseline demand is independent from day to day, whereas real sales often vary with weekdays, promotions, weather, trends, and seasons. Supplier lead time is zero, so no demand arrives while an order is in transit. Shortages become lost sales rather than backorders. The single-product scope also leaves out shared storage, budget constraints, product substitution, and supplier minimum-order requirements.

Those simplifications keep the first version inspectable, but they also point directly to the next one. An openly licensed retail dataset could replace the manually specified demand distribution. Positive lead time could be added by including outstanding orders in the state, and a later multi-product version could introduce shared capacity and budget constraints. The current `97%` service constraint provides a useful template for those larger feasible-set restrictions.

False precision is another concern. The baseline inputs are illustrative, so `19.4352` is not a prediction of any real company's daily cost. The category-neutral SKU also should not be mistaken for a hidden real product. These are internally consistent results under the assumptions listed in this report. Before real use, finance and operations teams would need to define the product category, review the service target and cost parameters, check demand data for bias and quality problems, and remain responsible for implementation.

## 10. Conclusion

This study applies an `(s, S)` replenishment rule to a category-neutral ecommerce case with stochastic demand. A finite Markov chain provides stationary long-run metrics evaluated to a declared numerical tolerance, and warm-up-adjusted Monte Carlo simulation independently checks the implementation. Within the audited 180-policy baseline grid, `(0, 14)` is the unconstrained cost minimum at `19.4352` per day. Once an illustrative `97%` fill-rate requirement is imposed, `(2, 15)` becomes the lowest-cost feasible choice at `19.7937` per day. Repeating the search under four demand distributions moves the cost optimum as far as `(2, 18)` during the promotion peak. All 19 reported selections stay below the artificial upper boundaries, and the stationary scenario costs lie within their corresponding simulation intervals.

No pair of thresholds is universally correct. Even the baseline ranking deserves care because `(1, 14)` is only `0.0031` per day more expensive than `(0, 14)`. The stronger conclusion is that an uncertain stocking decision can be expressed through assumptions, calculations, checks, and trade-offs that other people can inspect. Here, mathematical modelling, Python, and visual analysis support a supply-chain decision without hiding the judgement behind it.

## Reproducibility and AI Assistance Statement

The repository contains the implementation, inputs, generated outputs, executed notebook, test suite, formal PDF, and GitHub Actions workflow. Run `python3 -m unittest discover -s tests -v` to verify model behaviour, then run `python3 src/inventory_model.py` to regenerate the analytical outputs. AI assistance supported structured brainstorming, code review, debugging, prose editing, and visual inspection. Every accepted numerical claim is tied to generated evidence or a regression test. The author remains responsible for the framing, assumptions, mathematics, implementation choices, interpretation, and final presentation; a fuller record appears in [`docs/ai_workflow.md`](../docs/ai_workflow.md).

## References

1. Arrow, K. J., Harris, T., & Marschak, J. (1951). Optimal inventory policy. *Econometrica, 19*(3), 250-272. https://doi.org/10.2307/1906813
2. Scarf, H. (1960). The optimality of `(S, s)` policies in the dynamic inventory problem. In K. J. Arrow, S. Karlin, & P. Suppes (Eds.), *Mathematical Methods in the Social Sciences* (pp. 196-202). Stanford University Press. https://statistics.stanford.edu/technical-reports/optimality-ss-policies-dynamic-inventory-problem
3. Iglehart, D. L. (1963). Optimality of `(s, S)` policies in the infinite horizon dynamic inventory problem. *Management Science, 9*(2), 259-267. https://doi.org/10.1287/mnsc.9.2.259
4. Law, A. M. (2015). *Simulation Modeling and Analysis* (5th ed.). McGraw-Hill Education.

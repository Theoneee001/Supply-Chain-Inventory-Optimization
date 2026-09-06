# Application Materials Draft

## CV Bullet Draft

- Built a Python-based stochastic inventory optimisation model using an `(s, S)` replenishment policy, finite Markov-chain analysis, and Monte Carlo validation across 45 policy combinations.
- Produced reproducible visual analytics and sensitivity analysis to quantify the trade-off between average cost, stockout risk, and inventory holding; the baseline recommendation achieved a 93.91% fill rate.

## 150-200 Word Personal Statement Material

One of my recent academic projects examined how mathematical modeling can support supply-chain inventory decisions under uncertain demand. I built a Python simulation of an `(s, S)` replenishment policy, where a retailer places an order when inventory falls below a reorder point and replenishes stock to a target level. By modeling daily demand as a discrete random variable and comparing policies through repeated Monte Carlo simulations, I analyzed the trade-off between ordering cost, holding cost, and shortage risk. The project helped me see how probability and stochastic-process thinking can be transformed into practical business decision tools. Instead of treating mathematics as an abstract subject, I used it to answer an operational question: how can a firm make stable replenishment decisions when the future is uncertain? This experience strengthened my interest in applying mathematical reasoning, programming, and data visualization to business analytics and digital transformation problems.

## Interview Explanation: 60 Seconds

I built a supply-chain inventory optimisation project using an `(s, S)` policy. The model assumes daily demand is random, and the retailer must decide when to reorder and how much inventory to hold. I used Python to calculate exact long-run results with a finite Markov chain, then validated them through Monte Carlo simulation across 45 policy combinations. The lowest-cost baseline policy was `s = 1` and `S = 12`, but it still had a 10.69% stockout rate. That made the key learning more nuanced than simply finding a minimum: I could show the business cost of improving service by comparing it with policies such as `s = 2, S = 12`. The project showed me how mathematical modelling can turn uncertainty into a practical, explainable decision rule.

## Interview Explanation: 3 Minutes

I wanted to build a project that connected probability with a business decision people make every day: how much inventory should a retailer keep when it does not know tomorrow's demand? I used a single-product setting so the logic would be easy to inspect. The retailer reviews stock every day. If inventory falls below a reorder point `s`, it orders enough to raise stock to a target `S`. Demand is random, so the retailer must balance four forces: fixed ordering cost, unit purchasing cost, holding cost, and the cost of unmet demand.

Technically, I built the model in Python in two linked ways. The first was a finite Markov chain. Once the policy is fixed, tomorrow's inventory only depends on today's inventory state and the random demand realisation. That let me calculate an exact long-run average cost from the stationary distribution. The second was Monte Carlo simulation. I ran 200 replications of 365 days for every policy, using the same demand-path seeds across policies to make comparisons stable. The simulated result for the selected policy was very close to the Markov result, which gave me confidence that the implementation was correct.

Under the baseline assumptions, the lowest-cost policy was `(1, 12)`, with an exact average daily cost of 19.66 and a fill rate of 93.91%. But I did not present that as a universal answer. Its stockout rate was still 10.69%, so I compared it with `(2, 12)`, which cost only slightly more but reduced stockouts to 5.93%. I also ran a sensitivity analysis. When shortage cost increased, the model replenished earlier; when holding cost increased, it selected leaner inventory targets.

What I value about the project is that it made the trade-offs visible. Instead of saying a manager should hold more or less inventory based on intuition, the model provides an explicit rule, documents its assumptions, and allows the recommendation to be updated as the business learns more. It showed me how mathematical modelling, programming, and communication can work together in operations and business analytics.

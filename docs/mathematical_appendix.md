# Mathematical Appendix

## 1. Why this is a finite Markov chain

Fix a policy `(s, S)`. Let `I_t` be opening inventory on day `t`, before any order, and let `D_t` be that day's demand. The replenishment function is

```text
r(i) = S,  if i <= s
r(i) = i,  if i > s.
```

The next opening state is

```text
I_(t+1) = max(r(I_t) - D_t, 0).
```

Once `I_t` is known, earlier inventory values add no information about `I_(t+1)`. The only new uncertainty is `D_t`, which is independent from day to day in the baseline model. Therefore

```text
P(I_(t+1) = j | I_t = i, I_(t-1), ..., I_0)
= P(I_(t+1) = j | I_t = i).
```

This is the Markov property. Because replenishment never raises inventory above `S`, the state space is finite: `{0, 1, ..., S}`.

## 2. Transition probabilities

For current state `i`, available stock after the ordering decision is `a = r(i)`. The next state equals `max(a - d, 0)` when demand is `d`. Thus

```text
P_ij = sum P(D_t = d)
       over demand values d for which max(r(i) - d, 0) = j.
```

Several demand values may lead to `j = 0`, so their probabilities are added. Every element of `P` is non-negative, and each row sums to one. The tests verify both properties.

## 3. Stationary distribution

A stationary row vector `pi` satisfies

```text
pi = pi P,
sum_i pi_i = 1,
pi_i >= 0.
```

The code starts from a uniform probability vector and repeatedly applies `P`:

```text
pi_(n+1) = pi_n P.
```

Iteration stops when the largest element-wise change is below `1e-14`. For the tested policies, the chain reaches a unique recurrent pattern and the iteration converges. The resulting `pi_i` is interpreted as the long-run proportion of days that begin in state `i`.

This step uses linear algebra as well as probability. The stationary distribution is a left eigenvector of `P` associated with eigenvalue `1`, normalised to sum to one. Power iteration gives a direct numerical route to the same object.

## 4. Expected one-day reward and long-run cost

For state `i` and demand `d`, define order quantity `q(i) = r(i) - i`, shortage `u(i,d) = max(d - r(i), 0)`, and ending inventory `e(i,d) = max(r(i) - d, 0)`. One-day cost is

```text
g(i,d) = K * 1{q(i) > 0} + c*q(i) + h*e(i,d) + p*u(i,d).
```

The expected cost conditional on state `i` is

```text
g_bar(i) = sum_d P(D_t = d) * g(i,d).
```

The long-run average cost under a fixed policy is then

```text
C(s,S) = sum_i pi_i * g_bar(i).
```

The same stationary weighting produces stockout probability, expected ending inventory, expected order quantity, and fill rate. This is a Markov reward model: the chain determines how often states occur, while the reward function assigns an operational consequence to each state-demand pair.

## 5. Finite-grid optimisation

The feasible set is explicitly declared:

```text
s in {1, 2, 3, 4, 5, 6}
S in {s + 2, ..., 12}.
```

It contains 45 policies. The unconstrained decision is

```text
minimise C(s,S) over all 45 feasible policies.
```

The program evaluates every member of the set, so `(1, 12)` is a global minimum within this grid. No gradient method or heuristic search is needed. The result does not establish optimality outside the grid or under different assumptions.

The illustrative service-constrained decision is

```text
minimise C(s,S)
subject to FillRate(s,S) >= 0.97.
```

After removing policies that fail the constraint, `(2, 12)` has the lowest expected cost under baseline demand. The value `0.97` is a scenario chosen to demonstrate constrained optimisation, not an asserted industry standard. This formulation separates mathematical optimisation from management preference: the model calculates the best policy once the objective and constraint have been chosen.

## 6. Demand-distribution experiments

For a discrete demand scenario with values `d_k` and probabilities `p_k`, the first two moments are

```text
E[D] = sum_k p_k*d_k,
Var(D) = sum_k p_k*(d_k - E[D])^2.
```

The steady and volatile scenarios both have `E[D] = 3.00`, but their variances are `0.90` and `4.60`. Holding the mean constant while changing the variance separates demand level from tail risk. The promotion-peak scenario changes both the level and shape, with `E[D] = 4.79` and possible demand up to eight units.

For each distribution, the transition matrix is rebuilt because every `P_ij` depends on the demand probabilities. The stationary distribution, reward averages, and all 45 policy scores are then recalculated. The cost optimum remains `(1, 12)` across the four tested distributions. Under the illustrative 97% constraint, however, the minimum-cost trigger rises from two under steady or baseline demand to three under volatile demand and four during the promotion peak. This comparison shows why equal average demand does not imply equal service performance.

## 7. Monte Carlo estimator and confidence interval

For policy `a`, replication `r` produces a measured average cost `X_(a,r)` over `T = 365` days. The Monte Carlo estimate is

```text
X_bar_a = (1/R) * sum_r X_(a,r),    R = 200.
```

The reported approximate 95% interval is

```text
X_bar_a +/- 1.96 * s_a / sqrt(R),
```

where `s_a` is the sample standard deviation of the replication means. The interval quantifies simulation uncertainty; it does not describe uncertainty in the illustrative demand probabilities or cost assumptions.

Each replication discards 365 warm-up days. Without this step, every run begins at `S`, so the finite measurement window over-represents the chosen initial condition. After warm-up, the baseline simulated mean is `19.6571`, close to the stationary value `19.6568`, and the stationary result lies inside the simulated interval `[19.6053, 19.7089]`.

## 8. Common random numbers

Policy comparisons use the same seed for replication `r` across every policy. The policies therefore face the same demand path in that replication. This induces positive correlation between their cost estimates and reduces noise in pairwise differences. The technique is useful because the decision depends on relative performance, not only on the precision of each policy estimate in isolation.

## 9. Pareto efficiency

Policy `A` dominates policy `B` on the reported cost-stockout criteria if

```text
Cost_A <= Cost_B,
Stockout_A <= Stockout_B,
```

with at least one strict inequality. A dominated policy is never attractive when those are the only two criteria: another policy is no more expensive and no worse on stockouts. The generated Pareto frontier retains only non-dominated policies and makes the cost of improved service visible.

## 10. What the mathematics does not prove

The stationary analysis is numerically evaluated to a tolerance of `1e-14` for the model that was specified. It does not prove that demand is independent, that lead time is zero, that a shortage costs eight currency units, or that 97% is the correct service target. Those are assumptions, not theorems. This distinction matters. Mathematics gives a rigorous conditional answer; responsible modelling also states the conditions and tests how the answer moves when they change.

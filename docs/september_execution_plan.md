# September Execution Plan

## Project Name

Supply Chain Inventory Optimization with Stochastic Demand

Chinese positioning: 基于随机过程的供应链库存优化模型

## September Goal

By the end of September, produce a complete first version of the academic project:

- Complete English report
- Reproducible Python code
- Visual charts
- GitHub-ready README
- Narrative notebook
- Application-material notes

The September version now presents a complete workflow from mathematical model to business interpretation, with reproducible outputs and application-ready evidence.

## Project Outline

1. Problem Definition
   - Explain why uncertain demand creates an inventory decision problem.
   - Define the retailer, product, demand, cost, and replenishment setting.

2. Mathematical Model
   - Define inventory state `I_t`.
   - Define random demand `D_t`.
   - Define the `(s, S)` policy.
   - Define ordering, holding, and shortage costs.
   - Explain why the process can be interpreted through Markov-chain thinking.

3. Code Implementation
   - Build simulation function.
   - Build policy grid.
   - Run repeated Monte Carlo replications.
   - Export CSV results.

4. Visualization
   - Inventory path and demand.
   - Average cost heatmap across policies.
   - Inventory-stockout trade-off chart.
   - Cost-service Pareto frontier.

5. Business Interpretation
   - Identify the best policy under baseline assumptions.
   - Explain why the policy works.
   - Discuss operational trade-offs.
   - Connect the project to supply-chain, operations, and digital transformation programs.

6. Application Packaging
   - README for GitHub.
   - Formal report in Markdown and PDF.
   - Executed narrative Notebook.
   - CV, personal statement, interview, and LinkedIn material.

## Execution List

### Completed in Current First Version

- [x] Create project folder.
- [x] Create GitHub-ready README.
- [x] Create Python simulation script.
- [x] Define `(s, S)` inventory policy.
- [x] Define baseline demand distribution.
- [x] Define cost parameters.
- [x] Run grid search across policies.
- [x] Export baseline simulation trace.
- [x] Export policy evaluation summary.
- [x] Generate six SVG figures.
- [x] Complete English report with references, results, sensitivity analysis, and AI statement.
- [x] Complete narrative notebook with executable analysis cells.
- [x] Create deliverables checklist.

### Completed Refinements and Future Research Boundary

- [x] Expand report to 3000-5000 words.
- [x] Add literature/context paragraph on inventory management and stochastic processes.
- [x] Add sensitivity analysis for shortage cost.
- [x] Add sensitivity analysis for holding cost.
- [ ] Add positive lead time as a future research extension; it is outside the declared September baseline.
- [x] Add top-five policy table into README and report.
- [x] Convert report Markdown to a professionally formatted PDF.
- [x] Add all generated figures to the report.
- [x] Polish Notebook into a full narrative notebook.
- [x] Prepare CV bullets and PS paragraph.

## Current Numerical Result

Baseline grid-search result:

- Best reorder point: `s = 0`
- Best order-up-to level: `S = 14`
- Stationary average daily cost: `19.4352`
- Stationary stockout rate: `14.10%`
- Stationary average ending inventory: `5.33`

Interpretation:

Under the current assumptions, larger replenishment batches are favoured because fixed ordering cost is meaningful. The policy waits until opening stock reaches zero, then replenishes to 14, balancing fewer orders against shortage risk. The warm-up-adjusted Monte Carlo estimate is `19.4512`, compared with the numerically evaluated stationary Markov result of `19.4352`; the stationary value lies inside the simulated 95% interval. The search covers 180 policies, and all 19 published selections remain below the artificial upper boundaries.

Service-constrained result:

- Minimum required fill rate: `97%`
- Lowest-cost feasible policy: `(2, 15)`
- Stationary average daily cost: `19.7937`
- Stationary fill rate: `97.70%`
- Cost premium over the unconstrained optimum: `1.84%`
- Stockout-rate reduction: `9.40` percentage points

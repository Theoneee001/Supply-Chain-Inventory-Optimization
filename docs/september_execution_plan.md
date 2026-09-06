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

The September version does not need to be perfect. It needs to be complete enough to show a full workflow from mathematical model to business interpretation.

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

5. Business Interpretation
   - Identify the best policy under baseline assumptions.
   - Explain why the policy works.
   - Discuss operational trade-offs.
   - Connect the project to supply-chain, operations, and digital transformation programs.

6. Application Packaging
   - README for GitHub.
   - Report PDF later.
   - Notebook later.
   - CV and PS素材 later.

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
- [x] Generate three SVG figures.
- [x] Complete English report with references, results, sensitivity analysis, and AI statement.
- [x] Complete narrative notebook with executable analysis cells.
- [x] Create deliverables checklist.

### Next Refinement Round

- [x] Expand report to 3000-5000 words.
- [x] Add literature/context paragraph on inventory management and stochastic processes.
- [x] Add sensitivity analysis for shortage cost.
- [x] Add sensitivity analysis for holding cost.
- [ ] Add lead-time extension.
- [x] Add top-five policy table into README and report.
- [ ] Convert report markdown to PDF.
- [ ] Add generated figures into the report.
- [x] Polish Notebook into a full narrative notebook.
- [x] Prepare CV bullets and PS paragraph.

## Current Numerical Result

Baseline grid-search result:

- Best reorder point: `s = 1`
- Best order-up-to level: `S = 12`
- Exact average daily cost: `19.66`
- Exact stockout rate: `10.69%`
- Exact average ending inventory: `4.71`

Interpretation:

Under the current assumptions, larger replenishment batches are favored because fixed ordering cost is meaningful. The policy waits until inventory is low, then replenishes to a relatively high level, balancing fewer orders against manageable stockout risk. The Monte Carlo estimate of daily cost is `19.59`, close to the exact Markov result of `19.66`.

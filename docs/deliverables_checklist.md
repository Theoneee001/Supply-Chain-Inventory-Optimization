# Deliverables Checklist

## Minimum September Deliverables

- [x] English report completed in Markdown.
- [x] Problem definition clearly states the inventory decision problem.
- [x] Mathematical model explains inventory state, random demand, and `(s, S)` policy.
- [x] Python code runs from a clean environment.
- [x] Six labelled vector figures are generated.
- [x] GitHub README explains background, method, usage, and outputs.
- [x] AI assistance statement included.
- [x] Results include business interpretation, not only technical output.

## Final Submission-Ready Deliverables

- [x] Report exported as a 14-page PDF with contents, figures, tables, and references.
- [x] Jupyter Notebook contains narrative explanation, executable cells, and saved outputs.
- [x] Code is reproducible with a fixed random seed.
- [x] Six vector figures are labelled and visually checked.
- [x] Four valid demand distributions are compared across the same 45-policy grid.
- [x] The English report contains 3000-5000 words of prose under the repository's documented counting rule.
- [x] Direct Python dependencies are pinned in `requirements-lock.txt` and used by CI.
- [x] README includes result figures.
- [x] Repository contains no private or sensitive data.
- [x] Project summary is rewritten into CV bullet points.
- [x] 150-200 word PS material paragraph prepared.
- [x] Interview explanation prepared in 60-second version.
- [x] Interview explanation prepared in 3-minute version.
- [x] Mathematical appendix connects the model to probability, matrices, expectation, and optimisation.
- [x] AI workflow states what AI assisted with and what was independently verified.
- [x] GitHub Actions reruns tests, model outputs, Notebook execution, and PDF construction.

## Required Files

| File | Purpose | Current Status |
| --- | --- | --- |
| `README.md` | GitHub landing page | Complete |
| `report/final_report.md` | English research report source | Complete |
| `report/final_report.pdf` | Submission-ready report | Complete and visually checked |
| `src/inventory_model.py` | Reproducible simulation and Markov-chain code | Complete |
| `tests/` | Model, report, and artifact-verifier regression tests | Complete: 19 tests |
| `.github/workflows/reproducibility.yml` | GitHub automated verification | Complete |
| `scripts/verify_artifacts.py` | Cross-platform semantic output checks | Complete |
| `notebooks/supply_chain_inventory_optimization.ipynb` | Executed narrative analysis | Complete and deterministic |
| `outputs/demand_scenario_summary.csv` | Selected decisions under four demand distributions | Complete |
| `outputs/demand_scenario_policy_evaluation.csv` | Full scenario-policy evidence | Complete: 180 rows |
| `outputs/figures/` | Vector visual outputs | Six figures generated |
| `docs/mathematical_appendix.md` | Detailed derivation and assumptions | Complete |
| `docs/application_materials.md` | CV, PS, interview, and LinkedIn material | Complete |
| `docs/ai_workflow.md` | Responsible AI record | Complete |
| `data/README.md` | Data status and assumptions | Complete |

## Evidence-Based Quality Checks

- The 45-policy search is exhaustive within the declared grid.
- The stationary cost for `(1, 12)` is `19.6568`; the warm-up-adjusted simulation estimate is `19.6571` with 95% interval `[19.6053, 19.7089]`.
- The illustrative 97% fill-rate decision is `(2, 12)` under baseline demand, with `97.09%` fill rate and `20.11` expected daily cost.
- The four demand scenarios produce 180 auditable policy-scenario rows. The cost optimum stays `(1, 12)`, while the illustrative 97% reorder point rises as high as `4` in the promotion-peak case.
- The case study is category-neutral by design and makes no claim about a specific ecommerce product category.
- The Notebook produces the same file hash on consecutive executions.
- Application claims point to a named repository file rather than unsupported narrative.

# AI-Assisted Development and Verification Record

## Purpose

AI served as a development assistant, not as a source of business data or mathematical authority. This record separates AI-supported work from the decisions and checks that remain the author's responsibility.

## Where AI helped

| Activity | AI contribution | Human or programmatic check |
| --- | --- | --- |
| Project scoping | Suggested ways to connect stochastic processes with an inventory decision | The author limited the scope to one auditable SKU and documented each assumption |
| Code review | Flagged edge cases and inconsistencies between simulation and stationary results | Regression tests reproduce each accepted issue |
| Debugging | Helped investigate why the original Monte Carlo interval missed the stationary value | Controlled experiments isolated initial-state bias; warm-up test now guards it |
| Documentation | Proposed structure and edited prose for clarity | Generated outputs support every numerical claim |
| Demand scenarios | Suggested stress tests that separate the effects of mean demand and variance | Code validates every probability distribution and evaluates the same 180-policy grid in each scenario |
| Search-space review | Flagged that the first cost choice sat on the artificial `S=12` ceiling | The grid was expanded to 180 policies and a runtime audit now rejects any selected upper-bound policy |
| Visual QA | Helped identify overlapping labels, missing axis ticks, and unreadable PDF table headers | The final review rendered and inspected every PDF page and regenerated SVG file |
| Application materials | Helped translate technical work into CV and interview language | Repository methods and results set the limit for every claim |

## A concrete example of AI-assisted debugging

The first report stated that the simulated 95% interval `[19.54, 19.64]` closely validated the stationary Markov cost `19.66`. That wording hid a real issue: `19.66` was outside the interval.

I traced the data flow rather than patching the prose. Every simulation replication started at full inventory `S`, and the first 365 measured days retained a small transient effect. Experiments compared the original design with a 365-day warm-up and with stationary-state initialisation. Both alternatives removed the discrepancy. The final implementation uses a common warm-up because it preserves aligned demand paths across policy comparisons.

After the expanded search, the baseline cost choice is `(0, 14)`. Its simulated mean is `19.4512`, its interval is `[19.4020, 19.5004]`, and the stationary value `19.4352` lies inside. The stationary distribution is obtained numerically to a tolerance of `1e-14`, so the report does not claim a symbolic closed form. Tests now fail if warm-up handling, component reconciliation, the validation relationship, or the search-boundary rule regresses.

## Boundaries

AI did not:

- provide proprietary retailer data;
- choose hidden cost parameters;
- establish the Markov result without executable calculation;
- decide that cost should override customer service;
- verify its own claims without tests or generated evidence;
- determine authorship or academic responsibility.

## Verification rules

1. Numerical claims must come from generated CSV or JSON outputs.
2. Mathematical claims must be visible in code, derivation, or a cited source.
3. Suggested code changes require tests before acceptance.
4. Compare stationary and simulated methods independently.
5. Public prose must state when inputs are illustrative.
6. Disclose AI assistance in the final report and README.
7. Reject publication when a selected policy touches an artificial upper search boundary.

## Authorship statement

AI supported brainstorming, code review, debugging, prose editing, and visual inspection. The author remains responsible for the problem definition, assumptions, mathematical formulation, code accepted into the repository, interpretation, and final submission.

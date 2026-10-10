# Business analysis: provincial banking markets

[Documentation index](README.md) · [Executed questions and SQL](competency-questions.md)

Analysis period: **July 2026**, with same-month YoY comparisons to July 2025. Findings below refer to the recorded warehouse/CQ evidence, not live market conditions. The ten question queries were recorded on 10 October 2026; later documentation and assistant changes do not constitute new source retrieval.

## Decision context

Regional strategy and channel-planning teams need to compare banking-market size, growth, branch coverage, and economic context before selecting provinces for deeper investigation. Absolute balances are dominated by Bangkok and may reflect head-office booking. A useful comparison therefore needs normalized measures, explicit reference periods, and adjustable screening criteria.

The platform supports **market screening and question formation**. It does not have customer portfolios, individual-bank market share, credit quality, branch costs, or profitability data.

## Integrated evidence

The analysis combines BOT monthly provincial banking balances and branch counts with DOPA registered population, NESDC annual GPP, and national macro/policy context. The mart covers 77 provinces and 25 months. Geographic identifiers are mapped explicitly; availability rules prevent newer annual vintages from being treated as historically known data.

The current recorded World Bank vintage contains 66 annual observations but is unavailable for the earlier banking months. See [source methods and temporal limitations](data-sources.md). Macro ingestion success and usable historical macro coverage are different checks.

## Findings and appropriate follow-up

All financial balances below are **THB million** unless otherwise stated.

| Question | Recorded finding | Interpretation and next investigation |
| --- | --- | --- |
| Loan-growth consistency | Mukdahan leads latest-month loan YoY at approximately **+1.61%**; Pathum Thani has positive YoY in **12/12** recent months, averaging **+1.47%** | Latest-month rank and persistent growth are different measures. Inspect portfolio composition and demand before attributing the pattern |
| Deposits versus loans | Provincial totals: deposits **+3.89% YoY**, loans **−0.17%**; growth gap approximately **4.06 percentage points** | Examine where deposit growth exceeds lending growth; account for cross-area booking |
| Branch coverage | Branches fall from **4,790 to 4,516**, or **−5.72% YoY** | Branch density is a screening proxy. Assess digital usage, service locations, and competing channels |
| Comparable economic scale | Chon Buri GPP: **1,234,303**, loans: **450,683**; Rayong GPP: **1,099,856**, loans: **147,746** | Similar annual GPP does not imply similar banking demand. GPP 2024p and July 2026 balances have different reference periods |
| Policy-rate context | Month-end policy rate: **1.75%** in July 2025 versus **1.00%** in July 2026 | Compare timing descriptively; the dataset does not identify a causal policy effect on provincial lending |
| Fewer branches, growing loans | Pathum Thani: **−14 branches**, **+0.73% loan YoY**; Phang Nga: **−2**, **+1.47%** | Investigate channel changes and relocations; do not infer that branches are unnecessary |
| Adjustable shortlist | Excluding Bangkok, GPP ≥100,000, branches per 100,000 residents ≤15, and loans ≥50,000 returns **22 provinces** | Thresholds are explicit research hypotheses, not a ranking of investment suitability |
| Highest loan/deposit ratio | Roi Et: **127.36%**, from loans **48,648** and deposits **38,197** | This is a geographic balance ratio, not an individual bank's liquidity measure |
| Highest deposits per registered resident | Bangkok: **THB 2,111,467.67/person**, using registered population for 2025 | Recorded deposits and registered residents are not customer-level savings or actual resident wealth |
| Loan concentration | Bangkok: **76.38%**; top five provinces: **83.11%** of provincial recorded loans totaling **18,100,244** | Separate booking location from borrower residence; compare results with Bangkok excluded |

CQ01 specifically tests twelve-month growth consistency, not the separate latest-month growth ranking. CQ04 defines GPP peers as a gap no greater than **15% of the larger value**. See [all ten reproducible queries and their result rows](competency-questions.md); predefined question wording remains Thai to match the application.

## Recommended demonstration sequence

1. Open the market overview and inspect the selected banking month, balances, YoY, and concentration.
2. Compare two provinces; inspect population/GPP reference years and normalized measures.
3. Adjust shortlist thresholds and explain why each returned province meets the criteria.
4. Open a predefined business question and inspect its result, caveat, SQL, and bound period.
5. Ask the assistant for loans per registered resident, exclude Bangkok in a follow-up, and switch to a table.
6. Use the sources page to distinguish retrieval time, source vintage, and usable historical coverage.

Grafana provides a separate provisioned reporting view. Airflow's task/run history demonstrates orchestration only for observed runs; a screenshot of one successful run is not evidence of continuous scheduling.

## Interpretation boundaries

Monthly banking balances are stocks and must not be summed across time. Provincial figures are rounded to THB million, so their sum can differ slightly from BOT's independently rounded national total. Registered population is not the customer count, branch counts omit alternative channels, and national macro/policy context is not province-specific.

A defensible next stage would combine external market research, competitor information, channel usage, operating costs, and credit-quality evidence. None of those missing inputs is inferred by this prototype.

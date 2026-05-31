# Search-Term Analysis Weekly Agent Implementation Plan

## 1. Objective

Implement the weekly `Search-Term Analysis Agent` as a deterministic analytics
pipeline plus an executive-facing web dashboard. Each weekly run ingests the
latest Amazon Sponsored Products search-term report, compares performance
against target guardrails and prior outcomes, produces CUT / FIX / GROW actions,
and generates a web-based budget council dashboard for next-week ad budget
decisions.

The core math must stay reproducible in Python. The dashboard and narrative
layer should make the results easy for business leaders to understand, challenge,
and tune with human inputs.

## 2. Agent Architecture

### Core Agents

1. Run Orchestrator Agent
2. Load and Validation Agent
3. Campaign Enrichment Agent
4. Scorecard Agent
5. Negative Keyword CUT Agent
6. Harvest GROW Agent
7. Recommendation Writer Agent
8. Executive Dashboard Agent
9. W&B Reliability Agent
10. Regression Test Agent

### Execution Order

1. Run Orchestrator Agent initializes config, source paths, and run context.
2. Load and Validation Agent validates raw report structure and data quality.
3. Campaign Enrichment Agent normalizes campaign metadata and recomputes metrics.
4. Scorecard Agent calculates weighted bucket and blended performance.
5. Negative Keyword CUT Agent identifies wasted-spend terms.
6. Harvest GROW Agent identifies terms to promote into exact-match campaigns.
7. Recommendation Writer Agent writes the markdown operating report.
8. Executive Dashboard Agent generates dashboard data and web assets.
9. W&B Reliability Agent logs config, tables, metrics, artifacts, and checks.
10. Regression Test Agent validates known monthly or weekly baselines.

## 3. Shared Data Contracts

### Raw Input Schema

The raw report must provide these canonical fields:

- `Customer Search Term`
- `Match Type`
- `Campaign Name`
- `Clicks`
- `Impressions`
- `Spend`
- `Orders`
- `Sales`
- `ACoS`
- `CVR`
- `CTR`

The loader may accept Amazon export aliases, such as `7 Day Total Sales`,
`7 Day Total Orders (#)`, `Click-Thru Rate (CTR)`, and
`Total Advertising Cost of Sales (ACOS)`, but downstream agents use only the
canonical names.

### Enriched Row Schema

Each enriched row must include:

- Original canonical columns.
- `Customer Search Term Normalized`
- `Campaign Name Normalized`
- `Targeting type`
- `Bucket`
- Recomputed `ACoS`, `ROAS`, `CTR`, and `CVR`
- Exported metric reference columns.
- `Validation Flags`

### Campaign Classification Rules

Parse `Targeting type` from `Campaign Name`:

- Contains ` - Auto - `: `Auto`
- Contains ` - Disc KW - `: `Disc KW`
- Contains ` - Conv KW - `: `Conv KW`
- Contains ` - Conq PAT - `: `Conq PAT`
- Contains ` - Def PAT - `: `Def PAT`
- Else: `Other`

Parse `Bucket` from `Customer Search Term`:

- Normalized search term starts with `B0`: `Brand Defense`
- Else: `Discovery`

## 4. Config

All thresholds must be stored in `wandb.config` or the local W&B-compatible
manifest when W&B is unavailable.

Required defaults:

```yaml
target_acos_blended: 0.25
target_acos_discovery: 0.25
target_acos_brand: 0.20
neg_zero_order_min_spend: 50
neg_high_acos_min_spend: 100
high_acos_cutoff: 1.0
review_band_min: 0.5
review_band_max: 1.0
harvest_min_orders: 3
harvest_max_acos: 0.20
```

Dashboard defaults:

```yaml
cut_adoption_pct: 80
cpc_pressure_pct: 0
cvr_lift_pct: 0
experiment_reserve_default: 2500
```

## 5. Run Orchestrator Agent

### Mission

Own the weekly run. It wires the agents together, enforces execution order,
passes immutable config, stops on failed self-checks, and emits the final report
and dashboard paths.

### Inputs

- Weekly search-term CSV or Excel path.
- Optional prior-week run directory for outcome comparison.
- Output directory.
- W&B project and run metadata.
- Optional regression baseline.

### Implementation Steps

1. Parse CLI arguments.
2. Load default config and optional overrides.
3. Start W&B run or local manifest run.
4. Call each agent in sequence.
5. Persist each table artifact.
6. Stop on schema errors, scorecard tie-out failures, invalid HARVEST rows, or
   failed regression checks.
7. Emit `run_summary.json` with report path, dashboard path, metrics, checks,
   and artifact lineage.

### Outputs

- `next_month_recommendations.md`
- `dashboard/index.html`
- `dashboard/data.js`
- `run_summary.json`
- All CSV artifacts
- W&B/local manifest

## 6. Load and Validation Agent

### Mission

Load the weekly search-term report, validate required columns, normalize basic
strings, and coerce numeric fields.

### Implementation Steps

1. Read CSV or Excel. For Excel, default to `Data` sheet when present.
2. Map Amazon export aliases to the canonical schema.
3. Confirm all 11 canonical columns are available.
4. Trim search term, match type, and campaign name.
5. Flag blank campaigns and blank search terms.
6. Coerce spend, sales, clicks, impressions, and orders to numeric values.
7. Preserve exported ACoS, CVR, and CTR only for reference.
8. Produce a validation report.

### Key Checks

- Missing required columns fail the run.
- Numeric coercion failures fail the run.
- Blank campaigns are logged.
- Blank search terms are kept in total metrics but excluded from uploadable
  CUT/GROW actions.

## 7. Campaign Enrichment Agent

### Mission

Apply the campaign classification rules and recompute trusted metrics from raw
numerators and denominators.

### Implementation Steps

1. Normalize `Customer Search Term` to lowercase trimmed text.
2. Normalize `Match Type` to uppercase.
3. Parse `Targeting type` from `Campaign Name`.
4. Parse `Bucket` from normalized search term:
   - Starts with `B0`: `Brand Defense`
   - Otherwise: `Discovery`
5. Recompute row metrics:
   - `ACoS = Spend / Sales`
   - `ROAS = Sales / Spend`
   - `CTR = Clicks / Impressions`
   - `CVR = Orders / Clicks`
6. Handle divide-by-zero explicitly.
7. Write `enriched_search_terms.csv`.

### Outputs

- Enriched search-term table.
- Targeting type distribution.
- Bucket distribution.
- Unknown targeting count.

## 8. Scorecard Agent

### Mission

Create the weekly business scorecard by bucket and blended total.

### Implementation Steps

1. Group by `Bucket`.
2. Sum spend, sales, orders, clicks, and impressions.
3. Compute weighted ACoS, ROAS, CTR, and CVR from summed values.
4. Add blended total row.
5. Attach target ACoS by bucket.
6. Compute:
   - `variance = actual_acos - target`
   - `dollar_over_target = variance * sales`
7. Identify the bucket driving the miss.
8. Write a concise three-sentence narrative.
9. Assert blended spend and sales tie exactly to bucket totals.

### Outputs

- `scorecard.csv`
- Scorecard narrative.
- Driver bucket.
- Bucket-level metrics for dashboard use.

## 9. Negative Keyword CUT Agent

### Mission

Identify terms that should be cut or reviewed because they consume spend without
enough profitable sales.

### Classification Rules

- `Orders = 0 AND Spend >= 50`: `NEGATIVE: zero orders`
- `Spend >= 100 AND ACoS >= 100%`: `NEGATIVE: high ACoS`
- `Spend >= 100 AND 50% <= ACoS < 100%`: `REVIEW`
- Blank search term: `INVALID: blank search term`
- Else: `keep`

### Outputs

- `negative_keyword_candidates.csv`
- `negative_keyword_summary.csv`
- Negative candidate count.
- Review candidate count.
- Recoverable spend.

## 10. Harvest GROW Agent

### Mission

Find proven discovery terms that should be promoted into exact-match conversion
campaigns.

### Implementation Steps

1. Roll up by normalized search term.
2. Filter to terms with:
   - `Orders >= 3`
   - `ACoS < 20%`
   - Nonblank search term
3. Compute:
   - `clicks_in_auto_disc`
   - `clicks_in_conv_exact`
4. Assign verdict:
   - Auto/Disc clicks and no Conv Exact clicks: `HARVEST -> promote to Conv KW exact`
   - Conv Exact clicks present: `Already covered`
   - No Auto/Disc clicks: `Outside harvest source`
5. Assert every HARVEST row has discovery clicks and no exact coverage.

### Outputs

- `harvest_candidates.csv`
- HARVEST count.
- HARVEST sales.
- HARVEST orders.
- HARVEST weighted ACoS.

## 11. Recommendation Writer Agent

### Mission

Create the weekly markdown operating report for action owners.

### Report Sections

- Executive summary.
- Scorecard.
- CUT negative keyword list.
- FIX review terms.
- GROW harvest terms.
- Next-week targets.
- Caveats and checks.

### Notes

The markdown report is operator-oriented. The dashboard is leader-oriented.
Both should be generated from the same artifacts so they do not drift.

## 12. Executive Dashboard Agent

### Mission

Generate a web-based dashboard that communicates the weekly ad-performance
story to business leaders and lets them fine-tune next-week budgets through
what-if scenarios.

### Inputs

- `run_summary.json`
- `scorecard.csv`
- `negative_keyword_candidates.csv`
- `harvest_candidates.csv`
- Config thresholds.

### Dashboard Requirements

The dashboard must show:

- Current spend.
- Current sales.
- Blended ACoS vs target.
- Dollar over target.
- CUT opportunity.
- GROW pipeline.
- Brand Defense / Discovery / Blended scorecard.
- Decision posture.
- Budget what-if controls.
- Scenario metrics.
- CUT / FIX / GROW action tables.
- Board-ready decision memo.

### Human Inputs

Leaders can tune:

- Brand Defense budget.
- Discovery budget.
- Harvest exact-match budget.
- Experiment reserve.
- Target blended ACoS.
- CUT adoption rate.
- CPC pressure assumption.
- CVR lift or decline assumption.
- Notes or business constraints.

### What-If Scenarios

#### Efficiency Reset

Margin-first plan that does not simply cut budget. For each candidate budget
reduction, calculate:

```text
budget_cut = current_spend - proposed_spend
revenue_loss = current_sales - projected_sales
cut_efficiency_ratio = revenue_loss / budget_cut
```

Rank candidate reductions by lowest `cut_efficiency_ratio`, subject to:

- Projected ACoS improves.
- Target ACoS is met or moves meaningfully closer.
- Minimum sales floor is preserved.
- Mandatory CUT/FIX guardrails are applied.
- High-performing HARVEST terms are not starved.

The dashboard should show the ratio and concise note explaining whether the
proposed reduction is efficient, acceptable, or too sales-destructive.

#### Balanced Recovery

Restore target-ACoS discipline while funding proven HARVEST terms. This is the
default weekly planning scenario.

#### Growth Push

Increase spend on HARVEST and selected discovery opportunities while making the
ACoS risk explicit. Use only when leaders accept a growth exception.

### Scenario Calculations

For each scenario and human-edited plan, calculate:

- Proposed total budget.
- Projected sales.
- Projected ACoS.
- Target gap.
- CUT savings applied.
- Harvest coverage vs observed run-rate.
- Spend delta.
- Sales delta.
- For Efficiency Reset: `cut_efficiency_ratio`.

### Dashboard Notes

Generate concise, insightful notes:

- What changed vs actual week.
- Which bucket is driving the miss.
- Why the recommended budget is justified.
- Where leaders are accepting risk.
- Which actions are mandatory before budget release.

## 13. W&B Reliability Agent

### Mission

Guarantee reproducibility, visible threshold changes, and artifact lineage.

### Implementation Steps

1. Log every threshold to `wandb.config` or local manifest.
2. Log raw, enriched, scorecard, CUT, GROW, report, and dashboard artifacts.
3. Log self-checks as metrics.
4. Fail loudly on self-check failures.
5. Support sweeps over thresholds and scenario inputs.

### Key Metrics

- Blended ACoS.
- Dollar over target.
- Recoverable spend.
- Negative candidate count.
- Review candidate count.
- HARVEST count.
- HARVEST sales.
- HARVEST weighted ACoS.
- Dashboard scenario outcome metrics.

## 14. Regression Test Agent

### Mission

Protect the pipeline against silent logic drift.

### Baseline Checks

Keep one hand-verified period, such as April, with expected metrics:

- Blended spend.
- Blended sales.
- Dollar over target.
- Brand Defense spend/sales/ACoS.
- Discovery spend/sales/ACoS.
- Negative keyword count.
- Recoverable spend.
- HARVEST count.
- HARVEST sales.
- HARVEST weighted ACoS.

The regression must fail if campaign bucket logic, weighted metric logic, CUT
classification, or HARVEST classification changes unexpectedly.

## 15. Recommended Repository Layout

```text
amazon_business_analyst/
  agents/
    orchestrator.py
    load_validation_agent.py
    campaign_enrichment_agent.py
    scorecard_agent.py
    negative_kw_cut_agent.py
    harvest_grow_agent.py
    recommendation_writer_agent.py
    wandb_reliability_agent.py
    regression_test_agent.py
  dashboard_generator.py
  config.py
  io.py
  metrics.py
  schemas.py
dashboard/
  index.html
  styles.css
  app.js
  data.js
tests/
  fixtures/
    april_expected_metrics.json
  test_agents_unit.py
  test_pipeline_workbook.py
  test_dashboard_generator.py
```

## 16. MVP Build Order

1. Implement Load and Validation Agent.
2. Implement Campaign Enrichment Agent with search-term-based bucket logic.
3. Implement Scorecard Agent with weighted metrics and tie-outs.
4. Implement Negative Keyword CUT Agent.
5. Implement Harvest GROW Agent.
6. Implement Recommendation Writer Agent.
7. Implement Executive Dashboard Agent.
8. Add W&B/local artifact logging.
9. Add regression baseline.
10. Add dashboard scenario tests.

## 17. Acceptance Criteria

The implementation is complete when:

- A weekly CSV or Excel file can run end to end.
- All metrics are recomputed from raw spend, sales, clicks, orders, and
  impressions.
- Bucket logic uses `Customer Search Term` prefix `B0` for Brand Defense.
- `next_month_recommendations.md` is generated.
- Web dashboard files are generated.
- Dashboard accepts human budget inputs and recalculates scenarios live.
- Efficiency Reset reports `revenue_loss / budget_cut` and uses it to avoid
  sales-destructive cuts.
- W&B or local manifest captures config, metrics, self-checks, and artifacts.
- Regression tests pass against the hand-verified baseline.

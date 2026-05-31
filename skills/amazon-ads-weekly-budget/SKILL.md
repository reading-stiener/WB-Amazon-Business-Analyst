---
name: amazon-ads-weekly-budget
description: Use when Codex needs to analyze Amazon Sponsored Products search-term reports for pajamas or similar retail campaigns, generate weekly CUT/FIX/GROW recommendations, update or run the amazon_business_analyst pipeline, create or verify the executive web dashboard, support what-if budget scenarios, or explain next-week ad budget decisions using ACoS, spend, sales, and search-term performance.
---

# Amazon Ads Weekly Budget

## Core Workflow

Use the repo-local Python pipeline as the source of truth for math-heavy work.
Do not calculate scorecards or CUT/GROW rules by hand unless debugging a small
case.

1. Read the current request and identify whether the user wants code changes,
   a report run, dashboard work, or business interpretation.
2. Use the local project root when present:
   `/Users/jianfanl/tmp/weights_biases/WB-Amazon-Business-Analyst`.
3. Run or update the pipeline under `amazon_business_analyst/`.
4. Regenerate artifacts under `outputs/<run_name>/`.
5. Validate with `python -m unittest discover -s tests`.
6. For dashboard UI changes, verify `dashboard/app.js` with Node syntax check
   and browser-smoke-test the local dashboard.

## Canonical Run Command

Use the bundled runtime when available:

```bash
/Users/jianfanl/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
  -m amazon_business_analyst.agents.orchestrator \
  --input "/Users/jianfanl/tmp/weights_biases/WB-Amazon-Business-Analyst/IG PPC - Amazon Exercise.xlsx" \
  --sheet Data \
  --output-dir "/Users/jianfanl/tmp/weights_biases/WB-Amazon-Business-Analyst/outputs/april_validation" \
  --regression-baseline "/Users/jianfanl/tmp/weights_biases/WB-Amazon-Business-Analyst/tests/fixtures/april_expected_metrics.json"
```

Expected primary outputs:

- `next_month_recommendations.md`
- `scorecard.csv`
- `negative_keyword_candidates.csv`
- `harvest_candidates.csv`
- `run_summary.json`
- `dashboard/index.html`
- `dashboard/data.js`

## Classification Rules

Keep these rules synchronized across `plan.md`, implementation, tests, and
dashboard artifacts.

Targeting type from `Campaign Name`:

- ` - Auto - ` -> `Auto`
- ` - Disc KW - ` -> `Disc KW`
- ` - Conv KW - ` -> `Conv KW`
- ` - Conq PAT - ` -> `Conq PAT`
- ` - Def PAT - ` -> `Def PAT`
- Else -> `Other`

Bucket from normalized `Customer Search Term`:

- Starts with `B0` -> `Brand Defense`
- Else -> `Discovery`

## Weekly Rendering Rule

The dashboard must present weekly navigation, not a monthly-only view.

- If source rows contain weekly or daily date ranges, aggregate by calendar
  week directly.
- If source rows contain one broader report range, such as `Apr 1 - Apr 30`,
  synthesize calendar-week views by allocating each row across overlapping
  weeks by day count.
- Mark synthesized weeks as estimated in the dashboard note.
- Provide clickable `Week 1`, `Week 2`, etc. plus `Previous` and `Next`
  controls.

Do not hide that synthesized weekly views are estimates.

## CUT / FIX / GROW Rules

CUT:

- `Orders = 0 AND Spend >= 50` -> `NEGATIVE: zero orders`
- `Spend >= 100 AND ACoS >= 100%` -> `NEGATIVE: high ACoS`
- Blank search term -> invalid for uploadable negatives

FIX:

- `Spend >= 100 AND 50% <= ACoS < 100%` -> `REVIEW`
- Treat review terms as bid, copy, relevance, campaign-isolation, or landing
  page diagnostics, not automatic negatives.

GROW:

- Roll up by search term.
- Candidate when `Orders >= 3`, `ACoS < 20%`, and search term is nonblank.
- `Auto` or `Disc KW` clicks present and no `Conv KW` exact clicks ->
  `HARVEST -> promote to Conv KW exact`.
- Already in `Conv KW` exact -> `Already covered`.

## Dashboard Requirements

The executive dashboard must communicate business decisions clearly:

- Current spend, sales, ACoS, over-target dollars.
- Brand Defense / Discovery / blended scorecard.
- CUT opportunity and GROW pipeline.
- Week selector and previous/next controls.
- What-if controls for Brand Defense, Discovery, Harvest Exact, Experiment
  Reserve, target ACoS, CUT adoption, CPC pressure, CVR change, and leader notes.
- Scenario presets: `Efficiency Reset`, `Balanced Recovery`, `Growth Push`.
- Board-ready decision memo that updates with human inputs.

Efficiency Reset must not be a simple budget cut. Calculate:

```text
budget_cut = current_spend - proposed_spend
revenue_loss = current_sales - projected_sales
cut_efficiency_ratio = revenue_loss / budget_cut
```

Prefer low `cut_efficiency_ratio`, subject to ACoS improvement, minimum sales
floor, mandatory CUT/FIX guardrails, and not starving proven HARVEST terms.

## Validation

Run:

```bash
cd /Users/jianfanl/tmp/weights_biases/WB-Amazon-Business-Analyst
/Users/jianfanl/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
  -m unittest discover -s tests
```

Also run for dashboard JavaScript changes:

```bash
/Users/jianfanl/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node --check dashboard/app.js
```

If showing the dashboard, use the static server:

```bash
/Users/jianfanl/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
  -m http.server 8765 \
  --bind 127.0.0.1 \
  --directory "/Users/jianfanl/tmp/weights_biases/WB-Amazon-Business-Analyst/dashboard"
```

Dashboard URL:

```text
http://127.0.0.1:8765/index.html
```

## Business Interpretation Rules

- State whether weekly views are actual weekly source data or estimated from a
  broader report range.
- Explain budget recommendations in terms of ACoS movement, spend delta, sales
  delta, CUT savings, and HARVEST coverage.
- For leaders, keep notes concise and action-oriented.
- Keep deterministic pipeline outputs separate from judgment calls. Use Python
  artifacts for metrics; use analysis for risk framing and recommendations.

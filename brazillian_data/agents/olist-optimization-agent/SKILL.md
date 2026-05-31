---
name: olist-optimization-agent
description: Convert Brazilian Olist forecasts, health flags, seasonality findings, and operational opportunities into scored closed-loop business actions using SKILL.md instructions only.
---

# Olist Optimization Agent

## Role

Turn analysis into ranked actions for profitable growth. Do not write application code. Every recommendation must be measurable in the next monthly loop.

## Inputs

- `outputs/runs/<round_id>/monthly_sales_actuals.csv`
- `outputs/runs/<round_id>/monthly_forecasts.csv`
- `outputs/runs/<round_id>/forecast_backtest_results.csv`
- `outputs/runs/<round_id>/product_health_flags.csv`
- `outputs/runs/<round_id>/category_health_flags.csv`
- `outputs/runs/<round_id>/demand_seasonality_findings.md`
- `outputs/runs/<round_id>/ops_efficiency_opportunities.csv`

## Action Categories

Use these action types:

- Growth investment shift
- Promotion reduction or pause
- Regional seller or inventory expansion
- Free-shipping threshold
- Product bundle
- Installment-led upsell
- Delivery promise adjustment
- Seller quality intervention
- Category page or placement change
- Human investigation

## Scoring

Score every action:

```text
closed_loop_score =
  expected_sales_lift
+ expected_margin_proxy_lift
- operational_risk
- confidence_penalty
```

Use qualitative scores when precise money impact is not defensible:

- `high`
- `medium`
- `low`

Translate confidence conservatively:

- High confidence: supported by sales, margin proxy, and operational signals
- Medium confidence: supported by sales and one strong supporting signal
- Low confidence: sparse data, mixed signals, or weak causality

## Required Output

When a `round_id` is provided, write outputs under `outputs/runs/<round_id>/`.

Create `recommended_actions.csv` with:

- `rank`
- `action`
- `action_type`
- `target`
- `expected_sales_impact`
- `expected_margin_proxy_impact`
- `closed_loop_score`
- `evidence`
- `confidence`
- `risk`
- `owner`
- `time_to_impact`
- `next_measurement`

Create `closed_loop_scorecard.csv` with:

- `month`
- `action_rank`
- `action`
- `baseline_metric`
- `target_metric`
- `measurement_month`
- `status`
- `learning_to_capture`

## Recommendation Rules

- Favor actions that improve both revenue and margin proxy.
- Do not scale high-freight or poor-review segments without an operational fix.
- Pair growth actions with tracking metrics.
- Pair margin actions with customer-experience risk checks.
- Keep top recommendations few and concrete.

## Example Action Format

```text
Action: Regionalize top RJ demand in health/beauty and bed/bath/table.
Target: RJ category-state pairs with high GMV and low same-state fulfillment.
Expected sales impact: medium.
Expected margin-proxy impact: high.
Evidence: high affected revenue, weak same-state fulfillment, high late rate, low review score.
Confidence: medium.
Risk: seller onboarding may take longer than one monthly cycle.
Next measurement: RJ freight percentage, late delivery rate, review score, and category-state revenue.
```

## Handoff

Pass recommended actions and scorecard to:

- Critic and QA agent
- Executive summary agent

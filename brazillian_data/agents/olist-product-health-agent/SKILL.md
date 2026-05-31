---
name: olist-product-health-agent
description: Detect Brazilian Olist products and categories that are deteriorating using SKILL.md instructions only. Use when flagging products going bad from sales trend, category-relative share, forecast miss, reviews, freight, lateness, cancellation, and unavailable signals.
---

# Olist Product Health Agent

## Role

Flag products and categories that are going bad. Do not write application code. Do not flag a product only because sales declined; adjust for category trend, seasonality, and operational signals.

## Inputs

- `outputs/runs/<round_id>/monthly_sales_actuals.csv`
- `outputs/runs/<round_id>/monthly_forecasts.csv`
- `outputs/runs/<round_id>/forecast_backtest_results.csv`

## Health Signals

Use these signals:

- Revenue decline versus trailing 3-month average
- Unit decline versus trailing 3-month average
- Category-relative share loss
- Negative forecast miss
- Review score below 4.0 or declining
- Freight percentage rising
- Late delivery rate rising or above 10%
- Cancellation rate rising
- Unavailable rate rising
- Seller or state concentration risk

## Severity Rules

High severity:

- Revenue or units down more than 30% versus trailing average
- Segment underperforms its category or state trend
- At least one CX or operational signal is bad: review below 4.0, late rate above 10%, rising freight percentage, cancellation/unavailable issue

Medium severity:

- Revenue or units down 15-30%
- Segment underperforms category or forecast
- Supporting signal is mixed or weak

Low severity:

- Decline exists but may be seasonal, sparse, or category-wide

## Required Outputs

When a `round_id` is provided, write outputs under `outputs/runs/<round_id>/`.

Create `product_health_flags.csv` with:

- `month`
- `product_id`
- `category`
- `severity`
- `sales_change_pct`
- `units_change_pct`
- `category_share_change`
- `forecast_error_pct`
- `avg_review_score`
- `freight_pct`
- `late_delivery_rate`
- `cancellation_rate`
- `unavailable_rate`
- `likely_cause`
- `recommended_owner`
- `confidence`
- `next_measurement`

Create `category_health_flags.csv` with:

- `month`
- `category`
- `severity`
- `sales_change_pct`
- `units_change_pct`
- `forecast_error_pct`
- `avg_review_score`
- `freight_pct`
- `late_delivery_rate`
- `likely_cause`
- `recommended_owner`
- `confidence`
- `next_measurement`

## Diagnosis Labels

Use one or more:

- `demand_softness`
- `seasonality`
- `category_mix_shift`
- `pricing_or_aov_issue`
- `freight_margin_drag`
- `delivery_cx_issue`
- `review_quality_issue`
- `availability_or_cancellation_issue`
- `sparse_data`

## Guardrails

- Do not call a product bad when its category is declining similarly.
- Do not overreact to one-month drops for sparse products.
- Treat forecast misses as supporting evidence, not proof by themselves.
- Include confidence and the next metric to check.

## Handoff

Pass health flags to:

- Optimization agent
- Critic and QA agent
- Executive summary agent

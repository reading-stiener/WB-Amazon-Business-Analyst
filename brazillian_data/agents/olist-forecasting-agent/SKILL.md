---
name: olist-forecasting-agent
description: Forecast monthly Brazilian Olist sales and units using SKILL.md instructions only. Use when producing monthly forecasts, backtests, WAPE, MAPE, forecast bias, and confidence labels from monthly actuals.
---

# Olist Forecasting Agent

## Role

Forecast monthly sales and units, then compare forecasts with actuals. Do not write application code. Use transparent forecasting methods and explain confidence.

## Inputs

- `outputs/runs/<round_id>/monthly_sales_actuals.csv`
- `outputs/policy_memory.md`
- `outputs/runs/<previous_round_id>/learning_handoff.md` when available
- `outputs/runs/<previous_round_id>/forecast_method_leaderboard.csv` when available

## Forecast Levels

Forecast these grains when sufficient history exists:

- Marketplace total
- Product category
- Customer state
- Category by customer state
- Top products

For long-tail products with sparse history, avoid high-confidence product-level forecasts. Roll them up into category or category-state forecasts.

## Self-Improving Forecast Policy

Each round must improve the forecast policy from prior round evidence. Before producing the final forecast, read `outputs/policy_memory.md` and the previous round's `learning_handoff.md` when available. Apply active policy rules unless the critic or data clearly rejects them.

Do not use one method everywhere. Choose the forecast method per grain and, when history is sufficient, per segment.

```text
grain = aggregation level, such as marketplace, category, customer_state, category_customer_state, product
segment = one value inside a grain, such as category=health_beauty or customer_state=RJ
```

The next round must:

- Compare multiple candidate methods by rolling backtest WAPE and bias.
- Pick the best defensible method per grain/segment.
- Preserve champion methods unless challenger evidence is strong enough to promote.
- Allocate roughly 80% of eligible high-value segments to champion/exploit policies and 20% to challenger/explore policies.
- Apply bias correction where a segment is repeatedly over- or under-forecasted.
- Apply spike dampening after one-month demand spikes that are not confirmed by a second month.
- Use shrinkage for sparse segments by borrowing from the parent grain.
- Forecast units and AOV separately when revenue misses appear to be driven by price/basket mix.
- Keep product-level forecasts diagnostic unless product history is sufficient.

## Candidate Forecast Methods

Use simple, inspectable methods before advanced modeling:

- Last-month actual
- Trailing 3-month average
- Weighted trailing 3-month average
- Trailing 6-month average when sufficient history exists
- Same-month-prior-year value when enough history exists
- Seasonal index by month when there is sufficient history
- Trend-adjusted trailing average
- Units times AOV forecast
- Parent-share model for sparse child segments
- Shrinkage forecast: segment history blended with parent-grain trend
- Spike-dampened forecast after a one-month jump or drop

If methods disagree materially, lower confidence and explain why.

## Method Selection Rules

Use this order:

1. For marketplace and high-volume categories, choose the method with lowest recent rolling WAPE after checking bias.
2. For customer states, choose the lowest-WAPE method unless it worsens bias materially.
3. For category-state segments, use shrinkage toward category or state parent unless the segment has stable history.
4. For sparse products, allocate from category forecast using recent product share instead of direct product forecasting.
5. If a segment was over-forecasted for two consecutive rounds, dampen recent-trend weight and lower confidence.
6. If a segment was under-forecasted for two consecutive rounds, increase recent-trend weight, unless the miss looks like a one-time spike.

## Champion and Challenger Rules

For each grain, maintain:

- `champion_method`: current default method from policy memory
- `challenger_method`: method being tested
- `policy_role`: `exploit` or `explore`

Promote a challenger only if it beats the champion for two consecutive rounds or improves weighted WAPE by at least 10% without materially worsening bias or directional accuracy.

Rollback a newly promoted method if it worsens category WAPE, marketplace bias, or high-GMV segment accuracy in the next round.

## Hierarchical Forecasting

Forecast from stable to noisy:

```text
marketplace -> category -> customer_state -> category_customer_state -> product
```

Use parent totals as guardrails. Child segment forecasts should reconcile directionally to parent demand unless there is clear evidence of share shift.

## Backtest Metrics

Report:

- Forecast revenue
- Actual revenue
- Forecast error
- Absolute error
- WAPE
- MAPE
- Forecast bias
- Confidence level

Definitions:

- `forecast_error`: actual minus forecast
- `absolute_error`: absolute value of forecast error
- `WAPE`: sum of absolute errors divided by sum of actuals
- `MAPE`: average absolute percentage error where actual is nonzero
- `bias`: sum of forecast errors divided by sum of actuals

## Required Outputs

When a `round_id` is provided, write outputs under `outputs/runs/<round_id>/`.

Create `monthly_forecasts.csv` with:

- `forecast_month`
- `grain`
- `key`
- `forecast_sales_revenue`
- `forecast_units`
- `method`
- `confidence`
- `confidence_notes`

Create `forecast_method_candidates.csv` with:

- `forecast_month`
- `grain`
- `key`
- `candidate_method`
- `candidate_forecast_sales_revenue`
- `candidate_forecast_units`
- `rolling_wape`
- `rolling_bias`
- `directional_accuracy`
- `selected`
- `selection_reason`
- `policy_role`
- `champion_or_challenger`

Create `forecast_method_leaderboard.csv` with:

- `forecast_month`
- `grain`
- `method`
- `segments_tested`
- `weighted_wape`
- `weighted_bias`
- `directional_accuracy`
- `recommended_use`
- `avoid_when`

Create `forecast_policy_experiments.csv` with:

- `forecast_month`
- `grain`
- `segment`
- `champion_method`
- `challenger_method`
- `policy_role`
- `allocation_reason`
- `promotion_criteria`
- `rollback_criteria`
- `next_measurement`

Create `forecast_backtest_results.csv` with:

- `backtest_month`
- `grain`
- `key`
- `actual_sales_revenue`
- `forecast_sales_revenue`
- `forecast_error`
- `absolute_error`
- `absolute_pct_error`
- `wape_group`
- `bias_group`
- `method`
- `confidence`
- `notes`

## Guardrails

- Exclude partial months from training and backtesting unless clearly labeled.
- Do not train on future data.
- Do not overstate product-level confidence when monthly sales are sparse.
- Label volatile segments and explain likely causes.
- Do not choose a lower-WAPE method if it creates persistent large bias without explanation.
- Do not let category-state or product volatility override marketplace/category signal.
- If prior learning says a method failed for a segment, either apply the change or explain why it was rejected.
- Do not promote a challenger without critic approval in the policy memory update.
- Do not explore on so many high-GMV segments that business recommendations become unstable.

## Handoff

Pass forecast and backtest outputs to:

- Product health agent
- Demand and seasonality agent
- Optimization agent
- Critic and QA agent

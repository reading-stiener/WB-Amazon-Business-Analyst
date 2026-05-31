---
name: olist-forecasting-agent
description: Forecast monthly Brazilian Olist sales and units using SKILL.md instructions only. Use when producing monthly forecasts, backtests, WAPE, MAPE, forecast bias, and confidence labels from monthly actuals.
---

# Olist Forecasting Agent

## Role

Forecast monthly sales and units, then compare forecasts with actuals. Do not write application code. Use transparent forecasting methods and explain confidence.

## Inputs

- `outputs/runs/<round_id>/monthly_sales_actuals.csv`

## Forecast Levels

Forecast these grains when sufficient history exists:

- Marketplace total
- Product category
- Customer state
- Category by customer state
- Top products

For long-tail products with sparse history, avoid high-confidence product-level forecasts. Roll them up into category or category-state forecasts.

## Baseline Forecast Methods

Use simple, inspectable methods before advanced modeling:

- Last-month actual
- Trailing 3-month average
- Weighted trailing 3-month average
- Same-month-prior-year value when enough history exists
- Seasonal index by month when there is sufficient history

If methods disagree materially, lower confidence and explain why.

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

## Handoff

Pass forecast and backtest outputs to:

- Product health agent
- Demand and seasonality agent
- Optimization agent
- Critic and QA agent

---
name: olist-demand-seasonality-agent
description: Explain Brazilian Olist demand trends and seasonality using SKILL.md instructions only. Use when separating true demand changes from month-of-year effects, category mix, geography, AOV, payment, and operational friction.
---

# Olist Demand and Seasonality Agent

## Role

Explain demand movement. Do not write application code. Separate true growth or decline from seasonality, category mix, geography, price/AOV, and operational friction.

## Inputs

- `outputs/runs/<round_id>/monthly_sales_actuals.csv`
- `outputs/runs/<round_id>/monthly_forecasts.csv`
- `outputs/runs/<round_id>/forecast_backtest_results.csv`
- Product and category health flags when available

## Analysis Dimensions

Review demand by:

- Month
- Category
- Customer state
- Seller state
- Category by customer state
- AOV
- Units sold
- Freight percentage
- Payment type and installments
- Delivery speed and late rate
- Review score

## Seasonality Treatment

The Olist dataset has limited full seasonal cycles. Always label seasonality confidence:

- High: repeated pattern across comparable months and stable category mix
- Medium: plausible pattern with some supporting history
- Low: limited history, sparse segment, or one-time event likely

## Required Output

When a `round_id` is provided, write to `outputs/runs/<round_id>/demand_seasonality_findings.md`.

Create `demand_seasonality_findings.md` with:

- Demand trend summary
- Category growth and decline drivers
- Geography growth and decline drivers
- Seasonal effects and confidence
- AOV versus units contribution
- Operational friction contribution
- Forecast miss explanation
- Segments requiring human review

## Explanation Template

For each major movement, state:

- Segment
- What changed
- Whether the change is likely demand, seasonality, mix, or operations
- Evidence
- Confidence
- Recommended next check

## Guardrails

- Do not infer inventory stockouts from this dataset alone.
- Do not call seasonality high confidence with only one observed annual cycle.
- Do not use payment value as item sales without explaining freight and other payment components.
- Do not ignore delivery and review changes when demand weakens.

## Handoff

Pass findings to:

- Optimization agent
- Critic and QA agent
- Executive summary agent

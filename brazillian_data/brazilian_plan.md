# Brazilian Olist Closed-Loop Optimization Plan

## Context

The Olist CSV dataset supports sales, demand, customer experience, and operational-efficiency analysis, but it does not contain true inventory, COGS, seller commission, ad spend, or actual fulfillment cost.

Because of that, this plan should optimize for profitable growth using measurable proxies:

- Delivered item revenue, excluding freight
- Units sold
- Average order value (AOV)
- Freight as a percentage of item revenue
- Late delivery rate
- Review score
- Cancellation and unavailable rate
- Same-state versus cross-state fulfillment
- Product/category sales trend and category-relative share

## Final Goal Set

1. Forecast monthly sales and units at marketplace, category, state, category-state, and top-product levels; validate with WAPE, MAPE, and forecast bias.
2. Create product and category health flags that identify deterioration after adjusting for seasonality and category trend.
3. Rank margin-improvement opportunities using freight burden, AOV, delivery lateness, review score, and regional fulfillment gaps.
4. Explain demand trends by separating true growth, seasonality, geography, category mix, and operational friction.

## Closed-Loop System

The system should run as a decision loop, not just a one-time analysis.

```text
data -> forecast -> detect issues -> diagnose causes -> recommend actions
     -> score expected impact -> execute/track -> compare actuals -> learn/update
```

Monthly cadence:

1. Ingest latest sales data.
2. Rebuild monthly feature tables.
3. Forecast the next 1-3 months.
4. Compare the previous forecast against actuals.
5. Flag product, category, and geography deterioration.
6. Generate commercial and operational recommendations.
7. Score recommended actions.
8. Human reviews and approves actions.
9. Track actual sales, margin proxies, and customer experience next month.
10. Update thresholds, model weights, and recommendation logic.

## Multi-Agent Design

### 1. Data and Feature Agent

Purpose: Build clean monthly analytical tables from the Olist CSVs.

Inputs:

- `olist_orders_dataset.csv`
- `olist_order_items_dataset.csv`
- `olist_products_dataset.csv`
- `product_category_name_translation.csv`
- `olist_customers_dataset.csv`
- `olist_sellers_dataset.csv`
- `olist_order_payments_dataset.csv`
- `olist_order_reviews_dataset.csv`

Outputs:

- Monthly sales by category, product, customer state, seller state, and category-state
- Monthly units sold
- Monthly AOV
- Monthly freight percentage
- Monthly late delivery rate
- Monthly review score
- Monthly cancellation and unavailable rate
- Same-state versus cross-state fulfillment metrics

Key rules:

- Treat delivered item revenue as primary sales.
- Exclude freight from sales revenue unless explicitly analyzing payment value.
- Keep freight as a separate margin-pressure metric.
- Keep canceled, unavailable, shipped, and processing orders for operational-leakage analysis.

### 2. Forecasting Agent

Purpose: Forecast monthly sales and units, then backtest against actuals.

Forecast levels:

- Total marketplace
- Category
- Customer state
- Category-state
- Top products

Outputs:

- Forecasted revenue
- Forecasted units
- Actual revenue
- Actual units
- WAPE
- MAPE
- Forecast bias
- Confidence level

Recommended approach:

- Use simple robust baselines first: trailing averages, seasonal naive, and weighted moving average.
- Use hierarchical forecasting where product-level data is sparse.
- Prefer category and category-state forecasts over long-tail product forecasts when product history is thin.

Guardrails:

- Do not overfit sparse SKUs.
- Mark forecasts with limited history as low confidence.
- Separate full months from partial months.

### 3. Product Health Agent

Purpose: Flag products and categories that are going bad.

Inputs:

- Monthly sales and units
- Category-relative share
- Review score trend
- Late delivery trend
- Freight percentage trend
- Cancellation and unavailable trend

Flag logic should not rely on sales decline alone. A product may decline because of normal seasonality or category-wide softness.

Example high-risk flag:

```text
High risk =
  revenue down more than 30% versus trailing 3-month average
  and category revenue is flat or up
  and at least one of:
    review score below 4.0
    late delivery rate above 10%
    freight percentage rising materially
    cancellation/unavailable rate rising
```

Outputs:

- Product health flags
- Category health flags
- Root-cause hints
- Severity level
- Recommended owner: merchandising, pricing, logistics, seller management, or customer experience

### 4. Demand and Seasonality Agent

Purpose: Separate true demand movement from seasonality and mix effects.

Factors to analyze:

- Month of year
- Category
- Customer state
- Seller state
- Price and AOV
- Freight burden
- Payment installments
- Delivery speed
- Review score
- Order status

Outputs:

- Trend direction
- Seasonal lift or drop
- Category mix changes
- Geography shifts
- Price/AOV contribution
- Operational-friction contribution
- Confidence level

Important limitation:

The dataset has limited full seasonal cycles, so seasonality estimates should be labeled as low, medium, or high confidence.

### 5. Operational Efficiency Agent

Purpose: Identify margin-proxy leakage and operational fixes.

Primary metrics:

- Freight value divided by item revenue
- AOV
- Late delivery rate
- Review score
- Same-state fulfillment rate
- Cross-state fulfillment penalty
- Cancellation and unavailable rate

Opportunity types:

- High-GMV categories with high freight burden
- High-GMV states with low same-state seller coverage
- Low-AOV categories with high freight burden
- Categories with worsening review score
- Category-state pairs with high lateness and high sales
- Sellers or states creating avoidable fulfillment drag

Outputs:

- Ranked operational-efficiency opportunities
- Affected GMV
- Estimated margin-proxy impact
- Customer-experience risk
- Recommended fix

### 6. Optimization and Experiment Agent

Purpose: Convert analysis into testable business actions.

Example actions:

- Increase promotions for high-growth, lower-freight categories.
- Reduce or pause promotions in high-freight, low-review categories until operational fixes land.
- Add free-shipping thresholds for low-AOV categories.
- Create product bundles in categories with high multi-item potential.
- Recruit or prioritize local sellers in RJ, MG, South, BA, PE, and CE.
- Localize top SKUs to reduce cross-state shipping.
- Tighten delivery promises on weak cross-state lanes.

Each action should be scored by:

```text
expected sales lift
expected margin-proxy lift
confidence
execution difficulty
risk
time to impact
next measurement metric
```

Recommended action contract:

```json
{
  "action": "Add free-shipping threshold to selected low-AOV housewares baskets",
  "target": "housewares, selected states",
  "expected_sales_impact": "medium",
  "expected_margin_proxy_impact": "high",
  "evidence": [
    "housewares has high recent growth",
    "freight burden is above 20%",
    "low-AOV orders carry disproportionate freight burden"
  ],
  "confidence": "medium",
  "risk": "threshold may reduce conversion on very low basket orders",
  "next_measurement": "AOV, freight percentage, conversion proxy, monthly revenue"
}
```

### 7. Critic and QA Agent

Purpose: Challenge unsupported conclusions before recommendations reach decision makers.

Checks:

- Is the recommendation supported by structured metrics?
- Is the analysis confusing sales decline with seasonality?
- Is the product history too sparse for a product-level conclusion?
- Is there leakage from test data into forecast training?
- Is profit being overclaimed despite missing COGS?
- Are partial months excluded or labeled?
- Are forecast errors reported clearly?
- Are action risks and confidence levels explicit?

Outputs:

- QA findings
- Blockers
- Recommendation revisions
- Confidence downgrades

### 8. Executive Summary Agent

Purpose: Convert the analysis into a concise business decision memo.

Output format:

- What changed
- Why it matters
- Recommended actions
- Expected sales impact
- Expected margin-proxy impact
- Confidence
- Risks
- Next measurement checkpoint

## Closed-Loop Objective Function

Because true profit is unavailable, use a proxy objective:

```text
closed_loop_score =
  expected_sales_lift
+ expected_margin_proxy_lift
- operational_risk
- confidence_penalty
```

Margin-proxy lift should come from:

- Lower freight percentage
- Higher AOV
- Lower late delivery rate
- Better review score
- Lower cancellation and unavailable rate
- More same-state fulfillment

## Core Output Tables

Minimum useful artifacts:

```text
monthly_sales_actuals.csv
monthly_forecasts.csv
forecast_backtest_results.csv
product_health_flags.csv
category_health_flags.csv
ops_efficiency_opportunities.csv
recommended_actions.csv
closed_loop_scorecard.csv
executive_summary.md
```

## Recommended Metrics

### Sales Metrics

- Delivered item revenue
- Units sold
- Number of orders
- AOV
- Revenue growth month over month
- Revenue growth versus trailing 3-month average
- Category share
- Product share within category

### Forecast Metrics

- Actual revenue
- Forecast revenue
- Forecast error
- WAPE
- MAPE
- Bias
- Confidence level

### Product Health Metrics

- Revenue trend
- Unit trend
- Category-relative share trend
- Review score trend
- Freight percentage trend
- Late delivery trend
- Cancellation/unavailable trend

### Operational Efficiency Metrics

- Freight percentage
- Same-state fulfillment rate
- Cross-state fulfillment rate
- Delivery days
- Late delivery rate
- Low-AOV order share
- Multi-item order share

## Initial Business Hypotheses From The Dataset

These are starting hypotheses to validate in the closed loop:

1. Shift growth investment toward categories with stronger margin proxies:
   - Health/beauty
   - Perfumery
   - Watches/gifts
   - Selected pet shop and housewares opportunities after freight review

2. Fix operational drag before scaling traffic in categories with high freight or poor reviews:
   - Furniture/decor
   - Housewares
   - Telephony
   - Office furniture
   - Bed/bath/table

3. Regionalize supply outside SP:
   - RJ is the highest-priority state because it has high sales, low same-state supply, high late rate, and weak review score.
   - BA, PE, CE, and other Northeast states have high freight and late-delivery pressure.

4. Raise AOV:
   - Use free-shipping thresholds.
   - Add bundles.
   - Promote multi-item baskets.
   - Use installment-led upsell for higher-ticket categories.

## Implementation Notes

Use deterministic scripts for calculations and agents for reasoning.

Python should own:

- CSV loading and joins
- Monthly aggregation
- Forecasting
- Backtesting
- Scoring
- Table generation

Agents should own:

- Diagnosis
- Business interpretation
- Recommendation generation
- Critique
- Executive summarization

Do not let agents invent metrics. Agents should consume structured tables and produce decisions grounded in those tables.

## Suggested Repository Structure

```text
brazilian_olist_optimizer/
  data/
    raw/
    processed/
  scripts/
    build_monthly_features.py
    forecast_monthly_sales.py
    backtest_forecasts.py
    flag_product_health.py
    rank_ops_opportunities.py
    score_recommended_actions.py
  agents/
    data_feature_agent.md
    forecasting_agent.md
    product_health_agent.md
    demand_seasonality_agent.md
    ops_efficiency_agent.md
    optimization_agent.md
    critic_qa_agent.md
    executive_summary_agent.md
  outputs/
    monthly_sales_actuals.csv
    monthly_forecasts.csv
    forecast_backtest_results.csv
    product_health_flags.csv
    category_health_flags.csv
    ops_efficiency_opportunities.csv
    recommended_actions.csv
    closed_loop_scorecard.csv
    executive_summary.md
```

## Next Build Step

Build the first deterministic baseline:

1. Join orders, items, products, customers, sellers, payments, and reviews.
2. Create monthly actuals at total, category, state, category-state, and product levels.
3. Generate trailing-average and seasonal-naive forecasts.
4. Backtest against actuals.
5. Produce the first product-health and operational-efficiency flags.
6. Feed those tables into the critic and executive-summary agents.

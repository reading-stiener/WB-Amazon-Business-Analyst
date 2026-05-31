---
name: olist-data-feature-agent
description: Build the monthly analytical feature layer for Brazilian Olist optimization using SKILL.md instructions only. Use when converting Olist CSVs into monthly actuals, sales, AOV, freight, delivery, review, cancellation, and fulfillment metrics for downstream agents.
---

# Olist Data Feature Agent

## Role

Create the shared monthly feature layer used by all other agents. Do not write application code. Produce clear table definitions and structured CSV outputs from the available Olist CSVs.

## Primary Inputs

- Orders: status and timestamps
- Order items: product, seller, price, freight, item count
- Products: category and listing metadata
- Category translation: Portuguese to English category names
- Customers: customer state and city
- Sellers: seller state and city
- Payments: payment type and installments
- Reviews: review score

## Metric Definitions

- `sales_revenue`: delivered item price revenue, excluding freight
- `units_sold`: delivered order-item count
- `orders`: distinct delivered orders
- `aov`: `sales_revenue / orders`
- `freight_pct`: `freight_value / sales_revenue`
- `late_delivery_rate`: delivered orders where customer delivery date is after estimated delivery date
- `delivery_days`: days from purchase timestamp to delivered customer timestamp
- `same_state_fulfillment_rate`: item share where seller state equals customer state
- `cancellation_rate`: canceled orders divided by all orders
- `unavailable_rate`: unavailable orders divided by all orders
- `review_score`: average review score by order or item segment

## Required Grain

Produce monthly actuals at these levels:

- Marketplace total
- Product category
- Product
- Customer state
- Seller state
- Category by customer state
- Category by seller state

Use full months only when forecasting or backtesting. Label partial months explicitly if included for operational monitoring.

## Required Output

When a `round_id` is provided, write to `outputs/runs/<round_id>/monthly_sales_actuals.csv`. For ad hoc non-round work, `outputs/monthly_sales_actuals.csv` is acceptable.

Create `monthly_sales_actuals.csv` with columns:

- `month`
- `grain`
- `key`
- `sales_revenue`
- `units_sold`
- `orders`
- `aov`
- `freight_value`
- `freight_pct`
- `avg_review_score`
- `late_delivery_rate`
- `avg_delivery_days`
- `same_state_fulfillment_rate`
- `cancellation_rate`
- `unavailable_rate`
- `payment_credit_card_share`
- `payment_boleto_share`
- `avg_installments`
- `confidence_notes`

## Quality Checks

- Delivered revenue should exclude freight.
- Freight should remain separate as a margin-pressure metric.
- Distinguish item-level and order-level metrics before averaging.
- Avoid double-counting orders with multiple items.
- Preserve categories with missing translations as `unknown` or their original category name.
- Confirm date range and partial-month treatment.

## Handoff

Pass the round-scoped `monthly_sales_actuals.csv` to:

- Forecasting agent
- Product health agent
- Demand and seasonality agent
- Operational efficiency agent

---
name: olist-closed-loop-orchestrator
description: Coordinate the Brazilian Olist multi-agent closed-loop optimization using only SKILL.md-based agents. Use when the task is to run or plan monthly optimization rounds across forecasting, product health, demand seasonality, operational efficiency, recommendation scoring, critique, round scorecards, learning handoffs, next-round prompts, dashboards, and executive summary.
---

# Olist Closed-Loop Orchestrator

## Role

Coordinate the Olist optimization workflow from raw CSVs to final business actions. Do not write application code. Use the agent SKILL.md files as the implementation units and require structured handoffs between agents.

## Source Data

Use CSV files in the current `brazilian_data` directory:

- `olist_orders_dataset.csv`
- `olist_order_items_dataset.csv`
- `olist_products_dataset.csv`
- `product_category_name_translation.csv`
- `olist_customers_dataset.csv`
- `olist_sellers_dataset.csv`
- `olist_order_payments_dataset.csv`
- `olist_order_reviews_dataset.csv`

Do not assume true inventory, COGS, ad spend, seller commission, or actual fulfillment cost exists in this dataset.

## Agent Order

Run agents in this order:

1. `olist-data-feature-agent`
2. `olist-forecasting-agent`
3. `olist-product-health-agent`
4. `olist-demand-seasonality-agent`
5. `olist-ops-efficiency-agent`
6. `olist-optimization-agent`
7. `olist-critic-qa-agent`
8. `olist-executive-summary-agent`
9. `olist-round-scorecard-agent`
10. `olist-learning-handoff-agent`
11. `olist-next-round-prompt-agent`
12. `olist-round-dashboard-agent`

Agents 3, 4, and 5 may work in parallel after the forecasting agent has produced actuals and backtest outputs.

## Closed Loop

Use this loop every month:

1. Rebuild monthly actuals.
2. Forecast next 1-3 months.
3. Compare prior forecast against actuals.
4. Flag product, category, and geography deterioration.
5. Diagnose seasonality, trend, and operational causes.
6. Rank margin-proxy and sales-growth opportunities.
7. Score recommended actions.
8. Critique recommendations for unsupported claims.
9. Produce executive summary.
10. Score the round against the previous round.
11. Produce a learning handoff that the next round must apply.
12. Generate the next-round prompt.
13. Update the dashboard across all completed rounds.

The required pattern is:

```text
round output -> round_scorecard.csv -> learning_handoff.md -> next_round_prompt.md -> next round
```

## Required Output Folder

Use or create an `outputs/` folder in the dataset directory. Each round must write under `outputs/runs/<round_id>/`. Expected per-round artifacts:

- `monthly_sales_actuals.csv`
- `monthly_forecasts.csv`
- `forecast_backtest_results.csv`
- `product_health_flags.csv`
- `category_health_flags.csv`
- `demand_seasonality_findings.md`
- `ops_efficiency_opportunities.csv`
- `recommended_actions.csv`
- `critic_qa_findings.md`
- `closed_loop_scorecard.csv`
- `executive_summary.md`
- `round_scorecard.csv`
- `learning_handoff.md`
- `next_round_prompt.md`

Expected cross-round artifacts:

- `outputs/round_scorecard_history.csv`
- `outputs/round_dashboard_data.csv`
- `outputs/round_dashboard.md`

## Objective Function

Optimize for profitable growth using proxy metrics:

```text
closed_loop_score =
  expected_sales_lift
+ expected_margin_proxy_lift
- operational_risk
- confidence_penalty
```

Margin-proxy lift can come from:

- Lower freight percentage
- Higher AOV
- Lower late delivery rate
- Higher review score
- Lower cancellation or unavailable rate
- Higher same-state fulfillment rate

## Round Score

Use the round score to decide whether the current round moved closer to the goal than the last round:

```text
round_score =
  35 forecast_accuracy_score
+ 25 margin_proxy_score
+ 20 sales_growth_score
+ 10 recommendation_quality_score
+ 10 learning_quality_score
```

Set `closer_to_goal` from the scorecard:

- `yes` if current score improves versus prior round
- `no` if current score declines versus prior round
- `mixed` if total score improves but a critical metric worsens materially
- `baseline` if no prior round exists

## Decision Rules

- Prioritize actions that improve both sales and margin proxy.
- Do not recommend scaling paid growth into high-freight, low-review, or late-delivery pockets unless an operational fix is part of the action.
- Mark sparse product-level forecasts as low confidence.
- Separate actual seasonality from product deterioration.
- Always include the next metric to check in the next monthly loop.
- Read the previous round's `learning_handoff.md` before forecasting or recommending actions.
- If a prior learning is not applied, explain why in `critic_qa_findings.md` and the new `learning_handoff.md`.
- Update `outputs/round_dashboard.md` after every completed round.

## Final Handoff Contract

Every recommended action must include:

- Action
- Target category/product/state/seller segment
- Expected sales impact
- Expected margin-proxy impact
- Evidence
- Confidence
- Risk
- Owner
- Next measurement

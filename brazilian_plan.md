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
5. Score each monthly round against the prior round and carry forward a learning handoff into the next-round prompt.

## Closed-Loop System

The system should run as a decision loop, not just a one-time analysis.

```text
data -> forecast -> detect issues -> diagnose causes -> recommend actions
     -> score expected impact -> execute/track -> compare actuals -> learn/update
```

Each round must follow this explicit handoff pattern:

```text
round output -> round_scorecard.csv -> learning_handoff.md -> policy_memory.md -> next_round_prompt.md -> next round
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
10. Score the round against the prior round.
11. Write a learning handoff with explicit next-round rule updates.
12. Update persistent policy memory with critic-gated promotions, carry-forwards, and rollbacks.
13. Generate the next-round prompt.
14. Update the cross-round dashboard.

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
- Forecast method candidates by grain and segment
- Forecast method leaderboard by grain
- Forecast policy experiments with champion/challenger and explore/exploit decisions
- Actual revenue
- Actual units
- WAPE
- MAPE
- Forecast bias
- Directional accuracy
- Confidence level

Recommended approach:

- Read `outputs/policy_memory.md` and the prior `learning_handoff.md` before choosing methods.
- Compare multiple simple baselines each round: last-month, trailing averages, weighted trailing average, trailing 6-month average when possible, trend-adjusted average, units times AOV, parent-share, shrinkage, and spike-dampened forecasts.
- Choose method per grain and per segment using rolling WAPE, bias, directional accuracy, and the previous learning handoff.
- Use 80/20 explore/exploit intent: champion methods for most high-GMV segments and challenger methods for controlled tests.
- Use hierarchical forecasting where product-level data is sparse.
- Prefer category and category-state forecasts over long-tail product forecasts when product history is thin.
- Use shrinkage for sparse category-state/product forecasts and bias correction for repeatedly missed segments.

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
- Were active policy-memory rules applied, rejected with evidence, promoted with critic approval, or rolled back when they worsened WAPE, bias, or margin proxy?

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

### 9. Round Scorecard Agent

Purpose: Score whether the current round moved closer to the profitable-growth goal than the previous round.

Score formula:

```text
round_score =
  40 outcome_score
+ 40 forecast_policy_score
+ 20 learning_score
```

Historical rounds may use the legacy 35/25/20/10/10 or V2 50/30/20 scorecards. New rounds should use the V3 scorecard above and preserve legacy columns when useful for dashboard continuity.

Outputs:

- `round_scorecard.csv`
- updated `round_scorecard_history.csv`

### 10. Learning Handoff Agent

Purpose: Convert each round's misses, wins, risks, and QA findings into explicit rules for the next round.

Output:

- `learning_handoff.md`

The next round must apply each relevant prior learning or explicitly explain why it rejected the learning.

### 11. Policy Memory Agent

Purpose: Maintain persistent policy memory so the framework improves decision policy across rounds through active rules, champion/challenger methods, explore/exploit allocation, critic-gated promotions, and rollbacks.

Outputs:

- `policy_memory.md`
- `policy_change_log.csv`

The next round must read policy memory before forecasting or recommending actions.

### 12. Next-Round Prompt Agent

Purpose: Generate the exact prompt for the next optimization round, including training cutoff, forecast month, prior learning handoff path, score formula, required outputs, and comparison requirements.

Output:

- `next_round_prompt.md`

### 13. Round Dashboard Agent

Purpose: Generate a cross-round dashboard showing score trend, forecast accuracy, margin proxy, sales growth, policy quality, learning quality, top actions, applied learnings, active policy memory, and open risks.

Outputs:

- `round_dashboard.md`
- `round_dashboard_data.csv`

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
outputs/runs/<round_id>/monthly_sales_actuals.csv
outputs/runs/<round_id>/monthly_forecasts.csv
outputs/runs/<round_id>/forecast_method_candidates.csv
outputs/runs/<round_id>/forecast_method_leaderboard.csv
outputs/runs/<round_id>/forecast_policy_experiments.csv
outputs/runs/<round_id>/forecast_backtest_results.csv
outputs/runs/<round_id>/product_health_flags.csv
outputs/runs/<round_id>/category_health_flags.csv
outputs/runs/<round_id>/demand_seasonality_findings.md
outputs/runs/<round_id>/ops_efficiency_opportunities.csv
outputs/runs/<round_id>/recommended_actions.csv
outputs/runs/<round_id>/closed_loop_scorecard.csv
outputs/runs/<round_id>/critic_qa_findings.md
outputs/runs/<round_id>/executive_summary.md
outputs/runs/<round_id>/round_scorecard.csv
outputs/runs/<round_id>/learning_handoff.md
outputs/runs/<round_id>/next_round_prompt.md
outputs/round_scorecard_history.csv
outputs/policy_memory.md
outputs/policy_change_log.csv
outputs/round_dashboard_data.csv
outputs/round_dashboard.md
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

Use a SKILL.md-based multi-agent implementation. Each agent is represented by a folder under `agents/` with its own `SKILL.md`. Do not implement Python scripts for this workflow.

The agent skills should own:

- Diagnosis
- Business interpretation
- Metric definitions and table contracts
- Forecasting method selection
- Product/category health rules
- Operational opportunity ranking
- Recommendation generation
- Critique
- Executive summarization

Do not let agents invent metrics. Agents should consume structured table outputs and produce decisions grounded in those tables.

## Suggested Repository Structure

```text
brazilian_data/
  brazilian_plan.md
  olist_orders_dataset.csv
  olist_order_items_dataset.csv
  olist_products_dataset.csv
  product_category_name_translation.csv
  olist_customers_dataset.csv
  olist_sellers_dataset.csv
  olist_order_payments_dataset.csv
  olist_order_reviews_dataset.csv
  agents/
    olist-closed-loop-orchestrator/
      SKILL.md
    olist-data-feature-agent/
      SKILL.md
    olist-forecasting-agent/
      SKILL.md
    olist-product-health-agent/
      SKILL.md
    olist-demand-seasonality-agent/
      SKILL.md
    olist-ops-efficiency-agent/
      SKILL.md
    olist-optimization-agent/
      SKILL.md
    olist-critic-qa-agent/
      SKILL.md
    olist-executive-summary-agent/
      SKILL.md
    olist-round-scorecard-agent/
      SKILL.md
    olist-learning-handoff-agent/
      SKILL.md
    olist-policy-memory-agent/
      SKILL.md
    olist-next-round-prompt-agent/
      SKILL.md
    olist-round-dashboard-agent/
      SKILL.md
  outputs/
    runs/
      <round_id>/
        monthly_sales_actuals.csv
        monthly_forecasts.csv
        forecast_method_candidates.csv
        forecast_method_leaderboard.csv
        forecast_policy_experiments.csv
        forecast_backtest_results.csv
        product_health_flags.csv
        category_health_flags.csv
        demand_seasonality_findings.md
        ops_efficiency_opportunities.csv
        recommended_actions.csv
        closed_loop_scorecard.csv
        critic_qa_findings.md
        executive_summary.md
        round_scorecard.csv
        learning_handoff.md
        next_round_prompt.md
    round_scorecard_history.csv
    policy_memory.md
    policy_change_log.csv
    round_dashboard_data.csv
    round_dashboard.md
```

## Next Build Step

Run the first SKILL.md-based closed-loop baseline:

1. Use `agents/olist-closed-loop-orchestrator/SKILL.md` to coordinate the workflow.
2. Use `agents/olist-data-feature-agent/SKILL.md` to define and produce the monthly actuals table.
3. Use `agents/olist-forecasting-agent/SKILL.md` to produce forecasts and backtest results.
4. Use product health, demand seasonality, and operational efficiency agent skills to diagnose issues.
5. Use `agents/olist-optimization-agent/SKILL.md` to score recommended actions.
6. Use `agents/olist-critic-qa-agent/SKILL.md` to challenge the outputs.
7. Use `agents/olist-executive-summary-agent/SKILL.md` to produce the final business memo.
8. Use `agents/olist-round-scorecard-agent/SKILL.md` to score the round against the prior round.
9. Use `agents/olist-learning-handoff-agent/SKILL.md` to capture what should change next round.
10. Use `agents/olist-policy-memory-agent/SKILL.md` to update persistent policy memory from the scorecard, learning handoff, forecast leaderboard, and critic gate.
11. Use `agents/olist-next-round-prompt-agent/SKILL.md` to generate the next executable prompt.
12. Use `agents/olist-round-dashboard-agent/SKILL.md` to update the dashboard across all completed rounds.

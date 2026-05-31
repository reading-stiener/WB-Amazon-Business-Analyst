# Brazilian Olist Multi-Agent Optimization

This project uses the Brazilian Olist CSV dataset to run a SKILL.md-based multi-agent business analysis loop for profitable sales growth.

The system is designed like a senior Amazon e-commerce business analyst workflow: forecast demand, compare forecast against actuals, find product/category deterioration, diagnose operational friction, recommend actions, score the round, capture learnings, and improve the next round.

## Business Goal

Increase sales while improving profit-margin proxies.

True profit is not available in the Olist dataset because there is no COGS, ad spend, seller commission, inventory, or actual fulfillment cost. The framework therefore optimizes measurable margin proxies:

- Delivered item revenue, excluding freight
- Units sold
- Average order value, or AOV
- Freight as a percentage of item revenue
- Late delivery rate
- Review score
- Cancellation and unavailable rate
- Same-state fulfillment rate

The practical goal is not "grow revenue at any cost." The goal is profitable growth: scale demand only where freight burden, delivery quality, basket size, and customer experience can support it.

## Strategy

The strategy has four layers.

1. Forecast demand by grain

Forecast monthly sales and units at these grains:

- Marketplace
- Product category
- Customer state
- Category by customer state
- Top products, diagnostic only when sparse

Forecast accuracy is measured with WAPE, bias, and directional accuracy. Product-level forecasts are treated carefully because many SKUs are sparse and volatile.

2. Separate demand change from operational friction

A product or category is not flagged as bad just because sales declined. The agents compare sales movement against:

- Category trend
- Recent trailing average
- Forecast error
- Freight percentage
- Late delivery
- Review score
- Cancellation and unavailable rate

This helps separate true demand weakness from seasonality, mix shift, fulfillment drag, or noisy product-level history.

3. Prioritize margin-proxy actions

Recommended actions favor segments that can improve both sales and margin proxy:

- Shift growth toward lower-friction, higher-confidence categories.
- Avoid broad promotions in high-freight or late-delivery pockets.
- Raise AOV through bundles and free-shipping thresholds.
- Regionalize seller supply for high-GMV cross-state demand.
- Tighten delivery promises where late delivery hurts reviews.

4. Close the loop every round

Each round must produce structured artifacts, score itself, and generate the prompt for the next round.

```text
round output -> round_scorecard.csv -> learning_handoff.md -> policy_memory.md -> next_round_prompt.md -> next round
```

## Multi-Agent Architecture

Each agent is defined by a local `SKILL.md` file under `agents/`. No Python implementation is required for the agent contracts.

| Agent | Purpose |
| --- | --- |
| `olist-closed-loop-orchestrator` | Coordinates the full monthly workflow and handoffs. |
| `olist-data-feature-agent` | Defines monthly sales, AOV, freight, delivery, review, and fulfillment metrics. |
| `olist-forecasting-agent` | Compares forecast methods, produces forecasts, and backtests WAPE/bias. |
| `olist-product-health-agent` | Flags deteriorating products and categories. |
| `olist-demand-seasonality-agent` | Separates trend, seasonality, geography, mix, and operational friction. |
| `olist-ops-efficiency-agent` | Finds margin-proxy leakage and operational opportunities. |
| `olist-optimization-agent` | Converts findings into ranked, measurable business actions. |
| `olist-critic-qa-agent` | Challenges unsupported claims, leakage, overfit, and profit overclaims. |
| `olist-executive-summary-agent` | Writes the business decision memo. |
| `olist-round-scorecard-agent` | Scores whether the round moved closer to the goal. |
| `olist-learning-handoff-agent` | Converts misses and wins into next-round rules. |
| `olist-policy-memory-agent` | Maintains persistent policy memory, promotions, rollbacks, and active experiments. |
| `olist-next-round-prompt-agent` | Writes the executable prompt for the next round. |
| `olist-round-dashboard-agent` | Builds the cross-round dashboard and score history. |

## How The System Self-Improves

The system improves through explicit memory and scoring, not by silently changing prompts.

### 1. Each Round Produces Evidence

Every run writes structured outputs under:

```text
outputs/runs/<round_id>/
```

Key evidence files include:

- `monthly_sales_actuals.csv`
- `monthly_forecasts.csv`
- `forecast_method_candidates.csv`
- `forecast_method_leaderboard.csv`
- `forecast_policy_experiments.csv`
- `forecast_backtest_results.csv`
- `recommended_actions.csv`
- `critic_qa_findings.md`
- `round_scorecard.csv`
- `learning_handoff.md`
- `next_round_prompt.md`

### 2. The Scorecard Separates Business Outcome From Policy Quality

New rounds use the V3 scorecard:

```text
round_score =
  40 outcome_score
+ 40 forecast_policy_score
+ 20 learning_score
```

This matters because the agent cannot control the market. A month can have worse sales or delivery performance while the forecasting and decision policy still improves.

- `outcome_score`: actual sales, margin proxy, and customer experience movement.
- `forecast_policy_score`: WAPE, bias, directional accuracy, and policy discipline.
- `learning_score`: whether the round applied prior learning, updated rules, used policy memory, and avoided unsupported claims.

### 3. The Learning Handoff Converts Results Into Rules

`learning_handoff.md` records what worked, what failed, and what must change next round.

Examples:

- If a category is repeatedly over-forecasted, dampen recent-trend weight.
- If category-state forecasts are volatile, shrink them toward parent category or state.
- If revenue misses are caused by AOV movement, forecast units and AOV separately.
- If sales improves but freight or late delivery worsens, mark the round as mixed.

### 4. Policy Memory Makes Learnings Persistent

`outputs/policy_memory.md` is the long-lived memory layer. It stores:

- Active global rules
- Forecast policy by grain
- Champion and challenger methods
- Explore/exploit allocation
- Promotion rules
- Rollback rules
- Business guardrails
- Active experiments
- Retired policies
- Open risks

This prevents the system from forgetting prior failures or repeatedly rediscovering the same lesson.

### 5. Champion/Challenger Keeps Forecasting Adaptive

Forecasting uses champion and challenger policies:

- Champion: current default method for a grain or segment.
- Challenger: controlled alternative method being tested.

The current policy uses:

- 80% exploit: use critic-approved champions on high-confidence/high-GMV segments.
- 20% explore: test challengers on high-error segments.

A challenger is promoted only when it improves WAPE materially without worsening bias or directional accuracy, and the critic agent approves it.

### 6. Critic-Gated Promotion Prevents Overfit

The critic agent blocks or downgrades:

- One-month overfit
- Sparse product-level conclusions
- Sales-only recommendations
- True profit claims without COGS
- Challenger promotion without enough evidence
- Ignoring rollback rules

This is why the system can pursue higher scores without simply gaming the forecast.

### 7. Rollbacks Protect The Business Goal

Policy changes are rolled back when they worsen:

- Category WAPE
- Marketplace bias
- High-GMV segment accuracy
- Freight percentage
- Late delivery
- Same-state fulfillment

The system is not considered better just because the score rises. If sales improves but margin proxy deteriorates, the scorecard can mark the round `mixed`.

## Latest Four-Round Result

The latest exercise ran four iterative policy-improvement rounds against the 2018-08 holdout month.

The Olist data has complete delivered actuals through 2018-08. The 2018-09 and 2018-10 records are partial/non-delivered and are not treated as full monthly actuals.

| Round | Score | Delta | Category WAPE | Marketplace WAPE | Result |
| --- | ---: | ---: | ---: | ---: | --- |
| `2018-08-r1` | 72.34 | +1.38 | 0.175101 | 0.008530 | improved, mixed business outcome |
| `2018-08-r2` | 75.09 | +2.75 | 0.175790 | 0.000000 | improved, mixed business outcome |
| `2018-08-r3` | 82.32 | +7.23 | 0.123519 | 0.000000 | improved, mixed business outcome |
| `2018-08-r4` | 83.56 | +1.24 | 0.121199 | 0.000000 | improved, mixed business outcome |

All four scores improved consecutively. The final status is still `mixed` because August revenue, AOV, review score, and late delivery did not all improve.

## Current Active Policy

The latest policy memory promotes or carries forward:

- Marketplace: bias-calibrated `trend_adjusted_avg`
- Category: critic-gated challenger override on high-error segments
- Customer state: critic-gated challenger override on high-error states
- Category-state: critic-gated challenger override with rollback
- Product: diagnostic only

The next complete-month run should require a score above `83.56` and should roll back any challenger that worsens WAPE, bias, freight percentage, late delivery, or same-state fulfillment.

## Output Map

| File | Purpose |
| --- | --- |
| `brazilian_plan.md` | Main design and business plan. |
| `agents/*/SKILL.md` | Agent contracts and workflow rules. |
| `outputs/round_dashboard.md` | Cross-round executive dashboard. |
| `outputs/round_dashboard_data.csv` | Dashboard data table. |
| `outputs/round_scorecard_history.csv` | Score history across rounds. |
| `outputs/policy_memory.md` | Persistent policy memory. |
| `outputs/policy_change_log.csv` | Policy changes, promotions, rollbacks, and carry-forwards. |
| `outputs/runs/<round_id>/` | Per-round artifacts. |

## How To Run The Next Round

Use the orchestrator skill:

```text
Use agents/olist-closed-loop-orchestrator/SKILL.md.
```

For the next run, start from:

```text
outputs/runs/2018-08-r4/next_round_prompt.md
```

Only run the next calendar month when a new complete delivered month is available. If no new full month exists, run controlled policy experiments against a holdout and label them as offline optimization rounds.

## Guardrails

- Do not claim true profit improvement from this dataset.
- Do not optimize revenue alone.
- Do not treat freight as sales revenue.
- Do not train on future data.
- Do not score partial months as full monthly actuals.
- Do not promote sparse product-level wins into marketplace policy.
- Do not skip the critic gate before promotion or rollback.

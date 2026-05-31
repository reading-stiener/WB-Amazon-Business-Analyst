---
name: olist-critic-qa-agent
description: Critique Brazilian Olist closed-loop optimization outputs using SKILL.md instructions only. Use when checking forecasts, health flags, operational opportunities, and recommendations for unsupported claims, data leakage, sparse data, seasonality confusion, and overclaimed profit.
---

# Olist Critic and QA Agent

## Role

Challenge the analysis before it reaches decision makers. Do not write application code. Focus on errors, unsupported claims, overconfidence, and missing caveats.

## Inputs

- `outputs/runs/<round_id>/monthly_sales_actuals.csv`
- `outputs/runs/<round_id>/monthly_forecasts.csv`
- `outputs/runs/<round_id>/forecast_backtest_results.csv`
- `outputs/runs/<round_id>/product_health_flags.csv`
- `outputs/runs/<round_id>/category_health_flags.csv`
- `outputs/runs/<round_id>/demand_seasonality_findings.md`
- `outputs/runs/<round_id>/ops_efficiency_opportunities.csv`
- `outputs/runs/<round_id>/recommended_actions.csv`
- `outputs/runs/<round_id>/closed_loop_scorecard.csv`
- `outputs/runs/<round_id>/forecast_method_candidates.csv`
- `outputs/runs/<round_id>/forecast_method_leaderboard.csv`
- `outputs/runs/<round_id>/forecast_policy_experiments.csv`
- `outputs/policy_memory.md`

## QA Checks

Check for:

- True profit claims despite missing COGS
- Freight treated as revenue instead of margin pressure
- Orders double-counted across multi-item orders
- Partial months mixed with full months
- Product-level forecasts with sparse data marked high confidence
- Seasonality confused with deterioration
- Category-wide decline misread as product-specific failure
- Recommendations unsupported by metrics
- Free-shipping actions without AOV or margin-proxy guardrails
- Forecast backtest missing WAPE, MAPE, or bias
- Missing next measurement for a recommended action
- Policy changes that overfit to one round
- Challenger promotion without enough evidence
- Rollback not triggered when a policy worsened WAPE, bias, or margin proxy
- Explore allocation too large for high-GMV segments
- Active policy memory ignored without explanation

## Required Output

When a `round_id` is provided, write to `outputs/runs/<round_id>/critic_qa_findings.md`.

Create `critic_qa_findings.md` with:

- Blocking issues
- Non-blocking concerns
- Confidence downgrades
- Recommendations to revise
- Claims that need caveats
- Policy gate decisions
- Final approval status

Use this approval status:

- `approved`
- `approved_with_caveats`
- `needs_revision`

## Severity

Use:

- P0: invalidates recommendation or creates misleading executive conclusion
- P1: material risk or missing caveat
- P2: clarity issue or minor analytical weakness

## Guardrails

- Be skeptical but practical.
- Do not block because true profit is unavailable; require the recommendation to say margin proxy.
- Do not require perfect forecasting for sparse segments; require correct confidence labels.
- Prefer specific revision text over vague criticism.
- Approve, reject, or modify every proposed policy promotion or rollback.
- Do not approve a challenger promotion based only on sparse product or category-state wins.
- Require rollback when a policy materially worsens category WAPE or marketplace bias unless there is a documented business reason to continue testing.

## Handoff

Pass QA findings to:

- Optimization agent for revisions if needed
- Executive summary agent for caveats

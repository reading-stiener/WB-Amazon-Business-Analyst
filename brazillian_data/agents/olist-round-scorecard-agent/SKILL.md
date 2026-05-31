---
name: olist-round-scorecard-agent
description: Evaluate each Brazilian Olist optimization round against the prior round using a goal-progress and policy-improvement scorecard. Use when scoring business outcome, forecast policy quality, learning execution, and whether the run moved closer to the profitable-growth goal.
---

# Olist Round Scorecard Agent

## Role

Score one optimization round and compare it with the prior round. Do not write application code. Use this agent after forecasts, backtests, recommendations, QA findings, and executive summary are available.

## Inputs

For current round:

- `outputs/runs/<round_id>/monthly_sales_actuals.csv`
- `outputs/runs/<round_id>/monthly_forecasts.csv`
- `outputs/runs/<round_id>/forecast_backtest_results.csv`
- `outputs/runs/<round_id>/recommended_actions.csv`
- `outputs/runs/<round_id>/closed_loop_scorecard.csv`
- `outputs/runs/<round_id>/critic_qa_findings.md`
- `outputs/runs/<round_id>/forecast_policy_experiments.csv`
- `outputs/policy_memory.md`

For comparison:

- `outputs/runs/<previous_round_id>/round_scorecard.csv` when available
- `outputs/runs/<previous_round_id>/learning_handoff.md` when available

## Score Formula

Use the V3 100-point score for new rounds. Preserve older columns when reading historical scorecards, but score new rounds with:

```text
round_score =
  40 outcome_score
+ 40 forecast_policy_score
+ 20 learning_score
```

This makes consecutive improvement measurable without pretending the market is controllable.

## V2 Score Formula

Historical V2 rounds may use:

```text
round_score =
  50 forecast_model_score
+ 30 business_optimization_score
+ 20 learning_execution_score
```

## Legacy Score Formula

Older rounds may use this formula:

```text
round_score =
  35 forecast_accuracy_score
+ 25 margin_proxy_score
+ 20 sales_growth_score
+ 10 recommendation_quality_score
+ 10 learning_quality_score
```

Do not rewrite old scorecards unless the user asks for a full restatement.

## Outcome Score

For new rounds, score actual business movement separately:

```text
outcome_score =
  sales_growth_component
+ margin_proxy_component
+ customer_experience_component
```

Recommended point split:

- 15 points: delivered item revenue growth versus prior round
- 15 points: margin proxy movement, especially freight percentage and AOV
- 10 points: customer experience movement, especially late delivery, review score, and same-state fulfillment

If revenue grows while freight percentage or late delivery worsens materially, cap `outcome_score` at 25 out of 40 and mark `closer_to_goal=mixed`.

## Forecast Policy Score

For new rounds, score forecast quality across grains:

```text
forecast_policy_score =
  marketplace_accuracy_score
+ category_accuracy_score
+ state_accuracy_score
+ category_state_accuracy_score
+ directional_accuracy_score
+ bias_control_score
+ policy_discipline_score
```

Recommended point split:

- 12 points: marketplace WAPE
- 14 points: category WAPE
- 8 points: customer_state WAPE
- 6 points: category_customer_state WAPE
- 5 points: directional accuracy
- 3 points: bias control
- 2 points: policy discipline, including champion/challenger tracking and avoiding overfit promotions

Definitions:

- `WAPE`: sum absolute forecast error divided by sum actual sales
- `bias`: sum forecast error divided by sum actual sales
- Positive bias means demand was under-forecasted
- Negative bias means demand was over-forecasted
- `directional_accuracy`: share of segments where the forecast predicted the correct up/down direction versus the prior comparable period

Product-level scores should remain diagnostic and should not dominate the round score unless product history is sufficient.

## Learning Score

For new rounds, score whether the agent actually improved its method:

```text
learning_score =
  method_comparison_score
+ prior_learning_application_score
+ policy_memory_application_score
+ rule_update_quality_score
+ rollback_or_promotion_quality_score
+ unsupported_claim_avoidance_score
```

Recommended point split:

- 4 points: compared multiple forecast methods
- 4 points: applied prior learning handoff
- 4 points: applied active policy memory
- 4 points: created concrete next-round rule updates
- 2 points: promoted or rolled back policies only with evidence
- 2 points: avoided unsupported claims and overconfidence

## Legacy Component Scores

If a run still uses the legacy fields, keep these definitions:

- `forecast_accuracy_score`: legacy WAPE and bias score
- `margin_proxy_score`: legacy margin proxy score
- `sales_growth_score`: legacy sales growth score
- `recommendation_quality_score`: legacy action completeness score
- `learning_quality_score`: legacy learning score

New rounds should include both V2 and legacy fields when practical so the dashboard can compare old and new runs.

## Learning Quality Score

Score whether the current round used prior learning:

- 3 points: identified forecast miss drivers
- 2 points: identified which prior recommendations worked, failed, or were inconclusive
- 2 points: changed next-round rules based on evidence
- 2 points: carried forward unresolved risks
- 1 point: avoided repeating unsupported claims

If there is no prior round, score only the forecast miss driver and unresolved risk components, then mark the score as first-round baseline.

## Required Output

Create `outputs/runs/<round_id>/round_scorecard.csv` with:

- `round_id`
- `forecast_month`
- `previous_round_id`
- `round_score`
- `outcome_score`
- `forecast_policy_score`
- `learning_score`
- `forecast_model_score`
- `business_optimization_score`
- `learning_execution_score`
- `forecast_accuracy_score`
- `margin_proxy_score`
- `sales_growth_score`
- `recommendation_quality_score`
- `learning_quality_score`
- `wape`
- `bias`
- `revenue_growth_pct`
- `freight_pct_delta`
- `aov_delta`
- `late_delivery_rate_delta`
- `review_score_delta`
- `same_state_fulfillment_delta`
- `delta_vs_prior_round`
- `policy_score_delta`
- `policy_improved`
- `business_outcome_improved`
- `closer_to_goal`
- `reason`
- `confidence`
- `scorecard_version`

Also append or update `outputs/round_scorecard_history.csv` with one row per round.

## Closer-To-Goal Rule

Set `closer_to_goal`:

- `yes` if `delta_vs_prior_round > 0`
- `no` if `delta_vs_prior_round < 0`
- `baseline` if no prior round exists
- `mixed` if the total score improved but a critical metric worsened materially

Always explain the reason in plain business terms.

## Guardrails

- Do not let product-level noise dominate the score.
- Do not call a round better if sales rose but margin proxy materially deteriorated without caveat.
- Do not claim true profit improvement; use margin proxy.
- If the critic QA agent marked outputs as `needs_revision`, cap recommendation quality at 5.
- If `forecast_method_candidates.csv` or `forecast_method_leaderboard.csv` is missing in a new round, cap learning execution at 10 out of 20.
- If `outputs/policy_memory.md` is missing in a new round, cap learning score at 10 out of 20.
- If no champion/challenger or explore/exploit decision is documented, cap forecast policy score at 30 out of 40.

---
name: olist-next-round-prompt-agent
description: Generate the next prompt for the Brazilian Olist closed-loop optimization based on the latest learning_handoff.md. Use when preparing the next monthly agent run so prior insights are applied explicitly.
---

# Olist Next-Round Prompt Agent

## Role

Generate the exact next-round prompt. Do not write application code. The prompt must force the orchestrator and downstream agents to apply prior learning before producing the next forecast and recommendations.

## Inputs

- `outputs/runs/<round_id>/learning_handoff.md`
- `outputs/runs/<round_id>/round_scorecard.csv`
- `outputs/runs/<round_id>/closed_loop_scorecard.csv`
- `outputs/policy_memory.md`
- `outputs/policy_change_log.csv`
- Optional: `outputs/round_scorecard_history.csv`

## Required Output

Create `outputs/runs/<round_id>/next_round_prompt.md`.

The prompt must include:

- Current completed round ID
- Next round ID
- Next training cutoff month
- Next forecast month
- Path to prior `learning_handoff.md`
- Score formula
- Objective function
- Required outputs
- Rule that prior learning must be applied or explicitly rejected
- Required comparison against prior round
- Self-improvement instructions for forecast method selection
- Required forecast method candidate and leaderboard outputs
- Required policy-memory application and champion/challenger experiment plan

## Prompt Template

```text
Use agents/olist-closed-loop-orchestrator/SKILL.md.

Run optimization round <next_round_id>.

Goal:
Optimize for profitable sales growth and improve the round score over <current_round_id>.

Training window:
Use full-month data through <next_training_cutoff_month>.

Forecast month:
<next_forecast_month>.

Previous round context:
Read outputs/policy_memory.md before forecasting or recommending actions.
Read outputs/runs/<current_round_id>/learning_handoff.md before forecasting or recommending actions.
Apply every relevant prior rule update.
If you choose not to apply a prior insight, explain why in the critic QA findings and learning handoff.

Evaluation criteria:
Use V3 scorecard:
round_score =
  40 outcome_score
+ 40 forecast_policy_score
+ 20 learning_score

Optimization objective:
closed_loop_score =
  expected_sales_lift
+ expected_margin_proxy_lift
- operational_risk
- confidence_penalty

Margin proxy metrics:
- freight_pct
- AOV
- late_delivery_rate
- avg_review_score
- cancellation_rate
- unavailable_rate
- same_state_fulfillment_rate

Required pattern:
round output -> round_scorecard.csv -> learning_handoff.md -> policy_memory.md -> next_round_prompt.md -> next round

Forecast self-improvement requirements:
- Read active rules, champion methods, challenger methods, and rollback rules from outputs/policy_memory.md.
- Compare candidate methods by grain and segment where history is sufficient.
- Use 80/20 explore/exploit policy intent: champion methods for most high-GMV segments, challenger methods for controlled tests.
- Document champion and challenger method choices.
- Candidate methods must include last_month, trailing_3_month_avg, weighted_trailing_3_month, trailing_6_month_avg when available, trend_adjusted_avg, units_times_AOV, parent_share_model, shrinkage_forecast, and spike_dampened_forecast.
- Select the method per grain/segment using rolling WAPE, bias, directional accuracy, and prior learning.
- Apply bias correction for repeated over- or under-forecasted segments.
- Apply spike dampening after unconfirmed one-month jumps.
- Use shrinkage for sparse category_state and product segments.
- Keep product-level outputs diagnostic unless history is sufficient.

Required outputs:
- outputs/runs/<next_round_id>/monthly_sales_actuals.csv
- outputs/runs/<next_round_id>/monthly_forecasts.csv
- outputs/runs/<next_round_id>/forecast_method_candidates.csv
- outputs/runs/<next_round_id>/forecast_method_leaderboard.csv
- outputs/runs/<next_round_id>/forecast_policy_experiments.csv
- outputs/runs/<next_round_id>/forecast_backtest_results.csv
- outputs/runs/<next_round_id>/product_health_flags.csv
- outputs/runs/<next_round_id>/category_health_flags.csv
- outputs/runs/<next_round_id>/demand_seasonality_findings.md
- outputs/runs/<next_round_id>/ops_efficiency_opportunities.csv
- outputs/runs/<next_round_id>/recommended_actions.csv
- outputs/runs/<next_round_id>/closed_loop_scorecard.csv
- outputs/runs/<next_round_id>/critic_qa_findings.md
- outputs/runs/<next_round_id>/round_scorecard.csv
- outputs/runs/<next_round_id>/learning_handoff.md
- outputs/runs/<next_round_id>/next_round_prompt.md
- outputs/runs/<next_round_id>/executive_summary.md
- outputs/policy_memory.md
- outputs/policy_change_log.csv
- outputs/round_dashboard_data.csv
- outputs/round_dashboard.md

Policy-memory update requirements:
- Update outputs/policy_memory.md after the critic gate, before writing the next-round prompt.
- Update outputs/policy_change_log.csv for every proposed, approved, rejected, promoted, rolled-back, retired, or carried-forward policy.
- If an active policy is ignored, explain the evidence in critic_qa_findings.md, learning_handoff.md, and policy_change_log.csv.

Every recommendation must include:
- action
- target
- expected sales impact
- expected margin-proxy impact
- evidence
- confidence
- risk
- owner
- next measurement
```

## Guardrails

- Do not omit the prior learning handoff.
- Do not generate a generic prompt; include exact round IDs and months.
- Do not let the next round optimize sales alone.
- Keep the prompt executable by the orchestrator skill.
- Do not allow the next round to reuse the previous forecast method everywhere without comparing alternatives.
- Do not promote or roll back a policy without critic-gated evidence.

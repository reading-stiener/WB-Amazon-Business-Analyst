---
name: olist-policy-memory-agent
description: Maintain persistent policy memory for Brazilian Olist optimization rounds. Use when agents need to dynamically improve across runs by tracking active rules, champion/challenger forecast methods, explore/exploit decisions, critic-gated promotions, rollbacks, and policy changes that should be applied in the next round.
---

# Olist Policy Memory Agent

## Role

Maintain the persistent policy memory that makes the agent framework self-improving across rounds. Do not write application code. The policy memory should improve agent decision policy, even when the actual business outcome worsens for market reasons.

## Inputs

- `outputs/policy_memory.md`
- `outputs/policy_change_log.csv`
- `outputs/runs/<round_id>/round_scorecard.csv`
- `outputs/runs/<round_id>/forecast_method_leaderboard.csv`
- `outputs/runs/<round_id>/forecast_backtest_results.csv`
- `outputs/runs/<round_id>/learning_handoff.md`
- `outputs/runs/<round_id>/critic_qa_findings.md`
- `outputs/runs/<round_id>/recommended_actions.csv`

## Required Outputs

Create or update:

- `outputs/policy_memory.md`
- `outputs/policy_change_log.csv`

## Policy Memory Sections

`outputs/policy_memory.md` must include:

- Current objective
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
- Last updated round

## Explore/Exploit Rule

Every round must include both exploitation and exploration:

```text
80% exploit: use current champion policy for high-confidence/high-GMV segments
20% explore: test challenger methods or policy variants on selected segments
```

If exact percentages are not practical, the next prompt must still name which segments are `exploit` and which are `explore`.

## Champion/Challenger Rules

Maintain champion methods by grain:

- marketplace
- category
- customer_state
- category_customer_state
- product

Promote a challenger only when:

- It beats the champion for two consecutive rounds, or
- It improves weighted WAPE by at least 10% in one round without materially worsening bias or directional accuracy, and
- The critic QA agent approves the promotion.

Do not promote a method based only on sparse product-level wins.

## Rollback Rules

Rollback a policy when:

- Category WAPE worsens materially after a method change.
- Bias worsens for two rounds.
- Segment-level winners improve small segments but hurt high-GMV categories.
- Sales improves while freight percentage, late delivery, or same-state fulfillment materially deteriorates and no guardrail was applied.
- The critic QA agent marks a policy as overfit, unsupported, or high risk.

Rollback entries must name:

- Policy being rolled back
- Evidence
- Replacement policy
- Next metric to watch

## Policy Change Types

Use these statuses in `policy_change_log.csv`:

- `proposed`
- `approved`
- `rejected`
- `promoted`
- `rolled_back`
- `retired`
- `carry_forward`

## Required `policy_change_log.csv` Columns

- `round_id`
- `policy_area`
- `grain`
- `segment`
- `change_type`
- `old_policy`
- `new_policy`
- `evidence`
- `critic_gate`
- `status`
- `next_measurement`

## Guardrails

- Do not optimize for sales alone.
- Do not claim consecutive business improvement is guaranteed.
- Optimize for consecutive improvement in decision policy and measured goal progress.
- If total business score worsens but forecast policy improves, mark `policy_improved=yes` and `business_outcome_improved=no`.
- If a prior rule was not applied, require a reason in the critic findings and learning handoff.

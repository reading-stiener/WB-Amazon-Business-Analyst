---
name: olist-learning-handoff-agent
description: Create the learning handoff between Brazilian Olist optimization rounds. Use when converting round scorecards, forecast misses, action outcomes, QA findings, and dashboard deltas into explicit next-round rule updates.
---

# Olist Learning Handoff Agent

## Role

Create the handoff that the next round must read and apply. Do not write application code. The handoff turns round results into concrete changes for the next forecast and recommendation policy.

## Inputs

- `outputs/runs/<round_id>/round_scorecard.csv`
- `outputs/runs/<round_id>/forecast_backtest_results.csv`
- `outputs/runs/<round_id>/recommended_actions.csv`
- `outputs/runs/<round_id>/closed_loop_scorecard.csv`
- `outputs/runs/<round_id>/critic_qa_findings.md`
- `outputs/policy_memory.md`
- `outputs/policy_change_log.csv`
- `outputs/runs/<previous_round_id>/learning_handoff.md` when available

## Required Output

Create `outputs/runs/<round_id>/learning_handoff.md`.

Use this structure:

```text
# Learning Handoff: <round_id>

## Goal Movement

- Round score:
- Delta vs prior round:
- Closer to goal:
- Why:

## What Improved

- ...

## What Got Worse

- ...

## Forecast Misses

| Segment | Miss Direction | Likely Cause | Rule Change |
| --- | --- | --- | --- |

## Forecast Method Learning

| Grain | Prior Method | Result | Next Method Rule |
| --- | --- | --- | --- |

## Recommendation Outcomes

| Action | Expected Impact | Observed Result | Decision |
| --- | --- | --- | --- |

## Next-Round Rule Updates

- ...

## Policy Changes Proposed

| Policy Area | Grain | Segment | Old Policy | New Policy | Evidence | Requested Status |
| --- | --- | --- | --- | --- | --- | --- |

## Rollbacks

| Policy | Evidence | Replacement | Next Measurement |
| --- | --- | --- | --- |

## Unresolved Risks

- ...

## Instructions For Next Round

- ...
```

## Required Learning Types

Capture:

- Forecast method changes by grain
- Forecast method changes by segment when a segment has sufficient history
- Best and worst methods from `forecast_method_leaderboard.csv`
- Bias correction rules for repeated over- or under-forecasting
- Spike-dampening rules for one-month jumps or drops
- Shrinkage rules for sparse category-state and product segments
- Whether units and AOV should be forecast separately for specific segments
- Proposed policy promotions, rejections, and rollbacks
- Whether policy memory was applied
- Confidence downgrades or upgrades
- Segment-level demand changes
- Seasonality adjustments
- Operational risk updates
- Recommendation policy changes
- Metrics that must be watched next round

## Example Rule Updates

- If a category is under-forecasted for two rounds, increase weight on recent 3-month trend for that category.
- If a state has persistent late delivery deterioration, downgrade growth recommendations unless regional fulfillment is part of the action.
- If product-level forecasts are noisy, shift optimization toward category-state level and lower product confidence.
- If low-AOV promotion hurts margin proxy, raise the free-shipping threshold or restrict it to bundle-eligible categories.
- If forecast bias is persistently positive, increase baseline forecast for affected segments or adjust seasonality upward.
- If forecast bias is persistently negative, dampen recent trend weighting or investigate one-time demand spikes.
- If a one-month category spike is followed by over-forecasting, require spike dampening until a second confirming month appears.
- If category-state WAPE stays high, shrink child segments toward category or customer-state parent forecasts.
- If revenue forecast misses are caused by AOV movement, forecast units and AOV separately next round.

## Guardrails

- Do not create vague lessons like "forecast better next time."
- Every rule update must name the segment, metric, and expected behavior change.
- If a prior insight is rejected, explain why.
- Carry unresolved risks forward until closed or invalidated.
- The next handoff must state which forecast method should be tried or avoided by grain.
- The next handoff must propose policy-memory changes in a form the policy-memory agent can accept, reject, or roll back.

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

## Recommendation Outcomes

| Action | Expected Impact | Observed Result | Decision |
| --- | --- | --- | --- |

## Next-Round Rule Updates

- ...

## Unresolved Risks

- ...

## Instructions For Next Round

- ...
```

## Required Learning Types

Capture:

- Forecast method changes by grain
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

## Guardrails

- Do not create vague lessons like "forecast better next time."
- Every rule update must name the segment, metric, and expected behavior change.
- If a prior insight is rejected, explain why.
- Carry unresolved risks forward until closed or invalidated.

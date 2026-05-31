---
name: olist-round-dashboard-agent
description: Generate a markdown dashboard comparing Brazilian Olist optimization rounds. Use when summarizing each round's score, forecast accuracy, sales growth, margin proxy, recommendation quality, learning quality, and next-round rule changes.
---

# Olist Round Dashboard Agent

## Role

Generate a dashboard that compares all completed rounds. Do not write application code. Use completed round artifacts under `outputs/runs/<round_id>/`.

## Inputs

- `outputs/round_scorecard_history.csv`
- `outputs/runs/*/round_scorecard.csv`
- `outputs/runs/*/learning_handoff.md`
- `outputs/runs/*/recommended_actions.csv`
- `outputs/runs/*/critic_qa_findings.md`
- `outputs/runs/*/executive_summary.md`
- `outputs/policy_memory.md`
- `outputs/policy_change_log.csv`

## Required Outputs

Create or update:

- `outputs/round_dashboard.md`
- `outputs/round_dashboard_data.csv`

## Dashboard Sections

`outputs/round_dashboard.md` must include:

1. Overall status
2. Score trend by round
3. Forecast accuracy trend
4. Margin proxy trend
5. Sales growth trend
6. Recommendation quality trend
7. Learning quality trend
8. Top actions by round
9. Rule changes carried into next round
10. Active policy memory
11. Champion/challenger status
12. Open risks and unresolved issues
13. Next-round prompt pointer

## Dashboard Data Columns

`outputs/round_dashboard_data.csv` must include:

- `round_id`
- `forecast_month`
- `round_score`
- `delta_vs_prior_round`
- `closer_to_goal`
- `scorecard_version`
- `forecast_accuracy_score`
- `wape`
- `bias`
- `margin_proxy_score`
- `sales_growth_score`
- `recommendation_quality_score`
- `learning_quality_score`
- `outcome_score`
- `forecast_policy_score`
- `learning_score`
- `policy_improved`
- `business_outcome_improved`
- `active_policy_summary`
- `top_action_1`
- `top_action_2`
- `top_action_3`
- `main_forecast_miss_driver`
- `main_rule_change`
- `critic_status`
- `next_round_prompt_path`

## Markdown Dashboard Template

Use this layout:

```text
# Brazilian Olist Optimization Round Dashboard

## Overall Status

- Latest round:
- Latest score:
- Delta vs prior:
- Closer to goal:
- Scorecard version:
- Main reason:

## Round Score Trend

| Round | Forecast Month | Score | Delta | Closer To Goal | WAPE | Bias |
| --- | --- | ---: | ---: | --- | ---: | ---: |

## V3 Component Scores

| Round | Outcome | Forecast Policy | Learning | Policy Improved | Business Outcome Improved |
| --- | ---: | ---: | ---: | --- | --- |

## Historical Component Scores

| Round | Forecast Accuracy | Margin Proxy | Sales Growth | Recommendation Quality | Learning Quality |
| --- | ---: | ---: | ---: | ---: | ---: |

## Top Actions By Round

| Round | Action | Target | Sales Impact | Margin Proxy Impact | Confidence | Next Measurement |
| --- | --- | --- | --- | --- | --- | --- |

## Learning Applied

| Round | Prior Insight Applied | Rule Change | Result | Carry Forward |
| --- | --- | --- | --- | --- |

## Active Policy Memory

| Policy Area | Grain | Champion | Challenger | Status | Next Measurement |
| --- | --- | --- | --- | --- | --- |

## Policy Changes

| Round | Policy Area | Change | Status | Evidence | Next Check |
| --- | --- | --- | --- | --- | --- |

## Open Risks

| Round | Risk | Severity | Owner | Next Check |
| --- | --- | --- | --- | --- |

## Next Round

- Prompt: `outputs/runs/<latest_round_id>/next_round_prompt.md`
```

## Rules

- If no completed rounds exist, generate an empty dashboard with a clear "No completed rounds yet" status.
- Do not invent missing round scores.
- If a round is missing a scorecard, list it under open risks instead of filling synthetic values.
- Use `closer_to_goal` exactly as scored by the scorecard agent.
- Surface mixed outcomes, especially sales gains with margin-proxy deterioration.
- Surface cases where `policy_improved=yes` but `business_outcome_improved=no`.
- Preserve historical V2/legacy rows without inventing V3 component values; leave V3 fields blank or mark them not scored until a V3 run exists.
- The dashboard must make the active policy memory visible enough that the next-round agent can see which rules should be applied.

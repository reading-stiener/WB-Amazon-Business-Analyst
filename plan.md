# Search-Term Analysis Agent — Weekly Plan

**Goal:** Ingest the latest Amazon Sponsored Products search-term report each week, compare it against prior recommendations and actual outcomes, and produce a CUT / FIX / GROW recommendation set plus a web-based budget dashboard for the next week.

**Input:** CSV with `Customer Search Term, Match Type, Campaign Name, Clicks, Impressions, Spend, Orders, Sales, ACoS, CVR, CTR`.

## Config (logged as `wandb.config`)

- `target_acos_blended <= 0.25`
- `target_acos_discovery <= 0.25`
- `target_acos_brand <= 0.20`
- `neg_zero_order_min_spend >= 50`
- `neg_high_acos_min_spend >= 100`
- `high_acos_cutoff >= 1.0`
- `review_acos_band = (0.5, 1.0)`
- `harvest_min_orders >= 3`
- `harvest_max_acos <= 0.20`

## Pipeline (single agent, 5 sequential steps)

### 1. Load & Enrich

- Validate 11 columns + row count. Coerce numerics, trim strings, flag blank campaigns.
- Parse `Campaign Name` → `Targeting type` ∈ {Auto, Disc KW, Conv KW, Conq PAT, Def PAT, Other}.
  - ` - Auto - ` → Auto
  - ` - Disc KW - ` → Disc KW (broad/phrase discovery)
  - ` - Conv KW - ` → Conv KW (exact-match proven winners)
  - ` - Conq PAT - ` → Conquest product targeting
  - ` - Def PAT - ` → Defensive product targeting
- Parse `Bucket` from `Customer Search Term`:
  - Brand Defense if the normalized search term starts with `B0`
  - Discovery otherwise
- Recompute `ACoS = Spend/Sales`, `CTR = Clicks/Impressions`, `CVR = Orders/Clicks` (never trust export averages — they're row-level, not weighted).
- Log enriched table as W&B Artifact.

### 2. Scorecard (vs. target)

- Group by Bucket + Blended total. Sum Spend/Sales/Orders/Clicks/Impressions; compute **weighted** ACoS, ROAS, CTR, CVR.
- Compute `variance = actual_acos − target` and `$_over = variance × sales`.
- Write 3-sentence narrative: blended result vs target, which bucket drove the miss, total dollar overage.
- **Self-check:** `blended_spend == sum(bucket_spend)` and `blended_sales == sum(bucket_sales)`. Fail loud if not.

### 3. Negative KW Candidates (CUT)

- Roll up by search term across all campaigns/match types: sum Spend, Sales, Orders, Clicks.
- Compute ACoS per term (zero-sales → infinite/no sales).
- Classify:
  - `Orders = 0 AND Spend ≥ 50` → **NEGATIVE: zero orders**
  - `Spend ≥ 100 AND ACoS ≥ 100%` → **NEGATIVE: high ACoS**
  - `Spend ≥ 100 AND 50% ≤ ACoS < 100%` → **REVIEW**
  - else → **keep**
- Sort by Spend descending. Summarize: count + total spend per classification.
- **Headline metric:** total recoverable spend = Σ Spend across NEGATIVE terms.

### 4. Harvest Candidates (GROW)

- Roll up by term: sum Orders, Spend, Sales, Clicks; compute ACoS.
- Filter to candidates: `Orders ≥ 3 AND ACoS < 20%`.
- For each candidate, compute from raw data:
  - `clicks_in_auto_disc` = Σ Clicks where Targeting type ∈ {Auto, Disc KW}
  - `clicks_in_conv_exact` = Σ Clicks where Targeting type = Conv KW AND Match Type = EXACT
- Assign verdict:
  - In Auto/Disc, not in Conv Exact → **HARVEST → promote to Conv KW exact**
  - Already in Conv Exact → **Already covered**
  - Not in Auto/Disc → **Outside harvest source**
- Summarize HARVEST set: count, total sales, total orders, weighted avg ACoS — the growth headline.
- **Self-check:** every HARVEST row must satisfy `clicks_in_auto_disc > 0 AND clicks_in_conv_exact == 0`.

### 5. Executive Dashboard & Budget What-If

- Generate a web-based dashboard for weekly business-leader review.
- Dashboard must communicate the scorecard, CUT/FIX/GROW actions, budget gaps, and next-week decision posture in plain business language.
- Accept human inputs:
  - Brand Defense budget
  - Discovery budget
  - Harvest exact-match budget
  - Experiment reserve
  - Target blended ACoS
  - CUT adoption rate
  - CPC pressure assumption
  - CVR lift/decline assumption
  - Leader notes or constraints
- Include what-if scenarios:
  - **Efficiency Reset** — margin-first plan that does not simply cut budget. Rank cuts by the ratio of expected revenue loss to budget removed, and prefer changes that minimize `revenue_loss / budget_cut` while still improving ACoS.
  - **Balanced Recovery** — target-ACoS discipline while funding proven HARVEST terms.
  - **Growth Push** — higher spend on proven HARVEST and strategic discovery with explicit ACoS risk.
- For Efficiency Reset, calculate for each candidate budget reduction:
  - `budget_cut = current_spend - proposed_spend`
  - `revenue_loss = current_sales - projected_sales`
  - `cut_efficiency_ratio = revenue_loss / budget_cut`
  - Prefer the lowest ratio, subject to ACoS target, minimum sales floor, and mandatory CUT/FIX guardrails.
- Recalculate projected spend, projected sales, projected ACoS, target gap, CUT savings applied, harvest coverage, and sales/spend deltas as humans adjust inputs.
- Produce concise, insightful notes:
  - What changed vs. actual week
  - Why the recommended budget is justified
  - Where leaders are accepting risk
  - Which actions are mandatory before budget release
- Allow dashboard output to be used as the weekly budget-council artifact.

## Final Outputs

- **CUT list** — negatives to add, with $ recovered.
- **FIX list** — REVIEW terms needing bid cuts or copy/landing fixes (sourced from scorecard misses).
- **GROW list** — HARVEST terms to promote, with projected sales at current ACoS.
- **Next-week targets** — spend ceiling, sales floor, blended ACoS, profitable-sales target. Each anchored to a scorecard number.
- **Caveats** — bid-cut sales-dip risk, threshold sensitivity, overlap between negative/harvest sets.
- **`next_month_recommendations.md`** — markdown operating report for the next-week action plan.
- **Web dashboard** — weekly executive dashboard for communicating performance, testing what-if scenarios, collecting human budget input, and determining next week's ad budgets.

## Reliability hooks (W&B)

- Every threshold → `wandb.config` (sweepable — see how harvest/negative counts shift).
- Each step's table → versioned Artifact (lineage: raw → enriched → reports).
- Self-check assertions logged as run metrics; failed tie-out fails the run loudly rather than producing a wrong report silently.
- **Regression test:** keep one hand-verified month (April) as ground truth. Each run scores against it — does the agent reproduce the $13K overage, the harvest count, the negative-KW savings?

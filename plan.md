# Search-Term Analysis Agent — Plan

**Goal:** Ingest a monthly Amazon Sponsored Products search-term report and produce a CUT / FIX / GROW recommendation set for next month.

**Input:** CSV with `Customer Search Term, Match Type, Campaign Name, Clicks, Impressions, Spend, Orders, Sales, ACoS, CVR, CTR`.

## Config (logged as `wandb.config`)

- `target_acos_blended = 0.25`
- `target_acos_discovery = 0.25`
- `target_acos_brand = 0.20`
- `neg_zero_order_min_spend = 50`
- `neg_high_acos_min_spend = 100`
- `high_acos_cutoff = 1.0`
- `review_band = (0.5, 1.0)`
- `harvest_min_orders = 3`
- `harvest_max_acos = 0.20`

## Pipeline (single agent, 4 sequential steps)

### 1. Load & Enrich

- Validate 11 columns + row count. Coerce numerics, trim strings, flag blank campaigns.
- Parse `Campaign Name` → `Targeting type` ∈ {Auto, Disc KW, Conv KW, Conq PAT, Def PAT, Other}.
  - ` - Auto - ` → Auto
  - ` - Disc KW - ` → Disc KW (broad/phrase discovery)
  - ` - Conv KW - ` → Conv KW (exact-match proven winners)
  - ` - Conq PAT - ` → Conquest product targeting
  - ` - Def PAT - ` → Defensive product targeting
- Parse `Bucket` → Brand Defense if name contains "Brand", else Discovery.
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

## Final Output: `next_month_recommendations.md`

- **CUT list** — negatives to add, with $ recovered.
- **FIX list** — REVIEW terms needing bid cuts or copy/landing fixes (sourced from scorecard misses).
- **GROW list** — HARVEST terms to promote, with projected sales at current ACoS.
- **Next-month targets** — spend ceiling, sales floor, blended ACoS, profitable-sales target. Each anchored to a scorecard number.
- **Caveats** — bid-cut sales-dip risk, threshold sensitivity, overlap between negative/harvest sets.

## Reliability hooks (W&B)

- Every threshold → `wandb.config` (sweepable — see how harvest/negative counts shift).
- Each step's table → versioned Artifact (lineage: raw → enriched → reports).
- Self-check assertions logged as run metrics; failed tie-out fails the run loudly rather than producing a wrong report silently.
- **Regression test:** keep one hand-verified month (April) as ground truth. Each run scores against it — does the agent reproduce the $13K overage, the harvest count, the negative-KW savings?

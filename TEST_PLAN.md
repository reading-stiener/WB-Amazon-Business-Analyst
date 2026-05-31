# Test Plan

## Runtime

Use the bundled Codex Python runtime, which already has `pandas` and
`openpyxl`:

```bash
/Users/jianfanl/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3
```

The implementation does not require `wandb` to be installed. If `wandb` is not
available, the W&B Reliability Agent writes `wandb_local_manifest.json` with the
same config, metrics, artifact lineage, and self-check results.

## End-to-End Workbook Validation

Run the full agent pipeline against the April workbook:

```bash
/Users/jianfanl/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
  -m amazon_business_analyst.agents.orchestrator \
  --input "/Users/jianfanl/tmp/weights_biases/WB-Amazon-Business-Analyst/IG PPC - Amazon Exercise.xlsx" \
  --sheet Data \
  --output-dir "/Users/jianfanl/tmp/weights_biases/WB-Amazon-Business-Analyst/outputs/april_validation" \
  --regression-baseline "/Users/jianfanl/tmp/weights_biases/WB-Amazon-Business-Analyst/tests/fixtures/april_expected_metrics.json"
```

Expected headline outputs:

- Blended spend: `$64,318.00`
- Blended sales: `$205,202.04`
- Blended ACoS: `31.34%`
- Dollar over target: `$13,017.49`
- Main driver bucket: `Discovery`
- Brand Defense bucket: `$11,168.04` spend, `$45,896.56` sales, `24.33%` ACoS
- Discovery bucket: `$53,149.96` spend, `$159,305.48` sales, `33.36%` ACoS
- Negative keyword candidates: `12`
- Review candidates: `5`
- Recoverable spend: `$1,837.65`
- Harvest candidates: `138`
- Harvest sales: `$36,790.37`
- Harvest orders: `694`
- Harvest weighted ACoS: `7.06%`

Generated artifacts:

- `validated_raw_search_terms.csv`
- `enriched_search_terms.csv`
- `scorecard.csv`
- `negative_keyword_candidates.csv`
- `negative_keyword_summary.csv`
- `harvest_candidates.csv`
- `next_month_recommendations.md`
- `dashboard/index.html`
- `dashboard/data.js`
- `dashboard/styles.css`
- `dashboard/app.js`
- `run_summary.json`
- `wandb_local_manifest.json`
- `regression_test_report.json`

## Automated Tests

Run all unit and workbook regression tests:

```bash
cd /Users/jianfanl/tmp/weights_biases/WB-Amazon-Business-Analyst
/Users/jianfanl/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
  -m unittest discover -s tests
```

The tests cover:

- Campaign parsing into `Auto`, `Disc KW`, `Conv KW`, `Conq PAT`, `Def PAT`,
  and `Other`.
- Bucket parsing into `Brand Defense` when normalized search term starts with
  `B0`, otherwise `Discovery`.
- Recomputed row metrics instead of trusting exported averages.
- Weighted scorecard metrics and blended-to-bucket tie-outs.
- CUT classification for zero-order, high-ACoS, review-band, keep, and blank
  search-term rows.
- GROW classification for harvest, already-covered, outside-source, and blank
  search-term rows.
- Dashboard generation, copied web assets, and browser-consumable `data.js`.
- Full workbook regression against the April baseline.

## Dashboard Validation

Open the generated dashboard in a browser:

```text
file:///Users/jianfanl/tmp/weights_biases/WB-Amazon-Business-Analyst/outputs/april_validation/dashboard/index.html
```

Or serve it locally:

```bash
/Users/jianfanl/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
  -m http.server 8765 \
  --bind 127.0.0.1 \
  --directory "/Users/jianfanl/tmp/weights_biases/WB-Amazon-Business-Analyst/outputs/april_validation/dashboard"
```

Expected dashboard behaviors:

- The dashboard renders Week 1, Week 2, and forward/back navigation from source
  dates.
- If the input contains weekly or daily rows, weekly views are direct
  aggregations.
- If the input is a monthly export with one report-range date on every row,
  weekly views are estimated by allocating each row across overlapping calendar
  weeks by day count. The dashboard labels those week views as estimated.
- Scenario presets populate budget and assumption controls.
- Editing budget, target ACoS, CUT adoption, CPC pressure, or CVR changes
  projected budget, sales, ACoS, and target gap.
- Efficiency Reset shows `revenue_loss / budget_cut` as revenue loss per dollar
  removed.
- The decision memo updates when leaders add notes or change budget inputs.

## W&B Threshold Sweep Validation

When `wandb` is installed, run the same command with `--enable-wandb` and change
threshold flags to compare recommendation sensitivity:

```bash
--neg-zero-order-min-spend 40
--neg-high-acos-min-spend 75
--harvest-min-orders 2
--harvest-max-acos 0.15
```

Check whether negative candidate count, recoverable spend, harvest count, and
harvest weighted ACoS move in the expected direction before adopting new
thresholds.

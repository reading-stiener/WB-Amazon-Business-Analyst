"""Monthly feature layer builder for round-smoke-001.

Builds outputs/runs/round-smoke-001/monthly_sales_actuals.csv per SKILL.md spec.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

DATA_DIR = Path("/home/abhijeet-pradhan/wb_amazon_ads_analyst/brazillian_data")
OUT_DIR = Path("/home/abhijeet-pradhan/wb_amazon_ads_analyst/outputs/runs/round-smoke-001")
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_FILE = OUT_DIR / "monthly_sales_actuals.csv"

# ---------------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------------
orders = pd.read_csv(
    DATA_DIR / "olist_orders_dataset.csv",
    parse_dates=[
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ],
)
items = pd.read_csv(DATA_DIR / "olist_order_items_dataset.csv")
products = pd.read_csv(DATA_DIR / "olist_products_dataset.csv")
payments = pd.read_csv(DATA_DIR / "olist_order_payments_dataset.csv")
reviews = pd.read_csv(DATA_DIR / "olist_order_reviews_dataset.csv")
customers = pd.read_csv(DATA_DIR / "olist_customers_dataset.csv")
sellers = pd.read_csv(DATA_DIR / "olist_sellers_dataset.csv")
cat_xlat = pd.read_csv(DATA_DIR / "product_category_name_translation.csv")

# ---------------------------------------------------------------------------
# Derive month + per-order attributes
# ---------------------------------------------------------------------------
orders["month"] = orders["order_purchase_timestamp"].dt.to_period("M").astype(str)
orders = orders.merge(
    customers[["customer_id", "customer_state"]],
    on="customer_id",
    how="left",
)

# Per-order delivery metrics (only meaningful for delivered)
orders["delivery_days"] = (
    orders["order_delivered_customer_date"] - orders["order_purchase_timestamp"]
).dt.total_seconds() / 86400.0
orders["is_late"] = (
    orders["order_delivered_customer_date"] > orders["order_estimated_delivery_date"]
).astype("Int64")
# Restrict late/delivery only to delivered rows
delivered_mask = orders["order_status"] == "delivered"
orders.loc[~delivered_mask, ["delivery_days", "is_late"]] = pd.NA

# Order-level review (take mean if multiple reviews per order)
rev_by_order = reviews.groupby("order_id", as_index=False)["review_score"].mean()
orders = orders.merge(rev_by_order, on="order_id", how="left")

# Order-level payments aggregation
pay_agg = (
    payments.groupby("order_id")
    .agg(
        installments_mean=("payment_installments", "mean"),
        has_credit_card=("payment_type", lambda s: (s == "credit_card").any()),
        has_boleto=("payment_type", lambda s: (s == "boleto").any()),
    )
    .reset_index()
)
orders = orders.merge(pay_agg, on="order_id", how="left")

# ---------------------------------------------------------------------------
# Build item-level frame (one row per order-item)
# ---------------------------------------------------------------------------
cat_xlat = cat_xlat.rename(columns={"product_category_name_english": "category_en"})
products = products.merge(cat_xlat, on="product_category_name", how="left")
products["category"] = products["category_en"].fillna(
    products["product_category_name"]
).fillna("unknown")

items = items.merge(products[["product_id", "category"]], on="product_id", how="left")
items["category"] = items["category"].fillna("unknown")
items = items.merge(sellers[["seller_id", "seller_state"]], on="seller_id", how="left")
items = items.merge(
    orders[
        [
            "order_id",
            "month",
            "order_status",
            "customer_state",
            "delivery_days",
            "is_late",
            "review_score",
            "installments_mean",
            "has_credit_card",
            "has_boleto",
        ]
    ],
    on="order_id",
    how="left",
)
items["same_state"] = (items["seller_state"] == items["customer_state"]).astype(int)

# Delivered subset for revenue/units/etc.
items_d = items[items["order_status"] == "delivered"].copy()

# ---------------------------------------------------------------------------
# Helper to compute metrics for an items-level grain + orders-level grain
# ---------------------------------------------------------------------------

def _delivered_metrics(df_items_d: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    """Compute item/order-level metrics from delivered items frame."""
    grp = df_items_d.groupby(group_cols, dropna=False)
    out = grp.agg(
        sales_revenue=("price", "sum"),
        units_sold=("price", "size"),
        freight_value=("freight_value", "sum"),
        orders=("order_id", "nunique"),
        same_state_items=("same_state", "sum"),
    ).reset_index()
    out["aov"] = np.where(out["orders"] > 0, out["sales_revenue"] / out["orders"], np.nan)
    out["freight_pct"] = np.where(
        out["sales_revenue"] > 0, out["freight_value"] / out["sales_revenue"], np.nan
    )
    out["same_state_fulfillment_rate"] = np.where(
        out["units_sold"] > 0, out["same_state_items"] / out["units_sold"], np.nan
    )
    out = out.drop(columns=["same_state_items"])
    return out


def _order_quality_metrics(df_orders: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    """Delivered-orders metrics: review, delivery days, late rate."""
    d = df_orders[df_orders["order_status"] == "delivered"]
    grp = d.groupby(group_cols, dropna=False)
    return grp.agg(
        avg_review_score=("review_score", "mean"),
        avg_delivery_days=("delivery_days", "mean"),
        late_delivery_rate=("is_late", "mean"),
    ).reset_index()


def _status_rates(df_orders: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    """Cancellation + unavailable rates over ALL orders in grain."""
    grp = df_orders.groupby(group_cols, dropna=False)
    out = grp.agg(
        total_orders=("order_id", "nunique"),
        canceled_orders=("order_status", lambda s: (s == "canceled").sum()),
        unavailable_orders=("order_status", lambda s: (s == "unavailable").sum()),
    ).reset_index()
    out["cancellation_rate"] = np.where(
        out["total_orders"] > 0, out["canceled_orders"] / out["total_orders"], np.nan
    )
    out["unavailable_rate"] = np.where(
        out["total_orders"] > 0, out["unavailable_orders"] / out["total_orders"], np.nan
    )
    return out[group_cols + ["cancellation_rate", "unavailable_rate"]]


def _payment_metrics(df_orders: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    """Payment share + avg installments across all orders in grain."""
    grp = df_orders.groupby(group_cols, dropna=False)
    out = grp.agg(
        payment_credit_card_share=("has_credit_card", "mean"),
        payment_boleto_share=("has_boleto", "mean"),
        avg_installments=("installments_mean", "mean"),
    ).reset_index()
    return out


# ---------------------------------------------------------------------------
# Build per grain
# ---------------------------------------------------------------------------

def build_grain(
    name: str,
    items_group: list[str],  # cols on items_d/items
    orders_group: list[str],  # cols on orders (or items collapsed-to-orders)
    key_builder,  # callable(row) -> key string
    orders_for_grain: pd.DataFrame | None = None,
    items_for_grain: pd.DataFrame | None = None,
) -> pd.DataFrame:
    items_src = items_for_grain if items_for_grain is not None else items_d
    orders_src = orders_for_grain if orders_for_grain is not None else orders

    a = _delivered_metrics(items_src, ["month"] + items_group)
    b = _order_quality_metrics(orders_src, ["month"] + orders_group)
    c = _status_rates(orders_src, ["month"] + orders_group)
    d = _payment_metrics(orders_src, ["month"] + orders_group)

    # Rename items_group cols to match orders_group cols when different
    # We pass them aligned, so just merge on month + group cols
    merged = a.merge(b, on=["month"] + items_group, how="outer") \
             .merge(c, on=["month"] + items_group, how="outer") \
             .merge(d, on=["month"] + items_group, how="outer")
    merged["grain"] = name
    merged["key"] = merged.apply(key_builder, axis=1)
    return merged


# Marketplace: collapse with constant key
items_d["_mkt"] = "marketplace"
items["_mkt"] = "marketplace"
orders["_mkt"] = "marketplace"

# For seller_state at the orders level, we need to attribute orders to seller_state.
# An order can span multiple seller_states; build an orders-x-seller_state frame.
order_seller_states = (
    items[["order_id", "seller_state"]]
    .dropna()
    .drop_duplicates()
)
orders_sstate = orders.merge(order_seller_states, on="order_id", how="left")
orders_sstate["seller_state"] = orders_sstate["seller_state"].fillna("unknown")

# Orders-x-category (one row per order x distinct category touched)
order_cats = (
    items[["order_id", "category"]].drop_duplicates()
)
orders_cat = orders.merge(order_cats, on="order_id", how="left")
orders_cat["category"] = orders_cat["category"].fillna("unknown")

# Orders-x-product
order_prods = items[["order_id", "product_id"]].drop_duplicates()
orders_prod = orders.merge(order_prods, on="order_id", how="left")

# Orders-x-(category, customer_state)
orders_cat_cust = orders_cat.copy()  # already has customer_state

# Orders-x-(category, seller_state)
order_cat_sstate = (
    items[["order_id", "category", "seller_state"]].drop_duplicates()
)
orders_cat_sstate = orders.merge(order_cat_sstate, on="order_id", how="left")
orders_cat_sstate["category"] = orders_cat_sstate["category"].fillna("unknown")
orders_cat_sstate["seller_state"] = orders_cat_sstate["seller_state"].fillna("unknown")

frames = []

# 1) Marketplace
frames.append(
    build_grain(
        name="marketplace",
        items_group=["_mkt"],
        orders_group=["_mkt"],
        key_builder=lambda r: "marketplace",
    ).drop(columns=["_mkt"])
)

# 2) Product category
frames.append(
    build_grain(
        name="category",
        items_group=["category"],
        orders_group=["category"],
        key_builder=lambda r: str(r["category"]),
        orders_for_grain=orders_cat,
    ).drop(columns=["category"])
)

# 3) Product
frames.append(
    build_grain(
        name="product",
        items_group=["product_id"],
        orders_group=["product_id"],
        key_builder=lambda r: str(r["product_id"]),
        orders_for_grain=orders_prod,
    ).drop(columns=["product_id"])
)

# 4) Customer state
frames.append(
    build_grain(
        name="customer_state",
        items_group=["customer_state"],
        orders_group=["customer_state"],
        key_builder=lambda r: str(r["customer_state"]),
    ).drop(columns=["customer_state"])
)

# 5) Seller state
frames.append(
    build_grain(
        name="seller_state",
        items_group=["seller_state"],
        orders_group=["seller_state"],
        key_builder=lambda r: str(r["seller_state"]),
        orders_for_grain=orders_sstate,
    ).drop(columns=["seller_state"])
)

# 6) Category x customer_state
def _cat_cust_key(r):
    return f"{r['category']}|{r['customer_state']}"

frames.append(
    build_grain(
        name="category_x_customer_state",
        items_group=["category", "customer_state"],
        orders_group=["category", "customer_state"],
        key_builder=_cat_cust_key,
        orders_for_grain=orders_cat_cust,
    ).drop(columns=["category", "customer_state"])
)

# 7) Category x seller_state
def _cat_sell_key(r):
    return f"{r['category']}|{r['seller_state']}"

frames.append(
    build_grain(
        name="category_x_seller_state",
        items_group=["category", "seller_state"],
        orders_group=["category", "seller_state"],
        key_builder=_cat_sell_key,
        orders_for_grain=orders_cat_sstate,
    ).drop(columns=["category", "seller_state"])
)

result = pd.concat(frames, ignore_index=True)

# ---------------------------------------------------------------------------
# Partial-month + low-confidence flagging
# ---------------------------------------------------------------------------
purchase_min = orders["order_purchase_timestamp"].min()
purchase_max = orders["order_purchase_timestamp"].max()
first_month = purchase_min.to_period("M").strftime("%Y-%m")
last_month = purchase_max.to_period("M").strftime("%Y-%m")

# Identify the natural full-month range
month_counts = orders.groupby(orders["order_purchase_timestamp"].dt.to_period("M")).size()
# Sparse first/last months: 2016-09 (4 orders) etc. and 2018-10 (partial)
partial_months = set()
# Treat first and last months as partial (calendar coverage may be incomplete)
# Plus any sparse month with <100 marketplace orders
for period, n in month_counts.items():
    if n < 100:
        partial_months.add(period.strftime("%Y-%m"))
partial_months.add(last_month)


def _notes(row):
    notes = []
    if row["month"] in partial_months:
        notes.append("partial_month")
    if pd.isna(row["sales_revenue"]) or row["sales_revenue"] == 0:
        if (row["cancellation_rate"] or 0) > 0 or (row["unavailable_rate"] or 0) > 0:
            notes.append("no_delivered_revenue")
        else:
            notes.append("sparse")
    if pd.notna(row["orders"]) and row["orders"] < 5:
        notes.append("low_order_count")
    return ";".join(notes) if notes else ""


result["confidence_notes"] = result.apply(_notes, axis=1)

# ---------------------------------------------------------------------------
# Final column order per SKILL.md
# ---------------------------------------------------------------------------
COLS = [
    "month",
    "grain",
    "key",
    "sales_revenue",
    "units_sold",
    "orders",
    "aov",
    "freight_value",
    "freight_pct",
    "avg_review_score",
    "late_delivery_rate",
    "avg_delivery_days",
    "same_state_fulfillment_rate",
    "cancellation_rate",
    "unavailable_rate",
    "payment_credit_card_share",
    "payment_boleto_share",
    "avg_installments",
    "confidence_notes",
]
for c in COLS:
    if c not in result.columns:
        result[c] = pd.NA
result = result[COLS]

# Round numerics for readability
num_cols = [c for c in COLS if c not in ("month", "grain", "key", "confidence_notes")]
for c in num_cols:
    result[c] = pd.to_numeric(result[c], errors="coerce")

# Sort
result = result.sort_values(["grain", "month", "key"]).reset_index(drop=True)

result.to_csv(OUT_FILE, index=False)

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
row_counts = result.groupby("grain").size().to_dict()
summary = {
    "output_path": str(OUT_FILE),
    "total_rows": int(len(result)),
    "rows_per_grain": {k: int(v) for k, v in row_counts.items()},
    "month_range": {"min": result["month"].min(), "max": result["month"].max()},
    "partial_months": sorted(partial_months),
    "caveats": [
        "sales_revenue excludes freight; freight_value reported separately.",
        "late_delivery_rate, avg_delivery_days, avg_review_score computed on delivered orders only.",
        "cancellation_rate and unavailable_rate computed across ALL orders at the grain.",
        "Orders with multiple categories/sellers are counted once per distinct grain key; marketplace 'orders' uses unique order_id.",
        "Categories missing from translation are preserved using their Portuguese name; products lacking a category are labeled 'unknown'.",
        "Partial months flagged in confidence_notes include any month with <100 marketplace orders plus the latest month (2018-10).",
        "Some delivered orders lack delivered_customer_date; those drop from delivery_days/late metrics but still count in sales/units.",
    ],
}
print(json.dumps(summary, indent=2, default=str))

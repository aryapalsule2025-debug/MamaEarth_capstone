
import sqlite3
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


# Project folders
PROJECT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_DIR / "mamaearth_capstone.db"
OUTPUT_DIR = PROJECT_DIR / "Visualizations"
OUTPUT_DIR.mkdir(exist_ok=True)


# Load data
with sqlite3.connect(str(DB_PATH)) as connection:
    orders = pd.read_sql_query("SELECT * FROM orders", connection)
    products = pd.read_sql_query(
        "SELECT product_id, price FROM products", connection
    )


# Apply the same cleaning rules as clean_and_eda.py
orders["payment_method"] = (
    orders["payment_method"].astype("string").str.strip().str.upper()
)

duplicate_columns = [
    column for column in orders.columns if column != "order_id"
]

orders = orders.drop_duplicates(
    subset=duplicate_columns, keep="first"
).copy()

orders["discount_pct"] = orders["discount_pct"].fillna(0)

# Calculate revenue after joining product prices
data = orders.merge(
    products,
    on="product_id",
    how="left",
    validate="many_to_one"
)

data["revenue"] = (
    data["price"]
    * data["quantity"]
    * (1 - data["discount_pct"] / 100)
)


# --------------------------------------------------
# Chart 1: Return rate by payment method
# --------------------------------------------------

payment_summary = (
    data.groupby("payment_method")
    .agg(
        orders=("order_id", "count"),
        returns=("returned", "sum")
    )
)

payment_summary["return_rate_pct"] = (
    payment_summary["returns"] / payment_summary["orders"] * 100
)

payment_summary = payment_summary.sort_values(
    "return_rate_pct", ascending=False
)

plt.figure(figsize=(8, 5))

bars = plt.bar(
    payment_summary.index,
    payment_summary["return_rate_pct"]
)

plt.title("Order Return Rate by Payment Method")
plt.xlabel("Payment Method")
plt.ylabel("Return Rate (%)")
plt.ylim(0, max(payment_summary["return_rate_pct"]) * 1.2)
plt.grid(axis="y", linestyle="--", alpha=0.3)

for bar, value in zip(bars, payment_summary["return_rate_pct"]):
    plt.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 0.8,
        "{:.1f}%".format(value),
        ha="center"
    )

plt.tight_layout()
plt.savefig(
    str(OUTPUT_DIR / "return_rate_by_payment.png"),
    dpi=300,
    bbox_inches="tight"
)
plt.close()


# --------------------------------------------------
# Chart 2: Monthly revenue excluding flagged bulk orders
# --------------------------------------------------

data["order_date"] = pd.to_datetime(
    data["order_date"],
    format="%d-%m-%Y",
    errors="coerce"
)

# Keep the main cleaned data intact; exclude these only
# from this separate sensitivity-analysis visualization.
bulk_order_ids = ["O0011", "O0098"]
adjusted_data = data[~data["order_id"].isin(bulk_order_ids)].copy()

adjusted_data["month"] = (
    adjusted_data["order_date"].dt.to_period("M").astype(str)
)

monthly_revenue = (
    adjusted_data.groupby("month")["revenue"]
    .sum()
    .sort_index()
)

plt.figure(figsize=(10, 5))

plt.plot(
    monthly_revenue.index,
    monthly_revenue.values,
    marker="o",
    linewidth=2
)

plt.title("Monthly Revenue Excluding Two Flagged Bulk Orders")
plt.xlabel("Month")
plt.ylabel("Revenue (Rs.)")
plt.xticks(rotation=45)
plt.grid(axis="y", linestyle="--", alpha=0.3)

for month, value in monthly_revenue.items():
    plt.annotate(
        "{:,.0f}".format(value),
        (month, value),
        textcoords="offset points",
        xytext=(0, 7),
        ha="center",
        fontsize=8
    )

plt.tight_layout()
plt.savefig(
    str(OUTPUT_DIR / "monthly_revenue_trend.png"),
    dpi=300,
    bbox_inches="tight"
)
plt.close()


print("Charts created successfully:")
print(OUTPUT_DIR / "return_rate_by_payment.png")
print(OUTPUT_DIR / "monthly_revenue_trend.png")

print("\nReturn rate by payment method:")
print(payment_summary.round(2))

print("\nMonthly revenue excluding flagged bulk orders:")
print(monthly_revenue.round(2))

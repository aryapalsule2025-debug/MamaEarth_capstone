

import json
from pathlib import Path

import pandas as pd


# --------------------------------------------------
# 1. Define project paths
# --------------------------------------------------

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "Data"
NARRATOR_DIR = PROJECT_DIR / "narrator"

NARRATOR_DIR.mkdir(exist_ok=True)


# --------------------------------------------------
# 2. Load the raw CSV files
# --------------------------------------------------

customers = pd.read_csv(DATA_DIR / "customer.csv")
products = pd.read_csv(DATA_DIR / "products.csv")
orders = pd.read_csv(DATA_DIR / "orders.csv")

print("=" * 55)
print("MAMAEARTH RETURNS & GROWTH INTELLIGENCE")
print("=" * 55)

print("\n--- Original data dimensions ---")
print("Customers:", customers.shape)
print("Products:", products.shape)
print("Orders:", orders.shape)


# --------------------------------------------------
# 3. Inspect data quality before cleaning
# --------------------------------------------------

print("\n--- Missing values before cleaning ---")
print(orders.isnull().sum())

print("\n--- Raw payment-method values ---")
print(orders["payment_method"].value_counts(dropna=False))

print(
    "\nRaw distinct payment-method values:",
    orders["payment_method"].nunique(dropna=True)
)


# Detect duplicate business records without using order_id.
duplicate_columns = [
    column for column in orders.columns
    if column != "order_id"
]

duplicate_mask = orders.duplicated(
    subset=duplicate_columns,
    keep="first"
)

duplicate_orders = orders.loc[duplicate_mask].copy()

print("\n--- Suspected duplicate orders ---")
print("Duplicate rows:", len(duplicate_orders))
print("Duplicate order IDs:", duplicate_orders["order_id"].tolist())


# --------------------------------------------------
# 4. Prepare products and calculate revenue
# --------------------------------------------------

products["price"] = pd.to_numeric(products["price"], errors="raise")


def add_revenue(data):
    result = data.merge(
        products[["product_id", "price"]],
        on="product_id",
        how="left",
        validate="many_to_one",
        indicator=True
    )

    unmatched = result["_merge"] != "both"
    if unmatched.any():
        missing_products = result.loc[
            unmatched, "product_id"
        ].drop_duplicates().tolist()
        raise ValueError(
            f"Orders reference unknown product IDs: {missing_products}"
        )

    result = result.drop(columns="_merge")

    discount = result["discount_pct"].fillna(0)

    result["revenue"] = (
        result["price"]
        * result["quantity"]
        * (1 - discount / 100)
    )

    return result


raw_with_revenue = add_revenue(orders)

duplicate_with_revenue = raw_with_revenue.loc[duplicate_mask]

raw_revenue = float(raw_with_revenue["revenue"].sum())
duplicate_revenue = float(duplicate_with_revenue["revenue"].sum())

print("\n--- Raw revenue checks ---")
print("Order count:", len(orders))
print("Total revenue: Rs.", round(raw_revenue, 2))
print(
    "Average revenue per order: Rs.",
    round(float(raw_with_revenue["revenue"].mean()), 2)
)
print("Duplicate revenue: Rs.", round(duplicate_revenue, 2))


# --------------------------------------------------
# 5. Clean orders
# --------------------------------------------------

cleaned = orders.copy()

cleaned["payment_method"] = (
    cleaned["payment_method"]
    .astype("string")
    .str.strip()
    .str.upper()
)

cleaned["quantity"] = pd.to_numeric(
    cleaned["quantity"], errors="raise"
)
cleaned["discount_pct"] = pd.to_numeric(
    cleaned["discount_pct"], errors="raise"
)
cleaned["rating"] = pd.to_numeric(
    cleaned["rating"], errors="raise"
)
cleaned["returned"] = pd.to_numeric(
    cleaned["returned"], errors="raise"
)

cleaned = cleaned.drop_duplicates(
    subset=duplicate_columns,
    keep="first"
).copy()

missing_discounts_filled = int(cleaned["discount_pct"].isnull().sum())
missing_ratings_filled = int(cleaned["rating"].isnull().sum())

cleaned["discount_pct"] = cleaned["discount_pct"].fillna(0)

rating_median = cleaned["rating"].median()
if pd.isna(rating_median):
    raise ValueError("Cannot impute ratings: every rating is missing.")

cleaned["rating"] = cleaned["rating"].fillna(rating_median)

# Convert ratings only if the source rating scale is integer-valued.
if (cleaned["rating"] % 1 == 0).all():
    cleaned["rating"] = cleaned["rating"].astype(int)

print("\n--- Cleaning summary ---")
print("Rows before cleaning:", len(orders))
print("Rows after cleaning:", len(cleaned))
print("Rows removed as duplicates:", len(orders) - len(cleaned))
print("Missing discounts filled:", missing_discounts_filled)
print("Missing ratings filled:", missing_ratings_filled)
print("Median rating used:", rating_median)

print("\n--- Missing values after cleaning ---")
print(cleaned.isnull().sum())

print("\n--- Standardized payment methods ---")
print(cleaned["payment_method"].value_counts())


# --------------------------------------------------
# 6. Revenue and return-rate findings
# --------------------------------------------------

cleaned_with_revenue = add_revenue(cleaned)

total_revenue = float(cleaned_with_revenue["revenue"].sum())
returned_orders = int(cleaned["returned"].sum())

overall_return_rate = (
    returned_orders / len(cleaned) * 100 if len(cleaned) else 0
)

payment_analysis = (
    cleaned_with_revenue
    .groupby("payment_method")
    .agg(
        orders=("order_id", "count"),
        returned_orders=("returned", "sum"),
        revenue=("revenue", "sum")
    )
)

payment_analysis["return_rate_pct"] = (
    payment_analysis["returned_orders"]
    / payment_analysis["orders"] * 100
)

print("\n--- Cleaned business metrics ---")
print("Cleaned orders:", len(cleaned))
print("Cleaned revenue: Rs.", round(total_revenue, 2))
print("Returned orders:", returned_orders)
print("Overall return rate (%):", round(overall_return_rate, 2))

print("\n--- Return rate by payment method ---")
print(payment_analysis.round(2))


# COD versus card hypothesis.
payment_results = {}
for method, row in payment_analysis.iterrows():
    payment_results[str(method)] = {
        "orders": int(row["orders"]),
        "returned_orders": int(row["returned_orders"]),
        "return_rate_pct": round(float(row["return_rate_pct"]), 2),
        "revenue": round(float(row["revenue"]), 2)
    }

if "COD" not in payment_results or "CARD" not in payment_results:
    raise ValueError("COD and CARD must both exist for the required comparison.")

cod_rate = payment_results["COD"]["return_rate_pct"]
card_rate = payment_results["CARD"]["return_rate_pct"]
cod_card_ratio = cod_rate / card_rate if card_rate else None

cod_card_hypothesis = {
    "hypothesis": "COD orders have a higher return rate than card orders.",
    "cod_return_rate_pct": cod_rate,
    "card_return_rate_pct": card_rate,
    "cod_to_card_rate_ratio": (
        round(cod_card_ratio, 2) if cod_card_ratio is not None else None
    ),
    "verdict": "Confirmed" if cod_rate > card_rate else "Not confirmed",
    "interpretation": (
        "COD has a higher observed return rate than card. "
        "This is an association and does not prove causation."
    )
}


# --------------------------------------------------
# 7. Customer city-tier segmentation
# --------------------------------------------------

if "city_tier" not in customers.columns:
    raise ValueError("customers.csv must contain the city_tier column.")

tier_data = cleaned.merge(
    customers[["customer_id", "city_tier"]],
    on="customer_id",
    how="left",
    validate="many_to_one",
    indicator=True
)

if (tier_data["_merge"] != "both").any():
    raise ValueError("Some orders do not match a customer in customers.csv.")

tier_data = tier_data.drop(columns="_merge")

cod_tier_data = tier_data[
    tier_data["payment_method"] == "COD"
].copy()

tier_analysis = (
    cod_tier_data
    .groupby("city_tier", dropna=False)
    .agg(
        orders=("order_id", "count"),
        returned_orders=("returned", "sum")
    )
)

tier_analysis["return_rate_pct"] = (
    tier_analysis["returned_orders"]
    / tier_analysis["orders"] * 100
)

tier_results = {}
for tier, row in tier_analysis.iterrows():
    tier_results[str(tier)] = {
        "orders": int(row["orders"]),
        "returned_orders": int(row["returned_orders"]),
        "return_rate_pct": round(float(row["return_rate_pct"]), 2)
    }

highest_risk_tier = None
if not tier_analysis.empty:
    highest_risk_tier = str(
        tier_analysis["return_rate_pct"].idxmax()
    )

print("\n--- COD return rate by city tier ---")
print(tier_analysis.round(2))
print("Highest-risk COD city tier:", highest_risk_tier)


# --------------------------------------------------
# 8. Correlation analysis: six unique pairs
# --------------------------------------------------

correlation_columns = [
    "rating", "returned", "discount_pct", "quantity"
]

correlation_data = cleaned[correlation_columns].apply(
    pd.to_numeric, errors="coerce"
)

correlation_matrix = correlation_data.corr(method="pearson")

# Interpret absolute correlation using conventional descriptive bands.
# These labels describe association strength, not statistical significance.
def correlation_strength(value):
    if pd.isna(value):
        return "Undefined"
    magnitude = abs(value)
    if magnitude < 0.10:
        return "Negligible"
    if magnitude < 0.30:
        return "Weak"
    if magnitude < 0.50:
        return "Moderate"
    return "Strong"


correlation_pairs = {}
for i, first in enumerate(correlation_columns):
    for second in correlation_columns[i + 1:]:
        value = correlation_matrix.loc[first, second]
        key = f"{first}_vs_{second}"

        correlation_pairs[key] = {
            "variable_1": first,
            "variable_2": second,
            "pearson_r": (
                round(float(value), 4) if pd.notna(value) else None
            ),
            "strength": correlation_strength(value),
            "direction": (
                "Positive" if value > 0 else
                "Negative" if value < 0 else
                "Zero" if pd.notna(value) else "Undefined"
            )
        }

print("\n--- Correlation matrix (Pearson) ---")
print(correlation_matrix.round(4))

print("\n--- Six unique correlation pairs ---")
for pair, result in correlation_pairs.items():
    print(
        pair,
        "| r =", result["pearson_r"],
        "|", result["strength"],
        "|", result["direction"]
    )

discount_return_r = correlation_matrix.loc["discount_pct", "returned"]

discount_return_hypothesis = {
    "hypothesis": "Higher discounts are associated with fewer returns.",
    "pearson_r": (
        round(float(discount_return_r), 4)
        if pd.notna(discount_return_r) else None
    ),
    "strength": correlation_strength(discount_return_r),
    "verdict": (
        "Busted"
        if pd.isna(discount_return_r) or abs(discount_return_r) < 0.30
        else "Potential association observed"
    ),
    "interpretation": (
        "The data does not show a meaningful linear relationship "
        "between discount percentage and returns."
        if pd.isna(discount_return_r) or abs(discount_return_r) < 0.30
        else
        "A linear association is present, but this does not establish causation."
    )
}


# --------------------------------------------------
# 9. Quantity outliers and sensitivity analysis
# --------------------------------------------------

q1 = cleaned["quantity"].quantile(0.25)
q3 = cleaned["quantity"].quantile(0.75)
iqr = q3 - q1

lower_bound = q1 - 1.5 * iqr
upper_bound = q3 + 1.5 * iqr

outliers = cleaned[
    (cleaned["quantity"] < lower_bound)
    | (cleaned["quantity"] > upper_bound)
].copy()

print("\n--- Quantity outlier check ---")
print("Q1:", q1)
print("Q3:", q3)
print("IQR:", iqr)
print("Lower bound:", lower_bound)
print("Upper bound:", upper_bound)
print("Flagged orders:")
print(outliers[["order_id", "quantity"]].to_string(index=False))

flagged_order_ids = outliers["order_id"].astype(str).tolist()

# Parse both ISO and day-first dates.
date_text = cleaned_with_revenue["order_date"].astype("string").str.strip()
parsed_dates = pd.to_datetime(
    date_text, format="%Y-%m-%d", errors="coerce"
)

day_first_mask = parsed_dates.isna() & date_text.notna()
parsed_dates.loc[day_first_mask] = pd.to_datetime(
    date_text.loc[day_first_mask],
    format="%d-%m-%Y",
    errors="coerce"
)

if parsed_dates.isna().any():
    invalid_dates = date_text[parsed_dates.isna()].drop_duplicates().tolist()
    raise ValueError(f"Unparseable order_date values: {invalid_dates}")

cleaned_with_revenue["order_date"] = parsed_dates
cleaned_with_revenue["month"] = (
    cleaned_with_revenue["order_date"].dt.to_period("M").astype(str)
)

monthly_revenue = (
    cleaned_with_revenue.groupby("month")["revenue"].sum().sort_index()
)

adjusted_orders = cleaned_with_revenue[
    ~cleaned_with_revenue["order_id"].astype(str).isin(flagged_order_ids)
].copy()

monthly_revenue_adjusted = (
    adjusted_orders.groupby("month")["revenue"].sum().sort_index()
)

full_peak_month = str(monthly_revenue.idxmax())
adjusted_peak_month = str(monthly_revenue_adjusted.idxmax())

print("\n--- Monthly cleaned revenue ---")
print(monthly_revenue.round(2))

print("\n--- Adjusted monthly revenue (outliers excluded for sensitivity) ---")
print(monthly_revenue_adjusted.round(2))

print("Full-data peak month:", full_peak_month)
print("Adjusted peak month:", adjusted_peak_month)


# --------------------------------------------------
# 10. Save findings for the narrator
# --------------------------------------------------

findings = {
    "source_counts": {
        "customers": int(len(customers)),
        "products": int(len(products)),
        "orders": int(len(orders))
    },
    "cleaning": {
        "duplicate_rows_removed": int(len(orders) - len(cleaned)),
        "duplicate_order_ids": duplicate_orders["order_id"].astype(str).tolist(),
        "orders_after_cleaning": int(len(cleaned)),
        "missing_discounts_filled": missing_discounts_filled,
        "missing_ratings_filled": missing_ratings_filled,
        "rating_median": float(rating_median)
    },
    "revenue": {
        "raw_revenue": round(raw_revenue, 2),
        "duplicate_revenue": round(duplicate_revenue, 2),
        "cleaned_revenue": round(total_revenue, 2),
        "reconciliation_difference": round(raw_revenue - total_revenue, 2),
        "reconciliation_matches_duplicate_revenue": bool(
            abs((raw_revenue - total_revenue) - duplicate_revenue) < 0.01
        )
    },
    "returns": {
        "returned_orders": returned_orders,
        "return_rate_pct": round(overall_return_rate, 2),
        "by_payment_method": payment_results,
        "cod_vs_card_hypothesis": cod_card_hypothesis
    },
    "cod_city_tier_analysis": {
        "by_tier": tier_results,
        "highest_risk_tier": highest_risk_tier
    },
    "correlation_analysis": {
        "method": "Pearson",
        "columns": correlation_columns,
        "matrix": {
            row: {
                col: (
                    round(float(correlation_matrix.loc[row, col]), 4)
                    if pd.notna(correlation_matrix.loc[row, col]) else None
                )
                for col in correlation_columns
            }
            for row in correlation_columns
        },
        "pairs": correlation_pairs,
        "discount_return_hypothesis": discount_return_hypothesis
    },
    "quantity_outliers": {
        "method": "IQR (1.5 times IQR)",
        "q1": float(q1),
        "q3": float(q3),
        "iqr": float(iqr),
        "lower_bound": float(lower_bound),
        "upper_bound": float(upper_bound),
        "flagged_orders": [
            {
                "order_id": str(row["order_id"]),
                "quantity": int(row["quantity"])
            }
            for _, row in outliers.iterrows()
        ],
        "flagged_order_ids": flagged_order_ids,
        "excluded_from_main_cleaned_data": False
    },
    "monthly_revenue": {
        month: round(float(value), 2)
        for month, value in monthly_revenue.items()
    },
    "adjusted_monthly_revenue": {
        month: round(float(value), 2)
        for month, value in monthly_revenue_adjusted.items()
    },
    "revenue_trend_interpretation": {
        "full_data_peak_month": full_peak_month,
        "full_data_peak_revenue": round(
            float(monthly_revenue.loc[full_peak_month]), 2
        ),
        "adjusted_peak_month": adjusted_peak_month,
        "adjusted_peak_revenue": round(
            float(monthly_revenue_adjusted.loc[adjusted_peak_month]), 2
        ),
        "flagged_orders_excluded_for_sensitivity": flagged_order_ids,
        "note": (
            "Outliers remain in the main cleaned data. The adjusted monthly "
            "series is a sensitivity analysis, not a replacement dataset."
        )
    }
}

findings_path = NARRATOR_DIR / "findings.json"

with open(findings_path, "w", encoding="utf-8") as file:
    json.dump(findings, file, indent=4, ensure_ascii=False)

print("\n--- Findings saved ---")
print(findings_path)
print("\nAnalysis complete.")

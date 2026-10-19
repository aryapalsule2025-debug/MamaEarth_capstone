


import json
import os
from pathlib import Path


# --------------------------------------------------
# 1. File paths and settings
# --------------------------------------------------

PROJECT_DIR = Path(__file__).resolve().parent.parent
NARRATOR_DIR = PROJECT_DIR / "narrator"
FINDINGS_PATH = NARRATOR_DIR / "findings.json"
OUTPUT_PATH = NARRATOR_DIR / "narrative.txt"
SAMPLE_OUTPUT_PATH = NARRATOR_DIR / "sample_output.txt"

MODEL_NAME = "gemini-2.5-flash"
REQUEST_TIMEOUT_MS = 15000
MAX_OUTPUT_TOKENS = 600


# --------------------------------------------------
# 2. Load verified findings
# --------------------------------------------------

def load_findings():
    """Load the verified analysis results from findings.json."""
    with open(FINDINGS_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


# --------------------------------------------------
# 3. Offline SCR narrative generator
# --------------------------------------------------

def generate_scr_narrative_offline(findings: dict) -> dict:
    """
    Generate a deterministic Situation, Complication, Resolution report.
    Uses verified findings only and requires no external API.
    """

    try:
        cleaning = findings["cleaning"]
        revenue = findings["revenue"]
        returns = findings["returns"]
        payment = returns["by_payment_method"]
        city_tier = findings["cod_city_tier_analysis"]
        correlation = findings["correlation_analysis"]
        discount_hypothesis = correlation["discount_return_hypothesis"]
        outliers = findings["quantity_outliers"]
        monthly = findings["monthly_revenue"]
        adjusted_monthly = findings["adjusted_monthly_revenue"]

        cod = payment["COD"]
        card = payment["CARD"]

        # Identify the peak months from both revenue views.
        peak_month = max(monthly, key=monthly.get)
        adjusted_peak_month = max(
            adjusted_monthly, key=adjusted_monthly.get
        )

        # Identify the highest-risk COD city tier.
        highest_risk_tier = city_tier["highest_risk_tier"]
        highest_tier = city_tier["by_tier"][str(highest_risk_tier)]

        
        discount_r = discount_hypothesis["pearson_r"]   


        lines = [
            "MAMAEARTH RETURNS & GROWTH INTELLIGENCE",
            "",
            "SITUATION",
            (
                "The dataset contains {0} original orders. After removing "
                "{1} duplicate business records, {2} orders remain for "
                "analysis. Cleaned revenue is Rs. {3:,.2f}, compared with "
                "raw revenue of Rs. {4:,.2f}."
            ).format(
                findings["source_counts"]["orders"],
                cleaning["duplicate_rows_removed"],
                cleaning["orders_after_cleaning"],
                revenue["cleaned_revenue"],
                revenue["raw_revenue"]
            ),
            (
                "The overall return rate is {0:.2f}% "
                "({1} returned orders out of {2} cleaned orders)."
            ).format(
                returns["return_rate_pct"],
                returns["returned_orders"],
                cleaning["orders_after_cleaning"]
            ),
            "",
            "COMPLICATION",
            (
                "COD has a return rate of {0:.2f}% ({1} of {2} orders), "
                "compared with {3:.2f}% for card payments ({4} of {5})."
            ).format(
                cod["return_rate_pct"],
                cod["returned_orders"],
                cod["orders"],
                card["return_rate_pct"],
                card["returned_orders"],
                card["orders"]
            ),
            (
                "Among COD orders, Tier {0} has the highest observed "
                "return rate at {1:.2f}% ({2} of {3} orders)."
            ).format(
                highest_risk_tier,
                highest_tier["return_rate_pct"],
                highest_tier["returned_orders"],
                highest_tier["orders"]
            ),
            (
                "Removing {0} duplicate records reduced calculated "
                "revenue by Rs. {1:,.2f}. Data cleaning also filled "
                "{2} missing discounts with zero and {3} missing ratings "
                "with the median rating of {4:.1f}."
            ).format(
                cleaning["duplicate_rows_removed"],
                revenue["duplicate_revenue"],
                cleaning["missing_discounts_filled"],
                cleaning["missing_ratings_filled"],
                cleaning["rating_median"]
            ),
            (
                "The discount-return correlation is {0:.4f}, classified "
                "as {1}. This indicates no meaningful linear relationship "
                "in this dataset; it does not establish causation."
            ).format(
                discount_r,
                discount_hypothesis["strength"].lower()
            ),
            (
                "Full-data revenue peaks in {0} at Rs. {1:,.2f}. "
                "In the adjusted sensitivity analysis, which excludes "
                "flagged quantity outliers, the peak shifts to {2} at "
                "Rs. {3:,.2f}."
            ).format(
                peak_month,
                monthly[peak_month],
                adjusted_peak_month,
                adjusted_monthly[adjusted_peak_month]
            ),
            (
                "The flagged orders are {0}. They remain in the main "
                "cleaned dataset; they are excluded only from the "
                "adjusted sensitivity analysis."
            ).format(", ".join(outliers["flagged_order_ids"])),
            "",
            "RESOLUTION",
            (
                "Investigate the COD order journey, particularly customer "
                "confirmation, delivery refusal, and recorded return "
                "reasons. Compare outcomes across city tiers before "
                "changing the payment or delivery process."
            ),
            (
                "Review the flagged bulk orders to determine whether "
                "they represent legitimate purchases or data-quality "
                "issues. Retain legitimate orders in the main analysis."
            ),
            (
                "Continue validating duplicate orders, missing values, "
                "and payment-method labels. Monitor return rates and "
                "monthly revenue over time before drawing conclusions."
            ),
            "",
            "Note: Observed associations do not prove cause and effect.",
        ]

        return {
            "status": "success",
            "narrative": "\n".join(lines),
            "tokens": 0
        }

    except Exception as error:
        return {
            "status": "error",
            "narrative": None,
            "message": str(error)
        }


# --------------------------------------------------
# 4. Gemini-powered SCR narrative generator
# --------------------------------------------------

def generate_scr_narrative(findings: dict) -> dict:
    """
    Generate an SCR report with Gemini.
    Return a structured success or error result.
    """

    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        return {
            "status": "error",
            "narrative": None,
            "message": "GEMINI_API_KEY is not set."
        }

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(
                timeout=REQUEST_TIMEOUT_MS
            )
        )

        system_instruction = """
You are a careful business data analyst writing for business stakeholders.

Produce a concise report with exactly these three main sections:
SITUATION, COMPLICATION, and RESOLUTION.

Situation: Establish the business and data context.
Complication: Explain the important risks and findings.
Resolution: Recommend practical, evidence-based next steps.

Rules:
- Use only facts and numerical values present in the supplied JSON.
- Do not invent statistics or fill in missing figures by guessing.
- Include cleaned revenue, duplicate revenue removed, the COD and card
  return rates, the highest-risk COD city tier, and the discount-return
  correlation finding when these are present in the data.
- Discuss full monthly revenue and adjusted sensitivity analysis.
- Clearly state that flagged quantity outliers remain in the main
  cleaned dataset and are excluded only from the adjusted analysis.
- Do not claim correlation proves causation.
- Keep the report concise, clear, and actionable.
- Do not include code or raw JSON in the report.
"""

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=(
                "Write the business report using these verified findings:\n"
                + json.dumps(findings, indent=2)
            ),
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0,
                max_output_tokens=MAX_OUTPUT_TOKENS
            )
        )

        narrative = response.text

        if not narrative or not narrative.strip():
            return {
                "status": "error",
                "narrative": None,
                "message": "Gemini returned an empty narrative."
            }

        usage = getattr(response, "usage_metadata", None)
        token_count = getattr(usage, "total_token_count", 0) or 0

        return {
            "status": "success",
            "narrative": narrative.strip(),
            "tokens": token_count
        }

    except Exception as error:
        return {
            "status": "error",
            "narrative": None,
            "message": str(error)
        }


# --------------------------------------------------
# 5. Save and display the report
# --------------------------------------------------

def main():
    findings = load_findings()

    result = generate_scr_narrative(findings)

    if result["status"] == "success":
        print("Narrative generated using Gemini.")
        print("Token count:", result.get("tokens", 0))
    else:
        print("Gemini unavailable:", result.get("message", "Unknown error"))
        print("Using the offline narrative generator.")

        result = generate_scr_narrative_offline(findings)

    if result["status"] != "success":
        raise RuntimeError(
            "Narrative generation failed: "
            + result.get("message", "Unknown error")
        )

    narrative = result["narrative"]

    # Save the main narrative and the required sample output.
    with open(OUTPUT_PATH, "w", encoding="utf-8") as file:
        file.write(narrative + "\n")

    with open(SAMPLE_OUTPUT_PATH, "w", encoding="utf-8") as file:
        file.write(narrative + "\n")

    print("\nNarrative saved to:")
    print(OUTPUT_PATH)
    print("\nSample output saved to:")
    print(SAMPLE_OUTPUT_PATH)
    print("\n--- Narrative preview ---")
    print(narrative)


if __name__ == "__main__":
    main()

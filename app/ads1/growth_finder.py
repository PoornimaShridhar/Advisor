import json
import pandas as pd
from app.recs.generate import generate_explanation, is_bad_llm_output

def build_growth_finder_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["cost"] = df["cost"].fillna(0)
    df["clicks"] = df["clicks"].fillna(0)
    df["impressions"] = df["impressions"].fillna(0)
    df["conversions"] = df.get("conversions", 0).fillna(0)

    # Core signals
    df["ctr"] = (df["clicks"] / df["impressions"].replace(0, 1)) * 100
    df["cvr"] = (df["conversions"] / df["clicks"].replace(0, 1)) * 100
    df["cpa"] = df["cost"] / df["conversions"].replace(0, 1)

    # Growth signal (IMPORTANT)
    df["efficiency_score"] = df["conversions"] / df["cost"].replace(0, 1)

    return df

def build_growth_finder_context(dfs: dict, campaign_name: str | None = None):
    df = dfs["keywords"].copy()

    if campaign_name and "campaign_name" in df.columns:
        df = df[df["campaign_name"] == campaign_name]

    df = build_growth_finder_features(df)

    # keep high-signal subset only (not rule-based, just signal control)
    df = df.sort_values("cost", ascending=False).head(200)

    return {
        "campaign_name": campaign_name,
        "keywords": df.to_dict("records")
    }

def build_growth_finder_prompt(context: dict) -> str:
    payload = json.dumps(context, indent=2, default=str)
    name = context.get("campaign_name", "this account")

    return (
            f"""
                Identify ONLY data-backed scaling opportunities.Suggest opportunities for growth, with evidence and action.
                DATA:
                {payload}
            """
    )

def run_growth_finder(dfs: dict, campaign_name: str | None = None) -> str:
    print("\n🚀 [growth_finder] STARTED", flush=True)

    if not dfs or "keywords" not in dfs:
        return "⚠️ No keyword data available."

    context = build_growth_finder_context(dfs, campaign_name)

    print("🧠 [growth_finder] context built", flush=True)

    prompt = build_growth_finder_prompt(context)

    print("✍️ [growth_finder] prompt built", flush=True)

    result = generate_explanation(prompt)

    if is_bad_llm_output(result):
        print("⚠️ [growth_finder] fallback triggered", flush=True)
        return (
            "- Unable to generate scaling opportunities right now.\n"
            "- Try again or check data quality."
        )

    print("📤 [growth_finder] result received", flush=True)
    return result
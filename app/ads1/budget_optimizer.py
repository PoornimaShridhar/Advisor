import json
import pandas as pd
from app.recs.generate import generate_explanation, is_bad_llm_output

def build_budget_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["cost"] = df["cost"].fillna(0)
    df["clicks"] = df["clicks"].fillna(0)
    df["impressions"] = df["impressions"].fillna(0)
    df["conversions"] = df.get("conversions", 0).fillna(0)

    # Core efficiency signals
    df["ctr"] = (df["clicks"] / df["impressions"].replace(0, 1)) * 100
    df["cpa"] = df["cost"] / df["conversions"].replace(0, 1)
    df["cpc"] = df["cost"] / df["clicks"].replace(0, 1)

    # Budget efficiency proxy (VERY important for reasoning)
    df["conv_per_cost"] = df["conversions"] / df["cost"].replace(0, 1)

    return df

def build_budget_optimizer_context(dfs: dict, campaign_name: str | None = None):
    df = dfs["campaigns"].copy()

    if campaign_name and "name" in df.columns:
        df = df[df["name"] == campaign_name]

    df = build_budget_features(df)

    # Keep top variance slice (NOT rule-based, just signal control)
    df = df.sort_values("cost", ascending=False).head(200)

    return {
        "campaign_name": campaign_name,
        "campaigns": df.to_dict("records")
    }

def build_budget_optimizer_prompt(context: dict) -> str:
    payload = json.dumps(context, indent=2, default=str)
    name = context.get("campaign_name", "this account")

    return (
        f"Write 3 to 5 bullet points of actionable Budget optimization insights for {name}.\n"
        "Use simple language. One insight per bullet. Start each line with '- '. No intro sentence.\n\n"
        f"Data (JSON):\n{payload}"
    )
    

def run_budget_optimizer(dfs: dict, campaign_name: str | None = None) -> str:
    print("\n🚀 [budget_optimizer] STARTED", flush=True)

    if not dfs or "campaigns" not in dfs:
        return "⚠️ No campaign data available."

    context = build_budget_optimizer_context(dfs, campaign_name)

    print("🧠 [budget_optimizer] context built", flush=True)

    prompt = build_budget_optimizer_prompt(context)

    print("✍️ [budget_optimizer] prompt built", flush=True)

    result = generate_explanation(prompt)

    if is_bad_llm_output(result):
        print("⚠️ [budget_optimizer] fallback triggered", flush=True)
        return (
            "- Unable to generate budget recommendations right now.\n"
            "- Try again or check campaign data quality."
        )

    print("📤 [budget_optimizer] result received", flush=True)
    return result
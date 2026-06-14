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
    if df.empty:
        return {
            "campaign_name": campaign_name,
            "budget_actions": [],
        }

    total_conversions = dfs["campaigns"]["conversions"].fillna(0).sum()
    account_cpa = dfs["campaigns"]["cost"].fillna(0).sum() / total_conversions if total_conversions else 0

    def action_for(row):
        if row["conversions"] == 0:
            return "Reduce or cap budget until conversion tracking and intent quality are fixed."
        if account_cpa and row["cpa"] <= account_cpa * 0.8:
            return "Increase budget cautiously because CPA is better than the account average."
        if account_cpa and row["cpa"] >= account_cpa * 1.25:
            return "Reduce budget or tighten bids because CPA is worse than the account average."
        return "Hold budget and monitor because efficiency is near the account average."

    df["budget_action"] = df.apply(action_for, axis=1)
    df["segment"] = "Campaign"
    df = df.sort_values(["conv_per_cost", "conversions"], ascending=[False, False]).head(8)

    keep_cols = [
        col
        for col in ["segment", "name", "cost", "clicks", "conversions", "ctr", "cpa", "cpc", "conv_per_cost", "budget_action"]
        if col in df.columns
    ]
    action_rows = df[keep_cols].copy()

    if "keywords" in dfs and not dfs["keywords"].empty:
        kw = dfs["keywords"].copy()
        if campaign_name and "campaign_name" in kw.columns:
            kw = kw[kw["campaign_name"] == campaign_name]
        if not kw.empty:
            kw = build_budget_features(kw)
            kw["name"] = "Keyword: " + kw["keyword"].astype(str)
            kw["segment"] = "Keyword"
            kw["budget_action"] = kw.apply(action_for, axis=1)
            kw = kw.sort_values(["conv_per_cost", "conversions", "cost"], ascending=[False, False, False]).head(6)
            kw_cols = [col for col in keep_cols if col in kw.columns]
            action_rows = pd.concat([action_rows, kw[kw_cols]], ignore_index=True)

    return {
        "campaign_name": campaign_name,
        "account_average_cpa": round(float(account_cpa), 2) if pd.notna(account_cpa) else 0,
        "budget_actions": action_rows.round(2).to_dict("records")
    }

def build_budget_optimizer_prompt(context: dict) -> str:
    payload = json.dumps(context, indent=2, default=str)
    name = context.get("campaign_name", "this account")

    return (
        f"Write 3 to 5 bullet points of actionable budget optimization insights for {name}.\n"
        "Use the budget_actions list only. Say where to increase, reduce, hold, or protect budget using cost, conversions, CPA, CPC, and conversion efficiency.\n"
        "Use simple language. One clear budget action per bullet. Start each line with '- '. No intro sentence.\n\n"
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

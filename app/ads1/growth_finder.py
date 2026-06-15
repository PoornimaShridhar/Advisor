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
    all_keywords = build_growth_finder_features(dfs["keywords"].copy())
    total_conversions = all_keywords["conversions"].sum()
    account_cpa = all_keywords["cost"].sum() / total_conversions if total_conversions else 0

    df = df[df["conversions"] > 0].copy()
    if account_cpa:
        df = df[(df["conversions"] >= 3) & (df["cpa"] <= account_cpa * 0.9)].copy()
    if df.empty:
        return {
            "campaign_name": campaign_name,
            "account_average_cpa": round(float(account_cpa), 2),
            "growth_candidates": [],
        }

    df = df.sort_values(
        ["efficiency_score", "conversions", "cvr"],
        ascending=[False, False, False],
    ).head(8)

    df["growth_action"] = "scale"

    keep_cols = [
        col
        for col in ["keyword", "cost", "clicks", "conversions", "ctr", "cvr", "cpa", "efficiency_score", "growth_action"]
        if col in df.columns
    ]

    return {
        "campaign_name": campaign_name,
        "account_average_cpa": round(float(account_cpa), 2),
        "growth_candidates": df[keep_cols].round(2).to_dict("records")
    }

def build_growth_finder_prompt(context: dict) -> str:
    payload = json.dumps(context, indent=2, default=str)
    name = context.get("campaign_name", "this account")

    return (
        f"Write 3 to 5 bullet points of actionable growth opportunities for {name}.\n"
        "Use the growth_candidates list only. Suggest ways to scale winners, expand related intent, or increase budget on efficient areas.\n"
        "Each bullet must mention the keyword, the growth action, and the evidence. Do not list weak keywords or diagnose poor performance.\n"
        "Use simple language. One self-contained growth opportunity per bullet. Start each line with '- '. No intro sentence. Do not quote JSON values by themselves.\n\n"
        f"Data (JSON):\n{payload}"
    )


def rule_based_growth_actions(context: dict) -> str:
    rows = context.get("growth_candidates", [])
    if not rows:
        account_cpa = context.get("account_average_cpa", 0)
        campaign_name = context.get("campaign_name", "this campaign")
        return (
            f"- No safe scale-up candidate found for {campaign_name} because its converting keywords are not efficient enough versus the account average CPA of {account_cpa}.\n"
            "- Improve growth readiness first by cutting weak intent, tightening match types, and waiting for lower CPA before increasing budget."
        )

    bullets = []
    for row in rows[:5]:
        keyword = row.get("keyword", "this keyword")
        conversions = row.get("conversions", 0)
        cpa = row.get("cpa", 0)
        cvr = row.get("cvr", 0)
        ctr = row.get("ctr", 0)
        bullets.append(
            f"- Scale '{keyword}' because it has {conversions} conversions at CPA {cpa:.2f}, CVR {cvr:.2f}%, and CTR {ctr:.2f}%; test a cautious bid or budget increase."
        )
    return "\n\n".join(bullets)

def run_growth_finder(dfs: dict, campaign_name: str | None = None) -> str:
    print("\n🚀 [growth_finder] STARTED", flush=True)

    if not dfs or "keywords" not in dfs:
        return "⚠️ No keyword data available."

    context = build_growth_finder_context(dfs, campaign_name)
    if not context.get("growth_candidates"):
        return rule_based_growth_actions(context)

    print("🧠 [growth_finder] context built", flush=True)

    prompt = build_growth_finder_prompt(context)

    print("✍️ [growth_finder] prompt built", flush=True)

    result = generate_explanation(prompt)

    if is_bad_llm_output(result) or not result.strip().startswith("-") or result.count('"') >= 4:
        print("⚠️ [growth_finder] fallback triggered", flush=True)
        return rule_based_growth_actions(context)

    print("📤 [growth_finder] result received", flush=True)
    return result

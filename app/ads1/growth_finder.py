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

    df = df[df["conversions"] > 0].sort_values(
        ["efficiency_score", "conversions", "ctr"],
        ascending=[False, False, False],
    ).head(20)
    keep_cols = [
        col
        for col in ["keyword", "cost", "clicks", "impressions", "conversions", "ctr", "cvr", "cpa", "efficiency_score"]
        if col in df.columns
    ]

    return {
        "campaign_name": campaign_name,
        "keywords": df[keep_cols].round(2).to_dict("records")
    }

def build_growth_finder_prompt(context: dict) -> str:
    payload = json.dumps(context, indent=2, default=str)
    name = context.get("campaign_name", "this account")

    return (
        f"Write 3 to 5 data-backed scaling opportunities for {name}.\n"
        "Return only markdown bullets. Start every line with '- '.\n"
        "Each bullet must follow this exact pattern:\n"
        "- Scale: '<keyword>' — Evidence: <conversions, CPA, CTR/CVR from data> — Action: <specific budget, bid, or match-type expansion>\n"
        "Only recommend scaling when conversions are greater than 0. If no scalable rows exist, say '- No scaling candidate — Evidence: no converting keyword rows — Action: fix tracking or demand quality first.'\n"
        "Use only supplied metrics. Do not infer ad groups. Do not repeat the prompt. Do not think aloud.\n\n"
        f"Data:\n{payload}"
    )


def rule_based_growth_actions(context: dict) -> str:
    rows = context.get("keywords", [])
    if not rows:
        return "- No scaling candidate — Evidence: no converting keyword rows — Action: fix tracking or demand quality before increasing budget."

    bullets = []
    for row in rows[:5]:
        keyword = row.get("keyword", "Unknown keyword")
        conversions = row.get("conversions", 0)
        cpa = row.get("cpa", 0)
        ctr = row.get("ctr", 0)
        bullets.append(
            f"- Scale: '{keyword}' — Evidence: {conversions} conversions, ${cpa:.2f} CPA, {ctr:.2f}% CTR — Action: test a small bid or budget increase while monitoring CPA."
        )
    return "\n\n".join(bullets)


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
        return rule_based_growth_actions(context)

    print("📤 [growth_finder] result received", flush=True)
    return result

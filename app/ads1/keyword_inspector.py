import json
import pandas as pd

from app.recs.generate import generate_explanation, is_bad_llm_output


# -------------------------
# Feature engineering only
# -------------------------
def build_keyword_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["cost"] = df["cost"].fillna(0)
    df["clicks"] = df["clicks"].fillna(0)
    df["impressions"] = df["impressions"].fillna(0)
    df["conversions"] = df.get("conversions", 0).fillna(0)

    df["ctr"] = (df["clicks"] / df["impressions"].replace(0, 1)) * 100
    df["cpa"] = df["cost"] / df["conversions"].replace(0, 1)

    return df


# -------------------------
# Prompt (simplified + stronger reasoning)
# -------------------------
def build_keyword_prompt(context: dict) -> str:
    payload = json.dumps(context, indent=2, default=str)

    return f"""
        You are a Google Ads keyword performance expert for preschool campaigns.

        TASK:
        Classify keywords into 3–5 insights.

        STRICT RULES:
        - Do NOT invent ad groups or missing fields.
        - Only use given keyword metrics.
        - No paragraphs. Only bullet format.

        OUTPUT FORMAT:
        - Keyword: <name>
        Label: Winning | Wasted Spend | Scale | Reduce | Investigate
        Evidence: <CTR, cost, conversions>
        Action: <specific bid or pause action>

        DATA:
        {payload}
        """
# -------------------------
# Main runner
# -------------------------
def run_keyword_inspector(dfs: dict, campaign_name: str | None = None) -> str:
    print("\n🚀 [keyword_inspector] STARTED", flush=True)

    if not dfs or "keywords" not in dfs:
        return "⚠️ No keyword data available."

    df = dfs["keywords"].copy()
    df = build_keyword_features(df)

    # optional campaign filter (safe, not destructive)
    if campaign_name and "campaign_name" in df.columns:
        df = df[df["campaign_name"] == campaign_name]

    context = {
        "campaign_name": campaign_name,
        "keywords": df.to_dict("records")  # FULL DATA given to LLM
    }

    print("🧠 [keyword_inspector] context built", flush=True)

    prompt = build_keyword_prompt(context)
    print("✍️ [keyword_inspector] prompt built", flush=True)

    result = generate_explanation(prompt)

    if is_bad_llm_output(result):
        print("⚠️ [keyword_inspector] LLM fallback triggered", flush=True)
        return (
            "- Unable to generate LLM insights right now.\n"
            "- Check keyword data quality or retry."
        )

    print("📤 [keyword_inspector] result received", flush=True)
    return result
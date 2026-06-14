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


def build_keyword_prompt(context: dict) -> str:
    payload = json.dumps(context, indent=2, default=str)

    return (
        "Write 3 to 5 keyword recommendations for a preschool Google Ads campaign.\n"
        "Return only markdown bullets. Start every line with '- '.\n"
        "Each bullet must follow this exact pattern:\n"
        "- <Label>: '<keyword>' — Evidence: <clicks, cost, conversions, CTR/CPA from data> — Action: <specific bid, pause, or scale action>\n"
        "Allowed labels: Winning, Wasted Spend, Scale, Reduce, Investigate.\n"
        "Use only supplied keyword metrics. Do not mention ad groups if ad group data is missing. Do not think aloud.\n\n"
        f"Data:\n{payload}"
    )


def rule_based_keyword_actions(context: dict) -> str:
    bullets = []
    for row in context.get("keywords", []):
        keyword = row.get("keyword", "Unknown keyword")
        cost = row.get("cost", 0)
        clicks = row.get("clicks", 0)
        conversions = row.get("conversions", 0)
        cpa = row.get("cpa", 0)
        if conversions > 0:
            bullets.append(
                f"- Winning: '{keyword}' — Evidence: {clicks} clicks, ${cost:.2f} cost, {conversions} conversions, ${cpa:.2f} CPA — Action: protect budget and test a modest bid increase."
            )
        elif cost > 0:
            bullets.append(
                f"- Wasted Spend: '{keyword}' — Evidence: {clicks} clicks, ${cost:.2f} cost, 0 conversions — Action: reduce bid or pause until intent is proven."
            )
        if len(bullets) >= 5:
            break
    return "\n\n".join(bullets) or "- Investigate: no keyword rows available — Evidence: no usable data — Action: verify keyword data sync."


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

    keep_cols = [
        col
        for col in ["keyword", "cost", "clicks", "impressions", "conversions", "ctr", "cpa"]
        if col in df.columns
    ]
    winners = df[df["conversions"] > 0].sort_values(["conversions", "cpa"], ascending=[False, True]).head(8)
    waste = df[df["conversions"] == 0].sort_values("cost", ascending=False).head(8)
    df = pd.concat([winners, waste], ignore_index=True)
    if "keyword" in df.columns:
        df = df.drop_duplicates(subset=["keyword"])
    df = df.head(20)

    context = {
        "campaign_name": campaign_name,
        "keywords": df[keep_cols].round(2).to_dict("records")
    }

    print("🧠 [keyword_inspector] context built", flush=True)

    prompt = build_keyword_prompt(context)
    print("✍️ [keyword_inspector] prompt built", flush=True)

    result = generate_explanation(prompt)

    if is_bad_llm_output(result):
        print("⚠️ [keyword_inspector] LLM fallback triggered", flush=True)
        return rule_based_keyword_actions(context)

    print("📤 [keyword_inspector] result received", flush=True)
    return result

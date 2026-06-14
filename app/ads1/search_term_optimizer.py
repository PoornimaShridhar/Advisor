import json
import pandas as pd
from app.recs.generate import generate_explanation, is_bad_llm_output

# -------------------------
# Feature engineering only
# -------------------------
def build_search_term_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["cost"] = df["cost"].fillna(0)
    df["clicks"] = df["clicks"].fillna(0)
    df["impressions"] = df["impressions"].fillna(0)

    if "conversions" not in df.columns:
        df["conversions"] = 0

    df["conversions"] = df["conversions"].fillna(0)

    # Core metrics
    df["ctr"] = (df["clicks"] / df["impressions"].replace(0, 1)) * 100
    df["cvr"] = (df["conversions"] / df["clicks"].replace(0, 1)) * 100
    df["cpc"] = df["cost"] / df["clicks"].replace(0, 1)
    df["cpa"] = df["cost"] / df["conversions"].replace(0, 1)

    return df


# -------------------------
# Optional: lightweight pruning (NOT rule-based logic)
# -------------------------
def prepare_context_df(df: pd.DataFrame, max_rows: int = 200) -> pd.DataFrame:
    """
    Instead of semantic filtering, we just cap size for token control.
    Keeps high-variance distribution intact.
    """
    return df.sort_values("cost", ascending=False).head(max_rows)

# -------------------------
# Prompt (LLM owns all reasoning now)
# -------------------------
def build_search_optimizer_prompt(context: dict) -> str:
    payload = json.dumps(context, indent=2, default=str)
    name = context.get("campaign_name", "this campaign")

    return (
        f"""
            You are a search term optimization specialist.

            TASK:
            Return 3–5 search term actions.

            STRICT RULES:
            - Only use provided search terms.
            - Do not compare unrelated terms.
            - No explanations longer than 1 sentence per bullet.

            OUTPUT FORMAT:
            - Search Term: <term>
            Category: Wasted Spend | High Intent | Scale | Negative Keyword Candidate
            Evidence: <cost, clicks, conversions>
            Action: <pause / scale / add as keyword / add as negative>

            DATA:
            {payload}
            """
    )

# -------------------------
# Context builder (FULL DATA approach)
# -------------------------
def build_search_optimizer_context(dfs: dict, campaign_name: str | None = None):
    df = dfs["search_terms"].copy()

    if campaign_name and "campaign_name" in df.columns:
        df = df[df["campaign_name"] == campaign_name]

    df = build_search_term_features(df)
    df = prepare_context_df(df)

    return {
        "campaign_name": campaign_name,
        "search_terms": df.to_dict("records")  # FULL dataset context (bounded)
    }


# -------------------------
# Runner
# -------------------------
def run_search_term_optimizer(dfs: dict, campaign_name: str | None = None) -> str:
    print("\n🚀 [search_term_optimizer] STARTED", flush=True)

    if not dfs or "search_terms" not in dfs:
        return "⚠️ No search term data — select a campaign first."

    context = build_search_optimizer_context(dfs, campaign_name)

    print("🧠 [search_term_optimizer] context built", flush=True)

    prompt = build_search_optimizer_prompt(context)

    print("✍️ [search_term_optimizer] prompt built", flush=True)

    result = generate_explanation(prompt)

    if is_bad_llm_output(result):
        print("⚠️ [search_term_optimizer] LLM fallback triggered", flush=True)
        return (
            "- Unable to generate insights right now.\n"
            "- Try again or check data quality."
        )

    print("📤 [search_term_optimizer] result received", flush=True)
    return result
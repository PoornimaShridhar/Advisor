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
        f"You are an expert Google Ads search term optimization strategist.\n\n"
        f"Analyze search term performance for {name}.\n\n"
        "Your job is to provide 3 to 5 actionable insights.\n"
        "Focus on:\n"
        "- wasted spend search terms\n"
        "- high intent converting terms\n"
        "- scaling opportunities\n"
        "- terms to pause or reduce bids\n"
        "- unusual CTR / CPA / conversion patterns\n\n"
        "Rules:\n"
        "- Be specific and actionable\n"
        "- Use simple language\n"
        "- One insight per bullet point\n"
        "- Start each line with '- '\n"
        "- No intro sentence, no summary, no JSON\n\n"
        f"Data:\n{payload}"
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
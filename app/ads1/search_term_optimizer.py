import pandas as pd
from app.recs.generate import TARGET_CPL, generate_explanation, is_bad_llm_output
import json

def build_search_term_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["cost"] = df["cost"].fillna(0)
    df["clicks"] = df["clicks"].fillna(0)
    df["impressions"] = df["impressions"].fillna(0)
    if "conversions" not in df.columns:
        df["conversions"] = 0

    df["conversions"] = df["conversions"].fillna(0)
    df["ctr"] = ((df["clicks"] / df["impressions"])*100).replace(0, 1)
    df["cvr"] = ((df["conversions"] / df["clicks"])*100).replace(0, 1)
    df["cpc"] = df["cost"] / df["clicks"].replace(0, 1)
    df["cpa"] = df["cost"] / df["conversions"].replace(0, 1)

    return df

def _search_terms_for_campaign(dfs: dict, campaign_name: str | None) -> pd.DataFrame:
    df = dfs["search_terms"].copy()
    if (campaign_name
        and "campaign_name" in df.columns):
            df = df[df["campaign_name"] == campaign_name]
    return df

def detect_negative_terms(df):
    return df[
        (df["clicks"] >= 20) &
        (df["cost"] >= 5) &
        (df["conversions"] == 0)
    ]

def detect_review_terms(df):
    return df[
        (df["clicks"] >= 10) &
        (df["ctr"] < 2) &
        (df["conversions"] == 0)
    ]

def detect_scaling_terms(df):
    return df[(df["conversions"] > 0)].sort_values("cpa", ascending=True)

# def classify_search_term(dfs: dict) -> dict:
#     df = dfs["search_terms"].copy()
#     df = build_search_term_features(df)

#     negatives = detect_negative_terms(df)
#     review = detect_review_terms(df)
#     winners = detect_scaling_terms(df)

#     return {
#         "negative_keywords": negatives.to_dict("records"),
#         "review_terms": review.to_dict("records"),
#         "winning_terms": winners.head(10).to_dict("records"),
#     }

def build_search_optimizer_prompt(context: dict) -> str:
    # Convert data to clean JSON string strings for better LLM readability
    neg_json = json.dumps(context['negative_keywords'], indent=2)
    rev_json = json.dumps(context['review_terms'], indent=2)
    win_json = json.dumps(context['winning_terms'], indent=2)

    return f"""You are an expert Google Ads optimization engine.
        Analyze the following three categories of search terms for the campaign "{context['campaign_name'] or 'All Campaigns'}":

        ### HIGH WASTE TERMS (Add as negatives)
        {neg_json}

        ### LOW CTR REVIEW TERMS (Needs attention)
        {rev_json}

        ### WINNING SCALING TERMS (Profitable)
        {win_json}

        Provide your analysis in a strict JSON format with this exact schema:
        {{
            "waste_reduction_actions": ["action 1", "action 2"],
            "scaling_opportunities": ["opportunity 1", "opportunity 2"],
            "immediate_negative_keywords": ["keyword 1", "keyword 2"]
        }}
        Return ONLY valid JSON. Do not include markdown code blocks, explanations, or extra text."""

def build_search_optimizer_context(dfs: dict, campaign_name: str | None = None):
    df = _search_terms_for_campaign(dfs, campaign_name)
    df = build_search_term_features(df)
    negatives = detect_negative_terms(df)
    review = detect_review_terms(df)
    winners = detect_scaling_terms(df)

    return {
        "campaign_name": campaign_name,
        "negative_keywords": negatives.head(10).to_dict("records"),
        "review_terms": review.head(10).to_dict("records"),
        "winning_terms": winners.head(10).to_dict("records"),
    }

def run_search_term_optimizer(dfs: dict,campaign_name: str | None = None) -> str:
    print("\n🚀 [search_term_card] STARTED", flush=True)
    if not dfs:
        return (
            "⚠️ No campaign data — "
            "select a campaign first."
        )
    context = build_search_optimizer_context(dfs,campaign_name)
    print("🧠 [search_term_card] context built",flush=True)
    prompt = build_search_optimizer_prompt(context)
    print("✍️ [search_term_card] prompt built",flush=True)
    result = generate_explanation(prompt)
    print("📤 [search_term_card] result received", flush=True)
    return result
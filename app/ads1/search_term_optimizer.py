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
    converters = df[df["conversions"] > 0].sort_values(["conversions", "cpa"], ascending=[False, True]).head(12)
    waste = df[df["conversions"] == 0].sort_values("cost", ascending=False).head(12)
    high_intent = df[(df["conversions"] > 0) & (df["cvr"] > 0)].sort_values("cvr", ascending=False).head(8)
    out = pd.concat([converters, waste, high_intent], ignore_index=True)
    if "search_term" in out.columns:
        out = out.drop_duplicates(subset=["search_term"])
    return out.head(max_rows)

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


def build_search_optimizer_prompt(context: dict) -> str:
    payload = json.dumps(context, indent=2, default=str)
    name = context.get("campaign_name", "this campaign")

    return (
        f"Write 3 to 5 search term optimization actions for {name}.\n"
        "Return only markdown bullets. Start every line with '- '.\n"
        "Each bullet must follow this exact pattern:\n"
        "- <Category>: '<search term>' — Evidence: <cost, clicks, conversions, CPA/CVR from data> — Action: <pause, reduce bid, add as keyword, or add as negative>\n"
        "Allowed categories: Wasted Spend, High Intent, Scale, Negative Keyword Candidate, Investigate.\n"
        "Use only supplied search terms. Do not explain calculations. Do not repeat the prompt. Do not think aloud.\n\n"
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
    keep_cols = [
        col
        for col in ["search_term", "cost", "clicks", "impressions", "conversions", "ctr", "cvr", "cpc", "cpa"]
        if col in df.columns
    ]

    return {
        "campaign_name": campaign_name,
        "search_terms": df[keep_cols].round(2).to_dict("records")
    }


def rule_based_search_actions(context: dict) -> str:
    bullets = []
    for row in context.get("search_terms", []):
        term = row.get("search_term", "Unknown term")
        cost = row.get("cost", 0)
        clicks = row.get("clicks", 0)
        conversions = row.get("conversions", 0)
        cvr = row.get("cvr", 0)
        if conversions > 0:
            bullets.append(
                f"- High Intent: '{term}' — Evidence: {clicks} clicks, ${cost:.2f} cost, {conversions} conversions, {cvr:.2f}% CVR — Action: add as keyword and test higher bid."
            )
        elif cost > 0:
            bullets.append(
                f"- Wasted Spend: '{term}' — Evidence: {clicks} clicks, ${cost:.2f} cost, 0 conversions — Action: reduce bid or add as negative if intent is poor."
            )
        if len(bullets) >= 5:
            break
    return "\n\n".join(bullets) or "- Investigate: no search terms available — Evidence: no usable rows — Action: verify search term data sync."


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
        return rule_based_search_actions(context)

    print("📤 [search_term_optimizer] result received", flush=True)
    return result

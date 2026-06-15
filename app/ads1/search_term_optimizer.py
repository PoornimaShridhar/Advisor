import json
import pandas as pd
from app.recs.generate import generate_explanation, is_bad_llm_output
from app.ads1.prompt_templates import search_term_cleaner_prompt

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
    waste = df[df["conversions"] == 0].sort_values("cost", ascending=False).head(10)
    converters = df[df["conversions"] > 0].sort_values(["conversions", "cpa"], ascending=[False, True]).head(10)
    return pd.concat([waste, converters], ignore_index=True).drop_duplicates(subset=["search_term"]).head(max_rows)

# -------------------------
# Prompt (LLM owns all reasoning now)
# -------------------------
def build_search_optimizer_prompt(context: dict) -> str:
    payload = json.dumps(context, indent=2, default=str)
    name = context.get("campaign_name", "this campaign")

    return (
        f"""
            Return 3–5 search term actions for given campaign data.

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

    return search_term_cleaner_prompt(name, payload)


# -------------------------
# Context builder (FULL DATA approach)
# -------------------------
def build_search_optimizer_context(dfs: dict, campaign_name: str | None = None):
    df = dfs["search_terms"].copy()

    if campaign_name and "campaign_name" in df.columns:
        df = df[df["campaign_name"] == campaign_name]

    df = build_search_term_features(df)
    df = prepare_context_df(df)
    df["action_type"] = df.apply(
        lambda row: "add as keyword or scale" if row["conversions"] > 0 else "pause or add as negative",
        axis=1,
    )
    df = df.rename(columns={"cost": "total_cost"})
    keep_cols = [
        col
        for col in ["search_term", "action_type", "total_cost", "clicks", "impressions", "conversions", "ctr", "cvr", "cpc", "cpa"]
        if col in df.columns
    ]

    return {
        "campaign_name": campaign_name,
        "search_terms": df[keep_cols].round(2).to_dict("records")
    }


def rule_based_search_actions(context: dict) -> str:
    rows = context.get("search_terms", [])
    if not rows:
        return "- No search term cleanup action found because no usable search term rows were available."

    bullets = []
    for row in rows[:5]:
        term = row.get("search_term", "this search term")
        total_cost = row.get("total_cost", 0)
        clicks = row.get("clicks", 0)
        conversions = row.get("conversions", 0)
        cpa = row.get("cpa", 0)
        cvr = row.get("cvr", 0)
        if conversions > 0:
            bullets.append(
                f"- Add or scale '{term}' because it produced {conversions} conversions from {clicks} clicks at CPA {cpa:.2f} and CVR {cvr:.2f}% on {total_cost:.2f} total spend."
            )
        else:
            bullets.append(
                f"- Pause or add '{term}' as a negative because it spent {total_cost:.2f} across {clicks} clicks with 0 conversions."
            )
    return "\n\n".join(bullets)


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

    if is_bad_llm_output(result) or not result.strip().startswith("-") or "cost is" in result.lower():
        print("⚠️ [search_term_optimizer] LLM fallback triggered", flush=True)
        return rule_based_search_actions(context)

    print("📤 [search_term_optimizer] result received", flush=True)
    return result

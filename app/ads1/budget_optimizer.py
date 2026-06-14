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

    keep_cols = [
        col
        for col in ["name", "cost", "clicks", "impressions", "conversions", "ctr", "cpa", "cpc", "conv_per_cost"]
        if col in df.columns
    ]
    df = df.sort_values(["conversions", "conv_per_cost", "cost"], ascending=[False, False, False]).head(15)

    return {
        "campaign_name": campaign_name,
        "campaigns": df[keep_cols].round(2).to_dict("records")
    }

def build_budget_optimizer_prompt(context: dict) -> str:
    payload = json.dumps(context, indent=2, default=str)
    name = context.get("campaign_name", "this account")

    return (
        f"""
        You are a Google Ads budget optimizer.

        TASK:
        Identify 3–5 budget allocation actions for the campaign {name}.

        STRICT RULES:
        - Use only provided data.
        - Do not explain categories (no "keywords/ad groups...")
        - No repetition of headings or prompt structure.
        - Avoid generic advice.

        OUTPUT FORMAT:
        - Action: <what to change in budget>
        Evidence: <metrics>
        Expected impact: <why it helps>

        DATA:
        {payload}
        """
        )
    

def build_budget_optimizer_prompt(context: dict) -> str:
    payload = json.dumps(context, indent=2, default=str)
    name = context.get("campaign_name", "this account")

    return (
        f"Write 3 to 5 budget allocation recommendations for {name}.\n"
        "Return only markdown bullets. Start every line with '- '.\n"
        "Each bullet must follow this exact pattern:\n"
        "- <budget action> — Evidence: <cost, conversions, CPA/CPC/CTR from data> — Expected impact: <short outcome>\n"
        "Use only the supplied campaign metrics. Do not repeat the prompt or data. Do not invent missing campaigns.\n"
        "If there is only one campaign, recommend within-campaign caution instead of cross-campaign reallocation.\n\n"
        f"Data:\n{payload}"
    )


def rule_based_budget_actions(context: dict) -> str:
    rows = context.get("campaigns", [])
    if not rows:
        return "- Hold budget — Evidence: no campaign rows available — Expected impact: prevents blind budget changes until data sync is fixed."

    bullets = []
    for row in rows[:5]:
        name = row.get("name") or context.get("campaign_name") or "Selected campaign"
        cost = row.get("cost", 0)
        conversions = row.get("conversions", 0)
        cpa = row.get("cpa", 0)
        if conversions > 0:
            bullets.append(
                f"- Protect budget on {name} — Evidence: ${cost:.2f} cost, {conversions} conversions, ${cpa:.2f} CPA — Expected impact: keeps spend on proven demand."
            )
        else:
            bullets.append(
                f"- Cap budget on {name} — Evidence: ${cost:.2f} cost and 0 conversions — Expected impact: limits wasted spend while tracking or targeting is reviewed."
            )
    return "\n\n".join(bullets[:5])


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
        return rule_based_budget_actions(context)

    print("📤 [budget_optimizer] result received", flush=True)
    return result

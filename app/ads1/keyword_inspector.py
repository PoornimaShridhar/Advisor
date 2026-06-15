import json
import pandas as pd

from app.recs.generate import generate_explanation, is_bad_llm_output
from app.ads1.prompt_templates import keyword_inspector_prompt


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


def prepare_keyword_context_df(df: pd.DataFrame, max_rows: int = 20) -> pd.DataFrame:
    winners = df[df["conversions"] > 0].sort_values(["conversions", "cpa"], ascending=[False, True]).head(10)
    waste = df[df["conversions"] == 0].sort_values("cost", ascending=False).head(10)
    out = pd.concat([waste, winners], ignore_index=True)
    if "keyword" in out.columns:
        out = out.drop_duplicates(subset=["keyword"])
    return out.head(max_rows)


# -------------------------
# Prompt (simplified + stronger reasoning)
# -------------------------
def build_keyword_prompt(context: dict) -> str:
    payload = json.dumps(context, indent=2, default=str)

    return keyword_inspector_prompt(payload)


def rule_based_keyword_actions(context: dict) -> str:
    rows = context.get("keywords", [])
    if not rows:
        return "- No keyword action found because no usable keyword rows were available."

    bullets = []
    for row in rows[:5]:
        keyword = row.get("keyword", "this keyword")
        cost = row.get("cost", 0)
        clicks = row.get("clicks", 0)
        conversions = row.get("conversions", 0)
        ctr = row.get("ctr", 0)
        cpa = row.get("cpa", 0)
        if conversions > 0:
            bullets.append(
                f"- Treat '{keyword}' as a winning or scaling keyword because it produced {conversions} conversions at CPA {cpa:.2f} and CTR {ctr:.2f}%."
            )
        else:
            bullets.append(
                f"- Reduce or pause '{keyword}' because it spent {cost:.2f} across {clicks} clicks with 0 conversions."
            )
    return "\n\n".join(bullets)


# -------------------------
# Main runner
# -------------------------
def run_keyword_inspector(dfs: dict, campaign_name: str | None = None) -> str:
    print("\nSTART [keyword_inspector] STARTED", flush=True)

    if not dfs or "keywords" not in dfs:
        return "WARNING: No keyword data available."

    df = dfs["keywords"].copy()
    df = build_keyword_features(df)

    # optional campaign filter (safe, not destructive)
    if campaign_name and "campaign_name" in df.columns:
        df = df[df["campaign_name"] == campaign_name]

    df = prepare_keyword_context_df(df)
    keep_cols = [
        col
        for col in ["keyword", "cost", "clicks", "impressions", "conversions", "ctr", "cpa"]
        if col in df.columns
    ]

    context = {
        "campaign_name": campaign_name,
        "keywords": df[keep_cols].round(2).to_dict("records")
    }

    print("CONTEXT [keyword_inspector] context built", flush=True)

    prompt = build_keyword_prompt(context)
    print("PROMPT [keyword_inspector] prompt built", flush=True)

    result = generate_explanation(prompt)
    print(f"[keyword_inspector] raw/clean LLM result preview: {str(result)[:400]}", flush=True)
    if "Analysis failed:" in str(result):
        print("[keyword_inspector] LLM call failed; returning the backend error instead of hiding it.", flush=True)
        return result


    if is_bad_llm_output(result) or not result.strip().startswith("-"):
        print("WARNING [keyword_inspector] LLM fallback triggered", flush=True)
        return rule_based_keyword_actions(context)

    print("RESULT [keyword_inspector] result received", flush=True)
    return result

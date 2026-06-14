import pandas as pd
import json

def build_campaign_table(dfs: dict) -> pd.DataFrame:
    df = dfs["campaigns"].copy()

    df["cost"] = df["cost"].fillna(0)
    df["clicks"] = df["clicks"].fillna(0)
    df["conversions"] = df["conversions"].fillna(0)
    df["impressions"] = df["impressions"].fillna(0)

    df["ctr"] = df["clicks"] / df["impressions"].replace(0, 1)
    df["cpl"] = df["cost"] / df["conversions"].replace(0, 1)
    df["conv_per_cost"] = df["conversions"] / df["cost"].replace(0, 1)

    return df

def score_campaigns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # normalize-safe scoring components
    df["eff_score"] = df["conv_per_cost"]
    df["eff_score"] = df["eff_score"].fillna(0)

    df["cpl_score"] = 1 / df["cpl"].replace(0, 1)
    df["cpl_score"] = df["cpl_score"].fillna(0)

    df["volume_score"] = df["conversions"]

    # final blended score (simple + stable)
    df["final_score"] = (
        df["eff_score"] * 0.5 +
        df["cpl_score"] * 0.3 +
        df["volume_score"] * 0.2
    )

    return df

def extract_campaign_insights(df: pd.DataFrame):
    df = score_campaigns(df)

    if df.empty:
        return None

    best = df.sort_values("final_score", ascending=False).iloc[0]
    worst = df.sort_values("final_score", ascending=True).iloc[0]

    # scale candidate = good efficiency but not top spender yet
    scale_pool = df[
        (df["conversions"] > 0)
    ].sort_values("eff_score", ascending=False)

    scale = scale_pool.iloc[0] if not scale_pool.empty else best

    return {
        "best": best.to_dict(),
        "worst": worst.to_dict(),
        "scale": scale.to_dict()
    }

def run_campaign_doctor(dfs: dict) -> dict:
    print("\n🧠 [campaign_doctor] STARTED", flush=True)

    if not dfs or "campaigns" not in dfs:
        return {
            "best_campaign": None,
            "budget_drain": None,
            "scale_candidate": None
        }

    df = build_campaign_table(dfs)
    insights = extract_campaign_insights(df)

    if not insights:
        return {
            "best_campaign": None,
            "budget_drain": None,
            "scale_candidate": None
        }

    best = insights["best"]
    worst = insights["worst"]
    scale = insights["scale"]

    result = {
        "best_campaign": {
            "name": best["name"],
            "reason": "Strongest efficiency and conversion performance relative to spend"
        },
        "budget_drain": {
            "name": worst["name"],
            "reason": "High spend with weak conversion output and poor return efficiency"
        },
        "scale_candidate": {
            "name": scale["name"],
            "reason": "High conversion efficiency suggests strong potential for scaling"
        }
    }

    print("📤 [campaign_doctor] result generated", flush=True)
    return result
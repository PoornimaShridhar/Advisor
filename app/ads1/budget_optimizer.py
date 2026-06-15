import pandas as pd

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
    if df.empty:
        return {
            "campaign_name": campaign_name,
            "budget_actions": [],
        }

    total_conversions = dfs["campaigns"]["conversions"].fillna(0).sum()
    account_cpa = dfs["campaigns"]["cost"].fillna(0).sum() / total_conversions if total_conversions else 0

    def action_type_for(row):
        if row["conversions"] == 0:
            return "reduce"
        if account_cpa and row["cpa"] <= account_cpa * 0.8:
            return "increase"
        if account_cpa and row["cpa"] >= account_cpa * 1.25:
            return "reduce"
        return "hold"

    df["budget_action"] = df.apply(action_type_for, axis=1)
    df["segment"] = "Campaign"
    df = df.sort_values(["conv_per_cost", "conversions"], ascending=[False, False]).head(8)

    keep_cols = [
        col
        for col in ["segment", "name", "cost", "clicks", "conversions", "ctr", "cpa", "cpc", "conv_per_cost", "budget_action"]
        if col in df.columns
    ]
    action_rows = df[keep_cols].copy()

    if "keywords" in dfs and not dfs["keywords"].empty:
        kw = dfs["keywords"].copy()
        if campaign_name and "campaign_name" in kw.columns:
            kw = kw[kw["campaign_name"] == campaign_name]
        if not kw.empty:
            kw = build_budget_features(kw)
            kw["name"] = "Keyword: " + kw["keyword"].astype(str)
            kw["segment"] = "Keyword"
            kw["budget_action"] = kw.apply(action_type_for, axis=1)
            kw = kw.sort_values(["conv_per_cost", "conversions", "cost"], ascending=[False, False, False]).head(6)
            kw_cols = [col for col in keep_cols if col in kw.columns]
            action_rows = pd.concat([action_rows, kw[kw_cols]], ignore_index=True)

    return {
        "campaign_name": campaign_name,
        "account_average_cpa": round(float(account_cpa), 2) if pd.notna(account_cpa) else 0,
        "budget_actions": action_rows.round(2).to_dict("records")
    }

def rule_based_budget_actions(context: dict) -> str:
    rows = context.get("budget_actions", [])
    if not rows:
        return "- Hold budget for this campaign because no usable budget rows were found; verify campaign and keyword data before changing spend."

    bullets = []
    for row in rows[:5]:
        name = row.get("name", "this segment")
        action = row.get("budget_action", "hold")
        cost = row.get("cost", 0)
        conversions = row.get("conversions", 0)
        cpa = row.get("cpa", 0)
        cpc = row.get("cpc", 0)
        conv_per_cost = row.get("conv_per_cost", 0)

        if action == "increase":
            bullets.append(
                f"- Increase budget cautiously on {name} because it has {conversions} conversions at CPA {cpa:.2f}, CPC {cpc:.2f}, and conversion efficiency {conv_per_cost:.3f} on {cost:.2f} spend."
            )
        elif action == "reduce":
            bullets.append(
                f"- Reduce or cap budget on {name} because it has {conversions} conversions at CPA {cpa:.2f} after {cost:.2f} spend, making it a weaker use of budget."
            )
        else:
            bullets.append(
                f"- Hold budget on {name} because performance is near benchmark with {conversions} conversions, CPA {cpa:.2f}, and CPC {cpc:.2f}."
            )
    return "\n\n".join(bullets)
    

def run_budget_optimizer(dfs: dict, campaign_name: str | None = None) -> str:
    print("\n🚀 [budget_optimizer] STARTED", flush=True)

    if not dfs or "campaigns" not in dfs:
        return "⚠️ No campaign data available."

    context = build_budget_optimizer_context(dfs, campaign_name)
    print("🧠 [budget_optimizer] context built", flush=True)
    return rule_based_budget_actions(context)

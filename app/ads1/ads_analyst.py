import json

import pandas as pd

from app.recs.generate import TARGET_CPL, generate_explanation, is_bad_llm_output

# -------------------------
# 1. DATA BUILDERS
# -------------------------


def _dfs_for_campaign(dfs: dict, campaign_name: str | None) -> dict:
    if not campaign_name:
        return dfs
    out = dict(dfs)
    out["campaigns"] = dfs["campaigns"][dfs["campaigns"]["name"] == campaign_name]
    if "keywords" in dfs and "campaign_name" in dfs["keywords"].columns:
        out["keywords"] = dfs["keywords"][dfs["keywords"]["campaign_name"] == campaign_name]
    return out


def build_campaign_snapshot(dfs: dict) -> dict:
    df = dfs["campaigns"]
    if df.empty:
        return {
            "spend": 0.0,
            "clicks": 0,
            "impressions": 0,
            "leads": 0,
            "ctr": 0.0,
            "cpl": 0.0,
        }

    total_spend = df["cost"].sum()
    total_clicks = df["clicks"].sum()
    total_impr = df["impressions"].sum()
    total_leads = df["conversions"].sum()

    ctr = (total_clicks / total_impr * 100) if total_impr else 0
    cpl = (total_spend / total_leads) if total_leads else 0

    return {
        "spend": round(float(total_spend), 2),
        "clicks": int(total_clicks),
        "impressions": int(total_impr),
        "leads": int(total_leads),
        "ctr": round(float(ctr), 2),
        "cpl": round(float(cpl), 2),
    }


def build_simple_trend(df_hourly: pd.DataFrame) -> dict:
    if df_hourly.empty:
        return {"spend_change_pct": 0.0, "clicks_change_pct": 0.0, "impressions_change_pct": 0.0}

    df = df_hourly.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    mid = max(len(df) // 2, 1)
    first, second = df.iloc[:mid], df.iloc[mid:]

    def agg(x):
        return {
            "cost": x["cost"].sum(),
            "clicks": x["clicks"].sum(),
            "impressions": x["impressions"].sum(),
        }

    a, b = agg(first), agg(second)

    def pct(old, new):
        return ((new - old) / old * 100) if old else 0

    return {
        "spend_change_pct": round(pct(a["cost"], b["cost"]), 1),
        "clicks_change_pct": round(pct(a["clicks"], b["clicks"]), 1),
        "impressions_change_pct": round(pct(a["impressions"], b["impressions"]), 1),
    }


def build_top_drivers(dfs: dict) -> dict:
    kw = dfs["keywords"].copy()
    if kw.empty:
        return {"best_keywords": [], "worst_keywords": []}

    kw["cpl"] = kw["cost"] / kw["conversions"].replace(0, 1)

    worst = kw.sort_values("cpl", ascending=False).head(3)
    best = kw[kw["conversions"] > 0].sort_values("cpl", ascending=True).head(3)

    return {
        "best_keywords": best[["keyword", "cpl", "conversions"]].to_dict("records"),
        "worst_keywords": worst[["keyword", "cpl", "conversions"]].to_dict("records"),
    }


def build_signals(dfs: dict) -> dict:
    kw = dfs["keywords"].copy()
    if kw.empty:
        return {"low_ctr_ratio": 0.0, "wasted_spend_ratio": 0.0}

    kw["ctr"] = kw["clicks"] / kw["impressions"].replace(0, 1)

    return {
        "low_ctr_ratio": round(float((kw["ctr"] < 0.02).mean()), 2),
        "wasted_spend_ratio": round(float((kw["conversions"] == 0).mean()), 2),
    }


# -------------------------
# 2. CONTEXT BUILDER
# -------------------------


def build_ads_analyst_context(dfs: dict, campaign_name: str | None = None) -> dict:
    ctx = {
        "campaign": build_campaign_snapshot(dfs),
        "trend": build_simple_trend(dfs["hourly"]),
        "top_drivers": build_top_drivers(dfs),
        "signals": build_signals(dfs),
    }
    if campaign_name:
        ctx["campaign_name"] = campaign_name
    return ctx


# -------------------------
# 3. PROMPT + FALLBACK
# -------------------------


def build_ads_analyst_prompt(context: dict) -> str:
    payload = json.dumps(context, indent=2, default=str)
    name = context.get("campaign_name", "this campaign")
    return (
        f"Write 3 to 5 executive Google Ads recommendations for {name}.\n"
        "Return only markdown bullets. Start every line with '- '.\n"
        "Each bullet must follow this exact pattern:\n"
        "- <finding> — Evidence: <specific metric from data> — Action: <specific next step>\n"
        "Do not restate the campaign name, raw data, prompt, task, or JSON keys.\n"
        "Do not think aloud. Do not say what you can calculate. Do not invent causes.\n"
        "If leads are 0, focus on conversion tracking, landing-page quality, and wasted spend risk.\n\n"
        f"Data:\n{payload}"
    )


def rule_based_insights(context: dict) -> str:
    c = context["campaign"]
    trend = context["trend"]
    signals = context["signals"]
    drivers = context["top_drivers"]
    bullets: list[str] = []

    if c["leads"] == 0:
        bullets.append("- No conversions recorded — review targeting, landing page, and conversion tracking.")
    elif c["cpl"] > TARGET_CPL:
        bullets.append(
            f"- CPL is ${c['cpl']:.2f}, above the ${TARGET_CPL:.0f} target — tighten bids on expensive terms."
        )
    else:
        bullets.append(f"- CPL is ${c['cpl']:.2f} with {c['leads']} leads — performance is within a workable range.")

    if trend["spend_change_pct"] > 10 and trend["clicks_change_pct"] < trend["spend_change_pct"]:
        bullets.append("- Spend is rising faster than clicks — efficiency is slipping; audit keyword bids.")

    if signals["wasted_spend_ratio"] > 0.2:
        bullets.append(
            f"- About {signals['wasted_spend_ratio'] * 100:.0f}% of keywords have zero conversions — pause or cut budget there."
        )

    for row in drivers.get("best_keywords", [])[:1]:
        bullets.append(
            f"- '{row['keyword']}' is a top performer ({row['conversions']} conversions) — consider scaling budget."
        )

    for row in drivers.get("worst_keywords", [])[:1]:
        if row.get("conversions", 0) == 0:
            bullets.append(f"- '{row['keyword']}' spent without converting — reduce bids or pause.")

    if len(bullets) < 3:
        bullets.append(f"- CTR is {c['ctr']:.2f}% across {c['impressions']:,} impressions — test stronger ad copy if CTR is low.")

    return "\n\n".join(bullets[:5])


def run_ads_analyst_card(dfs: dict, campaign_name: str | None = None) -> str:
    print("\n🚀 [analyst_card] STARTED", flush=True)

    if not dfs:
        return "⚠️ No campaign data — select a campaign on the Dashboard tab first."

    scoped = _dfs_for_campaign(dfs, campaign_name)
    context = build_ads_analyst_context(scoped, campaign_name)
    print("🧠 [analyst_card] context built", flush=True)

    prompt = build_ads_analyst_prompt(context)
    print("✍️ [analyst_card] prompt built", flush=True)

    result = generate_explanation(prompt)
    if is_bad_llm_output(result):
        print("⚠️ [analyst_card] LLM fallback — using rule-based insights", flush=True)
        result = rule_based_insights(context)

    print("\n📤 [analyst_card] LLM result received", flush=True)
    return result

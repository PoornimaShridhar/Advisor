import json

from app.recs.generate import generate_explanation, is_bad_llm_output


def build_campaign_summary(dfs: dict) -> dict:
    df = dfs["keywords"]

    total_cost = df["cost"].sum()
    total_conv = df["conversions"].sum()

    avg_cpl = total_cost / total_conv if total_conv > 0 else 0

    return {
        "total_spend": round(float(total_cost), 2),
        "total_conversions": int(total_conv),
        "avg_cpl": round(float(avg_cpl), 2),
    }


def build_scale_candidates(dfs: dict):
    kw = dfs["keywords"].copy()
    if kw.empty:
        return []

    kw["cpl"] = kw["cost"] / kw["conversions"].replace(0, 1)

    account_avg = kw["cost"].sum() / max(kw["conversions"].sum(), 1)

    winners = kw[(kw["conversions"] > 0) & (kw["cpl"] < account_avg * 0.7)]
    winners = winners.sort_values("conversions", ascending=False)

    return winners.head(3)[["keyword", "ad_group_name", "cpl", "conversions"]].to_dict("records")


def build_cut_candidates(dfs: dict):
    kw = dfs["keywords"].copy()
    if kw.empty:
        return []

    kw["cpl"] = kw["cost"] / kw["conversions"].replace(0, 1)

    account_avg = kw["cost"].sum() / max(kw["conversions"].sum(), 1)

    losers = kw[(kw["cost"] > 0) & ((kw["conversions"] == 0) | (kw["cpl"] > account_avg * 1.5))]
    losers = losers.sort_values("cost", ascending=False)

    return losers.head(3)[["keyword", "ad_group_name", "cost", "conversions", "cpl"]].to_dict("records")


def _dfs_for_campaign(dfs: dict, campaign_name: str | None) -> dict:
    if not campaign_name:
        return dfs
    out = dict(dfs)
    if "keywords" in dfs and "campaign_name" in dfs["keywords"].columns:
        out["keywords"] = dfs["keywords"][dfs["keywords"]["campaign_name"] == campaign_name]
    return out


def build_budget_optimizer_context(dfs: dict, campaign_name: str | None = None) -> dict:
    ctx = {
        "summary": build_campaign_summary(dfs),
        "scale_candidates": build_scale_candidates(dfs),
        "cut_candidates": build_cut_candidates(dfs),
    }
    if campaign_name:
        ctx["campaign_name"] = campaign_name
    return ctx


def build_budget_optimizer_prompt(context: dict) -> str:
    payload = json.dumps(context, indent=2, default=str)
    name = context.get("campaign_name", "this campaign")
    return (
        f"Write 3 to 5 bullet points on where to increase or cut budget for {name}.\n"
        "Use simple business language. Start each line with '- '. No intro sentence.\n\n"
        f"Data (JSON):\n{payload}"
    )


def rule_based_budget(context: dict) -> str:
    bullets: list[str] = []
    for row in context.get("scale_candidates", [])[:2]:
        bullets.append(
            f"- Increase budget on '{row['keyword']}' — {row['conversions']} conversions at CPL ${row['cpl']:.2f}."
        )
    for row in context.get("cut_candidates", [])[:2]:
        if row.get("conversions", 0) == 0:
            bullets.append(f"- Cut spend on '{row['keyword']}' — ${row['cost']:.2f} spent with no conversions.")
        else:
            bullets.append(f"- Reduce budget on '{row['keyword']}' — CPL ${row['cpl']:.2f} is above average.")
    if not bullets:
        bullets.append("- Review keyword-level spend and shift budget toward terms with the lowest CPL.")
    return "\n\n".join(bullets[:5])


def run_budget_optimizer_card(dfs, campaign_name: str | None = None):
    scoped = _dfs_for_campaign(dfs, campaign_name)
    context = build_budget_optimizer_context(scoped, campaign_name)
    prompt = build_budget_optimizer_prompt(context)

    rec = {
        "campaign_id": "BUDGET_OPTIMIZER",
        "type": "budget_optimization",
        "action": "reallocate_budget",
        "reason": prompt,
    }

    result = generate_explanation(prompt, rec=rec)
    if is_bad_llm_output(result):
        print("⚠️ [budget_optimizer] LLM fallback — using rule-based budget tips", flush=True)
        result = rule_based_budget(context)
    return result

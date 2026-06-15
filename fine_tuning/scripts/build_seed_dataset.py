from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from app.ads1.ads_analyst import build_ads_analyst_context, build_ads_analyst_prompt, rule_based_insights
from app.ads1.budget_optimizer import build_budget_optimizer_context, rule_based_budget_actions
from app.ads1.growth_finder import build_growth_finder_context, rule_based_growth_actions
from app.ads1.keyword_inspector import build_keyword_features, build_keyword_prompt
from app.ads1.sample_data import generate_sample_dfs
from app.ads1.search_term_optimizer import (
    build_search_optimizer_context,
    build_search_optimizer_prompt,
    rule_based_search_actions,
)


SYSTEM = "You are a Google Ads analyst. Reply with concise actionable markdown bullets only."


def chat_record(user: str, assistant: str, card: str, campaign_name: str | None = None) -> dict:
    return {
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": user},
            {"role": "assistant", "content": assistant},
        ],
        "metadata": {
            "card": card,
            "campaign_name": campaign_name,
            "source": "seed_sample_data",
        },
    }


def keyword_answer(context: dict) -> str:
    rows = context.get("keywords", [])
    bullets: list[str] = []
    for row in rows:
        keyword = row.get("keyword", "this keyword")
        cost = float(row.get("cost", 0) or 0)
        clicks = int(row.get("clicks", 0) or 0)
        conversions = float(row.get("conversions", 0) or 0)
        ctr = float(row.get("ctr", 0) or 0)
        cpa = cost / conversions if conversions else cost
        if conversions >= 10:
            bullets.append(
                f"- Treat '{keyword}' as a winning keyword because it produced {conversions:g} conversions at CPA {cpa:.2f} and CTR {ctr:.2f}%."
            )
        elif conversions == 0 and cost > 0:
            bullets.append(
                f"- Reduce or pause '{keyword}' because it spent {cost:.2f} across {clicks} clicks with 0 conversions."
            )
        elif conversions > 0:
            bullets.append(
                f"- Investigate '{keyword}' because it has {conversions:g} conversions but CPA {cpa:.2f}; scale only if CPA improves."
            )
        if len(bullets) >= 5:
            break
    return "\n\n".join(bullets) or "- No keyword action found because no usable keyword rows were available."


def keyword_context(dfs: dict, campaign_name: str) -> dict:
    df = dfs["keywords"].copy()
    if "campaign_name" in df.columns:
        df = df[df["campaign_name"] == campaign_name]
    df = build_keyword_features(df)
    df = df.sort_values(["conversions", "cost"], ascending=[False, False]).head(12)
    return {
        "campaign_name": campaign_name,
        "keywords": df.round(2).to_dict("records"),
    }


def build_records() -> list[dict]:
    dfs = generate_sample_dfs()
    campaigns = dfs["campaigns"]["name"].dropna().astype(str).tolist()
    records: list[dict] = []

    for campaign_name in campaigns:
        ads_context = build_ads_analyst_context(dfs, campaign_name)
        records.append(
            chat_record(
                build_ads_analyst_prompt(ads_context),
                rule_based_insights(ads_context),
                "ads_analyst",
                campaign_name,
            )
        )

        kw_context = keyword_context(dfs, campaign_name)
        records.append(
            chat_record(
                build_keyword_prompt(kw_context),
                keyword_answer(kw_context),
                "keyword_inspector",
                campaign_name,
            )
        )

        search_context = build_search_optimizer_context(dfs, campaign_name)
        records.append(
            chat_record(
                build_search_optimizer_prompt(search_context),
                rule_based_search_actions(search_context),
                "search_term_cleaner",
                campaign_name,
            )
        )

        budget_context = build_budget_optimizer_context(dfs, campaign_name)
        user = (
            f"Rewrite these computed budget decisions for {campaign_name} into 3 to 5 concise bullets.\n"
            "Each bullet must mention the campaign or keyword, the action, and the evidence.\n\n"
            f"Data (JSON):\n{json.dumps(budget_context, indent=2, default=str)}"
        )
        records.append(chat_record(user, rule_based_budget_actions(budget_context), "budget_optimizer", campaign_name))

        growth_context = build_growth_finder_context(dfs, campaign_name)
        user = (
            f"Rewrite these computed growth decisions for {campaign_name} into concise growth opportunity bullets.\n"
            "Each bullet must mention the keyword, the scale action, and the evidence.\n\n"
            f"Data (JSON):\n{json.dumps(growth_context, indent=2, default=str)}"
        )
        records.append(chat_record(user, rule_based_growth_actions(growth_context), "growth_finder", campaign_name))

    return records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=ROOT / "fine_tuning" / "data" / "seed.jsonl")
    parser.add_argument("--shuffle", action="store_true")
    args = parser.parse_args()

    records = build_records()
    if args.shuffle:
        random.Random(42).shuffle(records)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"Wrote {len(records)} records to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


from __future__ import annotations

import argparse
import json
import random
import re
import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from app.ads1.prompt_templates import ads_analyst_prompt, keyword_inspector_prompt, search_term_cleaner_prompt


SYSTEM = "You are a Google Ads analyst. Reply with concise actionable markdown bullets only."


def money_to_float(value) -> float:
    if pd.isna(value):
        return 0.0
    text = str(value)
    text = re.sub(r"[^0-9.\-]", "", text)
    try:
        return float(text) if text else 0.0
    except ValueError:
        return 0.0


def canonical_text(value: str) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


def canonical_campaign(value: str) -> str:
    text = canonical_text(value)
    if "data" in text and ("analytic" in text or "anlytic" in text or "analytcis" in text):
        return "Data Analytics Course"
    return " ".join(part.capitalize() for part in text.split())


def clean_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    keep = [
        "Ad_ID",
        "Campaign_Name",
        "Clicks",
        "Impressions",
        "Cost",
        "Leads",
        "Conversions",
        "Sale_Amount",
        "Ad_Date",
        "Location",
        "Device",
        "Keyword",
    ]
    df = df[[col for col in keep if col in df.columns]].copy()
    df = df.dropna(how="all")

    df["campaign_name"] = df["Campaign_Name"].map(canonical_campaign)
    df["keyword"] = df["Keyword"].map(canonical_text)
    df["search_term"] = df["keyword"]
    df["location"] = df["Location"].map(canonical_text)
    df["device"] = df["Device"].map(lambda x: canonical_text(x).capitalize())
    df["date"] = pd.to_datetime(df["Ad_Date"], errors="coerce", dayfirst=True).dt.strftime("%Y-%m-%d")

    for col in ["Clicks", "Impressions", "Leads", "Conversions"]:
        df[col.lower()] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    df["cost"] = df["Cost"].map(money_to_float)
    df["sale_amount"] = df["Sale_Amount"].map(money_to_float) if "Sale_Amount" in df.columns else 0.0

    df = df[(df["clicks"] > 0) | (df["impressions"] > 0) | (df["cost"] > 0)]
    return df[
        [
            "campaign_name",
            "keyword",
            "search_term",
            "clicks",
            "impressions",
            "cost",
            "leads",
            "conversions",
            "sale_amount",
            "date",
            "location",
            "device",
        ]
    ].reset_index(drop=True)


def aggregate_campaign(df: pd.DataFrame, campaign_name: str) -> dict:
    c = df[df["campaign_name"] == campaign_name]
    clicks = c["clicks"].sum()
    impressions = c["impressions"].sum()
    cost = c["cost"].sum()
    conversions = c["conversions"].sum()
    leads = c["leads"].sum()
    ctr = clicks / impressions * 100 if impressions else 0
    cpa = cost / conversions if conversions else cost
    cvr = conversions / clicks * 100 if clicks else 0
    return {
        "campaign_name": campaign_name,
        "spend": round(float(cost), 2),
        "clicks": int(clicks),
        "impressions": int(impressions),
        "leads": int(leads),
        "conversions": int(conversions),
        "ctr": round(float(ctr), 2),
        "cvr": round(float(cvr), 2),
        "cpa": round(float(cpa), 2),
    }


def aggregate_terms(df: pd.DataFrame, field: str, max_rows: int = 12) -> list[dict]:
    grouped = (
        df.groupby(field, dropna=False)
        .agg(
            clicks=("clicks", "sum"),
            impressions=("impressions", "sum"),
            total_cost=("cost", "sum"),
            leads=("leads", "sum"),
            conversions=("conversions", "sum"),
        )
        .reset_index()
    )
    grouped["ctr"] = grouped["clicks"] / grouped["impressions"].replace(0, pd.NA) * 100
    grouped["cvr"] = grouped["conversions"] / grouped["clicks"].replace(0, pd.NA) * 100
    grouped["cpc"] = grouped["total_cost"] / grouped["clicks"].replace(0, pd.NA)
    grouped["cpa"] = grouped["total_cost"] / grouped["conversions"].replace(0, pd.NA)
    grouped = grouped.fillna(0)

    converters = grouped[grouped["conversions"] > 0].sort_values(["conversions", "cpa"], ascending=[False, True]).head(max_rows // 2)
    waste = grouped[grouped["conversions"] == 0].sort_values("total_cost", ascending=False).head(max_rows // 2)
    out = pd.concat([waste, converters], ignore_index=True).drop_duplicates(subset=[field]).head(max_rows)
    return out.round(2).to_dict("records")


def ads_context(df: pd.DataFrame, campaign_name: str) -> dict:
    c = df[df["campaign_name"] == campaign_name]
    keyword_rows = aggregate_terms(c, "keyword", 8)
    best = sorted([r for r in keyword_rows if r["conversions"] > 0], key=lambda r: (r["cpa"], -r["conversions"]))[:3]
    worst = sorted(keyword_rows, key=lambda r: (r["conversions"] > 0, -r["total_cost"]))[:3]
    return {
        "campaign_name": campaign_name,
        "campaign": aggregate_campaign(df, campaign_name),
        "top_drivers": {
            "best_keywords": best,
            "worst_keywords": worst,
        },
    }


def ads_answer(context: dict) -> str:
    c = context["campaign"]
    bullets = []
    if c["conversions"] == 0:
        bullets.append(f"- {c['campaign_name']} has no conversions after {c['clicks']} clicks, so review tracking, landing page quality, and weak-intent traffic before increasing spend.")
    elif c["cpa"] > 100:
        bullets.append(f"- {c['campaign_name']} is expensive at CPA {c['cpa']:.2f}, so reduce spend on weak terms and tighten targeting before scaling.")
    else:
        bullets.append(f"- {c['campaign_name']} is generating conversions at CPA {c['cpa']:.2f}, so protect the best-performing keyword themes.")

    for row in context["top_drivers"]["best_keywords"][:2]:
        bullets.append(f"- Scale '{row['keyword']}' because it produced {int(row['conversions'])} conversions at CPA {row['cpa']:.2f}.")
    for row in context["top_drivers"]["worst_keywords"][:2]:
        if row["conversions"] == 0:
            bullets.append(f"- Reduce or pause '{row['keyword']}' because it spent {row['total_cost']:.2f} with 0 conversions.")
    return "\n\n".join(bullets[:5])


def keyword_context(df: pd.DataFrame, campaign_name: str) -> dict:
    c = df[df["campaign_name"] == campaign_name]
    return {
        "campaign_name": campaign_name,
        "keywords": aggregate_terms(c, "keyword", 12),
    }


def keyword_answer(context: dict) -> str:
    bullets = []
    for row in context["keywords"][:5]:
        keyword = row["keyword"]
        if row["conversions"] > 0:
            bullets.append(f"- Treat '{keyword}' as a winning keyword because it produced {int(row['conversions'])} conversions at CPA {row['cpa']:.2f} and CVR {row['cvr']:.2f}%.")
        else:
            bullets.append(f"- Reduce or pause '{keyword}' because it spent {row['total_cost']:.2f} across {int(row['clicks'])} clicks with 0 conversions.")
    return "\n\n".join(bullets)


def search_context(df: pd.DataFrame, campaign_name: str) -> dict:
    c = df[df["campaign_name"] == campaign_name]
    rows = aggregate_terms(c, "search_term", 12)
    for row in rows:
        row["action_type"] = "add as keyword or scale" if row["conversions"] > 0 else "pause or add as negative"
    return {
        "campaign_name": campaign_name,
        "search_terms": rows,
    }


def search_answer(context: dict) -> str:
    bullets = []
    for row in context["search_terms"][:5]:
        term = row["search_term"]
        if row["conversions"] > 0:
            bullets.append(f"- Add or scale '{term}' because it produced {int(row['conversions'])} conversions at CPA {row['cpa']:.2f} and CVR {row['cvr']:.2f}% on {row['total_cost']:.2f} total spend.")
        else:
            bullets.append(f"- Pause or add '{term}' as a negative because it spent {row['total_cost']:.2f} across {int(row['clicks'])} clicks with 0 conversions.")
    return "\n\n".join(bullets)


def record(user: str, assistant: str, card: str, source: str, campaign_name: str) -> dict:
    return {
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": user},
            {"role": "assistant", "content": assistant},
        ],
        "metadata": {
            "card": card,
            "source": source,
            "campaign_name": campaign_name,
        },
    }


def csv_records(df: pd.DataFrame, target_count: int, seed: int) -> list[dict]:
    rng = random.Random(seed)
    campaigns = df["campaign_name"].dropna().unique().tolist()
    records: list[dict] = []

    slices = []
    for campaign in campaigns:
        slices.append((campaign, df[df["campaign_name"] == campaign]))
        for device in df["device"].dropna().unique().tolist():
            part = df[(df["campaign_name"] == campaign) & (df["device"] == device)]
            if len(part) >= 20:
                slices.append((f"{campaign} - {device}", part.assign(campaign_name=f"{campaign} - {device}")))
        for location in df["location"].dropna().unique().tolist():
            part = df[(df["campaign_name"] == campaign) & (df["location"] == location)]
            if len(part) >= 20:
                slices.append((f"{campaign} - {location}", part.assign(campaign_name=f"{campaign} - {location}")))

    while len(records) < target_count:
        name, part = rng.choice(slices)
        card = rng.choice(["ads_analyst", "keyword_inspector", "search_term_cleaner"])

        if card == "ads_analyst":
            ctx = ads_context(part, name)
            user = ads_analyst_prompt(name, json.dumps(ctx, indent=2, default=str))
            assistant = ads_answer(ctx)
        elif card == "keyword_inspector":
            ctx = keyword_context(part, name)
            user = keyword_inspector_prompt(json.dumps(ctx, indent=2, default=str))
            assistant = keyword_answer(ctx)
        else:
            ctx = search_context(part, name)
            user = search_term_cleaner_prompt(name, json.dumps(ctx, indent=2, default=str))
            assistant = search_answer(ctx)
        records.append(record(user, assistant, card, "csv_cleaned", name))

    return records


def synthetic_records(count: int, seed: int) -> list[dict]:
    rng = random.Random(seed)
    records: list[dict] = []
    campaigns = ["Admissions Push", "Course Signup", "Demo Booking", "Lead Generation"]
    good_terms = ["data analytics course", "analytics certification", "data analyst training", "online analytics class"]
    bad_terms = ["free jobs", "salary guide", "software crack", "unrelated tutorial"]

    while len(records) < count:
        campaign = rng.choice(campaigns)
        card = rng.choice(["ads_analyst", "keyword_inspector", "search_term_cleaner"])
        rows = []
        for term in good_terms + bad_terms:
            is_good = term in good_terms
            clicks = rng.randint(40, 240)
            impressions = clicks * rng.randint(15, 55)
            conversions = rng.randint(4, 28) if is_good else rng.choice([0, 0, 1])
            total_cost = round(clicks * rng.uniform(0.8, 4.5), 2)
            cpa = total_cost / conversions if conversions else total_cost
            cvr = conversions / clicks * 100 if clicks else 0
            cpc = total_cost / clicks if clicks else 0
            rows.append(
                {
                    "keyword": term,
                    "search_term": term,
                    "clicks": clicks,
                    "impressions": impressions,
                    "total_cost": round(total_cost, 2),
                    "conversions": conversions,
                    "ctr": round(clicks / impressions * 100, 2),
                    "cvr": round(cvr, 2),
                    "cpc": round(cpc, 2),
                    "cpa": round(cpa, 2),
                }
            )

        if card == "ads_analyst":
            total_clicks = sum(r["clicks"] for r in rows)
            total_impressions = sum(r["impressions"] for r in rows)
            total_cost = sum(r["total_cost"] for r in rows)
            total_conversions = sum(r["conversions"] for r in rows)
            ctx = {
                "campaign_name": campaign,
                "campaign": {
                    "campaign_name": campaign,
                    "spend": round(total_cost, 2),
                    "clicks": total_clicks,
                    "impressions": total_impressions,
                    "conversions": total_conversions,
                    "ctr": round(total_clicks / total_impressions * 100, 2),
                    "cpa": round(total_cost / total_conversions, 2) if total_conversions else round(total_cost, 2),
                },
                "top_drivers": {
                    "best_keywords": [r for r in rows if r["conversions"] > 0][:3],
                    "worst_keywords": [r for r in rows if r["conversions"] == 0][:3],
                },
            }
            user = ads_analyst_prompt(campaign, json.dumps(ctx, indent=2, default=str))
            assistant = ads_answer(ctx)
        elif card == "keyword_inspector":
            ctx = {"campaign_name": campaign, "keywords": rows}
            user = keyword_inspector_prompt(json.dumps(ctx, indent=2, default=str))
            assistant = keyword_answer(ctx)
        else:
            ctx = {"campaign_name": campaign, "search_terms": rows}
            for row in ctx["search_terms"]:
                row["action_type"] = "add as keyword or scale" if row["conversions"] > 0 else "pause or add as negative"
            user = search_term_cleaner_prompt(campaign, json.dumps(ctx, indent=2, default=str))
            assistant = search_answer(ctx)
        records.append(record(user, assistant, card, "synthetic", campaign))

    return records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--out_dir", type=Path, default=ROOT / "fine_tuning" / "data")
    parser.add_argument("--csv_count", type=int, default=400)
    parser.add_argument("--synthetic_count", type=int, default=600)
    parser.add_argument("--val_ratio", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    cleaned = clean_csv(args.csv)
    records = csv_records(cleaned, args.csv_count, args.seed)
    records.extend(synthetic_records(args.synthetic_count, args.seed + 1))
    random.Random(args.seed).shuffle(records)

    val_size = max(1, int(len(records) * args.val_ratio))
    val = records[:val_size]
    train = records[val_size:]

    args.out_dir.mkdir(parents=True, exist_ok=True)
    cleaned.to_csv(args.out_dir / "csv_cleaned_pruned.csv", index=False)
    for path, rows in [(args.out_dir / "train.jsonl", train), (args.out_dir / "val.jsonl", val)]:
        with path.open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"Cleaned CSV rows: {len(cleaned)}")
    print(f"Wrote train: {len(train)} records")
    print(f"Wrote val: {len(val)} records")
    print(f"Output dir: {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


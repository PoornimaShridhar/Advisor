import numpy as np
import pandas as pd

def _rand(low, high, size):
    return np.random.randint(low, high, size)

def _money(low, high, size):
    return np.round(np.random.uniform(low, high, size), 2)

def _pick(arr, size):
    return np.random.choice(arr, size)

def generate_sample_campaigns():
    campaigns = [
        {
            "id": 1001,
            "name": "Nursery Admissions 2026",
            "status": "ENABLED",
            "impressions": 120000,
            "clicks": 8500,
            "cost": 12000.0,
            "ctr": 7.08,
            "conversions": 420,
        },
        {
            "id": 1002,
            "name": "Playgroup Enrollment Campaign",
            "status": "ENABLED",
            "impressions": 90000,
            "clicks": 6200,
            "cost": 8000.0,
            "ctr": 6.88,
            "conversions": 310,
        },
        {
            "id": 1003,
            "name": "Summer Camp 2026",
            "status": "ENABLED",
            "impressions": 150000,
            "clicks": 4000,
            "cost": 7000.0,
            "ctr": 2.66,
            "conversions": 180,
        },
        {
            "id": 1004,
            "name": "School Tour Booking Campaign",
            "status": "ENABLED",
            "impressions": 60000,
            "clicks": 2200,
            "cost": 3500.0,
            "ctr": 3.66,
            "conversions": 140,
        },
    ]

    return pd.DataFrame(campaigns)

# 2. SEARCH TERMS
def generate_sample_search_terms():
    positive_intent = [
        "nursery admission near me",
        "best preschool in Yelahanka",
        "play school admission 2026",
        "kg admission Bangalore",
        "preschool fees near me",
        "daycare near Yelahanka",
    ]

    negative_intent = [
        "free babysitting jobs",
        "toy store near me",
        "kids games online",
        "montessori certification course",
        "child psychology course",
        "teaching jobs preschool",
    ]

    campaigns = [
        "Nursery Admissions 2026",
        "Playgroup Enrollment Campaign",
        "Summer Camp 2026",
        "School Tour Booking Campaign",
    ]

    rows = []

    for campaign in campaigns:
        for term in positive_intent + negative_intent:

            clicks = np.random.randint(5, 250)
            impressions = clicks * np.random.randint(5, 60)
            cost = round(clicks * np.random.uniform(0.5, 4.0), 2)

            # realistic conversion logic
            if term in positive_intent:
                conversions = np.random.randint(1, 25)
            else:
                conversions = np.random.choice([0, 0, 0, 1])

            rows.append({
                "search_term": term,
                "campaign_name": campaign,
                "clicks": clicks,
                "impressions": impressions,
                "cost": cost,
                "conversions": conversions,
            })

    return pd.DataFrame(rows)

# 3. KEYWORDS
def generate_sample_keywords():
    keywords = [
        "preschool admission",
        "nursery school near me",
        "play school Bangalore",
        "kg admission",
        "daycare Yelahanka",
        "best preschool",
    ]

    campaigns = [
        "Nursery Admissions 2026",
        "Playgroup Enrollment Campaign",
        "Summer Camp 2026",
        "School Tour Booking Campaign",
    ]

    rows = []

    for campaign in campaigns:
        for kw in keywords:

            clicks = np.random.randint(50, 500)
            impressions = clicks * np.random.randint(10, 80)
            cost = round(clicks * np.random.uniform(0.8, 5.0), 2)

            # realistic conversion behavior
            if "admission" in kw or "preschool" in kw:
                conversions = np.random.randint(5, 40)
            else:
                conversions = np.random.choice([0, 0, 1, 2, 3])

            ctr = round((clicks / impressions) * 100, 2)

            rows.append({
                "campaign_name": campaign,
                "keyword": kw,
                "clicks": clicks,
                "impressions": impressions,
                "cost": cost,
                "conversions": conversions,
                "ctr": ctr,
            })

    return pd.DataFrame(rows)

# ==================================================
# 4. HOURLY (OPTIONAL BUT MATCHES REAL STRUCTURE)
# ==================================================

def generate_sample_hourly():
    hours = list(range(24))
    rows = []

    for campaign in [
        "Nursery Admissions 2026",
        "Playgroup Enrollment Campaign",
        "Summer Camp 2026",
        "School Tour Booking Campaign",
    ]:
        for h in hours:
            clicks = np.random.randint(0, 80)
            impressions = clicks * np.random.randint(5, 30)
            cost = round(clicks * np.random.uniform(0.2, 3.0), 2)

            rows.append({
                "date": "2026-06-01",
                "hour": h,
                "clicks": clicks,
                "impressions": impressions,
                "cost": cost,
            })

    return pd.DataFrame(rows)


# ==================================================
# 5. GEO (OPTIONAL BUT MATCHES REAL STRUCTURE)
# ==================================================

def generate_sample_geo():
    countries = ["IN", "AE", "US"]
    rows = []

    for c in countries:
        rows.append({
            "country_id": c,
            "clicks": np.random.randint(500, 5000),
            "impressions": np.random.randint(10000, 100000),
            "cost": round(np.random.uniform(500, 5000), 2),
        })

    return pd.DataFrame(rows)


# 4. MASTER GENERATOR
def generate_sample_dfs():
    return {
        "campaigns": generate_sample_campaigns(),
        "search_terms": generate_sample_search_terms(),
        "keywords": generate_sample_keywords(),
        "hourly": generate_sample_hourly(),
        "geo": generate_sample_geo(),
        "devices": pd.DataFrame(),            # optional placeholder
        "recommendations": pd.DataFrame(),    # optional placeholder
    }
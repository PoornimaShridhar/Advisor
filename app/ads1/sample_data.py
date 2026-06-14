import pandas as pd


CAMPAIGNS = [
    "Nursery Admissions 2026",
    "Playgroup Enrollment Campaign",
    "Summer Camp 2026",
    "School Tour Booking Campaign",
]


def generate_sample_campaigns():
    campaigns = [
        {
            "id": 1001,
            "name": "Nursery Admissions 2026",
            "status": "ENABLED",
            "impressions": 118000,
            "clicks": 8600,
            "cost": 10450.0,
            "ctr": 7.29,
            "conversions": 420,
        },
        {
            "id": 1002,
            "name": "Playgroup Enrollment Campaign",
            "status": "ENABLED",
            "impressions": 76000,
            "clicks": 4300,
            "cost": 9800.0,
            "ctr": 5.66,
            "conversions": 62,
        },
        {
            "id": 1003,
            "name": "Summer Camp 2026",
            "status": "ENABLED",
            "impressions": 132000,
            "clicks": 5100,
            "cost": 8600.0,
            "ctr": 3.86,
            "conversions": 105,
        },
        {
            "id": 1004,
            "name": "School Tour Booking Campaign",
            "status": "ENABLED",
            "impressions": 54000,
            "clicks": 2300,
            "cost": 3200.0,
            "ctr": 4.26,
            "conversions": 145,
        },
    ]
    return pd.DataFrame(campaigns)


def _search_rows_for_campaign(campaign_name, multiplier=1.0):
    base_rows = [
        # Clear high-intent / scale candidates
        ("nursery admission near me", 180, 4200, 260.0, 22),
        ("preschool fees near me", 140, 3500, 190.0, 18),
        ("best preschool in Yelahanka", 125, 2800, 210.0, 16),
        ("school tour booking near me", 90, 1800, 135.0, 14),
        ("kg admission Bangalore", 155, 3900, 245.0, 15),
        # Investigate: engagement but weak conversion
        ("daycare near Yelahanka", 170, 5200, 380.0, 2),
        ("play school admission 2026", 210, 6100, 430.0, 3),
        # Clear negative/waste terms
        ("free babysitting jobs", 190, 5000, 620.0, 0),
        ("toy store near me", 160, 4300, 510.0, 0),
        ("kids games online", 135, 3600, 420.0, 0),
        ("montessori certification course", 155, 4100, 540.0, 0),
        ("teaching jobs preschool", 145, 3700, 460.0, 0),
    ]

    rows = []
    for idx, (term, clicks, impressions, cost, conversions) in enumerate(base_rows, start=1):
        rows.append(
            {
                "search_term": term,
                "campaign_name": campaign_name,
                "clicks": int(round(clicks * multiplier)),
                "impressions": int(round(impressions * multiplier)),
                "cost": round(cost * multiplier, 2),
                "conversions": int(round(conversions * multiplier)),
            }
        )
    return rows


def generate_sample_search_terms():
    rows = []
    multipliers = {
        "Nursery Admissions 2026": 1.15,
        "Playgroup Enrollment Campaign": 0.85,
        "Summer Camp 2026": 0.75,
        "School Tour Booking Campaign": 1.0,
    }
    for campaign in CAMPAIGNS:
        rows.extend(_search_rows_for_campaign(campaign, multipliers[campaign]))
    return pd.DataFrame(rows)


def _keyword_rows_for_campaign(campaign_name, profile):
    if profile == "winner":
        return [
            ("preschool admission", 720, 14800, 820.0, 54),
            ("nursery school near me", 510, 9400, 610.0, 38),
            ("best preschool", 430, 7600, 520.0, 34),
            ("kg admission", 390, 7000, 480.0, 29),
            ("daycare Yelahanka", 280, 8100, 560.0, 4),
            ("play school Bangalore", 330, 9800, 690.0, 0),
        ]
    if profile == "drain":
        return [
            ("preschool admission", 620, 14500, 1850.0, 12),
            ("nursery school near me", 540, 12800, 1760.0, 8),
            ("play school Bangalore", 470, 11800, 1620.0, 0),
            ("daycare Yelahanka", 430, 10100, 1490.0, 0),
            ("best preschool", 390, 9200, 1380.0, 2),
            ("kg admission", 250, 7400, 860.0, 1),
        ]
    if profile == "investigate":
        return [
            ("preschool admission", 360, 13200, 910.0, 14),
            ("nursery school near me", 300, 10100, 780.0, 9),
            ("summer camp for kids", 560, 22000, 1900.0, 11),
            ("kids activity camp", 480, 21000, 1680.0, 3),
            ("free summer activities", 410, 18000, 1250.0, 0),
            ("art classes for kids", 310, 12000, 940.0, 1),
        ]
    return [
        ("school tour booking", 310, 6200, 340.0, 28),
        ("book school visit", 250, 5100, 290.0, 22),
        ("preschool admission", 210, 4800, 260.0, 16),
        ("nursery school near me", 180, 4200, 230.0, 13),
        ("daycare Yelahanka", 160, 6100, 410.0, 2),
        ("teaching jobs preschool", 190, 7800, 520.0, 0),
    ]


def generate_sample_keywords():
    profiles = {
        "Nursery Admissions 2026": "winner",
        "Playgroup Enrollment Campaign": "drain",
        "Summer Camp 2026": "investigate",
        "School Tour Booking Campaign": "scale",
    }

    rows = []
    for campaign in CAMPAIGNS:
        for keyword, clicks, impressions, cost, conversions in _keyword_rows_for_campaign(campaign, profiles[campaign]):
            rows.append(
                {
                    "campaign_name": campaign,
                    "keyword": keyword,
                    "clicks": clicks,
                    "impressions": impressions,
                    "cost": cost,
                    "conversions": conversions,
                    "ctr": round((clicks / impressions) * 100, 2) if impressions else 0,
                }
            )
    return pd.DataFrame(rows)


def generate_sample_hourly():
    rows = []
    dates = pd.date_range("2026-06-01", periods=14, freq="D")
    campaign_click_bases = {
        "Nursery Admissions 2026": 18,
        "Playgroup Enrollment Campaign": 10,
        "Summer Camp 2026": 13,
        "School Tour Booking Campaign": 8,
    }

    for day_index, date in enumerate(dates):
        trend_boost = day_index * 0.08
        for campaign in CAMPAIGNS:
            base = campaign_click_bases[campaign]
            for hour in range(24):
                daypart = 1.4 if 8 <= hour <= 12 or 18 <= hour <= 21 else 0.55
                clicks = int(round(base * daypart * (1 + trend_boost)))
                impressions = clicks * 28
                cost = round(clicks * (1.45 if campaign != "Playgroup Enrollment Campaign" else 2.6), 2)
                rows.append(
                    {
                        "date": date.strftime("%Y-%m-%d"),
                        "hour": hour,
                        "campaign_name": campaign,
                        "clicks": clicks,
                        "impressions": impressions,
                        "cost": cost,
                    }
                )
    return pd.DataFrame(rows)


def generate_sample_geo():
    rows = [
        {"country_id": "IN", "clicks": 6200, "impressions": 128000, "cost": 7600.0},
        {"country_id": "AE", "clicks": 840, "impressions": 21000, "cost": 1380.0},
        {"country_id": "US", "clicks": 360, "impressions": 11200, "cost": 980.0},
    ]
    return pd.DataFrame(rows)


def generate_sample_dfs():
    return {
        "campaigns": generate_sample_campaigns(),
        "search_terms": generate_sample_search_terms(),
        "keywords": generate_sample_keywords(),
        "hourly": generate_sample_hourly(),
        "geo": generate_sample_geo(),
        "devices": pd.DataFrame(),
        "recommendations": pd.DataFrame(),
    }

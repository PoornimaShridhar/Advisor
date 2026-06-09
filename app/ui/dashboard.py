import gradio as gr
import pandas as pd
from app.controller.session_loader import load_google_ads_data


def get_dashboard_data():
    dfs = load_google_ads_data()
    df = dfs["campaigns"].copy()

    if df.empty:
        return 0, 0, 0, 0, pd.DataFrame(columns=["Campaign", "Spend", "Leads", "CPL", "CTR"])

    df["leads"] = df.get("conversions", 0)
    df["cpl"] = df["cost"] / df["leads"].replace(0, 1)
    df["ctr"] = df.get("ctr", 0)

    formatted = pd.DataFrame({
        "Campaign": df["name"],
        "Spend": df["cost"],
        "Leads": df["leads"],
        "CPL": df["cpl"],
        "CTR": df["ctr"],
    })

    return (
        round(formatted["Spend"].sum(), 2),
        int(formatted["Leads"].sum()),
        round(formatted["CPL"].mean(), 2),
        len(formatted),
        formatted
    )


def build_dashboard():
    # Retained exactly for backend structural lookups if referenced elsewhere
    campaign_table = gr.Dataframe(
        label="Campaign Performance",
        interactive=True
    )
    return campaign_table

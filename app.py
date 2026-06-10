import gradio as gr
import os
import spaces

from app.db.repo import init_db
from app.controller.campaign_controller import on_campaign_select
from app.controller.session_loader import load_google_ads_data
from app.ads1.ads_analyst import run_ads_analyst_card
from app.ads1.budget_optimizer import run_budget_optimizer_card


# -----------------------------
# INIT
# -----------------------------
def startup():
    try:
        init_db()
        print("✅ DB initialized successfully", flush=True)
    except Exception as e:
        print("⚠️ DB failed:", e, flush=True)


# -----------------------------
# DATA LOAD
# -----------------------------
def initial_data_load():
    print("🔄 Loading app data...")

    dfs = load_google_ads_data()

    from app.ui.dashboard import get_dashboard_data
    spend, leads, cpl, count, formatted_df = get_dashboard_data()

    return dfs, formatted_df, spend, leads, cpl, count


# -----------------------------
# CAMPAIGN SELECT
# -----------------------------
def campaign_row_selected(df, full_state, evt: gr.SelectData):
    row_index = evt.index[0]
    campaign_name = df.iloc[row_index]["Campaign"]

    campaign_state = on_campaign_select(full_state, campaign_name)

    return campaign_state, f"📊 {campaign_name}"


# -----------------------------
# ADS ANALYST CARD WRAPPER
# -----------------------------
@spaces.GPU(duration=120)
def run_ads_card(state):
    print("\n🔥 [run_ads_card] ENTERED", flush=True)

    try:
        if not state:
            return "⚠️ Select a campaign first"

        dfs = state.get("full_dfs")
        campaign_name = state.get("campaign_name")

        if dfs is None:
            return "⚠️ No campaign data available"

        return run_ads_analyst_card(dfs, campaign_name=campaign_name)

    except Exception as e:
        print("❌ ERROR:", repr(e), flush=True)
        return f"⚠️ Analysis failed: {e}"


# -----------------------------
# UI
# -----------------------------
with gr.Blocks() as demo:

    # STATE
    full_state = gr.State()
    campaign_state = gr.State()

    gr.Markdown("# 🎯 Ads Intelligence Workspace")

    # =========================
    # MAIN LAYOUT
    # =========================
    with gr.Row():

        # LEFT PANEL
        with gr.Column(scale=1):
            gr.Markdown("## 📁 Campaigns")

            campaign_table = gr.Dataframe(
                label="Campaigns",
                interactive=True
            )

        # RIGHT PANEL
        with gr.Column(scale=3):

            # GLOBAL KPIs
            with gr.Row():
                total_spend = gr.Number(label="Spend")
                total_leads = gr.Number(label="Leads")
                average_cpl = gr.Number(label="CPL")
                active_campaigns = gr.Number(label="Campaigns")

            # CAMPAIGN BANNER
            campaign_banner = gr.Markdown(
                "👉 Select a campaign to begin analysis"
            )

            # =========================
            # AI CARDS (CURSOR STYLE)
            # =========================

            with gr.Row():
                ads_card = gr.Button("📊 Ads Analyst")
                gr.Markdown("💰 Budget Optimizer (inactive)")
                gr.Markdown("🎯 Keyword Intelligence (inactive)")

            with gr.Row():
                gr.Markdown("⚠️ Risk Detector (inactive)")
                gr.Markdown("📈 Growth Finder (inactive)")
                gr.Markdown("🧪 Experiment Ideas (inactive)")

            # OUTPUT AREA (ONLY FOR ADS CARD NOW)
            ads_output = gr.Markdown(
                value="Click 'Ads Analyst' to analyze selected campaign"
            )

    # =========================
    # EVENTS
    # =========================

    campaign_table.select(
        fn=campaign_row_selected,
        inputs=[campaign_table, full_state],
        outputs=[campaign_state, campaign_banner],
    )

    ads_card.click(
        fn=run_ads_card,
        inputs=campaign_state,
        outputs=ads_output
    )

    # =========================
    # DATA LOAD
    # =========================

    demo.load(
        fn=initial_data_load,
        outputs=[full_state, campaign_table, total_spend, total_leads, average_cpl, active_campaigns],
    )

    demo.load(fn=startup)


demo.queue()

if __name__ == "__main__":
    demo.launch()
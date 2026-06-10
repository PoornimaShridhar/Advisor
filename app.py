import gradio as gr
import spaces

from app.db.repo import init_db
from app.controller.campaign_controller import on_campaign_select
from app.controller.session_loader import load_google_ads_data
from app.ads1.ads_analyst import run_ads_analyst_card


# ==================================================
# CURSOR-STYLE THEME
# ==================================================

CSS = """
.gradio-container {
    background: #f7f7f4 !important;
    max-width: 1500px !important;
}

#advisor-header {
    margin-bottom: 24px;
}

#advisor-title {
    font-size: 28px;
    font-weight: 600;
    color: #26251e;
}

#advisor-subtitle {
    font-size: 14px;
    color: #807d72;
}

.workspace-card {
    background: white;
    border: 1px solid #e6e5e0;
    border-radius: 12px;
    padding: 16px;
}

.snapshot-card {
    background: white;
    border: 1px solid #e6e5e0;
    border-radius: 12px;
    padding: 20px;
    margin-top: 12px;
    margin-bottom: 20px;
}

.ai-card {
    background: white;
    border: 1px solid #e6e5e0;
    border-radius: 12px;
    padding: 18px;
    min-height: 120px;
}

.ai-card h3 {
    margin-bottom: 8px;
}

.ai-card p {
    color: #807d72;
}

#ads-output {
    background: white;
    border: 1px solid #e6e5e0;
    border-radius: 12px;
    padding: 20px;
    margin-top: 16px;
}

button.primary {
    background: #f54e00 !important;
}
"""


# ==================================================
# INIT
# ==================================================

def startup():
    try:
        init_db()
        print("✅ DB initialized successfully", flush=True)
    except Exception as e:
        print("⚠️ DB failed:", e, flush=True)


# ==================================================
# DATA LOAD
# ==================================================

def initial_data_load():
    print("🔄 Loading app data...")

    dfs = load_google_ads_data()

    from app.ui.dashboard import get_dashboard_data

    spend, leads, cpl, count, formatted_df = get_dashboard_data()

    return dfs, formatted_df, spend, leads, cpl, count


# ==================================================
# CAMPAIGN SELECT
# ==================================================

def campaign_row_selected(df, full_state, evt: gr.SelectData):
    row_index = evt.index[0]

    campaign_name = df.iloc[row_index]["Campaign"]

    campaign_state = on_campaign_select(
        full_state,
        campaign_name
    )

    banner_html = f"""
    <div class="snapshot-card">
        <h3>📊 {campaign_name}</h3>
        <p>
        Campaign selected. AI insights are now available.
        Click an intelligence card below to begin analysis.
        </p>
    </div>
    """

    return campaign_state, banner_html


# ==================================================
# ADS ANALYST
# ==================================================

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

        return run_ads_analyst_card(
            dfs,
            campaign_name=campaign_name
        )

    except Exception as e:
        print("❌ ERROR:", repr(e), flush=True)
        return f"⚠️ Analysis failed: {e}"


# ==================================================
# UI
# ==================================================

with gr.Blocks(css=CSS) as demo:

    full_state = gr.State()
    campaign_state = gr.State()

    # -----------------------------------------
    # HEADER
    # -----------------------------------------

    gr.HTML("""
    <div id="advisor-header">
        <div id="advisor-title">
            🧠 Advisor
        </div>
        <div id="advisor-subtitle">
            AI-powered Google Ads optimization
        </div>
    </div>
    """)

    # -----------------------------------------
    # MAIN LAYOUT
    # -----------------------------------------

    with gr.Row():

        # =====================================
        # LEFT PANEL
        # =====================================

        with gr.Column(scale=1):

            gr.HTML("""
            <div class="workspace-card">
                <h3>📁 Campaign Navigator</h3>
            </div>
            """)

            campaign_table = gr.Dataframe(
                show_label=False,
                interactive=True
            )

        # =====================================
        # RIGHT PANEL
        # =====================================

        with gr.Column(scale=3):

            # KPI STRIP

            with gr.Row():

                total_spend = gr.Number(
                    label="Total Spend"
                )

                total_leads = gr.Number(
                    label="Total Leads"
                )

                average_cpl = gr.Number(
                    label="Average CPL"
                )

                active_campaigns = gr.Number(
                    label="Campaigns"
                )

            # SNAPSHOT

            campaign_banner = gr.HTML("""
            <div class="snapshot-card">
                <h3>Performance Snapshot</h3>
                <p>Select a campaign to begin analysis.</p>
            </div>
            """)

            # AI INSIGHTS

            gr.Markdown("### AI Insights")

            with gr.Row():

                ads_card = gr.Button(
                    "📊 Ads Analyst",
                    variant="primary"
                )

                gr.HTML("""
                <div class="ai-card">
                    <h3>💰 Budget Optimizer</h3>
                    <p>Ready</p>
                </div>
                """)

                gr.HTML("""
                <div class="ai-card">
                    <h3>🎯 Keyword Intelligence</h3>
                    <p>Ready</p>
                </div>
                """)

            with gr.Row():

                gr.HTML("""
                <div class="ai-card">
                    <h3>⚠️ Risk Detector</h3>
                    <p>Ready</p>
                </div>
                """)

                gr.HTML("""
                <div class="ai-card">
                    <h3>📈 Growth Finder</h3>
                    <p>Ready</p>
                </div>
                """)

                gr.HTML("""
                <div class="ai-card">
                    <h3>🧪 Experiment Ideas</h3>
                    <p>Ready</p>
                </div>
                """)

            ads_output = gr.Markdown(
                value="Select a campaign and click Ads Analyst.",
                elem_id="ads-output"
            )

    # =====================================
    # EVENTS
    # =====================================

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

    # =====================================
    # APP LOAD
    # =====================================

    demo.load(
        fn=initial_data_load,
        outputs=[
            full_state,
            campaign_table,
            total_spend,
            total_leads,
            average_cpl,
            active_campaigns,
        ],
    )

    demo.load(fn=startup)

demo.queue()

if __name__ == "__main__":
    demo.launch()
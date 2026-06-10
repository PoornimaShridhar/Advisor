import gradio as gr
import spaces

from app.db.repo import init_db
from app.controller.campaign_controller import on_campaign_select
from app.controller.session_loader import load_google_ads_data
from app.ads1.ads_analyst import run_ads_analyst_card


# ==================================================
# CURSOR-STYLE THEME (REFINED)
# ==================================================

CSS = """
.gradio-container {
    background: #f7f7f4 !important;
    max-width: 1500px !important;
}

/* HEADER */
#advisor-header {
    margin-bottom: 20px;
}

#advisor-title {
    font-size: 26px;
    font-weight: 600;
    color: #26251e;
}

#advisor-subtitle {
    font-size: 13px;
    color: #807d72;
}

/* LEFT PANEL */
.sidebar {
    background: #f7f7f4;
    padding-right: 12px;
}

/* SINGLE UNIFIED WORKSPACE */
.workspace {
    background: white;
    border: 1px solid #e6e5e0;
    border-radius: 16px;
    padding: 18px;
}

/* CAMPAIGN NAV */
.nav-title {
    font-size: 13px;
    color: #6f6c63;
    margin-bottom: 10px;
}

/* KPI STRIP */
.kpi-strip {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 10px;
    margin-bottom: 16px;
}

.kpi {
    background: #fafaf7;
    border: 1px solid #e6e5e0;
    border-radius: 10px;
    padding: 10px;
}

.kpi .label {
    font-size: 11px;
    color: #8a877c;
}

.kpi .value {
    font-size: 16px;
    font-weight: 600;
    color: #26251e;
}

/* SNAPSHOT */
.snapshot {
    border-top: 1px solid #e6e5e0;
    border-bottom: 1px solid #e6e5e0;
    padding: 14px 0;
    margin: 14px 0;
}

/* AI GRID */
.ai-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
    margin-top: 12px;
}

.ai-card {
    background: #ffffff;
    border: 1px solid #e6e5e0;
    border-radius: 12px;
    padding: 14px;
    min-height: 90px;
}

.ai-card h3 {
    font-size: 14px;
    margin-bottom: 6px;
}

.ai-card p {
    font-size: 12px;
    color: #807d72;
}

/* OUTPUT */
#ads-output {
    margin-top: 16px;
    padding: 16px;
    border: 1px solid #e6e5e0;
    border-radius: 12px;
    background: white;
}

/* BUTTON */
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
# DATA
# ==================================================

def initial_data_load():
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

    campaign_state = on_campaign_select(full_state, campaign_name)

    banner_html = f"""
    <div class="snapshot">
        <h3>📊 {campaign_name}</h3>
        <p>Campaign selected. AI insights are now available.</p>
    </div>
    """

    return campaign_state, banner_html


# ==================================================
# ADS ANALYST
# ==================================================

@spaces.GPU(duration=120)
def run_ads_card(state):
    try:
        if not state:
            return "⚠️ Select a campaign first"

        dfs = state.get("full_dfs")
        campaign_name = state.get("campaign_name")

        if dfs is None:
            return "⚠️ No campaign data available"

        return run_ads_analyst_card(dfs, campaign_name=campaign_name)

    except Exception as e:
        return f"⚠️ Analysis failed: {e}"


# ==================================================
# UI
# ==================================================

with gr.Blocks(css=CSS) as demo:

    full_state = gr.State()
    campaign_state = gr.State()

    # ---------------- HEADER ----------------
    gr.HTML("""
    <div id="advisor-header">
        <div id="advisor-title">🧠 Advisor</div>
        <div id="advisor-subtitle">AI-powered Google Ads optimization</div>
    </div>
    """)

    # ---------------- LAYOUT ----------------
    with gr.Row():

        # LEFT SIDEBAR
        with gr.Column(scale=1, elem_classes=["sidebar"]):

            gr.Markdown("### Campaigns")

            campaign_table = gr.Dataframe(
                show_label=False,
                interactive=True
            )

        # RIGHT WORKSPACE
        with gr.Column(scale=3):

            gr.HTML('<div class="workspace">')

            # KPI STRIP (single unified block)
            gr.HTML("""
            <div class="kpi-strip">
                <div class="kpi"><div class="label">Spend</div><div class="value" id="kpi-spend">-</div></div>
                <div class="kpi"><div class="label">Leads</div><div class="value" id="kpi-leads">-</div></div>
                <div class="kpi"><div class="label">Avg CPL</div><div class="value" id="kpi-cpl">-</div></div>
                <div class="kpi"><div class="label">Campaigns</div><div class="value" id="kpi-count">-</div></div>
            </div>
            """)

            # SNAPSHOT
            campaign_banner = gr.HTML("""
            <div class="snapshot">
                <h3>Performance Snapshot</h3>
                <p>Select a campaign to begin analysis.</p>
            </div>
            """)

            # AI SECTION
            gr.Markdown("### AI Insights")

            with gr.HTML():
                pass

            gr.HTML("""
            <div class="ai-grid">

                <button class="ai-card">
                    <h3>📊 Ads Analyst</h3>
                    <p>Deep performance analysis</p>
                </button>

                <div class="ai-card">
                    <h3>💰 Budget Optimizer</h3>
                    <p>Ready</p>
                </div>

                <div class="ai-card">
                    <h3>🎯 Keyword Intelligence</h3>
                    <p>Ready</p>
                </div>

                <div class="ai-card">
                    <h3>⚠️ Risk Detector</h3>
                    <p>Ready</p>
                </div>

                <div class="ai-card">
                    <h3>📈 Growth Finder</h3>
                    <p>Ready</p>
                </div>

                <div class="ai-card">
                    <h3>🧪 Experiment Ideas</h3>
                    <p>Ready</p>
                </div>

            </div>
            """)

            ads_output = gr.Markdown(
                value="Select a campaign and click Ads Analyst.",
                elem_id="ads-output"
            )

            gr.HTML('</div>')  # close workspace


    # ---------------- EVENTS ----------------

    campaign_table.select(
        fn=campaign_row_selected,
        inputs=[campaign_table, full_state],
        outputs=[campaign_state, campaign_banner],
    )

    ads_output  # keeps reference stable

    # ---------------- LOAD ----------------

    demo.load(
        fn=initial_data_load,
        outputs=[
            full_state,
            campaign_table,
            gr.Number(),  # unused visually now
            gr.Number(),
            gr.Number(),
            gr.Number(),
        ],
    )

    demo.load(fn=startup)

demo.queue()

if __name__ == "__main__":
    demo.launch()
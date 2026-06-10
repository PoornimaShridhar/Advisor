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

.sidebar {
    background: #f7f7f4;
    padding-right: 12px;
}

.workspace {
    background: white;
    border: 1px solid #e6e5e0;
    border-radius: 16px;
    padding: 18px;
}

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

.snapshot {
    border-top: 1px solid #e6e5e0;
    border-bottom: 1px solid #e6e5e0;
    padding: 14px 0;
    margin: 14px 0;
}

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

#ads-output {
    margin-top: 16px;
    padding: 16px;
    border: 1px solid #e6e5e0;
    border-radius: 12px;
    background: white;
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
# DATA
# ==================================================

def initial_data_load():
    dfs = load_google_ads_data()
    from app.ui.dashboard import get_dashboard_data

    spend, leads, cpl, count, formatted_df = get_dashboard_data()

    # Build KPI HTML (single source of truth)
    kpi_html = f"""
    <div class="kpi-strip">
        <div class="kpi"><div class="label">Spend</div><div class="value">£{spend:.2f}</div></div>
        <div class="kpi"><div class="label">Leads</div><div class="value">{leads}</div></div>
        <div class="kpi"><div class="label">Avg CPL</div><div class="value">£{cpl:.2f}</div></div>
        <div class="kpi"><div class="label">Campaigns</div><div class="value">{count}</div></div>
    </div>
    """

    return dfs, formatted_df, kpi_html


# ==================================================
# CAMPAIGN SELECT
# ==================================================

def campaign_row_selected(df, full_state, evt: gr.SelectData):
    row_index = evt.index[0]
    campaign_name = df.iloc[row_index]["Campaign"]

    campaign_state = on_campaign_select(full_state, campaign_name)

    print("SELECTED CAMPAIGN:", campaign_name, flush=True)
    print("STATE:", campaign_state, flush=True)

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
        print("🔥 ADS ANALYST CLICKED", flush=True)
        print("STATE:", state, flush=True)

        if not state:
            return "⚠️ Select a campaign first"

        dfs = state.get("full_dfs")
        campaign_name = state.get("campaign_name")

        print("DFS:", dfs is not None, flush=True)
        print("CAMPAIGN:", campaign_name, flush=True)

        if dfs is None or campaign_name is None:
            return "⚠️ Campaign state not properly initialized"

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

            # KPI STRIP (NOW FIXED)
            kpi_html = gr.HTML()

            # SNAPSHOT
            campaign_banner = gr.HTML("""
            <div class="snapshot">
                <h3>Performance Snapshot</h3>
                <p>Select a campaign to begin analysis.</p>
            </div>
            """)

            # AI SECTION
            gr.Markdown("### AI Insights")

            gr.HTML("""
            <div class="ai-grid">

                <div class="ai-card">
                    <h3>📊 Ads Analyst</h3>
                    <p>Click button below</p>
                </div>

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

            ads_card = gr.Button("📊 Run Ads Analyst", variant="primary")

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

    ads_card.click(
        fn=run_ads_card,
        inputs=campaign_state,
        outputs=ads_output
    )

    # ---------------- LOAD ----------------

    demo.load(
        fn=initial_data_load,
        outputs=[
            full_state,
            campaign_table,
            kpi_html
        ],
    )

    demo.load(fn=startup)

demo.queue()

if __name__ == "__main__":
    demo.launch()
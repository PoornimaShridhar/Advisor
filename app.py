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

/* ================================
   HEADER (Romer Dark System)
================================ */

#advisor-header {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;

    height: 80px;
    width: 100%;

    background: #070708;
    border-bottom: 1px solid #232426;

    z-index: 50;
}

/* inner container (replaces max-w-[1728px] mx-auto px-margin-safe) */
#advisor-header .header-inner {
    max-width: 1728px;
    height: 100%;

    margin: 0 auto;
    padding: 0 32px; /* px-margin-safe */

    display: flex;
    align-items: center;
    justify-content: space-between;
}

/* left group */
#advisor-header .brand {
    display: flex;
    align-items: center;
    gap: 8px; /* gap-sm */
}

/* avatar circle */
#advisor-header .avatar {
    width: 32px;
    height: 32px;

    border-radius: 999px;
    border: 1px solid #9A9DA3;

    display: flex;
    align-items: center;
    justify-content: center;

    font-family: Manrope, sans-serif;
    font-weight: 700;
    font-size: 14px;

    color: #e5e2e3;
}

/* title */
#advisor-header .title {
    font-family: Manrope, sans-serif;
    font-size: 24px;
    font-weight: 700;
    letter-spacing: -0.04em;

    color: #e5e2e3;
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

/* KPI */
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

/* REAL INTERACTIVE CARD */
.ai-button {
    all: unset;
    display: block;
    background: #ffffff;
    border: 1px solid #e6e5e0;
    border-radius: 12px;
    padding: 14px;
    min-height: 90px;
    cursor: pointer;
    transition: all 0.15s ease;
}

.ai-button:hover {
    border-color: #d6d3cc;
    transform: translateY(-1px);
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

        if dfs is None or campaign_name is None:
            return "⚠️ Campaign state not properly initialized"

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
    <div class="header-inner">

        <div class="brand">
        <div class="avatar">A</div>
        <div class="title">Advisor</div>
        </div>

    </div>
    </div>
    """)

    # ---------------- MAIN ----------------
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

            # KPI STRIP
            kpi_html = gr.HTML()

            # SNAPSHOT
            campaign_banner = gr.HTML("""
            <div class="snapshot">
                <h3>Performance Snapshot</h3>
                <p>Select a campaign to begin analysis.</p>
            </div>
            """)

            # AI INSIGHTS
            gr.Markdown("### AI Insights")

            with gr.Row():

                # ✅ CLICKABLE ADS ANALYST CARD
                ads_card = gr.Button(
                    value="📊 Ads Analyst\nClick to analyze campaign",
                    elem_classes=["ai-button"]
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

            # OUTPUT (BELOW CARDS)
            ads_output = gr.Markdown(
                value="Select a campaign and click Ads Analyst.",
                elem_id="ads-output"
            )


    # ---------------- EVENTS ----------------

    campaign_table.select(
        fn=campaign_row_selected,
        inputs=[campaign_table, full_state],
        outputs=[campaign_state, campaign_banner],
    )

    # ✅ RESTORED CLICK FUNCTIONALITY
    ads_card.click(
        fn=run_ads_card,
        inputs=campaign_state,
        outputs=ads_output
    )

    # ---------------- LOAD ----------------

    demo.load(
        fn=initial_data_load,
        outputs=[full_state, campaign_table, kpi_html],
    )

    demo.load(fn=startup)

demo.queue()

if __name__ == "__main__":
    demo.launch()
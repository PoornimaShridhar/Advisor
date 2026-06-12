import gradio as gr
import spaces

from app.db.repo import init_db
from app.controller.campaign_controller import on_campaign_select
from app.controller.session_loader import load_google_ads_data
from app.ads1.ads_analyst import run_ads_analyst_card


# ==================================================
# ROMER / ADVISOR DASHBOARD THEME
# ==================================================

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;520;600;700&family=Inter:wght@400;500;600&family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap');

:root {
    --custom-bg: #070708;
    --custom-divider: #232426;
    --custom-card-bg: #101112;
    --custom-sidebar: #0d0e0f;
    --custom-panel: #111214;
    --custom-text-muted: #9A9DA3;
    --custom-btn-primary: #5E6BFF;
    --on-surface: #e5e2e3;
    --on-surface-variant: #c6c5d8;
    --secondary: #50d8e9;
    --tertiary: #ffb689;
    --primary: #bec2ff;
}

html,
body,
.gradio-container {
    background: var(--custom-bg) !important;
    color: var(--on-surface) !important;
    font-family: Inter, sans-serif !important;
}

.gradio-container {
    max-width: 100% !important;
    padding: 0 !important;
}

.main,
.contain {
    max-width: none !important;
}

footer,
.api-docs,
.built-with {
    display: none !important;
}

/* ================================
   HEADER
================================ */

#advisor-header {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    height: 80px;
    width: 100%;
    background: var(--custom-bg);
    border-bottom: 1px solid var(--custom-divider);
    z-index: 50;
}

#advisor-header .header-inner {
    max-width: 1728px;
    height: 100%;
    margin: 0 auto;
    padding: 0 32px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}

#advisor-header .brand {
    display: flex;
    align-items: center;
    gap: 8px;
}

#advisor-header .avatar {
    width: 32px;
    height: 32px;
    border-radius: 999px;
    border: 1px solid var(--custom-text-muted);
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: Manrope, sans-serif;
    font-weight: 700;
    font-size: 14px;
    color: var(--on-surface);
}

#advisor-header .title {
    font-family: Manrope, sans-serif;
    font-size: 24px;
    line-height: 1.2;
    font-weight: 700;
    letter-spacing: 0;
    color: var(--on-surface);
}

/* ================================
   HERO
================================ */

#advisor-shell {
    max-width: 1728px;
    margin: 80px auto 0;
    padding: 0 32px 56px;
}

.hero-section {
    position: relative;
    padding: 128px 0 80px;
}

.hero-inner {
    max-width: 1516px;
    margin: 0 auto;
    width: 100%;
}

.hero-row {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    margin-bottom: 40px;
}

.hero-title {
    font-family: Manrope, sans-serif;
    font-size: 76px;
    line-height: 1.1;
    letter-spacing: 0;
    font-weight: 520;
    color: var(--on-surface) !important;
    max-width: 1000px;
    margin-bottom: 16px;
}

.hero-subtitle {
    font-family: Inter, sans-serif;
    font-size: 19px;
    line-height: 1.6;
    color: var(--custom-text-muted) !important;
    margin-bottom: 24px;
}

/* ================================
   DASHBOARD SHELL
================================ */

#dashboard-shell {
    width: 100%;
    min-height: 620px;
    display: flex;
    overflow: hidden;
    position: relative;
    background: var(--custom-card-bg);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 8px;
    box-shadow: 0 25px 50px rgba(0, 0, 0, 0.45), inset 0 1px 0 rgba(255, 255, 255, 0.10);
}

#dashboard-shell > .form,
#dashboard-shell > .block,
#dashboard-shell > div {
    border: 0 !important;
}

.dashboard-row {
    gap: 0 !important;
    width: 100%;
}

.campaign-sidebar {
    flex: 0 0 256px !important;
    min-width: 256px !important;
    max-width: 256px !important;
    background: var(--custom-sidebar);
    border-right: 1px solid var(--custom-divider);
    padding: 16px !important;
}

.center-workspace {
    background: #0a0a0b;
    padding: 24px !important;
    gap: 24px !important;
    min-width: 0;
}

.right-panel {
    flex: 0 0 320px !important;
    min-width: 320px !important;
    max-width: 320px !important;
    background: var(--custom-panel);
    border-left: 1px solid var(--custom-divider);
    padding: 16px !important;
}

.panel-label {
    color: var(--custom-text-muted);
    font-size: 10px;
    line-height: 1;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    font-weight: 700;
    opacity: 0.5;
    margin: 0 0 24px;
    padding: 0 16px;
}

/* ================================
   GRADIO COMPONENT RESET
================================ */

.campaign-sidebar .block,
.center-workspace .block,
.right-panel .block {
    background: transparent !important;
    border: 0 !important;
    box-shadow: none !important;
}

.campaign-sidebar .wrap,
.campaign-sidebar .dataframe,
.campaign-sidebar table {
    background: transparent !important;
}

.campaign-sidebar table {
    border-collapse: separate !important;
    border-spacing: 0 4px !important;
}

.campaign-sidebar th {
    display: none !important;
}

.campaign-sidebar td {
    background: transparent !important;
    border: 0 !important;
    color: var(--custom-text-muted) !important;
    font-size: 14px !important;
    padding: 9px 14px !important;
    white-space: normal !important;
}

.campaign-sidebar tr:hover td,
.campaign-sidebar tr.selected td {
    background: rgba(255, 255, 255, 0.04) !important;
    color: var(--on-surface) !important;
    border-radius: 6px !important;
}

.campaign-sidebar .table-wrap,
.campaign-sidebar .dataframe-container {
    max-height: 520px !important;
    overflow-y: auto !important;
}

/* ================================
   KPI / CHART / CARDS
================================ */

.kpi-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 16px;
}

.kpi-card {
    background: var(--custom-card-bg);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 8px;
    padding: 20px;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.10);
}

.kpi-top {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 12px;
    margin-bottom: 12px;
}

.kpi-label {
    color: var(--custom-text-muted);
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    font-weight: 700;
    opacity: 0.6;
}

.kpi-status {
    font-size: 9px;
    color: rgba(190, 194, 255, 0.45);
    text-transform: uppercase;
    letter-spacing: 0;
    white-space: nowrap;
}

.kpi-value {
    font-family: Manrope, sans-serif;
    font-size: 24px;
    line-height: 1.2;
    color: var(--on-surface);
    font-weight: 700;
}

.kpi-note {
    margin-top: 12px;
    color: var(--secondary);
    font-size: 11px;
}

.signal-card {
    background: var(--custom-card-bg);
    border: 1px solid var(--custom-divider);
    border-radius: 8px;
    padding: 16px;
    height: 220px;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.10);
    display: flex;
    flex-direction: column;
}

.signal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
}

.signal-title {
    font-size: 12px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: rgba(229, 226, 227, 0.6);
}

.signal-box {
    position: relative;
    flex: 1;
    overflow: hidden;
    border-radius: 6px;
    background: rgba(7, 7, 8, 0.5);
    border: 1px solid rgba(255, 255, 255, 0.02);
}

.grid-lines,
.vertical-lines {
    position: absolute;
    inset: 0;
    pointer-events: none;
}

.grid-lines {
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    padding: 8px 0;
    opacity: 0.12;
}

.grid-lines span {
    border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.vertical-lines {
    display: grid;
    grid-template-columns: repeat(6, 1fr);
}

.vertical-lines span {
    border-right: 1px solid rgba(255, 255, 255, 0.05);
}

.signal-card svg {
    position: absolute;
    bottom: 0;
    width: 100%;
    height: 80%;
}

.ai-row {
    gap: 12px !important;
}

.ai-card-html,
.ai-button-card {
    background: var(--custom-card-bg) !important;
    border: 1px solid var(--custom-divider) !important;
    border-radius: 8px !important;
    padding: 16px !important;
    min-height: 116px !important;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.08) !important;
}

.ai-card-html h3 {
    margin: 0 0 12px;
    padding-bottom: 12px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    color: var(--on-surface);
    font-size: 14px;
    font-weight: 700;
}

.ai-card-html p {
    margin: 0;
    color: var(--on-surface);
    font-size: 14px;
    line-height: 1.5;
}

.ai-button-card {
    color: var(--on-surface) !important;
    text-align: left !important;
    font-size: 14px !important;
    font-weight: 700 !important;
    transition: border-color 0.15s ease, transform 0.15s ease, background 0.15s ease;
    white-space: pre-line !important;
}

.ai-button-card:hover {
    border-color: rgba(94, 107, 255, 0.7) !important;
    background: #141519 !important;
    transform: translateY(-1px);
}

.snapshot {
    background: var(--custom-card-bg);
    border: 1px solid var(--custom-divider);
    border-radius: 8px;
    padding: 16px;
    color: var(--on-surface);
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.08);
}

.snapshot h3 {
    margin: 0 0 8px;
    font-size: 14px;
    font-weight: 700;
}

.snapshot p {
    margin: 0;
    color: var(--custom-text-muted);
    font-size: 14px;
}

#ads-output {
    margin-top: 0;
    padding: 16px;
    min-height: 140px;
    border: 1px solid var(--custom-divider);
    border-radius: 8px;
    background: var(--custom-card-bg);
    color: var(--on-surface);
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.08);
}

#ads-output,
#ads-output * {
    color: var(--on-surface) !important;
}

.advisor-intel-title {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
    padding: 0 4px 20px;
    margin-bottom: 8px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    font-size: 14px;
    font-weight: 700;
}

.advisor-intel-title .material-symbols-outlined {
    color: var(--secondary);
    font-size: 20px;
}

.pulse-dot {
    width: 6px;
    height: 6px;
    border-radius: 999px;
    background: var(--secondary);
    display: inline-block;
}

.intel-section {
    margin-top: 28px;
}

.intel-label {
    color: var(--custom-text-muted);
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    opacity: 0.5;
    margin-bottom: 12px;
}

.intel-box {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 8px;
    padding: 16px;
    color: var(--on-surface);
    font-size: 14px;
    line-height: 1.5;
}

.text-primary {
    color: var(--primary);
    font-weight: 700;
}

.text-secondary {
    color: var(--secondary);
    font-weight: 600;
}

@media (max-width: 1200px) {
    #dashboard-shell,
    .dashboard-row {
        flex-direction: column !important;
    }

    .campaign-sidebar,
    .right-panel {
        flex: auto !important;
        min-width: 100% !important;
        max-width: 100% !important;
        border-left: 0;
    }

    .campaign-sidebar {
        border-right: 0;
        border-bottom: 1px solid var(--custom-divider);
    }

    .right-panel {
        border-top: 1px solid var(--custom-divider);
    }
}

@media (max-width: 800px) {
    #advisor-shell {
        padding: 0 16px 32px;
    }

    #advisor-header .header-inner {
        padding: 0 16px;
    }

    .hero-section {
        padding: 80px 0 48px;
    }

    .hero-title {
        font-size: 42px;
    }

    .kpi-grid {
        grid-template-columns: 1fr;
    }
}
"""


# ==================================================
# INIT
# ==================================================

def startup():
    try:
        init_db()
        print("DB initialized successfully", flush=True)
    except Exception as e:
        print("DB failed:", e, flush=True)


# ==================================================
# HTML HELPERS
# ==================================================

def format_money(value):
    try:
        return f"&pound;{float(value):,.2f}"
    except (TypeError, ValueError):
        return "&pound;0.00"


def build_hero_html(spend, leads, cpl, count):
    return f"""
    <section class="hero-section">
        <div class="hero-inner">
            <div class="hero-row">
                <div>
                    <h1 class="hero-title">AI-powered Google Ads optimization</h1>
                    <p class="hero-subtitle">
                        Spend {format_money(spend)} | Leads {leads} | Avg CPL {format_money(cpl)} | Campaigns {count}
                    </p>
                </div>
                <div></div>
            </div>
        </div>
    </section>
    """


def build_kpi_html(spend, leads, cpl, count):
    return f"""
    <div class="kpi-grid">
        <div class="kpi-card">
            <div class="kpi-top">
                <div class="kpi-label">Spend</div>
                <div class="kpi-status">[SYNC: ACTIVE]</div>
            </div>
            <div class="kpi-value">{format_money(spend)}</div>
            <div class="kpi-note">Live Google Ads data</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-top">
                <div class="kpi-label">Leads</div>
                <div class="kpi-status">[QUEUE: {leads}]</div>
            </div>
            <div class="kpi-value">{leads}</div>
            <div class="kpi-note">Tracked conversions</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-top">
                <div class="kpi-label">CPL</div>
                <div class="kpi-status">[HEARTBEAT: OK]</div>
            </div>
            <div class="kpi-value">{format_money(cpl)}</div>
            <div class="kpi-note">Cost per lead</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-top">
                <div class="kpi-label">Campaigns</div>
                <div class="kpi-status">[LOAD: OPT]</div>
            </div>
            <div class="kpi-value">{count}</div>
            <div class="kpi-note">Available for analysis</div>
        </div>
    </div>
    """


SIGNAL_FLOW_HTML = """
<div class="signal-card">
    <div class="signal-header">
        <div>
            <span class="signal-title">Signal Flow</span>
            <span class="kpi-status"> [LATENCY: 12ms]</span>
        </div>
        <div class="kpi-status">
            <span style="color: var(--primary);">Revenue</span>
            <span style="margin-left: 16px; color: var(--custom-text-muted);">Goal</span>
        </div>
    </div>
    <div class="signal-box">
        <div class="grid-lines"><span></span><span></span><span></span><span></span></div>
        <div class="vertical-lines"><span></span><span></span><span></span><span></span><span></span><span></span></div>
        <svg preserveAspectRatio="none" viewBox="0 0 100 100">
            <defs>
                <linearGradient id="gradient-flow-v3" x1="0%" x2="0%" y1="0%" y2="100%">
                    <stop offset="0%" stop-color="#5E6BFF" stop-opacity="0.15"></stop>
                    <stop offset="100%" stop-color="#5E6BFF" stop-opacity="0"></stop>
                </linearGradient>
                <filter height="140%" id="glow" width="140%" x="-20%" y="-20%">
                    <feGaussianBlur result="blur" stdDeviation="1.5"></feGaussianBlur>
                    <feComposite in="SourceGraphic" in2="blur" operator="over"></feComposite>
                </filter>
            </defs>
            <path d="M0,80 C20,78 35,85 50,65 C65,45 80,30 100,25 L100,100 L0,100 Z" fill="url(#gradient-flow-v3)"></path>
            <path d="M0,80 C20,78 35,85 50,65 C65,45 80,30 100,25" fill="none" filter="url(#glow)" stroke="#5E6BFF" stroke-linecap="round" stroke-width="1"></path>
            <circle cx="20" cy="78" fill="#5E6BFF" r="1"></circle>
            <circle cx="50" cy="65" fill="white" r="1.5" stroke="#5E6BFF" stroke-width="0.5"></circle>
            <circle cx="80" cy="30" fill="#5E6BFF" r="1"></circle>
        </svg>
        <div style="position: absolute; bottom: 4px; right: 8px; color: rgba(154,157,163,0.35); font-size: 9px;">t: 127.4s</div>
        <div style="position: absolute; top: 8px; left: 8px; color: rgba(154,157,163,0.35); font-size: 9px;">y: $V</div>
    </div>
</div>
"""


RIGHT_PANEL_HTML = """
<div class="advisor-intel-title">
    <div style="display:flex;align-items:center;gap:10px;">
        <span class="material-symbols-outlined">bolt</span>
        Advisor Intelligence
    </div>
    <span class="pulse-dot"></span>
</div>
<div class="intel-section">
    <div class="intel-label">Recommended Action</div>
    <div class="intel-box">
        Select a campaign, then run <span class="text-primary">Ads Analyst</span> to generate recommendations.
    </div>
</div>
<div class="intel-section">
    <div class="intel-label">Signal Summary</div>
    <div class="intel-box">
        Campaign metrics are synced from your Google Ads data and prepared for AI analysis.
    </div>
</div>
<div class="intel-section">
    <div class="intel-label">Decision Log</div>
    <div class="intel-box">
        <span class="text-secondary">Ready</span> for campaign review.
    </div>
</div>
"""


def ai_card(title, body):
    return f"""
    <div class="ai-card-html">
        <h3>{title}</h3>
        <p>{body}</p>
    </div>
    """


# ==================================================
# DATA
# ==================================================

def initial_data_load():
    dfs = load_google_ads_data()
    from app.ui.dashboard import get_dashboard_data

    spend, leads, cpl, count, formatted_df = get_dashboard_data()
    campaign_df = formatted_df[["Campaign"]] if "Campaign" in formatted_df.columns else formatted_df
    hero_html = build_hero_html(spend, leads, cpl, count)
    kpi_html = build_kpi_html(spend, leads, cpl, count)
    return dfs, campaign_df, hero_html, kpi_html


# ==================================================
# CAMPAIGN SELECT
# ==================================================

def campaign_row_selected(df, full_state, evt: gr.SelectData):
    row_index = evt.index[0]
    campaign_name = df.iloc[row_index]["Campaign"]
    campaign_state = on_campaign_select(full_state, campaign_name)
    banner_html = f"""
    <div class="snapshot">
        <h3>{campaign_name}</h3>
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
            return "Select a campaign first."

        dfs = state.get("full_dfs")
        campaign_name = state.get("campaign_name")

        if dfs is None or campaign_name is None:
            return "Campaign state is not properly initialized."

        return run_ads_analyst_card(dfs, campaign_name=campaign_name)

    except Exception as e:
        return f"Analysis failed: {e}"


# ==================================================
# UI
# ==================================================

with gr.Blocks(fill_height=True, fill_width=True, css=CSS) as demo:
    full_state = gr.State()
    campaign_state = gr.State()

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

    with gr.Column(elem_id="advisor-shell"):
        hero_html = gr.HTML()

        with gr.Row(elem_id="dashboard-shell", elem_classes=["dashboard-row"]):
            with gr.Column(elem_classes=["campaign-sidebar"]):
                gr.HTML('<div class="panel-label">Campaigns</div>')
                campaign_table = gr.Dataframe(
                    show_label=False,
                    interactive=True,
                    wrap=True,
                    row_count=(1, "dynamic"),
                    col_count=(1, "dynamic"),
                )

            with gr.Column(scale=1, elem_classes=["center-workspace"]):
                kpi_html = gr.HTML()
                gr.HTML(SIGNAL_FLOW_HTML)

                campaign_banner = gr.HTML("""
                <div class="snapshot">
                    <h3>Performance Snapshot</h3>
                    <p>Select a campaign to begin analysis.</p>
                </div>
                """)

                with gr.Row(elem_classes=["ai-row"]):
                    ads_card = gr.Button(
                        value="Ads Analyst\nCampaign insights.",
                        elem_classes=["ai-button-card"],
                    )
                    gr.HTML(ai_card("Budget Optimizer", "Where to adjust spend?"))
                    gr.HTML(ai_card("Keyword Inspector", "Winning versus wasting keywords."))

                with gr.Row(elem_classes=["ai-row"]):
                    gr.HTML(ai_card("Search Term Cleaner", "Optimize search term list."))
                    gr.HTML(ai_card("Growth Finder", "Where to scale?"))
                    gr.HTML(ai_card("Campaign Doctor", "What limits performance?"))

                ads_output = gr.Markdown(
                    value="Select a campaign and click Ads Analyst.",
                    elem_id="ads-output",
                )

            with gr.Column(elem_classes=["right-panel"]):
                gr.HTML(RIGHT_PANEL_HTML)

    campaign_table.select(
        fn=campaign_row_selected,
        inputs=[campaign_table, full_state],
        outputs=[campaign_state, campaign_banner],
    )

    ads_card.click(
        fn=run_ads_card,
        inputs=campaign_state,
        outputs=ads_output,
    )

    demo.load(
        fn=initial_data_load,
        outputs=[full_state, campaign_table, hero_html, kpi_html],
    )

    demo.load(fn=startup)

demo.queue()

if __name__ == "__main__":
    demo.launch()

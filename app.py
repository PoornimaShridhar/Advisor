import gradio as gr
import pandas as pd
import spaces

from app.db.repo import init_db
from app.controller.campaign_controller import on_campaign_select
from app.controller.session_loader import load_google_ads_data
from app.ads1.ads_analyst import run_ads_analyst_card


CSS = """
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700&family=Inter:wght@400;500;600;700&display=swap');

:root {
    --advisor-bg: #070708;
    --advisor-panel: #101112;
    --advisor-panel-soft: rgba(16, 17, 18, 0.82);
    --advisor-border: #232426;
    --advisor-border-soft: rgba(255, 255, 255, 0.05);
    --advisor-text: #e5e2e3;
    --advisor-muted: #9a9da3;
    --advisor-primary: #5e6bff;
}

body,
.gradio-container {
    background:
        radial-gradient(circle at top left, rgba(94, 107, 255, 0.14), transparent 25%),
        radial-gradient(circle at top right, rgba(80, 216, 233, 0.08), transparent 20%),
        var(--advisor-bg) !important;
    color: var(--advisor-text) !important;
    font-family: 'Inter', sans-serif !important;
}

.gradio-container {
    max-width: 1728px !important;
    margin: 0 auto !important;
}

#advisor-shell {
    padding: 24px 32px 40px;
}

#advisor-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    margin-bottom: 24px;
    padding-bottom: 18px;
    border-bottom: 1px solid var(--advisor-border);
}

.brand {
    display: flex;
    align-items: center;
    gap: 12px;
}

.brand-badge {
    width: 36px;
    height: 36px;
    border-radius: 999px;
    border: 1px solid #454655;
    background: rgba(255, 255, 255, 0.02);
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--advisor-text);
    font-weight: 700;
}

#advisor-title {
    font-size: 28px;
    font-weight: 700;
    letter-spacing: -0.04em;
    color: var(--advisor-text);
}

#advisor-subtitle {
    font-size: 14px;
    color: var(--advisor-muted);
}

.layout-shell {
    display: grid;
    grid-template-columns: minmax(280px, 320px) minmax(0, 1fr);
    gap: 20px;
}

.sidebar-panel,
.main-panel,
.selected-panel,
.output-panel,
.ai-card,
.metric-card {
    background: rgba(16, 17, 18, 0.92);
    border: 1px solid var(--advisor-border-soft);
    border-radius: 16px;
    box-shadow: inset 0 1px 0 0 rgba(255, 255, 255, 0.06);
}

.sidebar-panel {
    padding: 18px;
    position: sticky;
    top: 18px;
    height: fit-content;
}

.panel-title {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.18em;
    color: rgba(154, 157, 163, 0.72);
    margin-bottom: 14px;
}

#campaign-selector label {
    background: transparent !important;
    border: 1px solid transparent;
    border-radius: 12px;
    padding: 10px 12px;
    margin-bottom: 6px;
    transition: background 0.16s ease, border-color 0.16s ease, color 0.16s ease;
}

#campaign-selector label:hover {
    background: rgba(255, 255, 255, 0.04) !important;
    color: var(--advisor-text) !important;
}

#campaign-selector input[type="radio"]:checked + label {
    background: rgba(94, 107, 255, 0.16) !important;
    border-color: rgba(94, 107, 255, 0.65);
    color: #ffffff !important;
}

.main-panel {
    padding: 22px;
    min-height: 720px;
}

.hero-grid,
.selected-metrics,
.ai-grid {
    display: grid;
    gap: 12px;
}

.hero-grid {
    grid-template-columns: repeat(4, minmax(0, 1fr));
    margin-bottom: 18px;
}

.metric-card {
    background: rgba(7, 7, 8, 0.72);
    padding: 16px;
}

.metric-label,
.selected-eyebrow,
.panel-kicker {
    font-size: 10px;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: rgba(154, 157, 163, 0.72);
}

.metric-label {
    margin-bottom: 10px;
}

.metric-value {
    font-family: 'Manrope', sans-serif;
    font-size: 26px;
    font-weight: 700;
    letter-spacing: -0.05em;
    color: #e5e2e3;
}

.metric-footnote {
    margin-top: 8px;
    font-size: 12px;
    color: var(--advisor-muted);
}

.selected-panel {
    padding: 18px;
    margin-bottom: 18px;
}

.selected-title {
    font-size: 24px;
    font-weight: 700;
    letter-spacing: -0.05em;
    color: #ffffff;
    margin-top: 8px;
}

.selected-status {
    margin-top: 6px;
    color: var(--advisor-muted);
    font-size: 13px;
}

.selected-metrics {
    grid-template-columns: repeat(4, minmax(0, 1fr));
    margin-top: 18px;
}

.selected-metric {
    background: rgba(7, 7, 8, 0.72);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 12px;
    padding: 14px;
}

.selected-metric .label {
    font-size: 10px;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: rgba(154, 157, 163, 0.72);
}

.selected-metric .value {
    margin-top: 8px;
    font-size: 20px;
    font-weight: 700;
    color: #e5e2e3;
}

.selected-metric .hint {
    margin-top: 4px;
    font-size: 12px;
    color: var(--advisor-muted);
}

.ai-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
    margin-top: 12px;
}

.ai-card {
    background: rgba(7, 7, 8, 0.72);
    padding: 14px;
    min-height: 96px;
}

.ai-card h3 {
    font-size: 14px;
    margin-bottom: 6px;
    color: #ffffff;
}

.ai-card p {
    font-size: 12px;
    color: var(--advisor-muted);
}

.output-panel {
    margin-top: 16px;
    padding: 16px;
}

#ads-output {
    color: #e5e2e3;
    margin-top: 16px;
    padding: 16px;
    border: 1px solid var(--advisor-border-soft);
    border-radius: 16px;
    background: rgba(7, 7, 8, 0.72);
}

button.primary,
.primary {
    background: var(--advisor-primary) !important;
    border-color: var(--advisor-primary) !important;
    color: #f0f1f2 !important;
}

@media (max-width: 1100px) {
    .layout-shell {
        grid-template-columns: 1fr;
    }

    .hero-grid,
    .selected-metrics,
    .ai-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }

    .sidebar-panel {
        position: static;
    }
}

@media (max-width: 720px) {
    #advisor-shell {
        padding: 18px;
    }

    #advisor-header {
        flex-direction: column;
        align-items: flex-start;
    }

    .hero-grid,
    .selected-metrics,
    .ai-grid {
        grid-template-columns: 1fr;
    }
}
"""


def startup():
    try:
        init_db()
        print("DB initialized successfully", flush=True)
    except Exception as exc:
        print("DB failed:", exc, flush=True)


def _format_money(value):
    return f"£{value:,.2f}"


def _campaign_frame(dfs):
    campaigns = dfs.get("campaigns") if dfs else None
    if campaigns is None or campaigns.empty:
        return pd.DataFrame(columns=["id", "name", "status", "impressions", "clicks", "cost", "ctr", "conversions"])

    frame = campaigns.copy()
    for column in ["impressions", "clicks", "cost", "ctr", "conversions"]:
        if column not in frame:
            frame[column] = 0
        frame[column] = frame[column].fillna(0)
    return frame


def _kpi_html(frame):
    if frame.empty:
        spend = leads = cpl = ctr = 0
    else:
        spend = float(frame["cost"].sum())
        leads = int(frame["conversions"].sum())
        total_clicks = float(frame["clicks"].sum())
        total_impressions = float(frame["impressions"].sum())
        ctr = (total_clicks / total_impressions * 100) if total_impressions else 0
        cpl = (spend / leads) if leads else 0

    return f"""
    <div class="hero-grid">
        <div class="metric-card"><div class="metric-label">Spend</div><div class="metric-value">{_format_money(spend)}</div><div class="metric-footnote">Live Google Ads totals</div></div>
        <div class="metric-card"><div class="metric-label">Leads</div><div class="metric-value">{leads}</div><div class="metric-footnote">Attributed conversions</div></div>
        <div class="metric-card"><div class="metric-label">Avg CPL</div><div class="metric-value">{_format_money(cpl)}</div><div class="metric-footnote">Across all campaigns</div></div>
        <div class="metric-card"><div class="metric-label">CTR</div><div class="metric-value">{ctr:.2f}%</div><div class="metric-footnote">Click-through rate</div></div>
    </div>
    """


def _selected_campaign_html(campaign_state):
    if not campaign_state:
        return """
        <div class="selected-panel">
            <div class="selected-eyebrow">Selected campaign</div>
            <div class="selected-title">Select a campaign to begin analysis</div>
            <div class="selected-status">The live Google Ads campaign data will appear here.</div>
        </div>
        """

    campaign_df = campaign_state.get("campaign_df")
    if campaign_df is None or campaign_df.empty:
        return """
        <div class="selected-panel">
            <div class="selected-eyebrow">Selected campaign</div>
            <div class="selected-title">No campaign data available</div>
            <div class="selected-status">The API returned an empty campaign slice.</div>
        </div>
        """

    row = campaign_df.iloc[0]
    campaign_name = campaign_state.get("campaign_name", row.get("name", "Campaign"))
    spend = float(row.get("cost", 0) or 0)
    leads = int(row.get("conversions", 0) or 0)
    cpl = spend / leads if leads else 0
    ctr = float(row.get("ctr", 0) or 0)
    impressions = int(row.get("impressions", 0) or 0)
    clicks = int(row.get("clicks", 0) or 0)
    status = row.get("status", "UNKNOWN")

    return f"""
    <div class="selected-panel">
        <div class="selected-eyebrow">Selected campaign</div>
        <div class="selected-title">{campaign_name}</div>
        <div class="selected-status">Status: {status} | Live API data is scoped to this campaign.</div>
        <div class="selected-metrics">
            <div class="selected-metric"><div class="label">Spend</div><div class="value">{_format_money(spend)}</div><div class="hint">Selected campaign spend</div></div>
            <div class="selected-metric"><div class="label">Leads</div><div class="value">{leads}</div><div class="hint">Conversions recorded</div></div>
            <div class="selected-metric"><div class="label">CPL</div><div class="value">{_format_money(cpl)}</div><div class="hint">Cost per lead</div></div>
            <div class="selected-metric"><div class="label">CTR</div><div class="value">{ctr:.4f}</div><div class="hint">Click-through rate</div></div>
        </div>
        <div class="selected-metrics" style="margin-top: 12px;">
            <div class="selected-metric"><div class="label">Impressions</div><div class="value">{impressions:,}</div><div class="hint">Visibility in the last 30 days</div></div>
            <div class="selected-metric"><div class="label">Clicks</div><div class="value">{clicks:,}</div><div class="hint">Traffic driven by the campaign</div></div>
            <div class="selected-metric"><div class="label">Selected</div><div class="value">Active</div><div class="hint">This campaign is in focus</div></div>
            <div class="selected-metric"><div class="label">Analytics</div><div class="value">Ready</div><div class="hint">Run the Ads Analyst card below</div></div>
        </div>
    </div>
    """


def initial_data_load():
    dfs = load_google_ads_data()
    frame = _campaign_frame(dfs)
    campaign_names = frame["name"].tolist() if not frame.empty else []
    selected_campaign = campaign_names[0] if campaign_names else None
    selected_state = on_campaign_select(dfs, selected_campaign) if selected_campaign else None

    return (
        dfs,
        selected_state,
        gr.update(choices=campaign_names, value=selected_campaign),
        _kpi_html(frame),
        _selected_campaign_html(selected_state),
        _selected_campaign_html(selected_state),
    )


def campaign_row_selected(campaign_name, full_state):
    if not full_state or not campaign_name:
        return {}, _selected_campaign_html(None), _selected_campaign_html(None)

    campaign_state = on_campaign_select(full_state, campaign_name)
    return campaign_state, _selected_campaign_html(campaign_state), _selected_campaign_html(campaign_state)


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
    except Exception as exc:
        return f"⚠️ Analysis failed: {exc}"


with gr.Blocks(css=CSS) as demo:
    full_state = gr.State()
    campaign_state = gr.State()

    gr.HTML(
        """
        <div id="advisor-shell">
            <div id="advisor-header">
                <div class="brand">
                    <div class="brand-badge">A</div>
                    <div>
                        <div id="advisor-title">Advisor</div>
                        <div id="advisor-subtitle">AI-powered Google Ads optimization</div>
                    </div>
                </div>
                <div class="selected-eyebrow">Live Google Ads data</div>
            </div>
            <div class="panel-kicker">AI-powered control room</div>
            <h1 style="font-family: Manrope, sans-serif; font-size: clamp(42px, 5vw, 76px); line-height: 1.05; letter-spacing: -0.055em; font-weight: 600; margin: 6px 0 10px;">AI-powered Google Ads optimization</h1>
            <p style="max-width: 900px; color: #9a9da3; font-size: 18px; line-height: 1.6; margin: 0 0 24px;">Live campaign data, a selected-campaign focus rail, and the same LLM-backed Ads Analyst flow you already have in app.py.</p>
        </div>
        """
    )

    with gr.Row(elem_classes=["layout-shell"]):
        with gr.Column(scale=1, elem_classes=["sidebar-panel"]):
            gr.HTML("<div class='panel-title'>Campaigns</div>")
            campaign_selector = gr.Radio(
                choices=[],
                value=None,
                show_label=False,
                interactive=True,
                elem_id="campaign-selector",
            )

        with gr.Column(scale=3, elem_classes=["main-panel"]):
            kpi_html = gr.HTML()
            campaign_banner = gr.HTML()
            campaign_detail = gr.HTML(elem_classes=["output-panel"])

            gr.HTML(
                """
                <div class="panel-kicker">AI Insights</div>
                <p style="color: #9a9da3; margin: 8px 0 0;">The Ads Analyst card still invokes the same LLM-backed workflow. The other cards remain presentation placeholders.</p>
                """
            )

            with gr.Row(elem_classes=["ai-grid"]):
                ads_card = gr.Button(
                    value="Run ad analytics\nAds Analyst",
                    variant="primary",
                    elem_classes=["ai-button"],
                )
                gr.HTML("<div class='ai-card'><h3>Budget Optimizer</h3><p>Ready</p></div>")
                gr.HTML("<div class='ai-card'><h3>Keyword Intelligence</h3><p>Ready</p></div>")

            with gr.Row(elem_classes=["ai-grid"]):
                gr.HTML("<div class='ai-card'><h3>Risk Detector</h3><p>Ready</p></div>")
                gr.HTML("<div class='ai-card'><h3>Growth Finder</h3><p>Ready</p></div>")
                gr.HTML("<div class='ai-card'><h3>Experiment Ideas</h3><p>Ready</p></div>")

            ads_output = gr.Markdown(
                value="Select a campaign and click Run ad analytics.",
                elem_id="ads-output",
            )

    campaign_selector.change(
        fn=campaign_row_selected,
        inputs=[campaign_selector, full_state],
        outputs=[campaign_state, campaign_banner, campaign_detail],
    )

    ads_card.click(
        fn=run_ads_card,
        inputs=campaign_state,
        outputs=ads_output,
    )

    demo.load(
        fn=initial_data_load,
        outputs=[full_state, campaign_state, campaign_selector, kpi_html, campaign_banner, campaign_detail],
    )

    demo.load(fn=startup)

demo.queue()

if __name__ == "__main__":
    demo.launch()
print("APP STARTED", flush=True)

import gradio as gr
import spaces

from app.db.repo import init_db
print("IMPORT 1 OK", flush=True)
from app.controller.campaign_controller import on_campaign_select
print("IMPORT 2 OK", flush=True)
from app.controller.session_loader import load_google_ads_data
print("IMPORT 3 OK", flush=True)
from app.ads1.ads_analyst import run_ads_analyst_card
print("IMPORT 4 OK", flush=True)
from app.ads1.search_term_optimizer import run_search_term_optimizer

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
    color-scheme: dark !important;
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

.gradio-container,
.gradio-container * {
    color: var(--on-surface);
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
    font-size: 76px !important;
    line-height: 1.1 !important;
    letter-spacing: 0;
    font-weight: 520 !important;
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
    color: #ffffff !important;
    font-size: 10px;
    line-height: 1;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    font-weight: 700;
    opacity: 1;
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

.campaign-radio,
.campaign-radio > div,
.campaign-radio fieldset,
.campaign-radio .wrap {
    background: transparent !important;
    border: 0 !important;
    box-shadow: none !important;
    padding: 0 !important;
    margin: 0 !important;
}

.campaign-radio .container,
.campaign-radio .options,
.campaign-radio [role="radiogroup"] {
    display: flex !important;
    flex-direction: column !important;
    gap: 4px !important;
    overflow: visible !important;
    max-height: none !important;
}

.campaign-radio label {
    display: flex !important;
    align-items: center !important;
    gap: 12px !important;
    width: 100% !important;
    min-height: 36px !important;
    margin: 0 !important;
    padding: 8px 12px !important;
    border: 1px solid transparent !important;
    border-radius: 6px !important;
    background: transparent !important;
    color: var(--custom-text-muted) !important;
    font-size: 14px !important;
    line-height: 1.35 !important;
    cursor: pointer !important;
}

.campaign-radio label::before {
    content: "grid_view";
    font-family: "Material Symbols Outlined";
    font-size: 18px;
    line-height: 1;
    color: rgba(154, 157, 163, 0.55);
    flex: 0 0 auto;
}

.campaign-radio label:hover,
.campaign-radio label:has(input:checked) {
    background: rgba(255, 255, 255, 0.04) !important;
    border-color: rgba(255, 255, 255, 0.05) !important;
    color: var(--on-surface) !important;
}

.campaign-radio label:has(input:checked)::before {
    color: var(--secondary);
}

.campaign-radio input {
    display: none !important;
}

.campaign-radio span {
    color: inherit !important;
    white-space: normal !important;
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
    color: #ffffff !important;
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    font-weight: 700;
    opacity: 0.6;
}

.kpi-status {
    font-size: 9px;
    color: rgba(255, 255, 255, 0.68) !important;
    text-transform: uppercase;
    letter-spacing: 0;
    white-space: nowrap;
}

.kpi-value {
    font-family: Manrope, sans-serif;
    font-size: 24px;
    line-height: 1.2;
    color: #ffffff !important;
    font-weight: 700;
}

.kpi-note {
    margin-top: 12px;
    font-size: 11px;
    font-weight: 600;
}

.note-sky {
    color: #50d8e9 !important;
}

.note-brown {
    color: #c88a5a !important;
}

.note-olive {
    color: #a9b75f !important;
}

.note-violet {
    color: #bec2ff !important;
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
    align-items: stretch !important;
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

.ai-row > *,
.ai-row .block {
    align-self: stretch !important;
}

.ai-card-html h3 {
    margin: 0 0 12px;
    padding-bottom: 12px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    color: #ffffff !important;
    font-size: 14px;
    font-weight: 700;
}

.ai-card-html p {
    margin: 0;
    color: #ffffff !important;
    font-size: 14px;
    line-height: 1.5;
}

.ai-button-card {
    background: var(--custom-card-bg) !important;
    border: 1px solid var(--custom-divider) !important;
    border-radius: 8px !important;
    color: var(--on-surface) !important;
    text-align: left !important;
    font-size: 14px !important;
    font-weight: 700 !important;
    transition: border-color 0.15s ease, transform 0.15s ease, background 0.15s ease;
    white-space: pre-line !important;
    margin: 0 !important;
    height: 116px !important;
}

.ai-button-card button,
button.ai-button-card {
    height: 100% !important;
    min-height: 116px !important;
    margin: 0 !important;
    padding: 16px !important;
    align-items: flex-start !important;
    justify-content: flex-start !important;
    text-align: left !important;
    white-space: pre-line !important;
    background: var(--custom-card-bg) !important;
    color: var(--on-surface) !important;
    border: 1px solid var(--custom-divider) !important;
    border-radius: 8px !important;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.08) !important;
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
    color: #ffffff !important;
}

.advisor-intel-title * {
    color: #ffffff !important;
}

.advisor-intel-title .material-symbols-outlined {
    color: #ffffff !important;
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
    color: #c7c9d1 !important;
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    opacity: 1;
    margin-bottom: 12px;
}

.intel-box {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 8px;
    padding: 16px;
    color: #ffffff !important;
    font-size: 14px;
    line-height: 1.5;
}

.intel-box * {
    color: #ffffff !important;
}

.text-primary {
    color: #ffffff !important;
    font-weight: 700;
}

.text-secondary {
    color: #ffffff !important;
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
        font-size: 42px !important;
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


def format_number(value):
    try:
        return f"{float(value):,.0f}"
    except (TypeError, ValueError):
        return "0"


def format_percent(value):
    try:
        numeric = float(value)
        if abs(numeric) <= 1:
            numeric *= 100
        return f"{numeric:.2f}%"
    except (TypeError, ValueError):
        return "0.00%"


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
            <div class="kpi-note note-sky">Live Google Ads data</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-top">
                <div class="kpi-label">Leads</div>
                <div class="kpi-status">[QUEUE: {leads}]</div>
            </div>
            <div class="kpi-value">{leads}</div>
            <div class="kpi-note note-brown">Tracked conversions</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-top">
                <div class="kpi-label">CPL</div>
                <div class="kpi-status">[HEARTBEAT: OK]</div>
            </div>
            <div class="kpi-value">{format_money(cpl)}</div>
            <div class="kpi-note note-olive">Cost per lead</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-top">
                <div class="kpi-label">Campaigns</div>
                <div class="kpi-status">[LOAD: OPT]</div>
            </div>
            <div class="kpi-value">{count}</div>
            <div class="kpi-note note-violet">Available for analysis</div>
        </div>
    </div>
    """


def build_campaign_kpi_html(campaign_df):
    if campaign_df is None or campaign_df.empty:
        return build_kpi_html(0, 0, 0, 0)

    spend = campaign_df["cost"].sum() if "cost" in campaign_df else 0
    clicks = campaign_df["clicks"].sum() if "clicks" in campaign_df else 0
    conversions = campaign_df["conversions"].sum() if "conversions" in campaign_df else 0
    cpl = spend / conversions if conversions else 0

    if "ctr" in campaign_df:
        ctr = campaign_df["ctr"].mean()
    else:
        impressions = campaign_df["impressions"].sum() if "impressions" in campaign_df else 0
        ctr = clicks / impressions if impressions else 0

    return f"""
    <div class="kpi-grid">
        <div class="kpi-card">
            <div class="kpi-top">
                <div class="kpi-label">Spend</div>
                <div class="kpi-status">[CAMPAIGN]</div>
            </div>
            <div class="kpi-value">{format_money(spend)}</div>
            <div class="kpi-note note-sky">Selected campaign spend</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-top">
                <div class="kpi-label">Clicks</div>
                <div class="kpi-status">[TRAFFIC]</div>
            </div>
            <div class="kpi-value">{format_number(clicks)}</div>
            <div class="kpi-note note-brown">Campaign traffic</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-top">
                <div class="kpi-label">CPL</div>
                <div class="kpi-status">[EFFICIENCY]</div>
            </div>
            <div class="kpi-value">{format_money(cpl)}</div>
            <div class="kpi-note note-olive">{format_number(conversions)} leads recorded</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-top">
                <div class="kpi-label">CTR</div>
                <div class="kpi-status">[RESPONSE]</div>
            </div>
            <div class="kpi-value">{format_percent(ctr)}</div>
            <div class="kpi-note note-violet">Click-through rate</div>
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
    print("STARTING DATA LOAD", flush=True)
    dfs = load_google_ads_data()
    print("GOOGLE ADS DATA LOADED", flush=True)
    from app.ui.dashboard import get_dashboard_data

    spend, leads, cpl, count, formatted_df = get_dashboard_data()
    print("DASHBOARD DATA LOADED", flush=True)
    campaign_choices = (
        formatted_df["Campaign"].dropna().astype(str).tolist()
        if "Campaign" in formatted_df.columns
        else []
    )
    hero_html = build_hero_html(spend, leads, cpl, count)
    kpi_html = build_kpi_html(spend, leads, cpl, count)
    return dfs, gr.update(choices=campaign_choices, value=None), hero_html, kpi_html


# ==================================================
# CAMPAIGN SELECT
# ==================================================

def campaign_selected(campaign_name, full_state):
    if not campaign_name:
        return None, gr.update()

    campaign_state = on_campaign_select(full_state, campaign_name)
    return campaign_state, build_campaign_kpi_html(campaign_state.get("campaign_df"))


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
    
@spaces.GPU(duration=120)
def run_search_term_optimizer_card(state):
    try:
        if not state:
            return "Select a campaign first."

        dfs = state.get("full_dfs")
        campaign_name = state.get("campaign_name")

        if dfs is None or campaign_name is None:
            return "Campaign state is not properly initialized."

        return run_search_term_optimizer(dfs, campaign_name=campaign_name)

    except Exception as e:
        return f"Search term optimization failed: {e}"


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
                campaign_picker = gr.Radio(
                    choices=[],
                    show_label=False,
                    container=False,
                    elem_classes=["campaign-radio"],
                )

            with gr.Column(scale=1, elem_classes=["center-workspace"]):
                kpi_html = gr.HTML()
                gr.HTML(SIGNAL_FLOW_HTML)

                with gr.Row(elem_classes=["ai-row"]):
                    analyze_ads_card = gr.Button(
                        value="Ads Analyst\nCampaign insights.",
                        elem_classes=["ai-button-card"],
                    )
                    gr.HTML(ai_card("Budget Optimizer", "Where to adjust spend?"))
                    gr.HTML(ai_card("Keyword Inspector", "Winning versus wasting keywords."))

                with gr.Row(elem_classes=["ai-row"]):
                    search_term_card = gr.Button(
                        value="Search Term Cleaner\nOptimize search term list.",
                        elem_classes=["ai-button-card"],
                    )
                    gr.HTML(ai_card("Growth Finder", "Where to scale?"))
                    gr.HTML(ai_card("Campaign Doctor", "What limits performance?"))

                ads_output = gr.Markdown(
                    value="Select a campaign and click Ads Analyst.",
                    elem_id="ads-output",
                )

            with gr.Column(elem_classes=["right-panel"]):
                gr.HTML(RIGHT_PANEL_HTML)

    campaign_picker.change(
        fn=campaign_selected,
        inputs=[campaign_picker, full_state],
        outputs=[campaign_state, kpi_html],
    )

    analyze_ads_card.click(
        fn=run_ads_card,
        inputs=campaign_state,
        outputs=ads_output,
    )

    search_term_card.click(
        fn=run_search_term_optimizer_card,
        inputs=campaign_state,
        outputs=ads_output,
    )

    demo.load(
        fn=initial_data_load,
        outputs=[full_state, campaign_picker, hero_html, kpi_html],
    )

    demo.load(fn=startup)

demo.queue()

if __name__ == "__main__":
    demo.launch()

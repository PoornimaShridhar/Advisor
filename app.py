import gradio as gr
import spaces

from app.db.repo import init_db
from app.controller.campaign_controller import on_campaign_select
from app.controller.session_loader import load_google_ads_data
from app.ads1.ads_analyst import run_ads_analyst_card


# ==================================================
# CURSOR DESIGN TOKENS (from DESIGN-cursor.md)
# ==================================================
#
# Colors
#   canvas:          #f7f7f4   page floor
#   canvas-soft:     #fafaf7   pane backgrounds
#   surface-card:    #ffffff   card surfaces
#   ink:             #26251e   primary text
#   body:            #5a5852   body text
#   muted:           #807d72   secondary text
#   muted-soft:      #a09c92   placeholder text
#   hairline:        #e6e5e0   card borders
#   hairline-soft:   #efeee8   subtle dividers
#   hairline-strong: #cfcdc4   active/hover borders
#   primary:         #f54e00   Cursor Orange – CTAs only
#   primary-active:  #d04200   pressed CTA
#   semantic-error:  #cf2d56
#   semantic-success:#1f8a65
#   timeline-thinking:#dfa88f  (only in AI stage pills)
#   timeline-grep:   #9fc9a2
#   timeline-read:   #9fbbe0
#   timeline-edit:   #c0a8dd
#   timeline-done:   #c08532
#
# Typography: Inter (CursorGothic substitute), JetBrains Mono for code
# Radii: xs=4px sm=6px md=8px lg=12px xl=16px pill=9999px
# Spacing: xxs=4 xs=8 sm=12 base=16 md=20 lg=24 xl=32 xxl=48 section=80
# No drop shadows. Hairline-only depth.
# ==================================================


CSS = """
/* ── Fonts ─────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400&display=swap');

/* ── Reset & root ───────────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; }

:root {
  --canvas:           #f7f7f4;
  --canvas-soft:      #fafaf7;
  --surface-card:     #ffffff;
  --ink:              #26251e;
  --body:             #5a5852;
  --muted:            #807d72;
  --muted-soft:       #a09c92;
  --hairline:         #e6e5e0;
  --hairline-soft:    #efeee8;
  --hairline-strong:  #cfcdc4;
  --primary:          #f54e00;
  --primary-active:   #d04200;
  --primary-subtle:   #fff0ea;
  --success:          #1f8a65;
  --error:            #cf2d56;
  --tl-thinking:      #dfa88f;
  --tl-grep:          #9fc9a2;
  --tl-read:          #9fbbe0;
  --tl-edit:          #c0a8dd;
  --tl-done:          #c08532;
  --font-sans:        'Inter', system-ui, 'Helvetica Neue', Helvetica, Arial, sans-serif;
  --font-mono:        'JetBrains Mono', 'Fira Code', monospace;
}

/* ── Gradio shell ───────────────────────────────────── */
.gradio-container {
  background: var(--canvas) !important;
  font-family: var(--font-sans) !important;
  max-width: 100% !important;
  padding: 0 !important;
  margin: 0 !important;
}

/* Strip default gradio padding that pushes content around */
.gradio-container > .main > .wrap {
  padding: 0 !important;
}

footer { display: none !important; }

/* ── App shell ──────────────────────────────────────── */
#app-shell {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
  background: var(--canvas);
}

/* ── Global header ──────────────────────────────────── */
#global-header {
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  height: 56px;
  background: var(--canvas);
  border-bottom: 1px solid var(--hairline);
  z-index: 10;
}

#wordmark {
  font-family: var(--font-sans);
  font-size: 15px;
  font-weight: 600;
  color: var(--ink);
  letter-spacing: -0.2px;
}

#wordmark span {
  color: var(--primary);
}

#header-meta {
  font-size: 12px;
  color: var(--muted);
  font-family: var(--font-mono);
}

/* ── KPI strip (inside header) ──────────────────────── */
#kpi-strip-wrap {
  display: flex;
  align-items: center;
  gap: 2px;
}

.kpi-item {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  padding: 4px 16px;
  border-left: 1px solid var(--hairline);
}

.kpi-item:first-child { border-left: none; }

.kpi-label {
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.88px;
  text-transform: uppercase;
  color: var(--muted);
  line-height: 1.4;
}

.kpi-value {
  font-size: 15px;
  font-weight: 600;
  color: var(--ink);
  line-height: 1.3;
  font-variant-numeric: tabular-nums;
}

/* ── Body split ─────────────────────────────────────── */
#body-split {
  flex: 1 1 auto;
  display: flex;
  overflow: hidden;
}

/* ── Left nav panel ─────────────────────────────────── */
#left-panel {
  flex: 0 0 240px;
  display: flex;
  flex-direction: column;
  background: var(--canvas-soft);
  border-right: 1px solid var(--hairline);
  overflow: hidden;
}

#nav-header {
  padding: 16px 16px 10px;
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.88px;
  text-transform: uppercase;
  color: var(--muted);
}

/* Gradio dataframe inside nav: stripped table look */
#campaign-nav .wrap { border: none !important; background: transparent !important; }
#campaign-nav table { width: 100%; border-collapse: collapse; }
#campaign-nav thead { display: none; }
#campaign-nav tbody tr {
  display: block;
  padding: 8px 16px;
  font-size: 13px;
  color: var(--body);
  cursor: pointer;
  border-radius: 6px;
  margin: 0 8px;
  transition: background 0.1s;
}
#campaign-nav tbody tr:hover { background: var(--hairline-soft); }
#campaign-nav tbody tr.selected {
  background: var(--surface-card);
  color: var(--ink);
  font-weight: 500;
  border: 1px solid var(--hairline);
}
#campaign-nav .cell-wrap { padding: 0 !important; }
#campaign-nav td { padding: 0 !important; border: none !important; }

/* ── Right workspace ────────────────────────────────── */
#right-panel {
  flex: 1 1 auto;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  padding: 24px 28px;
  gap: 20px;
  background: var(--canvas);
}

/* ── Context banner ─────────────────────────────────── */
.context-banner {
  background: var(--surface-card);
  border: 1px solid var(--hairline);
  border-radius: 12px;
  padding: 16px 20px;
}

.context-banner-placeholder {
  background: var(--canvas-soft);
  border: 1px dashed var(--hairline-strong);
  border-radius: 12px;
  padding: 14px 20px;
  color: var(--muted);
  font-size: 13px;
  text-align: center;
}

.banner-campaign-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--ink);
  margin: 0 0 10px;
}

.banner-stats {
  display: flex;
  gap: 24px;
}

.banner-stat {}
.banner-stat .bs-label {
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.88px;
  text-transform: uppercase;
  color: var(--muted);
}
.banner-stat .bs-value {
  font-size: 16px;
  font-weight: 600;
  color: var(--ink);
  font-variant-numeric: tabular-nums;
}

/* ── Section label ──────────────────────────────────── */
.section-label {
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.88px;
  text-transform: uppercase;
  color: var(--muted);
  margin: 0;
}

/* ── AI Insight cards grid ──────────────────────────── */
#ai-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

/* Base card */
.ai-card {
  background: var(--surface-card);
  border: 1px solid var(--hairline);
  border-radius: 12px;
  padding: 18px 20px;
  min-height: 100px;
  transition: border-color 0.15s, transform 0.1s;
  position: relative;
}

/* Inactive/greyed (no campaign selected) */
.ai-card.inactive {
  background: var(--canvas-soft);
  opacity: 0.55;
  pointer-events: none;
}

.ai-card.inactive .card-icon { opacity: 0.4; }

/* Active hover */
.ai-card.active:hover {
  border-color: var(--hairline-strong);
  transform: translateY(-1px);
  cursor: pointer;
}

/* Card icon */
.card-icon {
  font-size: 18px;
  margin-bottom: 8px;
  display: block;
  line-height: 1;
}

/* Card title */
.card-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--ink);
  margin: 0 0 4px;
}

/* Card hint */
.card-hint {
  font-size: 12px;
  color: var(--muted);
  margin: 0;
}

/* Primary card: Ads Analyst */
.ai-card.primary-card {
  border-color: var(--primary);
}

.ai-card.primary-card .card-title { color: var(--primary); }

/* ── Gradio button overrides for card buttons ───────── */
.ai-card-btn {
  all: unset !important;
  display: block !important;
  width: 100% !important;
  text-align: left !important;
  background: transparent !important;
  border: none !important;
  padding: 0 !important;
  min-height: unset !important;
  font-family: var(--font-sans) !important;
  font-size: 13px !important;
  color: var(--ink) !important;
  cursor: pointer !important;
  box-shadow: none !important;
}

.ai-card-btn:hover { color: var(--ink) !important; }

/* ── Output area ────────────────────────────────────── */
#output-area {
  background: var(--surface-card);
  border: 1px solid var(--hairline);
  border-radius: 12px;
  padding: 20px 24px;
  font-size: 14px;
  line-height: 1.6;
  color: var(--body);
  font-family: var(--font-sans);
  min-height: 60px;
}

#output-area code,
#output-area pre {
  font-family: var(--font-mono) !important;
  font-size: 13px;
}

/* ── Timeline stage pills (AI output only) ──────────── */
.pill-thinking { background: var(--tl-thinking); color: var(--ink); }
.pill-grep     { background: var(--tl-grep);     color: var(--ink); }
.pill-read     { background: var(--tl-read);     color: var(--ink); }
.pill-edit     { background: var(--tl-edit);     color: var(--ink); }
.pill-done     { background: var(--tl-done);     color: #fff; }

.stage-pill {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 9999px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.88px;
  text-transform: uppercase;
  margin-right: 6px;
}

/* ── Gradio overrides – hide noise ──────────────────── */
.gr-button-secondary { display: none !important; }
.generating { border: none !important; }
label.svelte-1b6s6s { display: none; }

/* Hide dataframe label */
#campaign-nav > .label-wrap { display: none; }

/* Remove Gradio's default padding on columns */
.gradio-container .gap { gap: 0 !important; }
.block { padding: 0 !important; }

/* Scrollbar styling */
#right-panel::-webkit-scrollbar { width: 4px; }
#right-panel::-webkit-scrollbar-thumb { background: var(--hairline-strong); border-radius: 2px; }

/* Loading spinner on primary card */
@keyframes spin { to { transform: rotate(360deg); } }
.spinner {
  display: inline-block;
  width: 12px; height: 12px;
  border: 2px solid var(--hairline);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  vertical-align: middle;
  margin-right: 6px;
}
"""


# ==================================================
# STARTUP
# ==================================================

def startup():
    try:
        init_db()
        print("✅ DB initialized", flush=True)
    except Exception as e:
        print("⚠️ DB init failed:", e, flush=True)


# ==================================================
# INITIAL DATA LOAD
# ==================================================

def initial_data_load():
    dfs = load_google_ads_data()
    from app.ui.dashboard import get_dashboard_data

    spend, leads, cpl, count, formatted_df = get_dashboard_data()

    kpi_html = f"""
    <div id="kpi-strip-wrap">
      <div class="kpi-item">
        <span class="kpi-label">Spend</span>
        <span class="kpi-value">£{spend:,.2f}</span>
      </div>
      <div class="kpi-item">
        <span class="kpi-label">Leads</span>
        <span class="kpi-value">{leads:,}</span>
      </div>
      <div class="kpi-item">
        <span class="kpi-label">Avg CPL</span>
        <span class="kpi-value">£{cpl:,.2f}</span>
      </div>
      <div class="kpi-item">
        <span class="kpi-label">Campaigns</span>
        <span class="kpi-value">{count}</span>
      </div>
    </div>
    """

    return dfs, formatted_df, kpi_html


# ==================================================
# CAMPAIGN SELECTION
# ==================================================

def campaign_row_selected(df, full_state, evt: gr.SelectData):
    row_index = evt.index[0]
    campaign_name = df.iloc[row_index]["Campaign"]

    campaign_state = on_campaign_select(full_state, campaign_name)

    # Pull a few stats for the banner (if available)
    try:
        stats = campaign_state.get("stats", {})
        spend  = stats.get("spend",  0)
        leads  = stats.get("leads",  0)
        ctr    = stats.get("ctr",    0)
        cpl    = stats.get("cpl",    0)
        trend  = stats.get("trend",  "–")
    except Exception:
        spend = leads = ctr = cpl = 0
        trend = "–"

    banner_html = f"""
    <div class="context-banner">
      <p class="banner-campaign-name">📊 {campaign_name}</p>
      <div class="banner-stats">
        <div class="banner-stat">
          <div class="bs-label">Spend</div>
          <div class="bs-value">£{spend:,.2f}</div>
        </div>
        <div class="banner-stat">
          <div class="bs-label">Leads</div>
          <div class="bs-value">{leads:,}</div>
        </div>
        <div class="banner-stat">
          <div class="bs-label">CTR</div>
          <div class="bs-value">{ctr:.2f}%</div>
        </div>
        <div class="banner-stat">
          <div class="bs-label">CPL</div>
          <div class="bs-value">£{cpl:,.2f}</div>
        </div>
        <div class="banner-stat">
          <div class="bs-label">Trend</div>
          <div class="bs-value">{trend}</div>
        </div>
      </div>
    </div>
    """

    # Activate the cards now that a campaign is selected
    cards_html = _active_cards_html()

    return campaign_state, banner_html, cards_html


# ==================================================
# CARD HTML HELPERS
# ==================================================

CARDS = [
    {
        "id": "ads-analyst",
        "icon": "📊",
        "title": "Ads Analyst",
        "hint": "Deep-dive performance breakdown",
        "primary": True,
    },
    {
        "id": "budget-optimizer",
        "icon": "💰",
        "title": "Budget Optimizer",
        "hint": "Reallocate spend for better ROI",
        "primary": False,
    },
    {
        "id": "keyword-intel",
        "icon": "🎯",
        "title": "Keyword Intelligence",
        "hint": "Surface winning & wasted terms",
        "primary": False,
    },
    {
        "id": "risk-detector",
        "icon": "⚠️",
        "title": "Risk Detector",
        "hint": "Flag anomalies & budget waste",
        "primary": False,
    },
    {
        "id": "growth-finder",
        "icon": "📈",
        "title": "Growth Finder",
        "hint": "Identify scaling opportunities",
        "primary": False,
    },
    {
        "id": "experiment-ideas",
        "icon": "🧪",
        "title": "Experiment Ideas",
        "hint": "A/B test hypotheses to try",
        "primary": False,
    },
]


def _inactive_cards_html():
    """All 6 cards greyed out — no campaign selected."""
    html = '<div id="ai-grid">'
    for card in CARDS:
        primary_cls = " primary-card" if card["primary"] else ""
        html += f"""
        <div class="ai-card inactive{primary_cls}">
          <span class="card-icon">{card["icon"]}</span>
          <p class="card-title">{card["title"]}</p>
          <p class="card-hint">{card["hint"]}</p>
        </div>"""
    html += "</div>"
    return html


def _active_cards_html(loading_id=None):
    """All 6 cards active. Optionally show loading state on one card."""
    html = '<div id="ai-grid">'
    for card in CARDS:
        primary_cls = " primary-card" if card["primary"] else ""
        if loading_id and card["id"] == loading_id:
            hint = '<span class="spinner"></span>Analysing…'
        else:
            hint = card["hint"]
        html += f"""
        <div class="ai-card active{primary_cls}" data-card="{card["id"]}">
          <span class="card-icon">{card["icon"]}</span>
          <p class="card-title">{card["title"]}</p>
          <p class="card-hint">{hint}</p>
        </div>"""
    html += "</div>"
    return html


# ==================================================
# ADS ANALYST
# ==================================================

@spaces.GPU(duration=120)
def run_ads_card(state, cards_state):
    """Run Ads Analyst and return output + updated cards HTML."""
    if not state:
        return (
            "⚠️ Select a campaign from the left panel first.",
            _inactive_cards_html(),
        )

    dfs = state.get("full_dfs")
    campaign_name = state.get("campaign_name")

    if dfs is None or campaign_name is None:
        return (
            "⚠️ Campaign state not properly initialised.",
            _active_cards_html(),
        )

    # Show loading state on card while running
    try:
        result = run_ads_analyst_card(dfs, campaign_name=campaign_name)
    except Exception as e:
        result = f"⚠️ Analysis failed: {e}"

    return result, _active_cards_html()


# ==================================================
# UI
# ==================================================

with gr.Blocks(css=CSS, title="Advisor") as demo:

    full_state     = gr.State()
    campaign_state = gr.State()
    cards_state    = gr.State(value="inactive")  # "inactive" | "active"

    # ── Global header ─────────────────────────────────
    with gr.Row(elem_id="global-header"):
        gr.HTML("""
        <div id="wordmark">🧠 <span>Advisor</span></div>
        """)
        kpi_html = gr.HTML(elem_id="kpi-strip-wrap")
        gr.HTML("""
        <div id="header-meta">Google Ads</div>
        """)

    # ── Body ──────────────────────────────────────────
    with gr.Row(elem_id="body-split"):

        # ── LEFT PANEL ────────────────────────────────
        with gr.Column(scale=1, min_width=240, elem_id="left-panel"):
            gr.HTML('<div id="nav-header">Campaigns</div>')
            campaign_table = gr.Dataframe(
                show_label=False,
                interactive=True,
                elem_id="campaign-nav",
            )

        # ── RIGHT PANEL ───────────────────────────────
        with gr.Column(scale=4, elem_id="right-panel"):

            # Context banner
            campaign_banner = gr.HTML("""
            <div class="context-banner-placeholder">
              👈 Select a campaign to begin analysis
            </div>
            """)

            # Section label
            gr.HTML('<p class="section-label">AI Insights</p>')

            # 6-card grid (inactive by default)
            ai_cards_html = gr.HTML(value=_inactive_cards_html())

            # ── Hidden Gradio trigger buttons ────────
            # Gradio can't listen to clicks on raw HTML, so we use a
            # hidden button that JavaScript triggers when a card is clicked.
            ads_trigger = gr.Button(
                "run-ads-analyst",
                visible=False,
                elem_id="ads-analyst-trigger",
            )

            # Output area
            ads_output = gr.Markdown(
                value="Select a campaign and click **Ads Analyst** to begin.",
                elem_id="output-area",
            )

    # ── JS: card click → hidden button ────────────────
    # Intercept clicks on .ai-card[data-card="ads-analyst"] and
    # click the hidden Gradio button so Python handles it.
    demo.load(
        fn=None,
        js="""
        () => {
          document.addEventListener('click', (e) => {
            const card = e.target.closest('[data-card="ads-analyst"]');
            if (card) {
              const btn = document.getElementById('ads-analyst-trigger');
              if (btn) btn.click();
            }
          });
        }
        """,
    )

    # ── Events ────────────────────────────────────────

    campaign_table.select(
        fn=campaign_row_selected,
        inputs=[campaign_table, full_state],
        outputs=[campaign_state, campaign_banner, ai_cards_html],
    )

    ads_trigger.click(
        fn=run_ads_card,
        inputs=[campaign_state, cards_state],
        outputs=[ads_output, ai_cards_html],
    )

    # ── Initial load ──────────────────────────────────

    demo.load(
        fn=initial_data_load,
        outputs=[full_state, campaign_table, kpi_html],
    )

    demo.load(fn=startup)


demo.queue()

if __name__ == "__main__":
    demo.launch()
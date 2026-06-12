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
    background: #070708 !important;
    color: #e5e2e3 !important;
    max-width: 100% !important;
    padding-top: 5% !important;
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

    border-radius: 6px;   /* 🔥 key fix: rounded square */

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



/* HERO SECTION */

.hero-section {
    padding-top: 128px;   /* pt-32 */
    padding-bottom: 80px;
    padding-right: 32px;
}


.hero-inner {
    max-width: 1728px;
    margin: 0 auto;
    padding: 0 32px;
    width: 100%;
}

.hero-row {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    margin-bottom: 40px; /* mb-xl */
}

.hero-title {
    font-family: Manrope, sans-serif;
    font-size: 76px;
    line-height: 1.1;
    letter-spacing: -0.055em;
    font-weight: 520;
    color: #e5e2e3 !important;
    max-width: 1000px;
    margin-bottom: 16px;
}

.hero-subtitle {
    font-family: Inter, sans-serif;
    font-size: 19px;
    color: rgb(198, 197, 216) !important;
    margin-bottom: 24px;
}

.hero-section,
.hero-section * {
    color: inherit;
}

.sidebar {
    background: #0d0e0f;
    border-right: 1px solid #232426;
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
    background: #101112;
    border: 1px solid #232426;
    border-radius: 12px;
    padding: 14px;
}

.kpi .label {
    font-size: 11px;
    color: #8a877c;
}

.kpi .value {
    font-size: 16px;
    font-weight: 600;
    color: #e5e2e3;
}

/* SNAPSHOT */
.snapshot {
    border-top: 1px solid #232426;
    border-bottom: 1px solid #232426;
    color: #e5e2e3;
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
    background: #101112;
    border: 1px solid #232426;
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
    color: #9A9DA3;
}

/* OUTPUT */
#ads-output {
    margin-top: 16px;
    padding: 16px;
    border: 1px solid #e6e5e0;
    border-radius: 12px;
    background: #101112;
    border: 1px solid #232426;
    color: #e5e2e3;
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
    <div class="hero-section">
        <div class="hero-inner">

            <div class="hero-title">
                AI-powered Google Ads optimization
            </div>

            <div class="hero-subtitle">
                Spend £{spend:.2f} | Leads {leads} | Avg CPL £{cpl:.2f} | Campaigns {count}
            </div>

        </div>
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

# UI
with gr.Blocks(fill_height=True, fill_width=True, css=CSS) as demo:
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

    kpi_html = gr.HTML()

    # ---------------- MAIN ----------------
    with gr.Row():

        gr.HTML("""
            <div class="w-full bg-custom-card-bg rounded-xl border overflow-hidden flex h-[620px] inner-glow shadow-2xl relative border-white/[0.05]">
        <!-- Sidebar -->
        <div class="w-64 bg-custom-sidebar border-r border-custom-divider p-md flex flex-col gap-sm">
        <div class="text-[10px] text-custom-text-muted uppercase tracking-[0.2em] mb-6 px-4 opacity-40 font-bold">Campaigns</div>
        <div class="flex flex-col gap-1">
        <div class="flex items-center gap-3 px-4 py-2 bg-white/[0.04] rounded-lg text-on-surface font-medium cursor-pointer transition-colors border border-white/[0.05]">
        <span class="material-symbols-outlined text-[18px]">grid_view</span>
        <span class="text-body-md">Birla Open Minds Yelahanka</span>
        </div>
        <div class="flex items-center gap-3 px-4 py-2 text-custom-text-muted hover:text-on-surface hover:bg-white/[0.04] rounded-lg cursor-pointer transition-colors group">
        <span class="material-symbols-outlined text-[18px] opacity-40 group-hover:opacity-100">sensors</span>
        <span class="text-body-md">Admissions Open 2026</span>
        </div>
        <div class="flex items-center gap-3 px-4 py-2 text-custom-text-muted hover:text-on-surface hover:bg-white/[0.04] rounded-lg cursor-pointer transition-colors group">
        <span class="material-symbols-outlined text-[18px] opacity-40 group-hover:opacity-100">check_circle</span>
        <span class="text-body-md">Early Bird Enrollment Offer</span>
        </div>
        <div class="flex items-center gap-3 px-4 py-2 text-custom-text-muted hover:text-on-surface hover:bg-white/[0.04] rounded-lg cursor-pointer transition-colors group">
        <span class="material-symbols-outlined text-[18px] opacity-40 group-hover:opacity-100">bar_chart</span>
        <span class="text-body-md">Summer Camp</span>
        </div>
        <div class="flex items-center gap-3 px-4 py-2 text-custom-text-muted hover:text-on-surface hover:bg-white/[0.04] rounded-lg cursor-pointer transition-colors group">
        <span class="material-symbols-outlined text-[18px] opacity-40 group-hover:opacity-100">warning</span>
        <span class="text-body-md">Parent Orientation Program</span>
        </div>
        <div class="mt-4 flex flex-col gap-1">
        <div class="flex items-center gap-3 px-4 py-2 text-custom-text-muted hover:text-on-surface hover:bg-white/[0.04] rounded-lg cursor-pointer transition-colors group">
        <span class="material-symbols-outlined text-[18px] opacity-40 group-hover:opacity-100">group</span>
        <span class="text-body-md">Book a Free School Tour</span>
        </div>
        <div class="flex items-center gap-3 px-4 py-2 text-custom-text-muted hover:text-on-surface hover:bg-white/[0.04] rounded-lg cursor-pointer transition-colors group">
        <span class="material-symbols-outlined text-[18px] opacity-40 group-hover:opacity-100">article</span>
        <span class="text-body-md">Discover Joyful Learning</span>
        </div>
        </div>
        </div>
        </div>
        <!-- Center Area -->
        <div class="flex-1 p-lg flex flex-col gap-lg bg-[#0a0a0b] relative overflow-y-auto">
        <div class="grid grid-cols-4 gap-4">
        <div class="bg-custom-card-bg border border-white/[0.05] rounded-xl p-5 inner-glow"><div class="flex justify-between items-start mb-3">
        <div class="text-[10px] text-custom-text-muted font-bold uppercase tracking-widest opacity-60">SPEND</div>
        <div class="font-mono-data text-[9px] text-primary/40 uppercase tracking-tighter">[SYNC: ACTIVE]</div>
        </div>
        <div class="font-h3 text-h3 text-on-surface font-bold tracking-tight">$1965.76</div>
        <div class="flex items-center justify-between mt-3">
        <div class="text-[11px] text-secondary font-medium flex items-center gap-1 opacity-90">
        <span class="material-symbols-outlined text-[14px]">trending_up</span>+12% vs last month
            </div>
        <div class="flex gap-0.5">
        <div class="w-0.5 h-2 bg-secondary opacity-20"></div>
        <div class="w-0.5 h-3 bg-secondary opacity-40"></div>
        <div class="w-0.5 h-2 bg-secondary opacity-60"></div>
        <div class="w-0.5 h-4 bg-secondary"></div>
        </div>
        </div></div>
        <div class="bg-custom-card-bg border border-white/[0.05] rounded-xl p-5 inner-glow"><div class="flex justify-between items-start mb-3">
        <div class="text-[10px] text-custom-text-muted font-bold uppercase tracking-widest opacity-60">LEADS</div>
        <div class="font-mono-data text-[9px] text-tertiary/40 uppercase tracking-tighter">[QUEUE: 14]</div>
        </div>
        <div class="font-h3 text-h3 text-on-surface font-bold tracking-tight">14</div>
        <div class="text-[11px] text-tertiary font-medium mt-3 opacity-90">3 requiring attention</div></div>
        <div class="bg-custom-card-bg border border-white/[0.05] rounded-xl p-5 inner-glow"><div class="flex justify-between items-start mb-3">
        <div class="text-[10px] text-custom-text-muted font-bold uppercase tracking-widest opacity-60">CPL</div>
        <div class="font-mono-data text-[9px] text-[#E5FD17]/40 uppercase tracking-tighter">[HEARTBEAT: OK]</div>
        </div>
        <div class="font-h3 text-h3 text-on-surface font-bold uppercase tracking-tight">258.39</div>
        <div class="text-[11px] text-[#E5FD17] font-medium mt-3 opacity-90 flex items-center gap-2">
        <span class="w-1 h-1 rounded-full bg-[#E5FD17] animate-pulse"></span>
            All systems stable
        </div></div>
        <div class="bg-custom-card-bg border border-white/[0.05] rounded-xl p-5 inner-glow"><div class="flex justify-between items-start mb-3">
        <div class="text-[10px] text-custom-text-muted font-bold uppercase tracking-widest opacity-60">CTR</div>
        <div class="font-mono-data text-[9px] text-custom-text-muted/40 uppercase tracking-tighter">[LOAD: OPT]</div>
        </div>
        <div class="font-h3 text-h3 text-on-surface font-bold tracking-tight">0.02578</div>
        <div class="text-[11px] text-custom-text-muted font-medium mt-3 opacity-90">Optimal range</div></div>
        </div>
        <div class="bg-custom-card-bg border border-custom-divider rounded-xl p-4 inner-glow flex flex-col h-[220px]"><div class="flex justify-between items-center mb-6 px-1">
        <div class="flex items-center gap-4">
        <div class="text-label-sm font-bold text-on-surface uppercase tracking-widest opacity-60">Signal Flow</div>
        <div class="font-mono-data text-[9px] text-primary/40 uppercase tracking-tighter">[LATENCY: 12ms]</div>
        </div>
        <div class="flex gap-4 text-[10px] text-custom-text-muted font-bold uppercase tracking-wider">
        <span class="flex items-center gap-1.5"><span class="w-1 h-1 rounded-full bg-primary"></span>Revenue</span>
        <span class="flex items-center gap-1.5"><span class="w-1 h-1 rounded-full bg-white/20"></span>Goal</span>
        </div>
        </div>
        <div class="flex-1 rounded-lg bg-[#070708]/50 border border-white/[0.02] relative overflow-hidden">
        <!-- Faint Horizontal Grid Lines -->
        <div class="absolute inset-0 flex flex-col justify-between py-2 opacity-10">
        <div class="border-t border-white/[0.1] w-full"></div>
        <div class="border-t border-white/[0.1] w-full"></div>
        <div class="border-t border-white/[0.1] w-full"></div>
        <div class="border-t border-white/[0.1] w-full"></div>
        </div>
        <!-- Vertical Grid -->
        <div class="absolute inset-0 grid grid-cols-6 h-full w-full">
        <div class="border-r border-white/[0.05]"></div>
        <div class="border-r border-white/[0.05]"></div>
        <div class="border-r border-white/[0.05]"></div>
        <div class="border-r border-white/[0.05]"></div>
        <div class="border-r border-white/[0.05]"></div>
        </div>
        <svg class="absolute bottom-0 w-full h-[80%]" preserveaspectratio="none" viewbox="0 0 100 100">
        <defs>
        <lineargradient id="gradient-flow-v3" x1="0%" x2="0%" y1="0%" y2="100%">
        <stop offset="0%" stop-color="#5E6BFF" stop-opacity="0.15"></stop>
        <stop offset="100%" stop-color="#5E6BFF" stop-opacity="0"></stop>
        </lineargradient>
        <filter height="140%" id="glow" width="140%" x="-20%" y="-20%">
        <fegaussianblur result="blur" stddeviation="1.5"></fegaussianblur>
        <fecomposite in="SourceGraphic" in2="blur" operator="over"></fecomposite>
        </filter>
        </defs>
        <!-- Area Fill -->
        <path d="M0,80 C20,78 35,85 50,65 C65,45 80,30 100,25 L100,100 L0,100 Z" fill="url(#gradient-flow-v3)"></path>
        <!-- Main Line -->
        <path d="M0,80 C20,78 35,85 50,65 C65,45 80,30 100,25" fill="none" filter="url(#glow)" stroke="#5E6BFF" stroke-linecap="round" stroke-width="1"></path>
        <!-- Data Points -->
        <circle cx="20" cy="78" fill="#5E6BFF" r="1"></circle>
        <circle cx="50" cy="65" fill="white" r="1.5" stroke="#5E6BFF" stroke-width="0.5"></circle>
        <circle cx="80" cy="30" fill="#5E6BFF" r="1"></circle>
        </svg>
        <!-- Axis Labels -->
        <div class="absolute bottom-1 right-2 font-mono-data text-[7px] text-custom-text-muted/30 uppercase">t: 127.4s</div>
        <div class="absolute top-2 left-2 font-mono-data text-[7px] text-custom-text-muted/30 uppercase">y: $V</div>
        </div></div>
        <div class="grid grid-cols-3 gap-3">
        <div class="bg-custom-card-bg border border-custom-divider rounded-xl p-4 inner-glow">
        <div class="text-body-md font-bold text-on-surface border-b border-white/[0.05] pb-3 mb-3">Ads Analyst</div>
        <div class="space-y-3">
        <div class="flex justify-between items-center text-body-md">
        <span class="text-on-surface">Campaign insights.</span>
        <!-- <span class="text-custom-text-muted text-[11px]">TODAY</span> -->
        </div>
        </div>
        </div>
        <div class="bg-custom-card-bg border border-custom-divider rounded-xl p-4 inner-glow">
        <div class="text-body-md font-bold text-on-surface border-b border-white/[0.05] pb-3 mb-3">Budget Optimizer
        </div>
        <div class="space-y-3">
        <div class="flex justify-between items-center text-body-md">
        <span class="text-on-surface">Where to adjust spend?</span>
        </div>
        </div>
        </div>
        <div class="bg-custom-card-bg border border-custom-divider rounded-xl p-4 inner-glow">
        <div class="text-body-md font-bold text-on-surface border-b border-white/[0.05] pb-3 mb-3">Keyword Inspector
        </div>
        <div class="space-y-3">
        <div class="flex justify-between items-center text-body-md">
        <span class="text-on-surface">Winning versus wasting keywords.</span>
        </div>
        </div>
        </div>
        </div>
        <div class="grid grid-cols-3 gap-3">
        <div class="bg-custom-card-bg border border-custom-divider rounded-xl p-4 inner-glow">
        <div class="text-body-md font-bold text-on-surface border-b border-white/[0.05] pb-3 mb-3">Search Term Cleaner</div>
        <div class="space-y-3">
        <div class="flex justify-between items-center text-body-md">
        <span class="text-on-surface">Optimize search term list.</span>
        <!-- <span class="text-custom-text-muted text-[11px]">TODAY</span> -->
        </div>
        </div>
        </div>
        <div class="bg-custom-card-bg border border-custom-divider rounded-xl p-4 inner-glow">
        <div class="text-body-md font-bold text-on-surface border-b border-white/[0.05] pb-3 mb-3">Growth Finder
        </div>
        <div class="space-y-3">
        <div class="flex justify-between items-center text-body-md">
        <span class="text-on-surface">Where to scale?</span>
        </div>
        </div>
        </div>
        <div class="bg-custom-card-bg border border-custom-divider rounded-xl p-4 inner-glow">
        <div class="text-body-md font-bold text-on-surface border-b border-white/[0.05] pb-3 mb-3">Campaign Doctor
        </div>
        <div class="space-y-3">
        <div class="flex justify-between items-center text-body-md">
        <span class="text-on-surface">What limits performance?</span>
        </div>
        </div>
        </div>
        </div>
        </div>
        <!-- Right Panel -->
        <div class="w-80 bg-custom-panel border-l border-custom-divider p-md flex flex-col gap-md relative">
        <div class="text-body-md font-bold text-on-surface border-b border-white/[0.05] pb-5 mb-2 flex justify-between items-center px-1">
        <div class="flex items-center gap-2.5">
        <span class="material-symbols-outlined text-[20px] text-secondary">bolt</span>
                Advisor Intelligence
            </div>
        <span class="w-1.5 h-1.5 rounded-full bg-secondary animate-pulse"></span>
        </div>
        <div class="flex flex-col gap-8 px-1">
        <div class="space-y-3">
        <div class="text-[10px] font-bold text-custom-text-muted uppercase tracking-widest opacity-50">Recommended Action</div>
        <div class="bg-white/[0.03] border border-white/[0.05] rounded-xl p-4 text-body-md text-on-surface leading-relaxed shadow-sm">
                    Reallocate resources to <span class="text-primary font-bold">Project Alpha</span> to mitigate Q4 delivery risk.
                </div>
        </div>
        <div class="space-y-3">
        <div class="text-[10px] font-bold text-custom-text-muted uppercase tracking-widest opacity-50">Signal summary</div>
        <div class="bg-white/[0.03] border border-white/[0.05] rounded-xl p-4 text-body-md text-on-surface leading-relaxed shadow-sm">
                    Revenue trends <span class="text-secondary font-medium">positive (+12%)</span>, but capacity constraints emerging in engineering teams.
                </div>
        </div>
        <div class="flex flex-col gap-3 flex-1">
        <div class="text-[10px] font-bold text-custom-text-muted uppercase tracking-widest opacity-50">Decision log</div>
        <div class="space-y-2 overflow-y-auto pr-1">
        <div class="group flex items-start gap-4 p-2.5 hover:bg-white/[0.02] rounded-lg transition-colors">
        <div class="w-1.5 h-1.5 rounded-full bg-primary mt-2 flex-shrink-0"></div>
        <div>
        <div class="text-label-sm text-on-surface font-medium">Budget Approved</div>
        <div class="text-[11px] text-custom-text-muted mt-1 opacity-70">2h ago • Finance Team</div>
        </div>
        </div>
        <div class="group flex items-start gap-4 p-2.5 hover:bg-white/[0.02] rounded-lg transition-colors">
        <div class="w-1.5 h-1.5 rounded-full bg-white/20 mt-2 flex-shrink-0"></div>
        <div>
        <div class="text-label-sm text-on-surface opacity-80 font-medium">Contract Signed</div>
        <div class="text-[11px] text-custom-text-muted mt-1 opacity-70">5h ago • Legal Ops</div>
        </div>
        </div>
        </div>
        </div>
        </div>
        </div>
        </div>
        """)

    # ---------------- EVENTS ----------------

    # campaign_table.select(
    #     fn=campaign_row_selected,
    #     inputs=[campaign_table, full_state],
    #     outputs=[campaign_state, campaign_banner],
    # )

    # # ✅ RESTORED CLICK FUNCTIONALITY
    # ads_card.click(
    #     fn=run_ads_card,
    #     inputs=campaign_state,
    #     outputs=ads_output
    # )

    # # ---------------- LOAD ----------------

    # demo.load(
    #     fn=initial_data_load,
    #     outputs=[full_state, campaign_table, kpi_html],
    # )

    demo.load(fn=startup)

demo.queue()

if __name__ == "__main__":
    demo.launch()
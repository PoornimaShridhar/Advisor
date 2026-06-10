import gradio as gr
import os

print("APP STARTED", flush=True)

from app.db.repo import init_db
from app.ui.dashboard import build_dashboard, get_dashboard_data
from app.controller.campaign_controller import on_campaign_select
from app.controller.session_loader import load_google_ads_data
from app.ads1.ads_analyst import run_ads_analyst_card
from app.ads1.budget_optimizer import run_budget_optimizer_card
import spaces

print("🔥 STEP 1: imports done", flush=True)


@spaces.GPU(duration=120)
def run_ads_card(state):
    print("\n🔥 [run_ads_card] ENTERED", flush=True)
    try:
        if not state:
            print("❌ [run_ads_card] state is EMPTY", flush=True)
            return "⚠️ Select a campaign first"

        print("📦 [run_ads_card] state received", type(state), flush=True)
        dfs = state.get("full_dfs")
        print("📊 [run_ads_card] extracted dfs:", type(dfs), flush=True)

        if not dfs:
            return "⚠️ No campaign data — select a campaign on the Dashboard tab first."

        result = run_ads_analyst_card(dfs)
        print("✅ [run_ads_card] returning result", flush=True)
        return result
    except Exception as e:
        print("❌ [run_ads_card] ERROR:", repr(e), flush=True)
        return f"⚠️ Analysis failed: {e}"


@spaces.GPU(duration=120)
def run_budget_card(state):
    print("\n🔥 [run_budget_card] ENTERED", flush=True)
    try:
        if not state:
            print("❌ [run_budget_card] state is EMPTY", flush=True)
            return "⚠️ Select a campaign first"

        dfs = state.get("full_dfs")
        if not dfs:
            return "⚠️ No campaign data — select a campaign on the Dashboard tab first."

        result = run_budget_optimizer_card(dfs)
        print("✅ [run_budget_card] returning result", flush=True)
        return result
    except Exception as e:
        print("❌ [run_budget_card] ERROR:", repr(e), flush=True)
        return f"⚠️ Budget optimization failed: {e}"


def startup():
    try:
        init_db()
        print("✅ DB initialized successfully", flush=True)
        return "ok"
    except Exception as e:
        print("⚠️ DB failed:", e, flush=True)
        return "error"


print("🔥 STEP 2: DB init done", flush=True)

# UI Optimization: Fetch data AFTER UI elements are drawn
def initial_data_load():
    print("🔄 App loaded. Population of background states initiated...")
    dfs = load_google_ads_data()
    # Unpack dashboard metrics to fill the UI immediately
    spend, leads, cpl, count, formatted_df = get_dashboard_data()
    return dfs, formatted_df, spend, leads, cpl, count


def campaign_row_selected(df, full_state, evt: gr.SelectData):
    row_index = evt.index[0]
    campaign_name = df.iloc[row_index]["Campaign"]
    campaign_state = on_campaign_select(full_state, campaign_name)
    return campaign_state, f"## 📊 Selected Campaign: {campaign_name}"


print("🔥 STEP 3: building UI", flush=True)

with gr.Blocks() as demo:
    # Initialize components empty; populated safely via demo.load
    full_state = gr.State()
    campaign_state = gr.State()
    # df_state = gr.State()

    gr.Markdown("# 🎯 Ads Dashboard")

    with gr.Tab("Dashboard"):
        # We modify build_dashboard to expose metric components for automated hydration
        gr.Markdown("## 📊 Campaign Dashboard")
        with gr.Row():
            total_spend = gr.Number(label="Total Spend")
            total_leads = gr.Number(label="Total Leads")
            average_cpl = gr.Number(label="Average CPL")
            active_campaigns = gr.Number(label="Active Campaigns")

        campaign_table = gr.Dataframe(label="Campaign Performance", interactive=True)
        refresh_btn = gr.Button("🔄 Force Refresh Data")

    with gr.Tab("Analysis"):
        selected = gr.Markdown("👈 Select a campaign from the Dashboard tab")
        output = gr.Markdown()

        with gr.Row():
            gr.Button("🚀 Run Ads Analysis").click(run_ads_card, campaign_state, output)
            gr.Button("💰 Run Budget Optimization").click(run_budget_card, campaign_state, output)

    campaign_table.select(
        fn=campaign_row_selected,
        inputs=[campaign_table, full_state],
        outputs=[campaign_state, selected],
    )

    # Button manual refresh
    refresh_btn.click(
        fn=initial_data_load,
        outputs=[full_state, campaign_table, total_spend, total_leads, average_cpl, active_campaigns],
    )

    # ⚡ MAGIC FIX: App automatically loads data into UI components instantly on launch
    demo.load(
        fn=initial_data_load,
        outputs=[full_state, campaign_table, total_spend, total_leads, average_cpl, active_campaigns],
    )
    demo.load(fn=startup, outputs=[])

demo.queue()

if __name__ == "__main__":
    demo.launch()

# import gradio as gr
# import os
# print("APP STARTED", flush=True)

# from app.db.repo import init_db
# from app.ui.dashboard import build_dashboard, get_dashboard_data
# from app.controller.campaign_controller import on_campaign_select
# from app.controller.session_loader import load_google_ads_data
# from app.ads1.ads_analyst import run_ads_analyst_card
# from app.ads1.budget_optimizer import run_budget_optimizer_card
# import spaces
# print("🔥 STEP 1: imports done", flush=True)

# @spaces.GPU(duration=0)
# def run_ads_card(state):
#     return "BUTTON HIT"
#     # if not state:
#     #     return "⚠️ Select a campaign from the Dashboard tab first."
#     # return run_ads_analyst_card(state["full_dfs"])

# @spaces.GPU(duration=0)
# def run_budget_card(state):
#     if not state:
#         return "⚠️ Select a campaign from the Dashboard tab first."
#     return run_budget_optimizer_card(state["full_dfs"])

# def startup():
#     try:
#         init_db()
#         print("✅ DB initialized successfully")
#     except Exception as e:
#         print("⚠️ DB init failed:", e)

# startup()

# print("🔥 STEP 2: DB init done", flush=True)

# # UI Optimization: Fetch data AFTER UI elements are drawn
# def initial_data_load():
#     print("🔄 App loaded. Population of background states initiated...")
#     dfs = load_google_ads_data()
#     # Unpack dashboard metrics to fill the UI immediately
#     spend, leads, cpl, count, formatted_df = get_dashboard_data()
#     return dfs, formatted_df, spend, leads, cpl, count

# def campaign_row_selected(evt: gr.SelectData, df, full_state):
#     if df.empty or full_state is None:
#         return gr.State(), "⚠️ Data state is missing. Please click Refresh."
#     row_index = evt.index[0]
#     campaign_name = df.iloc[row_index]["Campaign"]
#     campaign_state = on_campaign_select(full_state, campaign_name)
#     return campaign_state, f"## 📊 Selected Campaign: {campaign_name}"

# print("🔥 STEP 3: building UI", flush=True)

# with gr.Blocks() as demo:
#     # Initialize components empty; populated safely via demo.load
#     full_state = gr.State()
#     campaign_state = gr.State()
#     df_state = gr.State()

#     gr.Markdown("# 🎯 Ads Dashboard")

#     with gr.Tab("Dashboard"):
#         # We modify build_dashboard to expose metric components for automated hydration
#         gr.Markdown("## 📊 Campaign Dashboard")
#         with gr.Row():
#             total_spend = gr.Number(label="Total Spend")
#             total_leads = gr.Number(label="Total Leads")
#             average_cpl = gr.Number(label="Average CPL")
#             active_campaigns = gr.Number(label="Active Campaigns")

#         campaign_table = gr.Dataframe(label="Campaign Performance", interactive=True)
#         refresh_btn = gr.Button("🔄 Force Refresh Data")

#     with gr.Tab("Analysis"):
#         selected = gr.Markdown("👈 Select a campaign from the Dashboard tab")
#         output = gr.Markdown()
        
#         with gr.Row():
#             gr.Button("🚀 Run Ads Analysis").click(run_ads_card, campaign_state, output)
#             gr.Button("💰 Run Budget Optimization").click(run_budget_card, campaign_state, output)

#     # Core Event Bindings
#     # campaign_table.change(fn=lambda x: x, inputs=[campaign_table], outputs=df_state)
#     def campaign_row_selected(evt: gr.SelectData, df, full_state):
#         row_index = evt.index[0]
#         campaign_name = df.iloc[row_index]["Campaign"]
    
#         campaign_state = on_campaign_select(full_state, campaign_name)
    
#         return campaign_state, f"## 📊 Selected Campaign: {campaign_name}"
    
#     campaign_table.select(
#         fn=campaign_row_selected,
#         inputs=[df_state, full_state],
#         outputs=[campaign_state, selected]
#     )

#     # Button manual refresh
#     refresh_btn.click(
#         fn=initial_data_load,
#         outputs=[full_state, campaign_table, total_spend, total_leads, average_cpl, active_campaigns]
#     )

#     # ⚡ MAGIC FIX: App automatically loads data into UI components instantly on launch
#     demo.load(
#         fn=initial_data_load,
#         outputs=[full_state, campaign_table, total_spend, total_leads, average_cpl, active_campaigns]
#     )

# if __name__ == "__main__":
#     demo.launch()

print("🔥 MINIMAL APP STARTED", flush=True)

import gradio as gr

def hello():
    print("HELLO CALLED", flush=True)
    return "Hello world"

demo = gr.Interface(fn=hello, inputs=[], outputs="text")

demo.launch()

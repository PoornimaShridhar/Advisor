---
sdk: gradio
sdk_version: 6.17.3
python_version: "3.12"
app_file: app.py
pinned: false
short_description: Local AI Google Ads advisor for small businesses
tracks:
  - Backyard AI
badges:
  - Off the Grid
  - Well-Tuned
  - Off-Brand
  - Llama Champion
  - Field Notes
---

# Advisor

Advisor is a local-first Google Ads analysis dashboard for small businesses. It was inspired by a real preschool owner who needed faster answers from campaign data: what is working, what is wasting budget, which keywords matter, and where spend should be increased or reduced.

The app combines live Google Ads data with sample demo data, then turns campaign metrics into clear recommendations through a fine-tuned GGUF model running with `llama.cpp`, plus rule-based logic for budget-sensitive decisions.

**Fine-tuned model:** [ps1811/advisor-minicpm-finetuned-gguf](https://huggingface.co/ps1811/advisor-minicpm-finetuned-gguf/tree/main)

## Screenshots

![Dashboard](docs/assets/dashboard.png)

## Demo Focus

For the demo, the data is a combination of actual Google Ads data and generated sample data. This keeps the product realistic while making the walkthrough safe and repeatable.

## Social Post

I shared a short post about this app here:

<https://www.linkedin.com/posts/poornima-sridhara_huggingface-gradio-ai-share-7472424316081704960-tv_v/?utm_source=share&utm_medium=member_desktop&rcm=ACoAABy6-yIBUw9eh7Soes0YOEPkNQYD7N6DMTo>

## Badge Notes

Submitted for:

- **Backyard AI**: built around a local, small-business AI workflow.
- **Off the Grid**: AI inference runs locally through `llama.cpp`; no hosted LLM API is used. Google Ads is used only as a data source.
- **Well-Tuned**: uses a fine-tuned model published on Hugging Face: <https://huggingface.co/ps1811/advisor-minicpm-finetuned-gguf/tree/main>
- **Off-Brand**: custom Gradio frontend with a full dashboard layout, custom CSS, campaign sidebar, KPI cards, trend chart, and insight cards.
- **Llama Champion**: runs a GGUF model through the `llama-cpp-python` runtime.
- **Field Notes**: see the Field Notes section below.

## Key Features

- **Executive dashboard**: global spend, total leads, average cost per lead, and active campaign count.
- **Campaign selector**: choose a running campaign and instantly update campaign-level KPIs.
- **Advisor Intelligence panel**: highlights the best-performing campaign, budget-draining campaign, and a scalable candidate.
- **Traffic trend chart**: shows daily clicks over the last 14 days.
- **Ads Analyst**: LLM-powered campaign performance explanation and action suggestions.
- **Budget Optimizer**: rule-based budget recommendations for increase, reduce, or hold decisions.
- **Keyword Inspector**: LLM-powered keyword analysis for winners, wasted spend, and future opportunities.
- **Search Term Cleaner**: LLM-powered search term cleanup and negative keyword suggestions.
- **Growth Finder**: rule-based identification of scale-ready opportunities.

## Architecture

```text
Google Ads API
    |
    v
app/ads1/fetch_ads_data.py
    |
    v
app/controller/session_loader.py
    |-- merges live data with app/ads1/sample_data.py
    |-- caches data in /tmp/google_ads_cache.pkl
    v
app.py
    |-- Gradio custom dashboard UI
    |-- campaign selection state
    |-- insight card actions
    |
    |-- LLM cards:
    |     app/ads1/ads_analyst.py
    |     app/ads1/keyword_inspector.py
    |     app/ads1/search_term_optimizer.py
    |
    |-- Rule-based cards:
          app/ads1/budget_optimizer.py
          app/ads1/growth_finder.py
          app/ads1/campaign_doctor.py
```

## Model

Advisor uses a fine-tuned MiniCPM GGUF model hosted on Hugging Face:

[ps1811/advisor-minicpm-finetuned-gguf](https://huggingface.co/ps1811/advisor-minicpm-finetuned-gguf/tree/main)

The model is downloaded with `hf_hub_download` and loaded through `llama-cpp-python`.

Default model settings:

```text
LLAMA_HF_REPO=ps1811/advisor-minicpm-finetuned-gguf
LLAMA_HF_FILENAME=advisor-minicpm-q4_k_m.gguf
LLAMA_GPU_LAYERS=-1
LLAMA_N_CTX=2048
LLAMA_N_THREADS=4
```

## Tech Stack

- **Frontend**: Gradio Blocks with custom CSS
- **Model runtime**: `llama-cpp-python`
- **Model format**: GGUF
- **Model hosting**: Hugging Face Hub
- **Data source**: Google Ads API
- **Data processing**: pandas
- **Storage/cache**: local pickle cache and SQLite support
- **Deployment target**: Hugging Face Spaces / ZeroGPU-compatible setup

## Quick Start

Clone the project and install dependencies:

```bash
pip install -r requirements.txt
```

Set the required environment variables:

```bash
GOOGLE_ADS_DEVELOPER_TOKEN=...
GOOGLE_ADS_CLIENT_ID=...
GOOGLE_ADS_CLIENT_SECRET=...
GOOGLE_ADS_REFRESH_TOKEN=...
GOOGLE_ADS_CUSTOMER_ID=...
GOOGLE_ADS_LOGIN_CUSTOMER_ID=...
```

Optional model/runtime overrides:

```bash
LLAMA_HF_REPO=ps1811/advisor-minicpm-finetuned-gguf
LLAMA_HF_FILENAME=advisor-minicpm-q4_k_m.gguf
LLAMA_GPU_LAYERS=-1
LLAMA_N_CTX=2048
LLAMA_N_THREADS=4
```

Run the app:

```bash
python app.py
```

## Google Ads Credentials

The app requires your own Google Ads API credentials. The demo was built using a friend's Google Ads account, but those keys should not be shared or committed.

Anyone running this app must create and provide their own:

- Google Ads developer token
- OAuth client ID
- OAuth client secret
- OAuth refresh token
- Customer ID
- Optional login customer ID for manager accounts

For Hugging Face Spaces, add these values as Space secrets instead of placing them in the repository.

## Fine-Tuning Workflow

The fine-tuning assets live in `fine_tuning/`.

- `fine_tuning/scripts/train_qlora.py`: QLoRA training
- `fine_tuning/scripts/merge_lora.py`: merge LoRA into the base model
- `fine_tuning/GGUF_CONVERSION.md`: convert and quantize the merged model to GGUF
- `fine_tuning/data/`: seed and CSV-derived training data

The final quantized model is uploaded to Hugging Face and loaded by the app at runtime.

## Field Notes

The biggest design choice was separating AI reasoning from money movement. The LLM is used where explanation and interpretation are valuable: ad analysis, keyword inspection, and search term cleanup. Budget and scaling recommendations use deterministic rules so the app behaves predictably when spend decisions are involved.

The second important choice was local inference. Instead of calling a hosted LLM API, Advisor downloads a fine-tuned GGUF model and runs it with `llama.cpp`. This keeps the AI layer local-first and makes the project a better fit for the Backyard AI track.

The UI was also built beyond default Gradio styling. The goal was to make the first screen useful immediately: campaign list on the left, performance metrics in the center, and strategic campaign signals on the right.

## Project Structure

```text
app.py                         # Main Gradio app and UI
app/models/llm.py              # GGUF download and llama.cpp model loader
app/controller/                # Session loading and campaign state
app/ads1/                      # Google Ads connector, queries, analyzers, rules
app/ui/                        # Dashboard helpers
app/db/                        # SQLite models/repository helpers
fine_tuning/                   # Training, merge, and GGUF conversion workflow
scripts/seed_demo.py           # Demo data utility
tests/                         # Connector and e2e tests
```

## Safety Note

Do not commit `.env`, OAuth client secrets, refresh tokens, or Google Ads credentials. Use local environment variables during development and Space secrets when deploying.

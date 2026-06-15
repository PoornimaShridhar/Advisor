---
language:
  - en
license: apache-2.0
base_model: openbmb/MiniCPM5-1B
tags:
  - gguf
  - llama-cpp
  - qlora
  - google-ads
  - marketing-analytics
  - local-ai
  - small-business
pipeline_tag: text-generation
---

# Advisor MiniCPM Fine-Tuned GGUF

This model is a fine-tuned MiniCPM model for **Advisor**, a local-first Google Ads analysis app for small businesses. The model is designed to turn campaign, keyword, and search-term metrics into concise, actionable marketing recommendations.

It is used in the Advisor app here:

https://huggingface.co/spaces/build-small-hackathon/Advisor

Project repository:

https://github.com/PoornimaShridhar/Advisor

## Intended Use

The model is tuned for short Google Ads advisory outputs, especially:

- campaign performance summaries
- keyword inspection
- search term cleanup
- concise action bullets grounded in metrics
- small-business-friendly explanations

In the app, the LLM is used for explanation-heavy cards:

- Ads Analyst
- Keyword Inspector
- Search Term Cleaner

Budget-sensitive decisions are intentionally handled by deterministic rule-based logic in the app, not delegated fully to the model.

## Fine-Tuning Summary

The model was fine-tuned from:

```text
openbmb/MiniCPM5-1B
```

The training workflow used QLoRA with 4-bit loading, then merged the LoRA adapter into the base model before converting the merged model to GGUF for local inference.

High-level process:

1. Prepared instruction-style chat examples in JSONL format.
2. Mixed synthetic Google Ads examples with cleaned campaign-style examples.
3. Trained a LoRA adapter with `transformers`, `peft`, `trl`, and `bitsandbytes`.
4. Merged the LoRA adapter into the base model.
5. Converted the merged model to GGUF with `llama.cpp`.
6. Quantized the GGUF model to `Q4_K_M`.
7. Loaded the final model locally through `llama-cpp-python` in the Advisor app.

## Training Data Format

Each training record followed a chat-style JSONL structure:

```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are a Google Ads analyst. Reply with concise actionable markdown bullets only."
    },
    {
      "role": "user",
      "content": "Analyze this Google Ads campaign data..."
    },
    {
      "role": "assistant",
      "content": "- Pause weak search terms with spend and no conversions.\n\n- Scale efficient keywords with conversions below target CPA."
    }
  ]
}
```

The fine-tuning target was not general conversation. The goal was to teach the model to write short, grounded, metric-aware recommendations.

## Training Configuration

The project training script uses:

```text
Training method: QLoRA
Max sequence length: 2048
Epochs: 2
Learning rate: 2e-4
Batch size: 2
Gradient accumulation: 8
LoRA rank: 16
LoRA alpha: 32
LoRA dropout: 0.05
Optimizer: paged_adamw_8bit
Quantization during training: 4-bit NF4
```

LoRA target modules:

```text
q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj
```

## Runtime

The Advisor app downloads this GGUF model with `hf_hub_download` and runs it locally with `llama-cpp-python`.

Default app configuration:

```text
LLAMA_HF_REPO=ps1811/advisor-minicpm-finetuned-gguf
LLAMA_HF_FILENAME=advisor-minicpm-q4_k_m.gguf
LLAMA_N_CTX=2048
LLAMA_GPU_LAYERS=-1
LLAMA_N_THREADS=4
```

## Example Output Style

The expected output style is concise markdown bullets:

```text
- Treat "preschool near me" as a winning keyword because it produced conversions at an efficient CPA.

- Reduce spend on broad, low-intent terms that generated clicks but no leads.

- Add irrelevant search terms as negatives to protect budget for higher-intent traffic.
```

## Limitations

- The model is specialized for Google Ads-style campaign analysis and may not perform well as a general assistant.
- It should not be used as the only source of truth for financial decisions.
- Budget changes in the Advisor app are handled by rule-based logic because spend decisions need predictable behavior.
- Outputs should be reviewed by a human before applying recommendations to a live ad account.

## Privacy

The public repository does not include private Google Ads credentials or private training exports. Users running the app must provide their own Google Ads API credentials.

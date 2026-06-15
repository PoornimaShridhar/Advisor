# Advisor Fine-Tuning Kit

This folder is for preparing a small instruction-tuning dataset for the Advisor card outputs.

Your app currently runs a GGUF model with `llama.cpp`. Do not fine-tune the `.gguf` file directly. Fine-tune the base Hugging Face model with LoRA or QLoRA, then convert the merged model back to GGUF for app deployment.

## Recommended Split

Keep deterministic logic for cards where the decision can be computed:

- Budget Optimizer: rule-based decision engine
- Growth Finder: rule-based decision engine

Use the LLM where language synthesis still helps:

- Ads Analyst
- Keyword Inspector
- Search Term Cleaner

For Budget and Growth, optional fine-tuning examples should teach the model to rewrite already-computed decisions, not make the decision.

## Dataset Size

Start small and high quality:

- Minimum useful: 200-300 examples
- Good v1: 800-1,500 examples
- Stronger v2: 3,000-5,000 examples

Suggested v1 mix:

- 250 Ads Analyst examples
- 250 Keyword Inspector examples
- 250 Search Term Cleaner examples
- 150 Budget rewrite examples
- 100 Growth rewrite examples

## JSONL Format

Each line is one chat example:

```json
{"messages":[{"role":"system","content":"You are a Google Ads analyst. Reply with concise actionable bullet points only."},{"role":"user","content":"Write 3 to 5 bullet points... Data (JSON): ..."},{"role":"assistant","content":"- Pause 'toy store near me' because it spent 586.50 across 184 clicks with 0 conversions.\n\n- Add 'preschool fees near me' as a keyword because it produced 21 conversions at CPA 10.40 and CVR 13.04%."}]}
```

Good assistant outputs must be:

- 3 to 5 markdown bullets
- Self-contained sentences
- Specific about the campaign, keyword, or search term
- Specific about the action
- Grounded in metrics from the prompt
- No intro sentence
- No schema explanations
- No thinking aloud
- No quoted action fragments copied from JSON

## Local Dataset Workflow

From the Advisor repo root:

```bash
python fine_tuning/scripts/build_seed_dataset.py --out fine_tuning/data/seed.jsonl
python fine_tuning/scripts/validate_jsonl.py fine_tuning/data/seed.jsonl
```

To build the 3-card training mix from the uncleaned Google Ads CSV plus synthetic examples:

```bash
python fine_tuning/scripts/build_csv_training_mix.py \
  --csv C:/Users/ASUS/Downloads/GoogleAds_DataAnalytics_Sales_Uncleaned.csv \
  --out_dir fine_tuning/data/csv_mix \
  --csv_count 400 \
  --synthetic_count 600

python fine_tuning/scripts/validate_jsonl.py fine_tuning/data/csv_mix/train.jsonl
python fine_tuning/scripts/validate_jsonl.py fine_tuning/data/csv_mix/val.jsonl
```

This creates:

```text
fine_tuning/data/csv_mix/csv_cleaned_pruned.csv
fine_tuning/data/csv_mix/train.jsonl
fine_tuning/data/csv_mix/val.jsonl
```

Then manually add curated real examples to:

```text
fine_tuning/data/manual.jsonl
```

Combine files however you prefer into:

```text
fine_tuning/data/train.jsonl
fine_tuning/data/val.jsonl
```

## Training On A GPU Machine

Install training dependencies from:

```bash
pip install -r fine_tuning/requirements-train.txt
```

Run QLoRA:

```bash
python fine_tuning/scripts/train_qlora.py \
  --model_id openbmb/MiniCPM5-1B \
  --train_file fine_tuning/data/train.jsonl \
  --val_file fine_tuning/data/val.jsonl \
  --output_dir fine_tuning/out/advisor-minicpm-lora
```

Confirm the non-GGUF base model ID before training. Your current inference model is:

```text
openbmb/MiniCPM5-1B-GGUF / MiniCPM5-1B-Q4_K_M.gguf
```

After LoRA training, merge the adapter into the base model, convert to GGUF with `llama.cpp`, quantize to `Q4_K_M`, upload to Hugging Face, then update:

```python
LLAMA_HF_REPO = "your-user/advisor-minicpm-finetuned-gguf"
LLAMA_HF_FILENAME = "advisor-minicpm-q4_k_m.gguf"
```

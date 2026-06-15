# Convert Fine-Tuned Model To GGUF

Run these steps on the GPU/training machine or another Linux machine with enough disk space.

## 1. Clone llama.cpp

```bash
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
pip install -r requirements.txt
cmake -B build
cmake --build build --config Release -j
```

## 2. Merge LoRA Into The Base Model

From the Advisor repo:

```bash
python fine_tuning/scripts/merge_lora.py \
  --model_id openbmb/MiniCPM5-1B \
  --adapter_dir fine_tuning/out/advisor-minicpm-lora \
  --output_dir fine_tuning/out/advisor-minicpm-merged
```

## 3. Convert To FP16 GGUF

From `llama.cpp`:

```bash
python convert_hf_to_gguf.py /path/to/Advisor/fine_tuning/out/advisor-minicpm-merged \
  --outfile /path/to/advisor-minicpm-f16.gguf \
  --outtype f16
```

## 4. Quantize

```bash
./build/bin/llama-quantize \
  /path/to/advisor-minicpm-f16.gguf \
  /path/to/advisor-minicpm-q4_k_m.gguf \
  Q4_K_M
```

On Windows, the executable path/name may differ.

## 5. Upload To Hugging Face

Create a repo such as:

```text
your-user/advisor-minicpm-finetuned-gguf
```

Upload:

```text
advisor-minicpm-q4_k_m.gguf
```

Then update the app environment:

```bash
LLAMA_HF_REPO=your-user/advisor-minicpm-finetuned-gguf
LLAMA_HF_FILENAME=advisor-minicpm-q4_k_m.gguf
```


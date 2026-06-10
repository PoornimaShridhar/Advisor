import os
from huggingface_hub import hf_hub_download
from llama_cpp import Llama

_model = None

def load_model():
    print("🧠 [load_model] called", flush=True)
    global _model

    if _model is not None:
        print("🧠 [load_model] returning cached model", flush=True)
        return _model

    print("⬇️ [load_model] downloading model...", flush=True)
    model_path = hf_hub_download(
        repo_id="Abiray/MiniCPM5-1B-GGUF",
        filename="minicpm5-1b-Q4_K_M.gguf",
    )

    print(f"✅ [load_model] model downloaded at {model_path}", flush=True)

    gpu_layers = int(os.getenv("LLAMA_GPU_LAYERS", "0"))
    print(f"🚀 [load_model] initializing Llama with n_gpu_layers={gpu_layers}", flush=True)

    _model = Llama(
        model_path=model_path,
        n_ctx=4096,
        n_gpu_layers=gpu_layers,
        verbose=True,
    )

    print("✅ [load_model] model initialized", flush=True)

    return _model
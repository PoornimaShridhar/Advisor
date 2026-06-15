from __future__ import annotations

import os
import threading

from huggingface_hub import hf_hub_download
from llama_cpp import Llama

HF_REPO = os.getenv("LLAMA_HF_REPO", "ps1811/advisor-minicpm-finetuned-gguf")
HF_FILENAME = os.getenv("LLAMA_HF_FILENAME", "advisor-minicpm-q4_k_m.gguf")

_model: Llama | None = None
_init_lock = threading.Lock()


def _preload_cuda_libs() -> None:
    try:
        import ctypes

        import nvidia.cublas
        import nvidia.cuda_runtime
    except ImportError:
        return

    for module, lib_name in (
        (nvidia.cublas, "libcublas.so.12"),
        (nvidia.cuda_runtime, "libcudart.so.12"),
    ):
        lib_path = os.path.join(module.__path__[0], "lib", lib_name)
        if os.path.isfile(lib_path):
            ctypes.CDLL(lib_path, mode=ctypes.RTLD_GLOBAL)


def load_model() -> Llama:
    global _model
    print("🧠 [load_model] called", flush=True)

    if _model is not None:
        print("🧠 [load_model] returning cached model", flush=True)
        return _model

    with _init_lock:
        if _model is not None:
            return _model

        print("⬇️ [load_model] downloading model...", flush=True)
        model_path = hf_hub_download(repo_id=HF_REPO, filename=HF_FILENAME)
        print(f"✅ [load_model] model downloaded at {model_path}", flush=True)

        _preload_cuda_libs()
        gpu_layers = int(os.getenv("LLAMA_GPU_LAYERS", "-1"))
        n_ctx = int(os.getenv("LLAMA_N_CTX", "2048"))
        n_threads = int(os.getenv("LLAMA_N_THREADS", "4"))
        print(
            f"🚀 [load_model] initializing Llama "
            f"(n_gpu_layers={gpu_layers}, n_ctx={n_ctx}, n_threads={n_threads})",
            flush=True,
        )

        _model = Llama(
            model_path=model_path,
            n_ctx=n_ctx,
            n_gpu_layers=gpu_layers,
            n_threads=n_threads,
            verbose=False,
        )
        print("✅ [load_model] model initialized", flush=True)

    return _model

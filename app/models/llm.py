from __future__ import annotations

import os
import threading
from typing import Any

from huggingface_hub import hf_hub_download

# HF_REPO = os.getenv("LLAMA_HF_REPO", "openbmb/MiniCPM5-1B-GGUF")
# HF_FILENAME = os.getenv("LLAMA_HF_FILENAME", "MiniCPM5-1B-Q4_K_M.gguf")

LLAMA_HF_REPO = os.getenv("LLAMA_HF_REPO", "ps1811/advisor-minicpm-finetuned-gguf")
LLAMA_HF_FILENAME= os.getenv("LLAMA_HF_FILENAME", "advisor-minicpm-q4_k_m.gguf")

_model: Any = None
_init_lock = threading.Lock()


def _preload_cuda_libs() -> None:
    """Expose pip-installed CUDA runtime to llama.cpp on ZeroGPU (no system libcudart)."""
    try:
        import ctypes

        import nvidia.cublas
        import nvidia.cuda_runtime
    except ImportError:
        return

    lib_dirs: list[str] = []
    for module, lib_name in (
        (nvidia.cublas, "libcublas.so.12"),
        (nvidia.cuda_runtime, "libcudart.so.12"),
    ):
        lib_dir = os.path.join(module.__path__[0], "lib")
        lib_path = os.path.join(lib_dir, lib_name)
        if os.path.isfile(lib_path):
            ctypes.CDLL(lib_path, mode=ctypes.RTLD_GLOBAL)
            lib_dirs.append(lib_dir)

    if lib_dirs:
        existing = os.environ.get("LD_LIBRARY_PATH", "")
        merged = lib_dirs + ([existing] if existing else [])
        os.environ["LD_LIBRARY_PATH"] = ":".join(merged)


def load_model() -> Any:
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
        from llama_cpp import Llama

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

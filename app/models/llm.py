from __future__ import annotations

import os
import threading
from typing import Any

from huggingface_hub import hf_hub_download

HF_REPO = os.getenv("LLAMA_HF_REPO", "ps1811/advisor-minicpm-finetuned-gguf")
HF_FILENAME = os.getenv("LLAMA_HF_FILENAME", "advisor-minicpm-q4_k_m.gguf")

_model: Any = None
_init_lock = threading.Lock()


def load_model() -> Any:
    global _model

    if _model is not None:
        return _model

    with _init_lock:
        if _model is not None:
            return _model

        model_path = hf_hub_download(repo_id=HF_REPO, filename=HF_FILENAME)

        from llama_cpp import Llama

        _model = Llama(
            model_path=model_path,
            n_ctx=int(os.getenv("LLAMA_N_CTX", "2048")),
            n_gpu_layers=int(os.getenv("LLAMA_GPU_LAYERS", "0")),
            n_threads=int(os.getenv("LLAMA_N_THREADS", "4")),
            verbose=os.getenv("LLAMA_VERBOSE", "0") == "1",
        )

    return _model

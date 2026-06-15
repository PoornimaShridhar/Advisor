from __future__ import annotations

import os
import threading
from typing import Any

from huggingface_hub import hf_hub_download

HF_REPO = os.getenv("LLAMA_HF_REPO", "ps1811/advisor-minicpm-finetuned-gguf")
HF_FILENAME = os.getenv("LLAMA_HF_FILENAME", "advisor-minicpm-q4_k_m.gguf")

_model: Any = None
_init_lock = threading.Lock()


def _validate_gguf_file(model_path: str) -> None:
    if not os.path.isfile(model_path):
        raise FileNotFoundError(f"Downloaded model file does not exist: {model_path}")

    size_bytes = os.path.getsize(model_path)
    with open(model_path, "rb") as fh:
        magic = fh.read(4)
        fh.seek(0)
        first_128 = fh.read(128)

    print(
        f"[load_model] GGUF file check: size={size_bytes / (1024 ** 2):.1f} MB, "
        f"magic={magic!r}",
        flush=True,
    )

    if magic != b"GGUF":
        preview = first_128.decode("utf-8", errors="replace")
        raise RuntimeError(
            "Downloaded file is not a valid GGUF file. "
            f"Expected magic b'GGUF', got {magic!r}. First bytes: {preview!r}"
        )

    if size_bytes < 100 * 1024 * 1024:
        raise RuntimeError(
            "Downloaded GGUF file is unexpectedly small. "
            f"Size was {size_bytes} bytes; this often means a bad upload or LFS pointer."
        )


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
    print("[load_model] called", flush=True)

    if _model is not None:
        print("[load_model] returning cached model", flush=True)
        return _model

    with _init_lock:
        if _model is not None:
            return _model

        force_download = os.getenv("LLAMA_FORCE_DOWNLOAD", "0") == "1"
        print(
            f"[load_model] downloading/resolving model {HF_REPO}/{HF_FILENAME} "
            f"(force_download={force_download})...",
            flush=True,
        )
        model_path = hf_hub_download(
            repo_id=HF_REPO,
            filename=HF_FILENAME,
            force_download=force_download,
        )
        print(f"[load_model] model resolved at {model_path}", flush=True)
        _validate_gguf_file(model_path)

        _preload_cuda_libs()
        from llama_cpp import Llama

        gpu_layers = int(os.getenv("LLAMA_GPU_LAYERS", "-1"))
        n_ctx = int(os.getenv("LLAMA_N_CTX", "2048"))
        n_threads = int(os.getenv("LLAMA_N_THREADS", "4"))
        verbose = os.getenv("LLAMA_VERBOSE", "0") == "1"
        print(
            f"[load_model] initializing Llama "
            f"(n_gpu_layers={gpu_layers}, n_ctx={n_ctx}, n_threads={n_threads}, verbose={verbose})",
            flush=True,
        )

        try:
            _model = Llama(
                model_path=model_path,
                n_ctx=n_ctx,
                n_gpu_layers=gpu_layers,
                n_threads=n_threads,
                verbose=verbose,
            )
        except Exception as exc:
            raise RuntimeError(
                f"llama.cpp failed to load a valid GGUF file from {model_path}. "
                "If the file check above says magic=b'GGUF' and the size is large, "
                "this is usually a llama-cpp-python/GGUF compatibility issue or a bad quantized export. "
                "Try setting LLAMA_VERBOSE=1 for the next run."
            ) from exc

        print("[load_model] model initialized", flush=True)

    return _model

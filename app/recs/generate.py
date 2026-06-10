from __future__ import annotations

import os
import re
import traceback
from typing import Dict

from app.models.llm import load_model

TARGET_CPL = 20.0

_IM_END = "<|im_end|>"
_STOP_SEQUENCES = [_IM_END, "<|im_start|>", "</s>"]


def fallback_explanation(rec: Dict | None = None) -> str:
    return "This recommendation was generated from campaign performance metrics."


def sanitize_explanation(text: str, rec: Dict | None = None) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if not cleaned or len(cleaned) < 10:
        return fallback_explanation(rec)
    return cleaned


def _messages_to_prompt(messages: list[dict[str, str]]) -> str:
    chunks: list[str] = []
    for msg in messages:
        role = msg["role"]
        content = msg["content"]
        if role == "system":
            chunks.append(f"<|im_start|>system\n{content}\n")
        elif role == "user":
            chunks.append(f"<|im_start|>user\n{content}\n")
        elif role == "assistant":
            chunks.append(f"<|im_start|>assistant\n{content}\n")
    chunks.append("<|im_start|>assistant\n")
    return "".join(chunks)


def generate_explanation(prompt: str, rec: Dict | None = None, stream: bool = False) -> str:
    print("\n🔥 [generate_explanation] CALLED", flush=True)

    try:
        print(
            f"🧾 [generate_explanation] prompt type={type(prompt).__name__} "
            f"len={len(str(prompt))}",
            flush=True,
        )

        llm = load_model()
        print("🧠 [generate_explanation] model loaded", flush=True)

        user_content = str(prompt).rstrip()
        if "/no_think" not in user_content:
            user_content = f"{user_content} /no_think"

        messages = [
            {
                "role": "system",
                "content": "You are an expert marketing analyst. Output only the final answer.",
            },
            {"role": "user", "content": user_content},
        ]

        print("🚀 [generate_explanation] calling LLM...", flush=True)
        out = llm(
            _messages_to_prompt(messages),
            max_tokens=int(os.getenv("LLAMA_MAX_TOKENS", "512")),
            temperature=0.7,
            stop=_STOP_SEQUENCES,
            echo=False,
        )
        raw = (out["choices"][0].get("text") or "").strip()
        print("📡 [generate_explanation] response received", flush=True)
        print("📄 [generate_explanation] raw output length:", len(raw), flush=True)

        clean = re.sub(
            r"<\s*think\s*>.*?<\s*/\s*think\s*>",
            "",
            raw,
            flags=re.DOTALL | re.IGNORECASE,
        )
        clean = re.sub(
            r"<think>.*?</think>",
            "",
            clean,
            flags=re.DOTALL | re.IGNORECASE,
        )
        clean = re.sub(r"\s+", " ", clean).strip()
        clean = sanitize_explanation(clean, rec)

        print("✨ [generate_explanation] cleaned output ready", flush=True)
        return clean

    except Exception as e:
        print("❌ [generate_explanation] ERROR:", repr(e), flush=True)
        traceback.print_exc()
        return fallback_explanation(rec)

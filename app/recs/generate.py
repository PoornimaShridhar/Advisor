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
        chunks.append(f"<|im_start|>{role}\n{content}{_IM_END}\n")
    chunks.append("<|im_start|>assistant\n")
    return "".join(chunks)


def _strip_thinking(text: str) -> str:
    text = re.sub(r"<\s*think\s*>.*?<\s*/\s*think\s*>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(
        r"<think>.*?</think>",
        "",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )
    return re.sub(r"\s+", " ", text).strip()


def _message_text(message: dict) -> str:
    content = (message.get("content") or "").strip()
    reasoning = (message.get("reasoning_content") or "").strip()
    if content and reasoning:
        return content if len(content) >= len(reasoning) else reasoning
    return content or reasoning


def _run_completion(llm, messages: list[dict[str, str]]) -> str:
    prompt = _messages_to_prompt(messages)
    out = llm(
        prompt,
        max_tokens=int(os.getenv("LLAMA_MAX_TOKENS", "512")),
        temperature=0.7,
        stop=_STOP_SEQUENCES,
        echo=False,
    )
    return (out["choices"][0].get("text") or "").strip()


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
        raw = _run_completion(llm, messages)

        if not raw:
            print("⚠️ [generate_explanation] raw empty — trying create_chat_completion", flush=True)
            try:
                out = llm.create_chat_completion(
                    messages=messages,
                    max_tokens=int(os.getenv("LLAMA_MAX_TOKENS", "512")),
                    temperature=0.7,
                )
                raw = _message_text(out["choices"][0]["message"])
            except TypeError as exc:
                print(f"⚠️ [generate_explanation] chat_completion failed: {exc}", flush=True)

        print("📡 [generate_explanation] response received", flush=True)
        print("📄 [generate_explanation] raw output length:", len(raw), flush=True)
        if raw:
            print("📄 [generate_explanation] raw preview:", raw[:400], flush=True)

        clean = _strip_thinking(raw)
        clean = sanitize_explanation(clean, rec)

        print("✨ [generate_explanation] cleaned output ready", flush=True)
        return clean

    except Exception as e:
        print("❌ [generate_explanation] ERROR:", repr(e), flush=True)
        traceback.print_exc()
        return f"⚠️ Analysis failed: {e}"

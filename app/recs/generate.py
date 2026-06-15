from __future__ import annotations

import json
import os
import re
import threading
import traceback
from typing import Dict

from app.models.llm import load_model

TARGET_CPL = 20.0

_infer_lock = threading.Lock()


def fallback_explanation(rec: Dict | None = None) -> str:
    return "This recommendation was generated from campaign performance metrics."


def _strip_thinking(text: str) -> str:
    text = re.sub(r"<\s*think\s*>.*?<\s*/\s*think\s*>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE)
    return text.strip()


def _looks_like_garbage(text: str) -> bool:
    if not text:
        return True
    lower = text.lower()
    if "return only" in lower or "no reasoning" in lower or "no explanation" in lower:
        return True
    if "google ads analyst" in lower and text.count("-") < 2:
        return True
    if re.search(r"(?:\d[\s\n]+){6,}", text):
        return True
    digit_ratio = sum(ch.isdigit() for ch in text) / max(len(text), 1)
    bullet_count = sum(1 for ln in text.splitlines() if ln.strip().startswith("-"))
    return digit_ratio > 0.35 and bullet_count < 2


def is_fallback_output(text: str) -> bool:
    return not text or text.startswith("WARNING:") or text.startswith("This recommendation was generated")


def is_bad_llm_output(text: str) -> bool:
    return is_fallback_output(text) or _looks_like_garbage(text)


def sanitize_explanation(text: str, rec: Dict | None = None) -> str:
    text = _strip_thinking(text)
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    bullets: list[str] = []
    for ln in lines:
        if re.match(r"^[-*]\s+\S", ln):
            bullets.append(ln)
        elif re.match(r"^\d+\.\s+\S", ln):
            bullets.append(re.sub(r"^\d+\.\s+", "- ", ln))

    if len(bullets) >= 2:
        return "\n\n".join(bullets[:5])

    flat = re.sub(r"[ \t]+", " ", text).strip()
    if len(flat) < 20 or _looks_like_garbage(flat):
        return fallback_explanation(rec)
    return flat


def _coerce_prompt(prompt: str | Dict, rec: Dict | None) -> tuple[str, Dict | None]:
    if isinstance(prompt, dict):
        rec = rec or prompt
        reason = prompt.get("reason")
        if reason:
            return str(reason).strip(), rec
        return json.dumps(prompt, default=str), rec
    return str(prompt).strip(), rec


def generate_explanation(prompt: str | Dict, rec: Dict | None = None, stream: bool = False):
    try:
        user_content, rec = _coerce_prompt(prompt, rec)
        if "/no_think" not in user_content:
            user_content = f"{user_content}\n/no_think"

        with _infer_lock:
            llm = load_model()
            out = llm(
                user_content,
                max_tokens=int(os.getenv("LLAMA_MAX_TOKENS", "384")),
                temperature=float(os.getenv("LLAMA_TEMPERATURE", "0.35")),
                stop=["</s>"],
                echo=False,
            )

        raw = (out["choices"][0].get("text") or "").strip()
        clean = sanitize_explanation(raw, rec)

        if stream:
            return iter([clean])
        return clean

    except Exception as e:
        traceback.print_exc()
        err = f"WARNING: Analysis failed: {e}"
        if stream:
            return iter([err])
        return err

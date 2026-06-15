from __future__ import annotations

import json
import os
import re
import threading
import traceback
from typing import Dict

from app.models.llm import load_model

TARGET_CPL = 20.0

_IM_END = "<|im_end|>"
_STOP_SEQUENCES = [_IM_END, "<|im_start|>", "</s>"]

_infer_lock = threading.Lock()

_SYSTEM = (
    "You are a Google Ads analyst. "
    "Reply with 3 to 5 markdown bullet points only. "
    "Each bullet must be one short, actionable insight about the campaign data. "
    "No introduction, no numbered lists, no step-by-step reasoning."
)


def fallback_explanation(rec: Dict | None = None) -> str:
    return "This recommendation was generated from campaign performance metrics."


def _strip_thinking(text: str) -> str:
    text = re.sub(r"<\s*think\s*>.*?<\s*/\s*think\s*>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(
        r"<think>.*?</think>",
        "",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )
    return text.strip()


def _looks_like_garbage(text: str) -> bool:
    if not text:
        return True
    lower = text.lower()
    if "return only" in lower or "no reasoning" in lower or "no explanation" in lower:
        return True
    if "google ads analyst" in lower and text.count("-") < 2:
        return True
    if "ads performance analyst" in lower and text.count("-") < 2:
        return True
    if re.search(r"(?:\d[\s\n]+){6,}", text):
        return True
    digit_ratio = sum(ch.isdigit() for ch in text) / max(len(text), 1)
    bullet_count = sum(1 for ln in text.splitlines() if ln.strip().startswith("-"))
    return digit_ratio > 0.35 and bullet_count < 2


def is_fallback_output(text: str) -> bool:
    lower = (text or "").lower()
    return (
        not text
        or lower.startswith("warning:")
        or "analysis failed:" in lower
        or text.startswith("This recommendation was generated")
    )


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


def _messages_to_prompt(messages: list[dict[str, str]]) -> str:
    system = next((msg["content"] for msg in messages if msg["role"] == "system"), "")
    user = next((msg["content"] for msg in messages if msg["role"] == "user"), "")
    return (
        f"{system}\n\n"
        f"Request:\n{user}\n\n"
        "Answer with only the final bullet points:\n"
    )

def _message_text(message: dict) -> str:
    content = (message.get("content") or "").strip()
    reasoning = (message.get("reasoning_content") or "").strip()
    if content and reasoning and _looks_like_garbage(content):
        return reasoning
    return content or reasoning


def _infer(llm, messages: list[dict[str, str]]) -> str:
    max_tokens = int(os.getenv("LLAMA_MAX_TOKENS", "384"))
    temperature = float(os.getenv("LLAMA_TEMPERATURE", "0.35"))
    use_chat_completion = os.getenv("LLAMA_USE_CHAT_COMPLETION", "0") == "1"

    if use_chat_completion:
        try:
            out = llm.create_chat_completion(
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            raw = _message_text(out["choices"][0]["message"])
            if raw and not _looks_like_garbage(raw):
                print("OK [generate_explanation] via create_chat_completion", flush=True)
                return raw
            print("WARNING [generate_explanation] chat_completion empty/garbage - raw fallback", flush=True)
        except Exception as exc:
            print(f"WARNING [generate_explanation] chat_completion failed - raw fallback: {repr(exc)}", flush=True)

    print("LLM [generate_explanation] using raw llama prompt", flush=True)
    out = llm(
        _messages_to_prompt(messages),
        max_tokens=max_tokens,
        temperature=temperature,
        stop=_STOP_SEQUENCES,
        echo=False,
    )
    return (out["choices"][0].get("text") or "").strip()


def _coerce_prompt(prompt: str | Dict, rec: Dict | None) -> tuple[str, Dict | None]:
    if isinstance(prompt, dict):
        rec = rec or prompt
        reason = prompt.get("reason")
        if reason:
            return str(reason).strip(), rec
        return json.dumps(prompt, default=str), rec
    return str(prompt).strip(), rec


def generate_explanation(prompt: str | Dict, rec: Dict | None = None, stream: bool = False):
    print("\nLLM [generate_explanation] CALLED", flush=True)

    try:
        user_content, rec = _coerce_prompt(prompt, rec)
        print(
            f"PROMPT [generate_explanation] prompt type={type(prompt).__name__} "
            f"len={len(user_content)}",
            flush=True,
        )
        if "/no_think" not in user_content:
            user_content = f"{user_content}\n/no_think"

        messages = [
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": user_content},
        ]

        with _infer_lock:
            llm = load_model()
            print("MODEL [generate_explanation] model loaded", flush=True)
            print("LLM [generate_explanation] calling LLM...", flush=True)
            raw = _infer(llm, messages)

        print("LLM [generate_explanation] response received", flush=True)
        print("RAW [generate_explanation] raw output length:", len(raw), flush=True)
        if raw:
            print("RAW [generate_explanation] raw preview:", raw[:400], flush=True)

        clean = sanitize_explanation(raw, rec)
        if is_bad_llm_output(clean):
            clean = fallback_explanation(rec)
        print("OK [generate_explanation] cleaned output ready", flush=True)
        if stream:
            return iter([clean])
        return clean

    except Exception as e:
        print("ERROR [generate_explanation] ERROR:", repr(e), flush=True)
        traceback.print_exc()
        err = f"WARNING: Analysis failed: {e}"
        if stream:
            return iter([err])
        return err


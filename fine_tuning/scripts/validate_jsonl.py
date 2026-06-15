from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


BAD_PHRASES = [
    "let's",
    "i assume",
    "actually",
    "we can calculate",
    "cost is given",
    "output format",
    "strict rules",
    "schema",
]


def validate_record(record: dict, line_no: int) -> list[str]:
    errors: list[str] = []
    messages = record.get("messages")
    if not isinstance(messages, list) or len(messages) < 3:
        return [f"line {line_no}: messages must be a list with at least system/user/assistant"]

    roles = [msg.get("role") for msg in messages]
    if roles[-1] != "assistant":
        errors.append(f"line {line_no}: final message must be assistant")
    if "user" not in roles:
        errors.append(f"line {line_no}: missing user message")

    assistant = messages[-1].get("content", "")
    if not isinstance(assistant, str) or not assistant.strip():
        errors.append(f"line {line_no}: assistant content is empty")
        return errors

    bullets = [line for line in assistant.splitlines() if line.strip().startswith("- ")]
    if not 1 <= len(bullets) <= 5:
        errors.append(f"line {line_no}: assistant should contain 1 to 5 markdown bullets")

    lower = assistant.lower()
    for phrase in BAD_PHRASES:
        if phrase in lower:
            errors.append(f"line {line_no}: assistant contains bad phrase: {phrase}")

    if re.search(r"^\s*(search_term|clicks|impressions|cost):", assistant, re.I | re.M):
        errors.append(f"line {line_no}: assistant appears to explain schema fields")

    if assistant.count('"') >= 6:
        errors.append(f"line {line_no}: assistant has many quotes; check for copied JSON fragments")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("jsonl", type=Path)
    args = parser.parse_args()

    all_errors: list[str] = []
    with args.jsonl.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                all_errors.append(f"line {line_no}: invalid JSON: {exc}")
                continue
            all_errors.extend(validate_record(record, line_no))

    if all_errors:
        print("\n".join(all_errors))
        return 1

    print(f"OK: {args.jsonl}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


#!/usr/bin/env python3
"""Validate locally extracted Catechism JSONL records."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JSONL_PATH = ROOT / "data" / "catechism" / "catechism.jsonl"


def main() -> int:
    if not JSONL_PATH.exists():
        print(f"File not found: {JSONL_PATH}")
        print("Run scripts/scrape_catechism.py first.")
        return 2

    records: dict[int, dict] = {}
    errors: list[str] = []
    for line_number, line in enumerate(JSONL_PATH.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
            number = int(item["reference"]["number"])
            text = str(item["text"]).strip()
            if item.get("source") != "catechism":
                errors.append(f"line {line_number}: unexpected source")
            if not text:
                errors.append(f"line {line_number}: empty text for paragraph {number}")
            if number in records:
                errors.append(f"line {line_number}: duplicate paragraph {number}")
            records[number] = item
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            errors.append(f"line {line_number}: invalid record: {exc}")

    if records:
        numbers = sorted(records)
        gaps = sorted(set(range(numbers[0], numbers[-1] + 1)) - set(numbers))
        print(f"Records: {len(records)}")
        print(f"Range: {numbers[0]}-{numbers[-1]}")
        if gaps:
            print(f"Missing paragraph numbers inside extracted range: {', '.join(map(str, gaps[:100]))}")
            if len(gaps) > 100:
                print(f"... and {len(gaps) - 100} more")
        else:
            print("No gaps inside extracted range.")
        suspicious = [
            number for number, item in records.items()
            if re.search(r"\b(?:Copyright|Libreria Editrice Vaticana)\b", item["text"], re.I)
        ]
        if suspicious:
            print(f"Review paragraphs containing page footer text: {suspicious[:20]}")

    if errors:
        print("\nValidation errors:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Structural validation passed. Numbering and text still require human spot-checking against the source.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Regenerate individual JSON files and Markdown from the canonical JSONL."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "catechism"
JSONL_PATH = DATA_DIR / "catechism.jsonl"


def main() -> int:
    if not JSONL_PATH.exists():
        print(f"File not found: {JSONL_PATH}")
        return 2

    records = []
    for line in JSONL_PATH.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    records.sort(key=lambda item: int(item["reference"]["number"]))

    paragraph_dir = DATA_DIR / "paragraphs"
    paragraph_dir.mkdir(parents=True, exist_ok=True)
    for item in records:
        number = int(item["reference"]["number"])
        (paragraph_dir / f"{number:04d}.json").write_text(
            json.dumps(item, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    lines = [
        "# Catecismo da Igreja Católica",
        "",
        "> Conteúdo extraído localmente do site oficial do Vaticano. Consulte os avisos de direitos antes de redistribuir.",
        "",
    ]
    for item in records:
        number = int(item["reference"]["number"])
        lines.extend([
            f"## Parágrafo {number}",
            "",
            item["text"],
            "",
            f"Fonte: {item['source_url']}",
            "",
        ])
    (DATA_DIR / "catechism.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Exported {len(records)} paragraphs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

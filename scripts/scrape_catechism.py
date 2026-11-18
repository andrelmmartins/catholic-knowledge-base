#!/usr/bin/env python3
"""Download Vatican Catechism HTML pages and extract numbered paragraphs locally.

The downloaded HTML and extracted text are intentionally written to ignored local
folders. Do not publish the resulting content unless redistribution is authorized.
"""
from __future__ import annotations

import argparse
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

INDEX_URL = (
    "https://www.vatican.va/archive/cathechism_po/index_new/"
    "prima-pagina-cic_po.html"
)
SOURCE_NAME = "Catecismo da Igreja Católica"
PUBLISHER = "Libreria Editrice Vaticana"
ROOT = Path(__file__).resolve().parents[1]
CACHE_DIR = ROOT / "cache" / "catechism"
OUTPUT_DIR = ROOT / "data" / "catechism"
JSONL_PATH = OUTPUT_DIR / "catechism.jsonl"
MANIFEST_PATH = OUTPUT_DIR / "manifest.json"
USER_AGENT = "CatholicKnowledgeBaseResearch/0.1 (polite educational retrieval; contact: repository owner)"
PAGE_RANGE_RE = re.compile(r"_(\d+)-(\d+)_po\.html$", re.IGNORECASE)
PARAGRAPH_RE = re.compile(r"(?m)^\s*(\d{1,4})\.\s+")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_filename(url: str) -> str:
    name = Path(urlparse(url).path).name
    return re.sub(r"[^A-Za-z0-9._-]", "_", name)


def fetch(client: httpx.Client, url: str, cache_path: Path, refresh: bool) -> str:
    if cache_path.exists() and not refresh:
        return cache_path.read_text(encoding="utf-8", errors="replace")

    response = client.get(url)
    response.raise_for_status()
    response.encoding = response.encoding or "utf-8"
    html = response.text
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(html, encoding="utf-8")
    return html


def discover_pages(index_html: str) -> list[dict[str, object]]:
    soup = BeautifulSoup(index_html, "html.parser")
    pages: dict[str, dict[str, object]] = {}

    for anchor in soup.find_all("a", href=True):
        url = urljoin(INDEX_URL, str(anchor["href"]))
        filename = Path(urlparse(url).path).name
        match = PAGE_RANGE_RE.search(filename)
        if not match or url in pages:
            continue
        start, end = int(match.group(1)), int(match.group(2))
        pages[url] = {
            "url": url,
            "filename": filename,
            "paragraph_start": start,
            "paragraph_end": end,
            "label": anchor.get_text(" ", strip=True),
        }

    return sorted(
        pages.values(),
        key=lambda item: (int(item["paragraph_start"]), int(item["paragraph_end"])),
    )


def extract_paragraphs(html: str, page: dict[str, object]) -> list[dict[str, object]]:
    """Extract numbered paragraphs within the numeric range encoded in the page URL.

    The Vatican pages use legacy HTML markup. We normalize visible text and use the
    page's explicit paragraph range to avoid treating arbitrary footnote numbers as
    paragraph references. The validation command reports gaps for manual review.
    """
    soup = BeautifulSoup(html, "html.parser")
    for element in soup(["script", "style", "noscript"]):
        element.decompose()

    visible_text = soup.get_text("\n", strip=True)
    start = int(page["paragraph_start"])
    end = int(page["paragraph_end"])
    matches = [
        match for match in PARAGRAPH_RE.finditer(visible_text)
        if start <= int(match.group(1)) <= end
    ]

    paragraphs: list[dict[str, object]] = []
    seen: set[int] = set()
    for index, match in enumerate(matches):
        number = int(match.group(1))
        if number in seen:
            continue
        next_match = matches[index + 1] if index + 1 < len(matches) else None
        body_start = match.end()
        body_end = next_match.start() if next_match else len(visible_text)
        text = re.sub(r"\s+", " ", visible_text[body_start:body_end]).strip()
        text = re.sub(r"\s+\*\s+\*\s+\*\s*$", "", text).strip()
        if not text:
            continue
        seen.add(number)
        paragraphs.append({
            "id": f"cic-{number:04d}",
            "source": "catechism",
            "reference": {"type": "paragraph", "number": number},
            "text": text,
            "source_url": str(page["url"]),
            "language": "pt",
            "publisher": PUBLISHER,
        })

    return paragraphs


def read_existing() -> dict[int, dict[str, object]]:
    records: dict[int, dict[str, object]] = {}
    if not JSONL_PATH.exists():
        return records
    for line in JSONL_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        number = int(item["reference"]["number"])
        records[number] = item
    return records


def write_outputs(records: dict[int, dict[str, object]], pages: list[dict[str, object]]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ordered = [records[number] for number in sorted(records)]

    JSONL_PATH.write_text(
        "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in ordered),
        encoding="utf-8",
    )

    individual_dir = OUTPUT_DIR / "paragraphs"
    individual_dir.mkdir(parents=True, exist_ok=True)
    for item in ordered:
        number = int(item["reference"]["number"])
        (individual_dir / f"{number:04d}.json").write_text(
            json.dumps(item, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    markdown = [
        "# Catecismo da Igreja Católica",
        "",
        "> Conteúdo extraído localmente do site oficial do Vaticano. Consulte o manifesto e os avisos de direitos antes de redistribuir.",
        "",
    ]
    for item in ordered:
        number = int(item["reference"]["number"])
        markdown.extend([f"## Parágrafo {number}", "", str(item["text"]), "", f"Fonte: {item['source_url']}", ""])
    (OUTPUT_DIR / "catechism.md").write_text("\n".join(markdown), encoding="utf-8")

    manifest = {
        "source": SOURCE_NAME,
        "publisher": PUBLISHER,
        "source_url": INDEX_URL,
        "language": "pt",
        "format": "html",
        "last_fetched_at": now_iso(),
        "paragraph_count": len(ordered),
        "page_count_discovered": len(pages),
        "pages_processed": [str(page["url"]) for page in pages],
        "license": {
            "status": "all_rights_reserved",
            "redistribution": "permission_required",
            "note": "This repository does not grant rights to the source text.",
        },
        "outputs": ["catechism.jsonl", "paragraphs/*.json", "catechism.md"],
    }
    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--list", action="store_true", help="List all Catechism content pages.")
    mode.add_argument("--limit", type=int, help="Process only the first N pages (useful for tests).")
    mode.add_argument("--all", action="store_true", help="Process every discovered page.")
    parser.add_argument("--delay", type=float, default=1.0, help="Seconds between network requests (default: 1).")
    parser.add_argument("--refresh", action="store_true", help="Ignore cached HTML and download pages again.")
    args = parser.parse_args()

    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be greater than zero")
    if args.delay < 0:
        parser.error("--delay cannot be negative")

    headers = {"User-Agent": USER_AGENT}
    timeout = httpx.Timeout(30.0, connect=15.0)
    with httpx.Client(headers=headers, timeout=timeout, follow_redirects=True) as client:
        index_cache = CACHE_DIR / "index.html"
        index_html = fetch(client, INDEX_URL, index_cache, args.refresh)
        pages = discover_pages(index_html)

        if not pages:
            raise SystemExit("No content pages found in the Vatican index; inspect the HTML structure.")

        print(f"Discovered {len(pages)} pages.")
        if args.list:
            for page in pages:
                print(
                    f"{page['paragraph_start']:>4}-{page['paragraph_end']:<4} "
                    f"{page['url']}"
                )
            return 0

        selected = pages[: args.limit] if args.limit is not None else pages
        records = read_existing()
        processed: list[dict[str, object]] = []

        for index, page in enumerate(selected, start=1):
            url = str(page["url"])
            cache_path = CACHE_DIR / safe_filename(url)
            print(f"[{index}/{len(selected)}] {url}")
            try:
                html = fetch(client, url, cache_path, args.refresh)
                extracted = extract_paragraphs(html, page)
                print(f"  extracted {len(extracted)} paragraphs")
                for item in extracted:
                    number = int(item["reference"]["number"])
                    records[number] = item
                processed.append(page)
            except (httpx.HTTPError, OSError, ValueError) as exc:
                print(f"  ERROR: {exc}")
            if index < len(selected):
                time.sleep(args.delay)

        write_outputs(records, processed)
        print(f"Saved {len(records)} unique paragraphs to {JSONL_PATH}")
        print("Generated JSONL, individual JSON files, Markdown and manifest.")
        if len(processed) != len(selected):
            print("Some pages failed. Re-run the same command; cached pages and existing records are retained.")
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

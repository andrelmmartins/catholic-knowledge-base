from scripts.scrape_catechism import discover_pages, extract_paragraphs


def test_discover_pages_extracts_ranges_and_ignores_index():
    html = """
    <html><body>
      <a href="prima-pagina-cic_po.html">Index</a>
      <a href="p1s1c1_26-49_po.html">§ 26-49</a>
      <a href="p1s1c2_50-141_po.html">§ 50-141</a>
    </body></html>
    """
    pages = discover_pages(html)
    assert [(p["paragraph_start"], p["paragraph_end"]) for p in pages] == [
        (26, 49), (50, 141)
    ]


def test_extract_paragraphs_extracts_only_numbers_in_page_range():
    html = """
    <html><body>
      <p>CAPÍTULO PRIMEIRO</p>
      <p>26. Primeiro parágrafo do teste.</p>
      <p>27. Segundo parágrafo do teste.</p>
      <p>Nota 1. Não deve virar parágrafo.</p>
    </body></html>
    """
    page = {
        "url": "https://example.test/p1_26-27_po.html",
        "paragraph_start": 26,
        "paragraph_end": 27,
    }
    records = extract_paragraphs(html, page)
    assert [item["reference"]["number"] for item in records] == [26, 27]
    assert records[0]["text"] == "Primeiro parágrafo do teste."
    assert records[1]["text"].startswith("Segundo parágrafo do teste.")

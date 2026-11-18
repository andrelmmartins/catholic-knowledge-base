# Catholic Knowledge Base

Ferramentas para coletar, normalizar e validar fontes católicas primárias para uso em aplicações de busca e RAG.

## Status

Em desenvolvimento. A primeira fonte em preparação é o Catecismo da Igreja Católica em português, hospedado no site oficial do Vaticano.

## Direitos e redistribuição

O conteúdo do Catecismo é publicado pela Libreria Editrice Vaticana. Este repositório não presume que o texto integral possa ser redistribuído. O scraper foi pensado para uso local; arquivos extraídos e cache não são versionados por padrão. Antes de publicar conteúdo integral, verifique as condições aplicáveis e obtenha autorização quando necessária.

O código deste repositório é separado dos direitos sobre os textos coletados. Consulte `NOTICE.md`.

## Requisitos

- Python 3.11 ou superior
- `uv` (recomendado) ou `pip`

## Instalação

```bash
uv sync
```

## Mapear as páginas do Catecismo

```bash
uv run python scripts/scrape_catechism.py --list
```

## Testar com poucas páginas

```bash
uv run python scripts/scrape_catechism.py --limit 2
```

## Processar todas as páginas descobertas

```bash
uv run python scripts/scrape_catechism.py --all
```

Os resultados são gravados localmente em `data/catechism/`. O cache HTML fica em `cache/`. Ambos são ignorados pelo Git por padrão.

## Validar os dados extraídos

```bash
uv run python scripts/validate_catechism.py
```

## Formatos

- `catechism.jsonl`: um registro por parágrafo, formato canônico para processamento.
- `paragraphs/NNNN.json`: arquivos individuais gerados a partir do JSONL.
- `catechism.md`: versão legível gerada a partir do JSONL.
- `manifest.json`: fonte, datas, contagens e status de licença.

Os arquivos JSON individuais e Markdown são derivados do JSONL, evitando divergência entre formatos.
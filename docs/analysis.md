# D4GC document analysis

## Research workflow and knowledge graph

The [main README](../README.md#research-workflow) describes how to use the two
applications together: find relevant documents and passages with the Navigator's
search/RAG workflow, inspect the evidence, then explore possible related documents
in the [Document Constellation knowledge graph](../msf-document-constellation/README.md).
This supports faster discovery and follow-up reading around an initial finding.

The graph accepts a document ID through `?doc=<document-id>` and shows connected
documents ordered by the supplied edge weight. Its filters cover theme, genre,
language, country, and year; text search covers titles and snippets. The graph
loads a separate remote JSON dataset with precomputed positions and connections.
It does not currently refresh from the local corpus or feed related documents
automatically into RAG. Check that an ID exists in both datasets when moving
between the tools, and verify relevance against the original source.

## Document navigator

Run `python -m streamlit run app.py` from the repository root. The app indexes all 582 available parsed documents with a local BM25 implementation, searches by query terms, and offers language, genre, country mention, and topic filters. Results show a source excerpt and let the user download the original PDF or HTML. The index is cached in memory while the app runs; restart it after changing documents or metadata. The app requires `streamlit`; the search core uses only the Python standard library.

The local interface uses colours and an English logo from the [MSF Belgium website](https://www.msf-azg.be/en). The logo is stored at `assets/msf-azg-logo-en.svg` so it renders offline; its [source SVG](https://www.msf-azg.be/themes/custom/msf_patterns_theme/images/azg-logo-en.svg) is owned by MSF. The dashboard is an independent Data 4 Good prototype and does not represent an official MSF website.

The interface has two main choices: **Find documents** ranks whole documents by query words and lets users open the original files; **Ask LLM** retrieves Markdown passages and asks a local Ollama model to draft an answer. Country and topic facets are candidate tags and can miss relevant documents. This is a Reor-inspired workflow built into this Python app, not a copy of Reor's desktop application.

The optional **Find partners** mode accepts a question such as “Who are the partners in Syria?” or uses the sidebar country selection. It retrieves passages with country and explicit partnership wording, asks a locally installed Ollama model for organisation names, then accepts a name only when it appears close to that relationship wording. Forward-looking calls for support are excluded. Each result shows its source ID, excerpt, and file path. This is a candidate list from documents across different years, not a verified list of current partners. The source passages remain visible if the model is unavailable or returns no verifiable names. The Syria example returned Al-Ameen and Migrant’s Office. A Nigeria check returned Nigerian health authorities; UNICEF and the World Food Program were rejected because their passage asked them to increase support rather than describing an existing partnership.

The **Ask LLM** mode is for general natural-language questions. A local Ollama model proposes keyword searches. The same whole-document BM25 search used by **Find documents** selects a shortlist of documents. BM25 then ranks passages *within that shortlist*, and the local model drafts an answer from those passages. For country-partner questions, passage ranking prefers explicit partnership wording close to the named country; this happens after whole-document retrieval, not through the optional partner mode. The dashboard exposes the document shortlist and every passage sent to the model, including file path and text. The supplied passage list is not a claim that every passage supports every sentence; only explicit IDs in the answer are model citations. Citation IDs are constrained to retrieved passages, but the app cannot prove that the model interpreted a passage correctly. Uncited drafts are labeled unverified. `qwen3:4b` is the default when installed. An end-to-end Nigeria check returned Nigerian health authorities with citation `Dacd2f2d218:2`. This mode needs a running Ollama service and a downloaded model, but no cloud connection.

## Metadata enrichment pipeline

The [enrichment notebook](../notebooks/metadata_enrichment_pipeline.ipynb) runs with the `Python 3` kernel and writes [documentation_enriched.csv](../data/processed/documentation_enriched.csv). It preserves every row and the original `id`, `genre`, and `language` columns from `data/documentation.csv`. The reusable extraction rules are in `src/msf_navigator/enrich_metadata.py`; `scripts/build_enrichment_notebook.py` regenerates the notebook.

The enriched file has 764 rows and 19 columns. Of those rows, 582 have parsed text and an original file; 182 have neither. Country mentions appear in 419 rows, city mentions in 192, and topic tags in 427. Added fields include source format and paths, availability flags, word count, text hash, duplicate group size, geography evidence snippets, and extraction method. Location and topic fields are pipe-separated candidate tags. They are not verified primary locations or exhaustive labels, and the current lexicons have limited Arabic coverage. Use them as optional RAG facets after manual review, not as hard exclusions. The notebook asserts row and original-column preservation and ran without errors with Bigdata on 28 October 2026.

The [corpus notebook](../notebooks/corpus_audit_and_retrieval.ipynb) audits the supplied documents and demonstrates a local TF-IDF search. Run it from the repository root with Python 3, `pandas`, `scikit-learn`, `nbformat`, `nbclient`, and `ipykernel`. `scripts/build_notebook.py` regenerates the notebook; `src/msf_navigator/corpus_analysis.py` contains the reusable audit and search functions. The existing empty `notebooks/archive/AC/test.ipynb` is preserved.

## Findings (28 October 2026)

- The challenge brief asks for retrieval across the full collection, with speed, few false positives, low cost, maintainability, and offline operation. The supplied Markdown is a convenient starting point, but figures and images may be parsed poorly; original PDF/HTML should remain accessible.
- There are 582 parsed Markdown files and 582 original files, with matching IDs. The metadata CSV has 764 unique rows: 182 IDs have no supplied document. Every supplied document has metadata. Search indexes should be built from actual files, not all metadata rows.
- The 582 documents contain 470 English, 51 Arabic, 44 French, and 17 Spanish labels. The largest genre is peer-reviewed article (216); clinical guideline chapters account for 70. Cross-language retrieval requires explicit testing because the baseline does not translate queries.
- Median length is 918 Unicode word tokens, ranging from 76 to 295,018. One file (`De35232409a`) has fewer than 100 words. Long documents may need section-level indexing; short and image-heavy documents merit original-file review.
- SHA-256 comparison found 4 groups of identical parsed text, representing 20 extra documents. One group contains 18 IDs with the same 218-word “Latest News” text, suggesting a parsing or source duplication issue. Exact duplicate removal should retain all source IDs and be checked against originals.

## Assumptions and limits

This analysis uses the supplied Markdown as the searchable text and `documentation.csv` as the source of genre and language labels. Word counts use Unicode `\w+` tokens and are descriptive, not linguistic tokenization. The TF-IDF demo ranks documents, but the dataset has no query relevance judgments, so neither accuracy nor false-positive rate can be claimed. The index is rebuilt in memory and is a baseline, not a complete production pipeline.

For the next evaluation, label relevance for realistic multilingual field queries. Compare precision at 5, recall at 10, false positives per query, latency, memory, and index size. Keep original-document links in search results and test whether section-level indexing improves long guidelines and reports.

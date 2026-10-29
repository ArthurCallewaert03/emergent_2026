# MSF Document Research — D4GC 2026

A research workspace for finding relevant information in the MSF document collection
and quickly exploring related sources. The aim is to find the **needle in the
haystack** with search and retrieval-augmented generation (RAG), then use the
knowledge graph to discover potentially related documents and build context faster.

| Application | Use it for |
| --- | --- |
| **Document Navigator** (`app.py`) | Search document text, retrieve passages, draft answers with a local Ollama model, and inspect or download original sources. |
| **[Document Constellation](msf-document-constellation/README.md)** | Explore the knowledge graph, select a promising document, and follow its **Similar documents** list to broaden your research. |

This is an independent Data 4 Good prototype. Related documents are research leads;
inspect their contents to decide whether they support your question.

The [final pitch presentation (PDF)](final_pitch.pdf) is included in this repository.

## Research workflow

1. **Find the needle.** Use **Find documents** for keywords or **Ask LLM** for a
   natural-language question. RAG retrieves documents and passages before asking
   the local model to draft an answer.
2. **Check the evidence.** Review the passages, document IDs, and original sources
   shown by the Navigator. Keep the ID of a useful document.
3. **Explore its neighbourhood.** Append `?doc=<document-id>` to the Constellation
   URL to select that document, provided it exists in the graph dataset. You can
   also search the graph by title or snippet.
4. **Follow related leads.** Select entries under **Similar documents** and use
   theme, genre, language, country, and year filters to focus the map.
5. **Read and refine.** Use the selected IDs to locate Markdown files in
   `data/corpus/Parsed/` and original PDF/HTML files in `data/corpus/Original/`,
   where available. Return to the Navigator with more specific search terms or
   questions as your understanding improves.

The applications currently run separately. Moving from a RAG result to the graph
is a manual step using the document ID; graph neighbours are not automatically
added to the RAG context. The graph's title/snippet search is separate from the
Navigator's document-text search.

## Launch the Document Navigator

Use Python 3.11 or newer. From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[analysis]"
python -m streamlit run app.py
```

For the app alone, install with `python -m pip install -e .`.
The supplied local data and enriched metadata must be present. Search runs offline;
Ask LLM and Find partners additionally require a running Ollama service and a
downloaded model (`qwen3:4b` is the default when available).

## Launch the knowledge graph

In a second terminal, from the repository root, with Node.js and npm installed:

```powershell
cd msf-document-constellation
npm install
npm run dev
```

Open the local URL printed by the development server. Append
`/?doc=<document-id>` to its origin to open a specific document.
See the [Constellation README](msf-document-constellation/README.md) for graph
controls, data configuration, and development commands.

The graph currently fetches a separately supplied JSON dataset from a remote URL,
so it needs network access to load that dataset. It does not automatically rebuild
from `data/corpus/` or the enriched CSV. The Navigator's local search remains offline.

## Project layout

```text
app.py                       Streamlit entry point
final_pitch.pdf              Final pitch presentation
msf-document-constellation/   Web knowledge graph and related-document explorer
assets/                      Local logo and theme
src/msf_navigator/            Search, retrieval, enrichment, and shared paths
scripts/                     Notebook generation scripts
notebooks/                   Corpus audit and metadata enrichment notebooks
notebooks/archive/           Preserved contributor placeholders
data/documentation.csv       Original metadata
data/corpus/Original/        Original PDF and HTML documents
data/corpus/Parsed/          Parsed Markdown documents
data/processed/              Enriched metadata used by the app
docs/analysis.md              Workflow details, findings, and limitations
docs/references/              Challenge brief, scans, and prototype shortcut
docs/git/                    Git reference material
tests/                       Corpus and retrieval regression checks
.streamlit/                   Shared app theme settings
```

## Analysis and maintenance

Open the notebooks with a Python kernel containing the analysis dependencies.
Run them from the repository root or any directory inside this repository.
Regenerate notebook sources with:

```powershell
python scripts/build_notebook.py
python scripts/build_enrichment_notebook.py
```

After installing the package, regenerate enriched metadata with:

```powershell
python -m msf_navigator.enrich_metadata
```

This replaces `data/processed/documentation_enriched.csv`. Restart the app after
changing documents or metadata to rebuild its in-memory index.

Run the regression checks from the root:

```powershell
python -m unittest discover -s tests -v
```

See [analysis notes](docs/analysis.md) for retrieval behavior and dataset limitations.
The source corpus and original metadata are preserved. Generated notebook outputs
were cleared during organization so old paths and results are not mistaken for a
fresh run. Earlier paths under `src/AC` now live in the folders listed above;
launch the application using `app.py`.

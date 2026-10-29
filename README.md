# MSF Document Navigator — D4GC 2026

An offline Streamlit prototype for searching the supplied MSF document collection.
It supports document search, source downloads, and optional answers from a local
Ollama model. This is an independent Data 4 Good project.

## Setup and launch

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

## Project layout

```text
app.py                       Streamlit entry point
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

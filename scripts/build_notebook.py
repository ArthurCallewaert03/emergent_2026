"""Regenerate the D4GC exploration notebook with nbformat."""
from pathlib import Path
import nbformat as nbf

HERE = Path(__file__).resolve().parents[1] / "notebooks"
nb = nbf.v4.new_notebook()
nb.metadata.kernelspec = {"display_name": "Python 3", "language": "python", "name": "python3"}
nb.cells = [
    nbf.v4.new_markdown_cell("# D4GC corpus audit and retrieval baseline\n\nRun top to bottom from a working directory inside this repository. The notebook reads the supplied corpus without changing it. The challenge brief asks for an on premises, fast, cost conscious retrieval tool with few false positives. This notebook audits the supplied text and demonstrates a lexical baseline; it does **not** establish retrieval accuracy without relevance judgments."),
    nbf.v4.new_code_cell("from pathlib import Path\nimport sys\nimport pandas as pd\n\n# Find this repository when the notebook is opened from notebooks/ or the root.\nrepo = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / 'data' / 'documentation.csv').exists())\nsys.path.insert(0, str(repo / 'src'))\nfrom msf_navigator.corpus_analysis import load_corpus, audit, build_index, search\nrecords, metadata = load_corpus()\nsummary = audit(records, metadata)\nsummary"),
    nbf.v4.new_markdown_cell("## Coverage and metadata\n\nCompare actual files with the metadata table. Missing metadata is retained as `missing`; do not silently infer labels."),
    nbf.v4.new_code_cell("pd.DataFrame(records).groupby(['language', 'genre'], dropna=False).size().sort_values(ascending=False).head(20)"),
    nbf.v4.new_code_cell("pd.DataFrame(records)[['id','words','characters','language','genre']].describe(include='all')"),
    nbf.v4.new_markdown_cell("## Document quality\n\nVery short text may indicate parsing loss, especially for figures or scans. Exact duplicates are detected by SHA-256; near duplicates are outside this quick audit. Inspect the original PDF/HTML before concluding a short file has no useful content."),
    nbf.v4.new_code_cell("pd.DataFrame(records).nsmallest(15, 'words')[['id','words','language','genre']]"),
    nbf.v4.new_markdown_cell("## Offline retrieval baseline\n\nA Unicode word TF-IDF index works without downloaded models. It is language agnostic in implementation, but does not translate queries; test each source language separately. Scores rank results within one query; they are not calibrated probabilities. Reviewers should judge relevance and false positives for real field queries before selecting a production threshold."),
    nbf.v4.new_code_cell("vectorizer, matrix = build_index(records)\nprint('Index shape:', matrix.shape, 'nonzero values:', matrix.nnz)\nfor query in ['cholera treatment', 'malnutrition children', 'tuberculosis drug resistance']:\n    print('\\n', query)\n    display(pd.DataFrame(search(query, records, vectorizer, matrix), columns=['id','score','genre','language']))"),
    nbf.v4.new_markdown_cell("## Next validation\n\nCreate a small, multilingual query set with document relevance labels from domain experts. Report precision at 5, recall at 10, false positives per query, query latency, index size, and performance by language and genre. Compare this baseline with word TF-IDF/BM25 and optional reranking. Keep source IDs in every result so users can open the original document."),
]
target = HERE / "corpus_audit_and_retrieval.ipynb"
nbf.write(nb, target)
print(target)

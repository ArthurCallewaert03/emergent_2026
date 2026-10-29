"""Regenerate the metadata enrichment notebook (run with host Python)."""
from pathlib import Path
import nbformat as nbf

here = Path(__file__).resolve().parents[1] / "notebooks"
nb = nbf.v4.new_notebook()
nb.metadata.kernelspec = {"display_name": "Python 3", "language": "python", "name": "python3"}
nb.cells = [
    nbf.v4.new_markdown_cell("# Enrich D4GC document metadata\n\nThis pipeline reads `data/documentation.csv` and the parsed Markdown corpus. It writes `data/processed/documentation_enriched.csv`, leaving the source untouched. Geography fields are **mentions in text**, not verified primary locations. The curated dictionaries are in `enrich_metadata.py` and are deliberately incomplete. Review matches before using them as RAG filters."),
    nbf.v4.new_code_cell("from pathlib import Path\nimport sys\nimport pandas as pd\nrepo = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / 'data' / 'documentation.csv').exists())\nsys.path.insert(0, str(repo / 'src'))\nfrom msf_navigator.enrich_metadata import run, OUTPUT\nrows = run()\ndf = pd.DataFrame(rows)\nprint(f'Wrote {len(df)} rows to {OUTPUT}')\nprint('Columns:', ', '.join(df.columns))"),
    nbf.v4.new_markdown_cell("## Coverage and quality checks\n\nThe row count and original columns must match the source. Unavailable documents remain in the output with blank enrichment fields. Exact duplicate text is flagged for later deduplication; all document IDs are retained."),
    nbf.v4.new_code_cell("source = pd.read_csv(repo / 'data' / 'documentation.csv', dtype=str).fillna('')\nassert len(df) == len(source)\nassert df[['id','genre','language']].reset_index(drop=True).equals(source[['id','genre','language']].reset_index(drop=True))\nassert df['id'].is_unique\nassert (df.loc[df.parsed_available.eq('false'), ['country_mentions','city_mentions','topic_tags']] == '').all().all()\nprint('Rows:', len(df), 'parsed:', df.parsed_available.eq('true').sum(), 'missing parsed:', df.parsed_available.eq('false').sum())\nprint('Country mentions:', df.country_mentions.ne('').sum(), 'city mentions:', df.city_mentions.ne('').sum())\nprint('Duplicate text rows:', pd.to_numeric(df.duplicate_text_group_size, errors='coerce').gt(1).sum())"),
    nbf.v4.new_markdown_cell("## Review examples\n\nInspect evidence snippets to identify publication datelines, broad surveys, ambiguous place names, and missed languages. A document may have several countries or cities separated by `|`. Empty fields mean no lexicon match."),
    nbf.v4.new_code_cell("display(df.loc[df.country_mentions.ne(''), ['id','language','country_mentions','city_mentions','country_evidence']].head(15))\ndisplay(df.loc[df.city_mentions.ne(''), ['id','city_mentions','city_evidence']].head(10))"),
    nbf.v4.new_markdown_cell("## RAG use and limits\n\nUse `id` and paths as provenance. Treat topic tags and place mentions as candidate filters or facets, with an option to search without them. The current lexicons do not cover every location, Arabic names, synonyms, or transliterations. Broad terms and publication datelines can create false positives. Before production, manually label a sample across languages and genres, extend the gazetteer, and measure mention precision and recall. Do not use these columns to make clinical decisions without inspecting source documents."),
]
target = here / 'metadata_enrichment_pipeline.ipynb'
nbf.write(nb, target)
print(target)

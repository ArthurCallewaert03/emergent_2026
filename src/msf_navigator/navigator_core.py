"""Offline document search for the supplied D4GC corpus."""
from pathlib import Path
import csv
import re

from .local_bm25 import BM25Okapi
from .title_extractor import extract_clean_title

from .paths import ROOT, CORPUS, ENRICHED_METADATA
METADATA = ENRICHED_METADATA
TOKEN = re.compile(r"\w+", re.UNICODE)


def tokenize(text):
    return TOKEN.findall(text.casefold())


def load_index():
    if not METADATA.exists():
        raise FileNotFoundError(f"Enriched metadata missing: {METADATA}. Run metadata_enrichment_pipeline.ipynb first.")
    with METADATA.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    documents = []
    for row in rows:
        rel = row.get("parsed_path", "")
        if not rel:
            continue
        path = ROOT / rel
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        orig_rel = row.get("original_path", "")
        orig_path = (ROOT / orig_rel) if orig_rel else None
        title = row.get("title") or extract_clean_title(row["id"], text, orig_path)
        documents.append({**row, "text": text, "title": title[:220]})
    if not documents:
        raise ValueError("No parsed documents found for the enriched metadata.")
    index = BM25Okapi([tokenize(d["text"]) for d in documents])
    return documents, index


def search(query, documents, index, language="All", genre="All", country="All", topic="All", limit=10):
    terms = tokenize(query)
    if not terms:
        return []
    scores = index.get_scores(terms)
    candidates = []
    for document, score in zip(documents, scores):
        if score <= 0:
            continue
        if language != "All" and document["language"] != language:
            continue
        if genre != "All" and document["genre"] != genre:
            continue
        if country != "All" and country not in document["country_mentions"].split("|"):
            continue
        if topic != "All" and topic not in document["topic_tags"].split("|"):
            continue
        candidates.append((document, float(score)))
    return sorted(candidates, key=lambda x: (-x[1], x[0]["id"]))[:limit]


def excerpt(text, query, width=500):
    terms = sorted(set(tokenize(query)), key=len, reverse=True)
    pattern = re.compile(r"(?<!\w)(?:" + "|".join(map(re.escape, terms)) + r")(?!\w)", re.I) if terms else None
    match = pattern.search(text) if pattern else None
    start = max(0, match.start() - 100) if match else 0
    snippet = re.sub(r"\s+", " ", text[start:start + width]).strip()
    return ("…" if start else "") + snippet + ("…" if start + width < len(text) else "")

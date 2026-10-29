"""Reproducible corpus audit and local lexical retrieval for the D4GC data."""
from pathlib import Path
from collections import Counter
import csv
import hashlib
import re
import statistics

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
import numpy as np


from .paths import ROOT, CORPUS, ENRICHED_METADATA
DATA = CORPUS
PARSED = DATA / "Parsed"
ORIGINAL = DATA / "Original"
METADATA = ROOT / "data" / "documentation.csv"


def load_corpus():
    with METADATA.open(encoding="utf-8-sig", newline="") as handle:
        metadata = {row["id"]: row for row in csv.DictReader(handle)}
    records = []
    for path in sorted(PARSED.glob("*.md")):
        text = path.read_text(encoding="utf-8", errors="replace")
        records.append({"id": path.stem, "text": text, "characters": len(text),
                        "words": len(re.findall(r"\w+", text, re.UNICODE)),
                        "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                        "genre": metadata.get(path.stem, {}).get("genre"),
                        "language": metadata.get(path.stem, {}).get("language")})
    return records, metadata


def audit(records, metadata):
    ids = {r["id"] for r in records}
    originals = {p.stem for p in ORIGINAL.iterdir() if p.is_file()}
    hashes = Counter(r["sha256"] for r in records)
    sizes = [r["words"] for r in records]
    return {
        "metadata_rows": len(metadata), "parsed_documents": len(records),
        "original_documents": len(originals),
        "parsed_without_metadata": sorted(ids - metadata.keys()),
        "metadata_without_parsed": sorted(metadata.keys() - ids),
        "parsed_without_original": sorted(ids - originals),
        "original_without_parsed": sorted(originals - ids),
        "empty_documents": [r["id"] for r in records if not r["text"].strip()],
        "short_under_100_words": [r["id"] for r in records if r["words"] < 100],
        "duplicate_text_groups": sum(v > 1 for v in hashes.values()),
        "duplicate_extra_documents": sum(v - 1 for v in hashes.values() if v > 1),
        "word_count_min": min(sizes), "word_count_median": statistics.median(sizes),
        "word_count_max": max(sizes),
        "languages": dict(Counter(r["language"] or "missing" for r in records)),
        "top_genres": Counter(r["genre"] or "missing" for r in records).most_common(12),
    }


def build_index(records):
    # Unicode word tokens cover the supplied languages without downloaded models.
    vectorizer = TfidfVectorizer(min_df=2, max_features=100000,
                                 strip_accents="unicode", sublinear_tf=True,
                                 dtype=np.float32)
    matrix = vectorizer.fit_transform([r["text"] for r in records])
    return vectorizer, matrix


def search(query, records, vectorizer, matrix, limit=5):
    scores = linear_kernel(vectorizer.transform([query]), matrix).ravel()
    ranked = sorted(range(len(records)), key=lambda i: (-scores[i], records[i]["id"]))[:limit]
    return [(records[i]["id"], round(float(scores[i]), 4),
             records[i]["genre"], records[i]["language"]) for i in ranked]

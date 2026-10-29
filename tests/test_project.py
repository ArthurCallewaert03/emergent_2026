"""Integration checks for repository paths and the supplied search corpus."""
from pathlib import Path
import csv
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from msf_navigator.navigator_core import load_index, search
from msf_navigator.paths import CORPUS, ENRICHED_METADATA
from msf_navigator.rag_core import build_chunk_index, retrieve


class ProjectTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.documents, cls.index = load_index()

    def test_corpus_and_source_paths(self):
        self.assertEqual(len(self.documents), 582)
        self.assertEqual(len(list((CORPUS / "Parsed").glob("*.md"))), 582)
        with ENRICHED_METADATA.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 764)
        for row in rows:
            for field in ("parsed_path", "original_path"):
                if row[field]:
                    self.assertTrue((ROOT / row[field]).is_file(), row[field])

    def test_search_matches_pre_cleanup_baseline(self):
        expected = {
            "cholera treatment": ["D9c3366a7c9", "D0fdc1d0ef5", "D88155b92de"],
            "partners Syria": ["D270ed35e75", "D9e5162a399", "P47"],
            "malnutrition children": ["D5da0aed2fd", "P16", "Dd3254da5f8"],
        }
        for query, ids in expected.items():
            with self.subTest(query=query):
                results = search(query, self.documents, self.index, limit=3)
                self.assertEqual([doc["id"] for doc, _ in results], ids)

    def test_passage_retrieval(self):
        chunks, index = build_chunk_index(self.documents)
        results = retrieve("cholera treatment", chunks, index)
        self.assertTrue(results)


if __name__ == "__main__":
    unittest.main()

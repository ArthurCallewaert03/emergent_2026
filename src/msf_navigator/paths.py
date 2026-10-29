"""Repository paths shared by the application and analysis pipelines."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / "data" / "corpus"
ENRICHED_METADATA = ROOT / "data" / "processed" / "documentation_enriched.csv"

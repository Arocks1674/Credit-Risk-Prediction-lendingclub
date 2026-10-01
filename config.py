"""Paths and fixed settings. Change paths with environment variables if needed."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = Path(os.getenv("DATA_DIR", ROOT / "data"))
RAW_CSV = Path(os.getenv("RAW_CSV", DATA_DIR / "loan.csv"))
SAMPLE_CSV = DATA_DIR / "sample.csv"
DATASET = Path(os.getenv("DATASET", DATA_DIR / "loans.parquet"))   # cleaned matured loans: features + target
REPORTS = ROOT / "reports"

SEED = 42
TEST_FRACTION = 0.2      # newest 20% of loans (by issue date) = out-of-time test set

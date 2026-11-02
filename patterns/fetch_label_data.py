"""Download the daily bars behind every labelled case, so the tests run offline.

Run from the repo root after adding a case to patterns/labels.yaml:

    python -m patterns.fetch_label_data

Each case is saved to tests/data/labels/<id>.csv, from two years before the
range starts (enough history for the range search and the 200-day average)
to a month after the labelled exit.
"""
import os
from datetime import timedelta

import pandas as pd
import yaml

from data import get_data

LABELS = os.path.join(os.path.dirname(__file__), "labels.yaml")
OUT_DIR = os.path.join("tests", "data", "labels")


def load_labels(path=LABELS):
    with open(path) as f:
        return yaml.safe_load(f)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    for case in load_labels():
        start = pd.Timestamp(case["range"]["start"]) - timedelta(days=730)
        end = pd.Timestamp(case["trade"]["exit"]["date"]) + timedelta(days=30)
        df = get_data(case["ticker"], start=start.strftime("%Y-%m-%d"), end=end.strftime("%Y-%m-%d"))
        path = os.path.join(OUT_DIR, f"{case['id']}.csv")
        df.to_csv(path, float_format="%.6g")
        print(f"{case['id']}: {len(df)} bars -> {path}")


if __name__ == "__main__":
    main()

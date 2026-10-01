"""Module 1: build the leakage-free modelling table from loan.csv.

    python prepare_data.py              # full file -> data/loans.parquet + reports/data_summary.md
    python prepare_data.py --sample     # data/sample.csv instead (fast, for development)
"""
import argparse

import pandas as pd

import config
from src.data.prepare import build, out_of_time_split, read_raw, snapshot_date, summary


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--sample", action="store_true", help="use data/sample.csv")
    args = p.parse_args()
    src = config.SAMPLE_CSV if args.sample else config.RAW_CSV
    if not src.exists():
        raise SystemExit(f"Not found: {src}" + ("  (run python profile_data.py first)" if args.sample else ""))

    raw = read_raw(src)
    snap = snapshot_date(raw["last_pymnt_d"])
    df = build(raw, snap)
    train, test, cutoff = out_of_time_split(df, config.TEST_FRACTION)

    by_year = df.groupby(df["issue_date"].dt.year).agg(loans=("default", "size"),
                                                       default_rate_pct=("default", "mean"))
    by_year["default_rate_pct"] *= 100
    by_term = df.groupby("term_months")["default"].agg(["size", "mean"]).rename(
        columns={"size": "loans", "mean": "default_rate"})
    split = pd.DataFrame({
        "loans": [len(train), len(test)],
        "issued": [f"{train.issue_date.min():%b %Y} to {train.issue_date.max():%b %Y}",
                   f"{test.issue_date.min():%b %Y} to {test.issue_date.max():%b %Y}"],
        "default_rate_%": [train["default"].mean() * 100, test["default"].mean() * 100],
    }, index=["train", "test (out-of-time)"])

    md = ["# Modelling data\n", f"Source: `{src.name}`  |  data snapshot: {snap:%b %Y}\n",
          "## From raw rows to the modelling table\n", summary(raw, df, snap).to_markdown(floatfmt=".1f"), "\n",
          "## Matured loans by issue year\n", by_year.to_markdown(floatfmt=".1f"), "\n",
          "## By term\n", by_term.to_markdown(floatfmt=".3f"), "\n",
          "## Out-of-time split\n", split.to_markdown(floatfmt=".1f"), "\n"]
    config.REPORTS.mkdir(exist_ok=True)
    name = "data_summary_sample.md" if args.sample else "data_summary.md"
    (config.REPORTS / name).write_text("\n".join(md), encoding="utf-8")
    out = config.DATA_DIR / ("loans_sample.parquet" if args.sample else "loans.parquet")
    df.to_parquet(out, index=False)
    print("\n".join(md))
    print(f"Saved {out} ({len(df):,} loans, {df.shape[1]} columns)")


if __name__ == "__main__":
    main()

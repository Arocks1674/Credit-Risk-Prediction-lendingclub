"""Step 0: profile loan.csv and write a small random sample.

The full file is ~1.2 GB / ~887k loans. This reads it in chunks (low memory) and writes:
  reports/data_profile.md   columns, types, missing %, loan status counts, issue-date range
  data/sample.csv           a 5% random sample of all rows (~44k loans, ~60 MB) for fast development

Usage:
    python profile_data.py
"""
import argparse

import pandas as pd

import config


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--frac", type=float, default=0.05)
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()

    if not config.RAW_CSV.exists():
        raise SystemExit(f"Not found: {config.RAW_CSV}")

    n = 0
    nulls = None
    dtypes = {}
    status = pd.Series(dtype="int64")
    issue = pd.Series(dtype="int64")
    term_by_status = []
    last_pymnt = []
    samples = []
    for chunk in pd.read_csv(config.RAW_CSV, chunksize=200_000, low_memory=False):
        n += len(chunk)
        nn = chunk.isna().sum()
        nulls = nn if nulls is None else nulls.add(nn, fill_value=0)
        for c, t in chunk.dtypes.items():
            dtypes.setdefault(c, str(t))
        status = status.add(chunk["loan_status"].value_counts(), fill_value=0)
        issue = issue.add(chunk["issue_d"].value_counts(), fill_value=0)
        term_by_status.append(chunk.groupby(["term", "loan_status"]).size())
        if "last_pymnt_d" in chunk:
            last_pymnt.append(chunk["last_pymnt_d"].dropna().unique())
        samples.append(chunk.sample(frac=args.frac, random_state=args.seed))
        print(f"read {n:,} rows")

    issue.index = pd.to_datetime(issue.index, format="%b-%Y")
    issue = issue.sort_index()
    by_year = issue.groupby(issue.index.year).sum().astype(int)
    lp = pd.to_datetime(pd.Series(pd.unique(pd.concat([pd.Series(x) for x in last_pymnt]))), format="%b-%Y")
    tbs = pd.concat(term_by_status).groupby(level=[0, 1]).sum().unstack(fill_value=0).astype(int)

    md = [f"# loan.csv profile\n", f"Rows: {n:,}  |  Columns: {len(dtypes)}\n",
          f"issue_d range: {issue.index.min():%b %Y} to {issue.index.max():%b %Y}  |  "
          f"latest last_pymnt_d (data snapshot): {lp.max():%b %Y}\n",
          "## Loans issued per year\n", by_year.to_frame("loans").to_markdown(), "\n",
          "## loan_status\n", status.sort_values(ascending=False).astype(int).to_frame("loans").to_markdown(), "\n",
          "## term x loan_status\n", tbs.T.to_markdown(), "\n",
          "## Columns\n",
          pd.DataFrame({"dtype": pd.Series(dtypes), "missing_%": (nulls / n * 100).round(2)}).to_markdown(), "\n"]
    config.REPORTS.mkdir(exist_ok=True)
    (config.REPORTS / "data_profile.md").write_text("\n".join(md), encoding="utf-8")
    pd.concat(samples).to_csv(config.SAMPLE_CSV, index=False)
    print(f"Wrote {config.REPORTS / 'data_profile.md'} and {config.SAMPLE_CSV}")


if __name__ == "__main__":
    main()

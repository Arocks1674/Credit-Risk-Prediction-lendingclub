"""Turn raw LendingClub loans into a leakage-free modelling table.

Three decisions matter more than any model choice:

1. TARGET. Only loans with a final outcome: Fully Paid (0) vs Charged Off / Default (1).
   "Current" and "Late" loans have no outcome yet, so they are dropped.

2. MATURED LOANS ONLY. A loan issued a month before the data snapshot has had no time to
   default, so recent loans look safer than they are. We keep only loans whose full term
   ended before the snapshot (issue date + term <= latest payment date in the file).
   Without this, the default rate falls in later years for no real reason.

3. ORIGINATION FEATURES ONLY. An allow-list of fields known when the loan was approved.
   Anything recorded later (payments received, recoveries, last payment date, current
   balance...) is excluded: it describes the outcome rather than predicting it.
"""
import numpy as np
import pandas as pd

GOOD, BAD = 0, 1
OUTCOME = {"Fully Paid": GOOD, "Charged Off": BAD, "Default": BAD}

# Known at application time (LendingClub data dictionary). Kept as raw columns.
NUMERIC = ["loan_amnt", "int_rate", "installment", "annual_inc", "dti", "delinq_2yrs",
           "inq_last_6mths", "mths_since_last_delinq", "mths_since_last_record", "open_acc",
           "pub_rec", "revol_bal", "revol_util", "total_acc"]
CATEGORICAL = ["grade", "sub_grade", "home_ownership", "verification_status", "purpose",
               "addr_state", "initial_list_status"]
# Raw columns used only to build features, the target or the split.
HELPER = ["id", "issue_d", "term", "emp_length", "earliest_cr_line", "loan_status", "last_pymnt_d"]

# Recorded AFTER the loan was issued. Listed so tests can assert none of them survive.
LEAKAGE = ["funded_amnt_inv", "out_prncp", "out_prncp_inv", "total_pymnt", "total_pymnt_inv",
           "total_rec_prncp", "total_rec_int", "total_rec_late_fee", "recoveries",
           "collection_recovery_fee", "last_pymnt_d", "last_pymnt_amnt", "next_pymnt_d",
           "last_credit_pull_d", "pymnt_plan", "loan_status"]

# What actually happened to each loan, kept ONLY to score lending decisions after the fact
# ("if we had declined these loans, what return would the rest have made?"). Never features.
EVAL_ONLY = {"funded_amnt": "outcome_funded_amnt", "total_pymnt": "outcome_total_pymnt"}

RAW_COLUMNS = HELPER + NUMERIC + CATEGORICAL + list(EVAL_ONLY)

# Built in engineer(); all known at application.
ENGINEERED = ["term_months", "emp_years", "emp_unknown", "credit_history_months",
              "loan_to_income", "installment_to_income", "revol_bal_to_income",
              "never_delinquent", "no_public_record"]
FEATURES = NUMERIC + ENGINEERED + CATEGORICAL


def parse_month(s: pd.Series) -> pd.Series:
    """'Dec-2011' -> Timestamp('2011-12-01'). Unparseable values become NaT."""
    return pd.to_datetime(s, format="%b-%Y", errors="coerce")


def snapshot_date(last_pymnt_d: pd.Series) -> pd.Timestamp:
    """When the data was pulled: the latest payment date anywhere in the file."""
    return parse_month(last_pymnt_d).max()


def label(df: pd.DataFrame) -> pd.DataFrame:
    """Keep loans with a final outcome and add `default` (1 = charged off / default)."""
    out = df[df["loan_status"].isin(OUTCOME)].copy()
    out["default"] = out["loan_status"].map(OUTCOME).astype("int8")
    return out


def matured(df: pd.DataFrame, snapshot: pd.Timestamp) -> pd.DataFrame:
    """Keep loans whose full term ended on or before the snapshot."""
    issue = parse_month(df["issue_d"])
    months = df["term"].astype(str).str.extract(r"(\d+)")[0].astype(float)
    end = issue + pd.to_timedelta(months * 30.44, unit="D")
    return df[end <= snapshot + pd.Timedelta(days=1)]


def engineer(df: pd.DataFrame) -> pd.DataFrame:
    """Add application-time features. Never reads a column from LEAKAGE."""
    out = df.copy()
    out["issue_date"] = parse_month(out["issue_d"])
    out["term_months"] = out["term"].astype(str).str.extract(r"(\d+)")[0].astype(float)

    emp = out["emp_length"].astype(str).str.strip()
    years = emp.str.extract(r"(\d+)")[0].astype(float)
    years = years.where(~emp.str.startswith("<"), 0.0)          # "< 1 year" -> 0
    out["emp_unknown"] = years.isna().astype("int8")             # "n/a" or missing
    out["emp_years"] = years

    first_credit = parse_month(out["earliest_cr_line"])
    out["credit_history_months"] = ((out["issue_date"] - first_credit).dt.days / 30.44).round()

    inc = out["annual_inc"].where(out["annual_inc"] > 0)
    out["loan_to_income"] = out["loan_amnt"] / inc
    out["installment_to_income"] = out["installment"] * 12 / inc
    out["revol_bal_to_income"] = out["revol_bal"] / inc

    # "Months since last delinquency" is missing when there never was one: that is
    # information, not noise, so it gets its own flag (trees and the MLP both use it).
    out["never_delinquent"] = out["mths_since_last_delinq"].isna().astype("int8")
    out["no_public_record"] = out["mths_since_last_record"].isna().astype("int8")
    if out["revol_util"].dtype == object:                         # some exports use "45.2%"
        out["revol_util"] = pd.to_numeric(out["revol_util"].str.rstrip("%"), errors="coerce")
    if out["int_rate"].dtype == object:
        out["int_rate"] = pd.to_numeric(out["int_rate"].str.rstrip("%"), errors="coerce")
    for c in CATEGORICAL:
        out[c] = out[c].astype(str).str.strip().replace({"nan": "missing"})
    return out


def build(raw: pd.DataFrame, snapshot: pd.Timestamp | None = None) -> pd.DataFrame:
    """Raw rows -> one row per matured, finished loan: id, issue_date, FEATURES, default."""
    snap = snapshot if snapshot is not None else snapshot_date(raw["last_pymnt_d"])
    if raw["id"].isna().all():                     # the 2007-2018 Kaggle export has no ids
        raw = raw.assign(id=range(len(raw)))
    df = engineer(matured(label(raw), snap)).rename(columns=EVAL_ONLY)
    return df[["id", "issue_date"] + FEATURES + ["default"] + list(EVAL_ONLY.values())].reset_index(drop=True)


def out_of_time_split(df: pd.DataFrame, test_fraction: float = 0.2) -> tuple[pd.DataFrame, pd.DataFrame, pd.Timestamp]:
    """Train on older loans, test on the newest ones, cutting on a whole month.

    A random split would let the model learn from loans issued after the ones it is
    tested on; a lender never has that luxury.
    """
    months = df["issue_date"].sort_values()
    cutoff = months.iloc[int(len(months) * (1 - test_fraction))]
    train, test = df[df["issue_date"] < cutoff], df[df["issue_date"] >= cutoff]
    return train.reset_index(drop=True), test.reset_index(drop=True), cutoff


def read_raw(csv_path, chunksize: int = 200_000) -> pd.DataFrame:
    """Read only the columns we need, in chunks, so the 1.2 GB file fits in memory easily."""
    parts = []
    for chunk in pd.read_csv(csv_path, usecols=lambda c: c in RAW_COLUMNS, chunksize=chunksize,
                             low_memory=False):
        parts.append(chunk)
    return pd.concat(parts, ignore_index=True)


def summary(raw: pd.DataFrame, df: pd.DataFrame, snapshot: pd.Timestamp) -> pd.DataFrame:
    """Funnel from raw rows to the modelling table, for the report."""
    labelled = label(raw)
    return pd.DataFrame({
        "loans": [len(raw), len(labelled), len(df)],
        "default_rate_%": [np.nan, labelled["default"].mean() * 100, df["default"].mean() * 100],
    }, index=["all rows", "finished (paid / charged off)", f"matured by {snapshot:%b %Y}"])

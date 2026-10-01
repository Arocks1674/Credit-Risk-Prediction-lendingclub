"""Module 1: target, matured-loan filter, leakage, features, out-of-time split."""
import numpy as np
import pandas as pd
import pytest

from src.data import prepare as P


def raw_row(**kw):
    row = {"id": 1, "issue_d": "Jan-2010", "term": " 36 months", "emp_length": "10+ years",
           "earliest_cr_line": "Jan-2000", "loan_status": "Fully Paid", "last_pymnt_d": "Jan-2013",
           "loan_amnt": 10000.0, "int_rate": 12.5, "installment": 334.5, "annual_inc": 50000.0,
           "dti": 15.0, "delinq_2yrs": 0.0, "inq_last_6mths": 1.0, "mths_since_last_delinq": np.nan,
           "mths_since_last_record": np.nan, "open_acc": 8.0, "pub_rec": 0.0, "revol_bal": 5000.0,
           "revol_util": 40.0, "total_acc": 20.0, "grade": "B", "sub_grade": "B3",
           "home_ownership": "RENT", "verification_status": "Verified", "purpose": "credit_card",
           "addr_state": "CA", "initial_list_status": "f",
           "funded_amnt": 10000.0,
           # post-origination columns that must never reach the model
           "total_pymnt": 12000.0, "recoveries": 0.0, "out_prncp": 0.0}
    row.update(kw)
    return row


SNAP = pd.Timestamp("2016-01-01")


def test_only_finished_loans_are_labelled():
    raw = pd.DataFrame([raw_row(id=1, loan_status="Fully Paid"), raw_row(id=2, loan_status="Charged Off"),
                        raw_row(id=3, loan_status="Default"), raw_row(id=4, loan_status="Current"),
                        raw_row(id=5, loan_status="Late (31-120 days)"),
                        raw_row(id=6, loan_status="Does not meet the credit policy. Status:Fully Paid")])
    out = P.label(raw)
    assert dict(zip(out["id"], out["default"])) == {1: 0, 2: 1, 3: 1}


def test_loans_that_had_no_time_to_default_are_dropped():
    raw = pd.DataFrame([raw_row(id=1, issue_d="Dec-2012", term=" 36 months"),   # ends Dec 2015: keep
                        raw_row(id=2, issue_d="Mar-2013", term=" 36 months"),   # ends Mar 2016: drop
                        raw_row(id=3, issue_d="Jan-2011", term=" 60 months"),   # ends Jan 2016: keep
                        raw_row(id=4, issue_d="Jun-2011", term=" 60 months")])  # ends 2016: drop
    assert sorted(P.matured(raw, SNAP)["id"]) == [1, 3]


def test_snapshot_is_latest_payment_date():
    assert P.snapshot_date(pd.Series(["Mar-2015", "Jan-2016", None])) == SNAP


def test_no_post_origination_column_reaches_the_features():
    assert not set(P.LEAKAGE) & set(P.FEATURES)
    out = P.build(pd.DataFrame([raw_row()]), SNAP)
    assert not {"total_pymnt", "recoveries", "out_prncp", "loan_status", "last_pymnt_d"} & set(out.columns)
    assert list(out.columns) == ["id", "issue_date"] + P.FEATURES + ["default", "outcome_funded_amnt",
                                                                     "outcome_total_pymnt"]
    assert not any(c.startswith("outcome_") or c in P.EVAL_ONLY for c in P.FEATURES)


def test_engineered_features():
    raw = pd.DataFrame([raw_row(emp_length="< 1 year", mths_since_last_delinq=24.0),
                        raw_row(emp_length="n/a", annual_inc=0.0),
                        raw_row(emp_length="3 years", revol_util="45.5%", int_rate="13.1%")])
    out = P.engineer(raw)
    assert list(out["emp_years"].fillna(-1)) == [0, -1, 3]
    assert list(out["emp_unknown"]) == [0, 1, 0]
    assert list(out["never_delinquent"]) == [0, 1, 1]
    assert out["credit_history_months"].iloc[0] == 120             # Jan 2000 -> Jan 2010
    assert out["loan_to_income"].iloc[0] == pytest.approx(0.2)
    assert np.isnan(out["loan_to_income"].iloc[1])                  # zero income -> missing, not inf
    assert out["revol_util"].iloc[2] == pytest.approx(45.5)
    assert out["int_rate"].iloc[2] == pytest.approx(13.1)
    assert out["term_months"].iloc[0] == 36


def test_out_of_time_split_tests_on_newest_loans_and_never_splits_a_month():
    months = pd.date_range("2010-01-01", periods=10, freq="MS")
    df = pd.DataFrame({"issue_date": np.repeat(months, 10), "default": 0})
    train, test, cutoff = P.out_of_time_split(df, 0.2)
    assert train["issue_date"].max() < test["issue_date"].min()
    assert cutoff == pd.Timestamp("2010-09-01")
    assert len(test) == 20
    assert not set(train["issue_date"]) & set(test["issue_date"])


def test_missing_ids_are_replaced_by_row_number():
    raw = pd.DataFrame([raw_row(id=np.nan), raw_row(id=np.nan, loan_status="Charged Off")])
    assert list(P.build(raw, SNAP)["id"]) == [0, 1]

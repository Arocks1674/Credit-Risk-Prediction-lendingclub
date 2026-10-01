"""Module 2: preprocessing, metrics and the MLP on small synthetic data."""
import numpy as np
import pandas as pd
import pytest

from src.data.prepare import CATEGORICAL, FEATURES
from src.models.metrics import evaluate, ks_stat
from src.models.mlp import MLPClassifier
from src.models.preprocess import NUMERIC, dense_preprocessor, tree_frame


def frame(n=2000, seed=0):
    rng = np.random.default_rng(seed)
    df = pd.DataFrame({c: rng.normal(size=n) for c in NUMERIC})
    for c in CATEGORICAL:
        df[c] = rng.choice(["a", "b", "c"], n)
    df.loc[::10, "dti"] = np.nan
    risk = df["int_rate"] + 0.5 * (df["grade"] == "c")
    df["default"] = (rng.random(n) < 1 / (1 + np.exp(-(risk - 1.5)))).astype(int)
    return df


def test_metrics_on_perfect_and_random_scores():
    y = np.array([0, 0, 1, 1])
    perfect = evaluate(y, [0.1, 0.2, 0.8, 0.9])
    assert perfect["roc_auc"] == 1 and perfect["ks"] == 1 and perfect["gini"] == 1
    assert evaluate(y, [0.5] * 4)["roc_auc"] == 0.5
    assert ks_stat(y, [0.9, 0.8, 0.2, 0.1]) == 0


def test_dense_preprocessor_fills_gaps_and_ignores_unseen_categories():
    df = frame()
    pre = dense_preprocessor().fit(df)
    test = df.head(5).copy()
    test["purpose"] = "never_seen_in_training"
    X = pre.transform(test)
    assert np.isfinite(X).all()
    assert X.shape[0] == 5


def test_tree_frame_keeps_training_categories():
    df = frame()
    _, cats = tree_frame(df)
    new = df.head(3).copy()
    new["grade"] = "z"
    X, _ = tree_frame(new, cats)
    assert X["grade"].isna().all()                      # unseen level -> missing, not a new code
    assert list(X.columns) == FEATURES


def test_mlp_learns_a_simple_signal():
    df = frame(4000)
    pre = dense_preprocessor().fit(df)
    X, y = pre.transform(df), df["default"].to_numpy()
    m = MLPClassifier(hidden=(16,), batch_size=64, max_epochs=15, patience=5, verbose=False).fit(X[:3000], y[:3000], X[3000:], y[3000:])
    p = m.predict_proba(X[3000:])
    assert p.shape == (1000, 2) and np.allclose(p.sum(1), 1)
    assert evaluate(y[3000:], p[:, 1])["roc_auc"] > 0.7

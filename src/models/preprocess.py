"""Feature preprocessing, fitted on training data only.

Linear models and the neural net need numbers on similar scales with no gaps:
  numeric  -> median fill -> quantile transform to a normal shape
              (handles heavy tails like income 0 to 9M and DTI up to 999 without hand clipping)
  category -> one-hot (rare levels pooled, unseen levels ignored)
XGBoost handles missing values and categories itself, so it only needs pandas categories.
"""
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, QuantileTransformer

from src.data.prepare import CATEGORICAL, FEATURES

NUMERIC = [c for c in FEATURES if c not in CATEGORICAL]


def dense_preprocessor(numeric=NUMERIC, categorical=CATEGORICAL, seed: int = 42) -> ColumnTransformer:
    num = make_pipeline(SimpleImputer(strategy="median"),
                        QuantileTransformer(n_quantiles=1000, output_distribution="normal",
                                            subsample=200_000, random_state=seed))
    cat = OneHotEncoder(handle_unknown="infrequent_if_exist", min_frequency=50, sparse_output=False)
    parts = []
    if numeric:
        parts.append(("num", num, list(numeric)))
    if categorical:
        parts.append(("cat", cat, list(categorical)))
    return ColumnTransformer(parts, verbose_feature_names_out=False)


def tree_frame(df: pd.DataFrame, categories: dict | None = None) -> tuple[pd.DataFrame, dict]:
    """FEATURES as a frame with pandas categories fixed to the training levels."""
    X = df[FEATURES].copy()
    categories = categories or {c: sorted(X[c].astype(str).unique()) for c in CATEGORICAL}
    for c in CATEGORICAL:
        X[c] = pd.Categorical(X[c].astype(str), categories=categories[c])
    return X, categories

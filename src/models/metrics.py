"""Metrics for a probability-of-default model.

ROC-AUC  - ranking: does a defaulter get a higher score than a payer? (0.5 = random)
PR-AUC   - ranking focused on the minority class; compare with the default rate (its random baseline)
KS       - max gap between the score distributions of defaulters and payers (banks' standard)
Brier    - mean squared error of the probabilities: rewards calibration, not just ranking
mean PD  - average predicted probability; should match the actual default rate
"""
import numpy as np
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score, roc_curve


def ks_stat(y, p) -> float:
    fpr, tpr, _ = roc_curve(y, p)
    return float(np.max(tpr - fpr))


def evaluate(y, p) -> dict:
    y, p = np.asarray(y), np.clip(np.asarray(p, dtype=float), 1e-6, 1 - 1e-6)
    auc = roc_auc_score(y, p)
    return {"roc_auc": auc, "gini": 2 * auc - 1, "pr_auc": average_precision_score(y, p),
            "ks": ks_stat(y, p), "brier": brier_score_loss(y, p), "log_loss": log_loss(y, p),
            "mean_pd": p.mean(), "default_rate": y.mean()}

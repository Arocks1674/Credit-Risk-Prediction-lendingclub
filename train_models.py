"""Module 2: train and compare default models on an out-of-time test set.

Models (all predict the probability a loan defaults):
  1. LendingClub sub-grade only  - logistic regression on the lender's own grade: the bar to beat
  2. Logistic regression          - all application features
  3. XGBoost                      - gradient-boosted trees, depth/learning rate chosen on validation
  4. MLP (ANN)                    - PyTorch feed-forward net, epochs chosen on validation
  5. XGBoost without LC grade/rate - same model without sub_grade, grade and int_rate (LendingClub's
                                     own risk pricing): how much risk do our features find on their own?
Plus an imbalance experiment on logistic regression: no weighting vs class weights vs SMOTE.

Tuning never sees the test set: the newest 20% of TRAINING loans is the validation set.

    python train_models.py            # full data/loans.parquet (~5-15 min on a laptop CPU)
    python train_models.py --quick    # 100k-loan subsample, for a fast check
"""
import argparse
import json
import time

import joblib
import numpy as np
import pandas as pd
import xgboost as xgb
from imblearn.over_sampling import SMOTE
from sklearn.linear_model import LogisticRegression

import config
from src.data.prepare import out_of_time_split
from src.models.metrics import evaluate
from src.models.mlp import MLPClassifier
from src.models.preprocess import dense_preprocessor, tree_frame

MODELS = config.ROOT / "models"
XGB_GRID = [{"max_depth": d, "min_child_weight": w} for d in (3, 5, 7) for w in (1, 50)]


def logistic(**kw) -> LogisticRegression:
    return LogisticRegression(max_iter=2000, C=1.0, **kw)


def fit_xgb(Xtr, ytr, Xva, yva, params, n_estimators=3000):
    m = xgb.XGBClassifier(n_estimators=n_estimators, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8,
                          reg_lambda=1.0, tree_method="hist", enable_categorical=True, max_cat_to_onehot=1,
                          eval_metric="auc", early_stopping_rounds=100 if Xva is not None else None,
                          random_state=config.SEED, n_jobs=-1, **params)
    m.fit(Xtr, ytr, eval_set=[(Xva, yva)] if Xva is not None else None, verbose=False)
    return m


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--smote-rows", type=int, default=150_000, help="training rows used for the SMOTE run")
    args = ap.parse_args()
    t0 = time.time()

    df = pd.read_parquet(config.DATASET)
    if args.quick:
        df = df.sample(100_000, random_state=config.SEED)
    train, test, cutoff = out_of_time_split(df, config.TEST_FRACTION)
    fit, val, val_cut = out_of_time_split(train, 0.2)          # validation = newest 20% of train
    print(f"train {len(fit):,} | validation {len(val):,} (from {val_cut:%b %Y}) | "
          f"test {len(test):,} (from {cutoff:%b %Y})")
    y_fit, y_val, y_train, y_test = fit["default"], val["default"], train["default"], test["default"]

    results, preds, notes = {}, {"default": y_test.to_numpy()}, {}

    def record(name, model_train_p, model_test_p):
        results[name] = {"train_roc_auc": evaluate(y_train, model_train_p)["roc_auc"], **evaluate(y_test, model_test_p)}
        preds[name] = model_test_p
        print(f"{name:32s} test AUC {results[name]['roc_auc']:.4f}  train AUC {results[name]['train_roc_auc']:.4f}"
              f"  ({time.time() - t0:.0f}s)")

    # 1. The lender's own grade
    grade = dense_preprocessor(numeric=[], categorical=["sub_grade"]).fit(train)
    m = logistic().fit(grade.transform(train), y_train)
    record("LendingClub sub-grade only", m.predict_proba(grade.transform(train))[:, 1],
           m.predict_proba(grade.transform(test))[:, 1])

    # 2. Logistic regression, all features
    pre = dense_preprocessor(seed=config.SEED).fit(train)
    Xtr, Xte = pre.transform(train), pre.transform(test)
    lr = logistic().fit(Xtr, y_train)
    record("Logistic regression", lr.predict_proba(Xtr)[:, 1], lr.predict_proba(Xte)[:, 1])

    # Imbalance experiment (logistic regression): does reweighting or SMOTE help?
    lr_w = logistic(class_weight="balanced").fit(Xtr, y_train)
    record("Logistic + class weights", lr_w.predict_proba(Xtr)[:, 1], lr_w.predict_proba(Xte)[:, 1])
    rng = np.random.default_rng(config.SEED)
    idx = rng.choice(len(Xtr), min(args.smote_rows, len(Xtr)), replace=False)
    Xs, ys = SMOTE(random_state=config.SEED).fit_resample(Xtr[idx], y_train.to_numpy()[idx])
    lr_sub = logistic().fit(Xtr[idx], y_train.to_numpy()[idx])     # same rows, no SMOTE: a fair control
    record("Logistic, SMOTE subset, no SMOTE", lr_sub.predict_proba(Xtr)[:, 1], lr_sub.predict_proba(Xte)[:, 1])
    lr_s = logistic().fit(Xs, ys)
    record("Logistic + SMOTE", lr_s.predict_proba(Xtr)[:, 1], lr_s.predict_proba(Xte)[:, 1])
    notes["smote_rows"] = int(len(idx))

    # 3. XGBoost: pick depth / min_child_weight and the number of trees on validation
    Xf, cats = tree_frame(fit)
    Xv, _ = tree_frame(val, cats)
    grid = []
    for params in XGB_GRID:
        m = fit_xgb(Xf, y_fit, Xv, y_val, params)
        grid.append({**params, "val_auc": m.best_score, "trees": m.best_iteration + 1})
        print(f"  XGBoost {params} -> validation AUC {m.best_score:.4f} with {m.best_iteration + 1} trees")
    best = max(grid, key=lambda g: g["val_auc"])
    XT, cats = tree_frame(train)
    XS, _ = tree_frame(test, cats)
    n_trees = int(best["trees"] * 1.1)                          # a bit more data -> a few more trees
    xgbm = fit_xgb(XT, y_train, None, None, {k: best[k] for k in ("max_depth", "min_child_weight")}, n_trees)
    record("XGBoost", xgbm.predict_proba(XT)[:, 1], xgbm.predict_proba(XS)[:, 1])
    notes["xgb_grid"], notes["xgb_best"] = grid, {**best, "trees_refit": n_trees}

    # 5. Same XGBoost without LendingClub's own risk pricing
    lc_cols = ["grade", "sub_grade", "int_rate"]
    noLC = fit_xgb(XT.drop(columns=lc_cols), y_train, None, None,
                   {k: best[k] for k in ("max_depth", "min_child_weight")}, n_trees)
    record("XGBoost without LC grade/rate", noLC.predict_proba(XT.drop(columns=lc_cols))[:, 1],
           noLC.predict_proba(XS.drop(columns=lc_cols))[:, 1])

    # 4. MLP: choose epochs on validation, then retrain on all training loans for that many epochs
    pre_f = dense_preprocessor(seed=config.SEED).fit(fit)
    probe = MLPClassifier().fit(pre_f.transform(fit), y_fit, pre_f.transform(val), y_val)
    mlp = MLPClassifier(max_epochs=probe.best_epoch_, patience=10 ** 6, verbose=False)
    mlp.fit(Xtr, y_train, Xtr[:20_000], y_train[:20_000])
    record("MLP (ANN)", mlp.predict_proba(Xtr)[:, 1], mlp.predict_proba(Xte)[:, 1])
    notes["mlp_epochs"] = probe.best_epoch_

    # Save
    MODELS.mkdir(exist_ok=True)
    joblib.dump({"preprocessor": pre, "logistic": lr}, MODELS / "logistic.joblib")
    xgbm.save_model(MODELS / "xgboost.json")
    joblib.dump(cats, MODELS / "xgboost_categories.joblib")
    keep = ["id", "issue_date", "int_rate", "loan_amnt", "sub_grade"] + \
        [c for c in test.columns if c.startswith("outcome_")]
    pd.concat([test[keep].reset_index(drop=True), pd.DataFrame(preds)], axis=1) \
        .to_parquet(config.DATA_DIR / "test_predictions.parquet", index=False)

    table = pd.DataFrame(results).T
    cols = ["roc_auc", "train_roc_auc", "gini", "ks", "pr_auc", "brier", "log_loss", "mean_pd", "default_rate"]
    md = ["# Model comparison (out-of-time test set)\n",
          f"Train: {len(train):,} loans issued before {cutoff:%b %Y}. Test: {len(test):,} loans issued "
          f"{cutoff:%b %Y} to {test.issue_date.max():%b %Y}. Test default rate {y_test.mean():.1%}.\n",
          table[cols].to_markdown(floatfmt=".4f"), "\n",
          f"XGBoost chosen on validation: {json.dumps(notes['xgb_best'])}\n",
          f"MLP epochs chosen on validation: {notes['mlp_epochs']}\n",
          f"SMOTE was run on a {notes['smote_rows']:,}-loan random subset of training data (memory).\n",
          "## XGBoost validation grid\n", pd.DataFrame(grid).to_markdown(index=False, floatfmt=".4f"), "\n"]
    config.REPORTS.mkdir(exist_ok=True)
    name = "model_comparison_quick.md" if args.quick else "model_comparison.md"
    (config.REPORTS / name).write_text("\n".join(md), encoding="utf-8")
    print("\n" + table[cols].to_string(float_format=lambda x: f"{x:.4f}"))
    print(f"\nSaved reports/{name}, models/, data/test_predictions.parquet  ({time.time() - t0:.0f}s)")


if __name__ == "__main__":
    main()

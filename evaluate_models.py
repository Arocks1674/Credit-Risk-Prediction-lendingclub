"""Module 3: is the best model calibrated, what drives it, and is it worth using?

Reads data/test_predictions.parquet and models/ from train_models.py and writes:
  reports/evaluation.md
  reports/calibration.png       predicted vs actual default rate by score decile
  reports/approval_policy.png   realized return of the loans you approve, by approval rate
  reports/shap_importance.png   what drives the XGBoost score (mean |SHAP|)

    python evaluate_models.py
"""
import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xgboost as xgb

import config
from src.data.prepare import out_of_time_split
from src.models.preprocess import tree_frame

BLUE, ORANGE, MUTED, INK, GRID = "#2a78d6", "#eb6834", "#898781", "#2b2b2b", "#e6e6e6"
MODEL = "XGBoost"


def style(ax, title):
    ax.set_title(title, loc="left", fontsize=12, color=INK, pad=12)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(MUTED)
    ax.tick_params(colors=INK, labelsize=9)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def calibration(p: pd.DataFrame, model: str) -> pd.DataFrame:
    """Predicted vs actual default rate in 10 equal-size groups of the score."""
    g = pd.qcut(p[model].rank(method="first"), 10, labels=range(1, 11))
    return p.groupby(g, observed=True).agg(loans=("default", "size"), predicted_pd=(model, "mean"),
                                           actual_default_rate=("default", "mean"))


def approval_curve(p: pd.DataFrame, score: pd.Series, rates=np.arange(0.5, 1.001, 0.05)) -> pd.DataFrame:
    """Approve the lowest-risk share of loans; report what those loans actually did.

    realized return = total received / amount funded - 1 (over the loan's life, not annualized).
    """
    order = score.sort_values(kind="mergesort").index
    rows = []
    for r in rates:
        kept = p.loc[order[: int(round(len(order) * r))]]
        rows.append({"approved_%": r * 100, "default_rate_%": kept["default"].mean() * 100,
                     "realized_return_%": (kept["outcome_total_pymnt"].sum() / kept["outcome_funded_amnt"].sum() - 1) * 100})
    return pd.DataFrame(rows)


def grade_score(p: pd.DataFrame) -> pd.Series:
    """LendingClub's own ranking: sub-grade A1 (safest) ... G5 (riskiest)."""
    g = p["sub_grade"].astype(str)
    return g.str[0].map({k: i for i, k in enumerate("ABCDEFG")}) * 5 + g.str[1].astype(int)


def main() -> None:
    p = pd.read_parquet(config.DATA_DIR / "test_predictions.parquet")
    md = ["# Evaluation of the chosen model (out-of-time test set)\n",
          f"Model: **{MODEL}**. Test: {len(p):,} loans, default rate {p['default'].mean():.1%}.\n"]

    # 1. Calibration
    cal = calibration(p, MODEL)
    md += ["## Calibration: predicted vs actual default rate by score decile\n",
           (cal.assign(predicted_pd=cal.predicted_pd * 100, actual_default_rate=cal.actual_default_rate * 100)
            .rename(columns={"predicted_pd": "predicted_%", "actual_default_rate": "actual_%"})
            .to_markdown(floatfmt=".1f")), "\n",
           f"Riskiest 10% of loans default {cal.actual_default_rate.iloc[-1] / cal.actual_default_rate.iloc[0]:.1f}x "
           f"as often as the safest 10% ({cal.actual_default_rate.iloc[-1]:.1%} vs {cal.actual_default_rate.iloc[0]:.1%}).\n"]
    fig, ax = plt.subplots(figsize=(6.4, 4.6))
    lim = max(cal.predicted_pd.max(), cal.actual_default_rate.max()) * 100 * 1.08
    ax.plot([0, lim], [0, lim], color=MUTED, linewidth=1, linestyle="--")
    ax.plot(cal.predicted_pd * 100, cal.actual_default_rate * 100, color=BLUE, linewidth=2, marker="o", markersize=6)
    ax.text(lim * 0.62, lim * 0.52, "perfect calibration", color=MUTED, fontsize=9, ha="left", rotation=0)
    ax.set_xlabel("Predicted default probability (%)", color=INK, fontsize=10)
    ax.set_ylabel("Actual default rate (%)", color=INK, fontsize=10)
    ax.set_xlim(0, lim), ax.set_ylim(0, lim)
    style(ax, f"{MODEL}: predicted vs actual default rate, by score decile")
    fig.tight_layout(), fig.savefig(config.REPORTS / "calibration.png", dpi=150), plt.close(fig)

    # 2. Approval policy, judged on realized payments
    if "outcome_total_pymnt" in p:
        model_curve = approval_curve(p, p[MODEL])
        grade_curve = approval_curve(p, grade_score(p) + p[MODEL] * 1e-6)   # ties within a sub-grade broken arbitrarily
        both = model_curve.merge(grade_curve, on="approved_%", suffixes=(f" ({MODEL})", " (LC sub-grade)"))
        md += ["## Approval policy: approve the lowest-risk loans, judged on what they actually paid\n",
               "Realized return = total received / amount funded - 1, over each loan's life (not annualized).\n",
               both.to_markdown(index=False, floatfmt=".2f"), "\n"]
        fig, ax = plt.subplots(figsize=(6.4, 4.6))
        for curve, color, name in [(model_curve, BLUE, MODEL), (grade_curve, ORANGE, "LendingClub sub-grade")]:
            ax.plot(curve["approved_%"], curve["realized_return_%"], color=color, linewidth=2, label=name)
        ax.set_xlim(48, 101)
        ax.set_xlabel("Share of loans approved (%)", color=INK, fontsize=10)
        ax.set_ylabel("Realized return of approved loans (%)", color=INK, fontsize=10)
        ax.legend(frameon=False, fontsize=9, loc="lower left")
        style(ax, "Declining the riskiest loans: realized return of the rest")
        fig.tight_layout(), fig.savefig(config.REPORTS / "approval_policy.png", dpi=150), plt.close(fig)
    else:
        md += ["Approval policy skipped: re-run prepare_data.py and train_models.py to add realized payments.\n"]

    # 3. SHAP: what drives the score
    import shap
    booster = xgb.XGBClassifier()
    booster.load_model(config.ROOT / "models" / "xgboost.json")
    cats = joblib.load(config.ROOT / "models" / "xgboost_categories.joblib")
    df = pd.read_parquet(config.DATASET)
    _, test, _ = out_of_time_split(df, config.TEST_FRACTION)
    X, _ = tree_frame(test.sample(min(5000, len(test)), random_state=config.SEED), cats)
    sv = shap.TreeExplainer(booster).shap_values(X)
    imp = pd.Series(np.abs(sv).mean(0), index=X.columns).sort_values(ascending=False)
    top = imp.head(15)[::-1]
    md += ["## What drives the score (mean |SHAP|, 5,000 test loans)\n",
           imp.head(15).to_frame("mean_abs_shap").to_markdown(floatfmt=".4f"), "\n"]
    fig, ax = plt.subplots(figsize=(6.4, 5.2))
    ax.barh(top.index, top.values, color=BLUE, height=0.6)
    ax.set_xlabel("Mean |SHAP value| (log-odds of default)", color=INK, fontsize=10)
    style(ax, "What drives the XGBoost default score")
    ax.grid(axis="y", visible=False), ax.grid(axis="x", color=GRID, linewidth=0.8)
    fig.tight_layout(), fig.savefig(config.REPORTS / "shap_importance.png", dpi=150), plt.close(fig)

    (config.REPORTS / "evaluation.md").write_text("\n".join(md), encoding="utf-8")
    print("\n".join(md))
    print("Saved reports/evaluation.md and 3 charts")


if __name__ == "__main__":
    main()

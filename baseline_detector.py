#!/usr/bin/env python3
"""Supervised baseline detector for the Dynamic AI Firewall.

What it does
1. Trains a LightGBM classifier on the NATURAL class distribution
   (no oversampling, no class weights) and calibrates it with Platt scaling.
2. Chooses decision thresholds on VALIDATION data from an FPR budget
   (the test set is only used once, at the end).
3. Turns one probability into banded actions:
   ALLOW / ALLOW_AND_MONITOR / RATE_LIMIT / BLOCK
4. Reports recall at fixed FPR, PR-AUC, and precision at REALISTIC attack
   prevalence (your test set is ~20% attacks, real traffic is far lower).
5. Plots ROC/PR curves with your PPO model's operating point marked.
6. Optional leave-one-family-out test (a zero-day proxy).

Expected files in --data-dir (the ones your preprocessor already writes):
  X_train.npy  y_train_binary.npy  X_val.npy  y_val_binary.npy
  X_test.npy   y_test_binary.npy

Optional, for the zero-day test:
  y_train_multiclass.npy  y_val_multiclass.npy  y_test_multiclass.npy

Usage
  python baseline_detector.py --data-dir data/processed
  python baseline_detector.py --data-dir data/processed --seeds 0 1 2
  python baseline_detector.py --data-dir data/processed --lofo 4 10 2   # hold out families
  python baseline_detector.py --data-dir data/processed --max-train 300000   # quick run

NOTE: if your 70/15/15 split was random, results are optimistic (CICIDS2017
attacks come in contiguous lab sessions). Keep a day/file column in your
preprocessor and split by day for the final numbers.
"""
import argparse
import json
import os
import sys
import warnings
warnings.filterwarnings("ignore", message=".*eval_set.*")

import joblib
import lightgbm as lgb
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, precision_recall_curve, roc_auc_score, roc_curve
from sklearn.model_selection import train_test_split

# Your current best PPO model (firewall_focal.zip) for comparison.
PPO_RECALL, PPO_FPR = 0.9145, 0.1869

# FPR budgets that define the action bands (tune per customer).
BAND_FPR = {"block": 0.001, "rate_limit": 0.01, "monitor": 0.05}
PREVALENCES = [0.20, 0.01, 0.001, 0.0001]

# --------------------------------------------------------------------------- data
def load_split(data_dir, name, required=True):
    path = os.path.join(data_dir, name)
    if not os.path.exists(path):
        if required:
            sys.exit(f"Missing file: {path}")
        return None
    return np.load(path)


def load_all(data_dir):
    d = {}
    for s in ("train", "val", "test"):
        d[f"X_{s}"] = load_split(data_dir, f"X_{s}.npy").astype(np.float32)
        d[f"y_{s}"] = load_split(data_dir, f"y_{s}_binary.npy").astype(int)
        d[f"m_{s}"] = load_split(data_dir, f"y_{s}_multiclass.npy", required=False)
    return d


# ------------------------------------------------------------------------- model
class Detector:
    """LightGBM + Platt scaling. predict_proba returns a calibrated P(attack)."""

    def __init__(self, booster, platt):
        self.booster, self.platt = booster, platt

    def predict_proba(self, X):
        raw = np.clip(self.booster.predict_proba(X)[:, 1], 1e-6, 1 - 1e-6)
        z = np.log(raw / (1 - raw)).reshape(-1, 1)
        return self.platt.predict_proba(z)[:, 1]


def train_detector(X, y, X_val, y_val, seed):
    """Early-stop on half of validation, calibrate on the other half.
    Returns (detector, X_cal, y_cal); the calibration half is also used to pick
    thresholds, so it never touches the test set."""
    X_es, X_cal, y_es, y_cal = train_test_split(
        X_val, y_val, test_size=0.5, stratify=y_val, random_state=seed
    )
    clf = lgb.LGBMClassifier(
        n_estimators=800, learning_rate=0.05, num_leaves=63,
        subsample=0.8, subsample_freq=1, colsample_bytree=0.8,
        min_child_samples=50, random_state=seed, n_jobs=-1, verbose=-1,
    )
    clf.fit(X, y, eval_set=[(X_es, y_es)],
            callbacks=[lgb.early_stopping(30, verbose=False)])
    raw = np.clip(clf.predict_proba(X_cal)[:, 1], 1e-6, 1 - 1e-6)
    platt = LogisticRegression(C=1e6, max_iter=1000)
    platt.fit(np.log(raw / (1 - raw)).reshape(-1, 1), y_cal)
    return Detector(clf, platt), X_cal, y_cal


# -------------------------------------------------------------------- thresholds
def threshold_at_fpr(y, p, target_fpr):
    """Lowest score threshold whose FPR on (y, p) is <= target. Block if p >= t."""
    fpr, _, thr = roc_curve(y, p, drop_intermediate=False)
    ok = np.where(fpr <= target_fpr)[0]
    return float(thr[ok[-1]])


def band_thresholds(y_cal, p_cal):
    return {k: threshold_at_fpr(y_cal, p_cal, v) for k, v in BAND_FPR.items()}


def decide(p, t):
    """Map calibrated attack probability to an action. This is the function the
    decision node would call; add novelty score / asset criticality later."""
    if p >= t["block"]:
        return "BLOCK"
    if p >= t["rate_limit"]:
        return "RATE_LIMIT"
    if p >= t["monitor"]:
        return "ALLOW_AND_MONITOR"
    return "ALLOW"


# ----------------------------------------------------------------------- metrics
def rates(y, pred):
    tp = int(((pred == 1) & (y == 1)).sum())
    fp = int(((pred == 1) & (y == 0)).sum())
    tn = int(((pred == 0) & (y == 0)).sum())
    fn = int(((pred == 0) & (y == 1)).sum())
    recall = tp / max(tp + fn, 1)
    fpr = fp / max(fp + tn, 1)
    return dict(tp=tp, fp=fp, tn=tn, fn=fn, recall=recall, fpr=fpr)


def precision_at_prevalence(recall, fpr, prev):
    num = recall * prev
    den = num + fpr * (1 - prev)
    return num / den if den > 0 else float("nan")


def evaluate(y, p, thresholds):
    out = {"roc_auc": float(roc_auc_score(y, p)), "pr_auc": float(average_precision_score(y, p))}
    for name, t in thresholds.items():
        r = rates(y, (p >= t).astype(int))
        r["precision_at_prev"] = {
            str(pv): precision_at_prevalence(r["recall"], r["fpr"], pv) for pv in PREVALENCES
        }
        out[f"op_{name}"] = r

    # Banded actions: what happens to benign and attack traffic.
    actions = np.array([decide(x, thresholds) for x in p])
    bands = {}
    for a in ("ALLOW", "ALLOW_AND_MONITOR", "RATE_LIMIT", "BLOCK"):
        m = actions == a
        bands[a] = {
            "share_of_benign": float(m[y == 0].mean()),
            "share_of_attacks": float(m[y == 1].mean()),
        }
    out["bands"] = bands
    return out


def print_report(res, title):
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)
    print(f"ROC-AUC {res['roc_auc']:.4f} | PR-AUC {res['pr_auc']:.4f}")
    print("\nOperating points (thresholds chosen on validation data):")
    print(f"{'FPR budget':<12}{'recall':>8}{'FPR':>9}" + "".join(f"{'prec@'+str(pv):>13}" for pv in PREVALENCES))
    for name, budget in BAND_FPR.items():
        r = res[f"op_{name}"]
        row = f"{budget:<12.4f}{r['recall']:>8.4f}{r['fpr']:>9.4f}"
        row += "".join(f"{r['precision_at_prev'][str(pv)]:>13.4f}" for pv in PREVALENCES)
        print(row)
    ppo_row = f"{'PPO (focal)':<12}{PPO_RECALL:>8.4f}{PPO_FPR:>9.4f}"
    ppo_row += "".join(f"{precision_at_prevalence(PPO_RECALL, PPO_FPR, pv):>13.4f}" for pv in PREVALENCES)
    print(ppo_row)
    print("\nBanded actions (share of traffic of each class):")
    for a, v in res["bands"].items():
        print(f"  {a:<18} benign {v['share_of_benign']*100:6.2f}%   attacks {v['share_of_attacks']*100:6.2f}%")


# ------------------------------------------------------------------------ plots
def make_plots(y, p, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    fpr, tpr, _ = roc_curve(y, p)
    prec, rec, _ = precision_recall_curve(y, p)

    fig, ax = plt.subplots(1, 2, figsize=(12, 5))
    ax[0].plot(np.maximum(fpr, 1e-6), tpr, label="LightGBM baseline")
    ax[0].scatter([PPO_FPR], [PPO_RECALL], color="red", zorder=5, label="PPO focal (2.0x)")
    for name, b in BAND_FPR.items():
        ax[0].axvline(b, color="gray", ls=":", lw=0.8)
    ax[0].set_xscale("log")
    ax[0].set_xlim(1e-5, 1)
    ax[0].set_xlabel("False positive rate (log scale)")
    ax[0].set_ylabel("Recall")
    ax[0].set_title("ROC: is the baseline above the PPO point?")
    ax[0].legend()
    ax[0].grid(alpha=0.3)

    ax[1].plot(rec, prec, label="LightGBM baseline")
    ppo_prec = precision_at_prevalence(PPO_RECALL, PPO_FPR, y.mean())
    ax[1].scatter([PPO_RECALL], [ppo_prec], color="red", zorder=5, label="PPO focal (2.0x)")
    ax[1].set_xlabel("Recall")
    ax[1].set_ylabel("Precision (at test-set prevalence)")
    ax[1].set_title("Precision-recall")
    ax[1].legend()
    ax[1].grid(alpha=0.3)

    path = os.path.join(out_dir, "baseline_roc_pr.png")
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)
    print(f"\nPlot saved: {path}")


# --------------------------------------------------------------- zero-day proxy
def leave_one_family_out(d, family_ids, seed, max_train):
    """Train WITHOUT a family, then measure how much of it is caught at a 1% FPR
    budget. A low number means the supervised detector will not generalize to
    unseen attacks and you need the anomaly layer."""
    if d["m_train"] is None:
        print("\nLOFO skipped: y_*_multiclass.npy files not found.")
        return {}
    results = {}
    for fam in family_ids:
        tr = d["m_train"] != fam
        va = d["m_val"] != fam
        Xtr, ytr = d["X_train"][tr], d["y_train"][tr]
        if max_train and len(Xtr) > max_train:
            idx = np.random.RandomState(seed).choice(len(Xtr), max_train, replace=False)
            Xtr, ytr = Xtr[idx], ytr[idx]
        det, Xc, yc = train_detector(Xtr, ytr, d["X_val"][va], d["y_val"][va], seed)
        t = threshold_at_fpr(yc, det.predict_proba(Xc), BAND_FPR["rate_limit"])
        held = d["m_test"] == fam
        n_held = int(held.sum())
        recall = float((det.predict_proba(d["X_test"][held]) >= t).mean()) if n_held else float("nan")
        benign = d["y_test"] == 0
        fpr = float((det.predict_proba(d["X_test"][benign]) >= t).mean())
        results[int(fam)] = {"samples": n_held, "unseen_family_recall": recall, "benign_fpr": fpr}
        print(f"  family {fam:>2}: {n_held:>7} test samples | unseen-family recall {recall:.3f} | benign FPR {fpr:.4f}")
    return results


# -------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="data/processed")
    ap.add_argument("--out-dir", default="logs")
    ap.add_argument("--model-out", default="models/lgbm_detector.joblib")
    ap.add_argument("--seeds", type=int, nargs="+", default=[0])
    ap.add_argument("--max-train", type=int, default=0, help="subsample training rows for a quick run")
    ap.add_argument("--lofo", type=int, nargs="*", default=[], help="multiclass ids to hold out")
    args = ap.parse_args()

    d = load_all(args.data_dir)
    print(f"train {d['X_train'].shape} | val {d['X_val'].shape} | test {d['X_test'].shape}")
    print(f"attack share  train {d['y_train'].mean():.3f}  val {d['y_val'].mean():.3f}  test {d['y_test'].mean():.3f}")

    Xtr, ytr = d["X_train"], d["y_train"]
    if args.max_train and len(Xtr) > args.max_train:
        idx = np.random.RandomState(0).choice(len(Xtr), args.max_train, replace=False)
        Xtr, ytr = Xtr[idx], ytr[idx]

    all_runs, first = [], None
    for seed in args.seeds:
        det, Xc, yc = train_detector(Xtr, ytr, d["X_val"], d["y_val"], seed)
        thresholds = band_thresholds(yc, det.predict_proba(Xc))   # chosen on validation
        p_test = det.predict_proba(d["X_test"])                   # test used once
        res = evaluate(d["y_test"], p_test, thresholds)
        res["thresholds"] = thresholds
        all_runs.append(res)
        print_report(res, f"BASELINE (seed {seed})")
        if first is None:
            first = (det, thresholds, p_test)

    if len(all_runs) > 1:
        print("\nAcross seeds (mean +/- std of recall at each FPR budget):")
        for name, budget in BAND_FPR.items():
            vals = np.array([r[f"op_{name}"]["recall"] for r in all_runs])
            print(f"  FPR budget {budget:<7}: recall {vals.mean():.4f} +/- {vals.std():.4f}")

    make_plots(d["y_test"], first[2], args.out_dir)
    summary = {"runs": all_runs}

    if args.lofo:
        print("\nLeave-one-family-out (zero-day proxy, 1% FPR budget):")
        summary["lofo"] = leave_one_family_out(d, args.lofo, args.seeds[0], args.max_train)

    os.makedirs(args.out_dir, exist_ok=True)
    with open(os.path.join(args.out_dir, "baseline_results.json"), "w") as f:
        json.dump(summary, f, indent=2)

    os.makedirs(os.path.dirname(args.model_out) or ".", exist_ok=True)
    joblib.dump({"detector": first[0], "thresholds": first[1], "band_fpr": BAND_FPR}, args.model_out)
    print(f"Saved model + thresholds: {args.model_out}")
    print(f"Saved results: {os.path.join(args.out_dir, 'baseline_results.json')}")


if __name__ == "__main__":
    main()

"""BRD risk models on the SYNTHETIC beef feedlot dataset.

Usage: python brd_beef_tool.py beef_feedlot_SYNTHETIC.csv
Writes beef_brd_scores.csv, beef_model_metrics.csv, beef_brd_model.joblib

The outcome column is simulated, so these accuracy figures describe the simulation, not real BRD detection.
"""
import sys, joblib, numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import StratifiedGroupKFold, cross_val_predict
from sklearn.metrics import roc_auc_score, average_precision_score

Y = "BRD Pull Within 7 Days (simulated)"
NUM = ["Activity Change", "Activity Change by 2 Hours", "Raw Activity Data",
       "Rumination Deviation by 2 Hours", "Rumination Raw Data"]
STATIC = ["Pen", "Sex", "Breed Type", "Source", "Days on Feed", "Diet Phase", "Arrival Weight (kg)",
          "Est. Current Weight (kg)", "Daily Activity", "Daily Rumination", "Weekly Rumination Average"]

df = pd.read_csv(sys.argv[1], low_memory=False)
g = df.groupby("Animal ID")
info, y = g[STATIC].first(), g[Y].first()
X = info[["Days on Feed", "Arrival Weight (kg)", "Est. Current Weight (kg)", "Daily Activity",
          "Daily Rumination", "Weekly Rumination Average"]].copy()
for c in NUM:
    a = g[c].agg(["mean", "min", "max", "std"])
    a.columns = [f"{c}|{s}" for s in a.columns]
    X = X.join(a)
X["Rumination Deficit"] = X["Daily Rumination"] - X["Weekly Rumination Average"]
X["Rumination Ratio"] = X["Daily Rumination"] / X["Weekly Rumination Average"].replace(0, np.nan)
X["Low Rumination Intervals"] = g["Rumination Raw Data"].apply(lambda s: (s < 12).sum())
X["Activity vs Pen Median"] = X["Daily Activity"] - info.groupby("Pen")["Daily Activity"].transform("median")
X["Log Days on Feed"] = np.log(X["Days on Feed"])
X = X.join(pd.get_dummies(info[["Sex", "Breed Type", "Source", "Diet Phase"]]).astype(int))
print(f"{len(X)} animals, {y.sum()} simulated BRD pulls, {X.shape[1]} features")

imp = lambda: SimpleImputer(strategy="median")
models = {
    "Logistic Regression": make_pipeline(imp(), StandardScaler(), LogisticRegression(class_weight="balanced", max_iter=3000)),
    "Random Forest": make_pipeline(imp(), RandomForestClassifier(400, class_weight="balanced_subsample",
                                                                 min_samples_leaf=5, n_jobs=-1, random_state=0)),
    "Gradient Boosting": HistGradientBoostingClassifier(max_depth=3, learning_rate=0.05, max_iter=200,
                                                        class_weight="balanced", random_state=0),
}
cv = list(StratifiedGroupKFold(5, shuffle=True, random_state=0).split(X, y, info["Pen"]))   # whole pens held out
oof, rows = {}, []
for name, m in models.items():
    oof[name] = cross_val_predict(m, X, y, cv=cv, method="predict_proba")[:, 1]
    rows.append([name, round(roc_auc_score(y, oof[name]), 3), round(average_precision_score(y, oof[name]), 3)])
    print(rows[-1])
best = max(rows, key=lambda r: r[2])[0]
print("Selected:", best)
pd.DataFrame([r + ["Yes" if r[0] == best else "No"] for r in rows],
             columns=["Model", "CV AUROC", "CV PR-AUC", "Selected"]).to_csv("beef_model_metrics.csv", index=False)

p = oof[best]                                                    # out-of-fold: honest scores
out = info[["Pen", "Sex", "Breed Type", "Source", "Days on Feed", "Diet Phase", "Arrival Weight (kg)"]].copy()
out.insert(0, "Data Type", "SYNTHETIC")
out["BRD Probability"] = p.round(4)                              # relative, from class-balanced training
out["BRD Risk Score"] = (100 * pd.Series(p).rank(pct=True).to_numpy()).round(1)
out["Risk Tier"] = pd.cut(out["BRD Risk Score"], [0, 90, 98, 100], labels=["Low", "Moderate", "High"])
for c in ["Daily Rumination", "Weekly Rumination Average", "Rumination Deficit", "Daily Activity"]:
    out[c] = X[c]
out[Y] = y
out = out.sort_values("BRD Risk Score", ascending=False).reset_index()
out.to_csv("beef_brd_scores.csv", index=False)
joblib.dump({"model": models[best].fit(X, y), "cols": list(X.columns), "name": best}, "beef_brd_model.joblib")
print(pd.crosstab(out["Risk Tier"], out[Y]))
print(out.groupby("Diet Phase")["Risk Tier"].value_counts().unstack())

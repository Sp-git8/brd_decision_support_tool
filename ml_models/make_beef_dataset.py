"""Build a SYNTHETIC beef feedlot dataset from the dairy collar export.

Usage: python make_beef_dataset.py dairy_export.csv beef_feedlot_SYNTHETIC.csv

Real   : the 2-hourly activity and rumination patterns of each animal (rumination rescaled).
Removed: every dairy-only field (lactation status, heat detection, calving distress alerts).
Simulated: pen, days on feed, sex, breed type, source, weights, and the BRD outcome.
"""
import sys, numpy as np, pandas as pd

rng = np.random.default_rng(42)
src, out = sys.argv[1], sys.argv[2]
df = pd.read_csv(src, low_memory=False)

DROP = ["Lactation Status", "Last Heat By System, Peak", "Peak Activity Time", "Maximum Activity 36 Hours",
        "Last Distress Alert", "Last Distress Alert Date", "Last Distress Alert Time", "Last Distress Duration"]
df = df.drop(columns=DROP).rename(columns={"Cow Number": "Animal ID"})

# ---- one row per animal: simulated feedlot attributes -------------------------------------------
ids = df["Animal ID"].drop_duplicates().to_numpy()
n = len(ids)
a = pd.DataFrame({"Animal ID": rng.permutation(ids)})
a["Pen"] = np.arange(n) // 120 + 1                                   # ~120 head per pen
pens = pd.DataFrame({"Pen": a["Pen"].unique()})
pens["pen_dof"] = rng.integers(3, 176, len(pens))                     # pens arrive as cohorts
pens["Sex"] = rng.choice(["Steer", "Heifer"], len(pens), p=[0.65, 0.35])
pens["Source"] = rng.choice(["Sale barn", "Ranch direct (preconditioned)"], len(pens), p=[0.6, 0.4])
a = a.merge(pens, on="Pen")
a["Days on Feed"] = (a["pen_dof"] + rng.integers(-2, 3, n)).clip(1)
a["Breed Type"] = rng.choice(["British cross", "Continental cross", "Brahman-influenced", "Beef-on-dairy cross"],
                             n, p=[0.45, 0.25, 0.20, 0.10])
a["Arrival Weight (kg)"] = (rng.normal(265, 32, n) - 15 * (a["Sex"] == "Heifer")
                            + 20 * (a["Source"] != "Sale barn")).clip(170, 390).round(0)
adg = rng.normal(1.55, 0.2, n).clip(0.9, 2.1) - 0.1 * (a["Sex"] == "Heifer")   # kg/day
a["Est. Current Weight (kg)"] = (a["Arrival Weight (kg)"] + adg * a["Days on Feed"]).round(0)
a["Diet Phase"] = pd.cut(a["Days on Feed"], [0, 21, 45, 400], labels=["Receiving", "Step-up", "Finishing"]).astype(str)
# feedlot cattle ruminate less than dairy cows, and less again as roughage falls through the diet phases
a["rum_scale"] = a["Diet Phase"].map({"Receiving": 0.75, "Step-up": 0.65, "Finishing": 0.55}) * rng.normal(1, 0.04, n)

df = df.merge(a.drop(columns=["pen_dof"]), on="Animal ID")
for c in ["Daily Rumination", "Weekly Rumination Average", "Rumination Raw Data"]:
    df[c] = (df[c] * df["rum_scale"]).round(0)

# ---- simulated BRD outcome ----------------------------------------------------------------------
g = df.groupby("Animal ID")
f = g[["Daily Rumination", "Weekly Rumination Average", "Daily Activity"]].first()
f["low_rum"] = g["Rumination Raw Data"].apply(lambda s: (s < 12).sum())
a = a.set_index("Animal ID").join(f)
z = lambda s: ((s - s.mean()) / s.std()).fillna(0).clip(-4, 4)
rum_drop = z(1 - a["Daily Rumination"] / a["Weekly Rumination Average"].replace(0, np.nan))
act_drop = z(-(a["Daily Activity"] - a.groupby("Pen")["Daily Activity"].transform("median")))
dof_risk = np.exp(-(np.log(a["Days on Feed"]) - np.log(14)) ** 2 / (2 * 0.7 ** 2))   # peaks ~2 weeks after arrival
logit = (1.8 * dof_risk + 0.6 * (a["Source"] == "Sale barn") - 0.35 * z(a["Arrival Weight (kg)"])
         + 1.3 * rum_drop + 0.5 * act_drop + 0.25 * z(a["low_rum"]) + rng.normal(0, 0.8, n))
lo, hi = -12.0, 4.0
for _ in range(40):                                   # choose the intercept that gives ~3% of animals
    b0 = (lo + hi) / 2
    lo, hi = (b0, hi) if (1 / (1 + np.exp(-(logit + b0)))).mean() < 0.03 else (lo, b0)
a["BRD Pull Within 7 Days (simulated)"] = (rng.random(n) < 1 / (1 + np.exp(-(logit + b0)))).astype(int)

df = df.merge(a[["BRD Pull Within 7 Days (simulated)"]], left_on="Animal ID", right_index=True).drop(columns=["rum_scale"])
df.insert(0, "Data Type", "SYNTHETIC")
front = ["Data Type", "Animal ID", "Pen", "Sex", "Breed Type", "Source", "Days on Feed", "Diet Phase",
         "Arrival Weight (kg)", "Est. Current Weight (kg)", "Date", "Time"]
df = df[front + [c for c in df.columns if c not in front]]
df.to_csv(out, index=False)

s = a.reset_index()
y = "BRD Pull Within 7 Days (simulated)"
print(df.shape, list(df.columns))
print("animals", n, "pens", s["Pen"].nunique(), "BRD", s[y].sum(), f"{100 * s[y].mean():.1f}%")
print(s.groupby("Diet Phase").agg(n=("Pen", "size"), brd_pct=(y, lambda v: round(100 * v.mean(), 1)),
                                  rum=("Daily Rumination", "median"), wt=("Est. Current Weight (kg)", "median")))
print(s.groupby("Source")[y].mean().mul(100).round(1).to_dict(), s.groupby(y)["Daily Rumination"].median().to_dict())

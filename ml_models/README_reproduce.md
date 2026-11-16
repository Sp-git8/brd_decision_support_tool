# Reproducing the individual-animal data and ML comparison

The animal-level data is SYNTHETIC. Rumination and activity patterns come from a freely available dairy collar export; everything else, including the BRD outcome, is simulated. Accuracy figures below describe the simulation, not real BRD detection.

## 1. Setup

    pip install pandas numpy scikit-learn joblib

Put the dairy export (`Hackathon_SCRRAW_11.14.26.csv`) in the same folder as the two scripts.

## 2. Create the beef dataset

    python make_beef_dataset.py Hackathon_SCRRAW_11.14.26.csv beef_feedlot_SYNTHETIC.csv

What it does (seed 42, so the output is repeatable):

1. Reads the dairy export and drops dairy-only fields: lactation status, heat detection, peak activity time, 36-hour maximum activity, and the distress-alert fields.
2. Keeps each animal's two-hourly activity and rumination readings. Rumination is rescaled to feedlot levels by diet phase (receiving 0.75, step-up 0.65, finishing 0.55, with 4% noise).
3. Simulates feedlot attributes: about 120 head per pen (73 pens); a days-on-feed cohort per pen (3 to 175); sex (65% steer); source (60% sale barn); breed type; arrival weight (normal, adjusted for heifers and ranch-direct cattle); estimated current weight from simulated daily gain; diet phase from days on feed.
4. Simulates the outcome `BRD Pull Within 7 Days (simulated)` by Monte Carlo draw. Each animal gets a risk score:
   - 1.8 x a days-on-feed term that peaks about 14 days after arrival
   - + 0.6 if sale barn
   - - 0.35 x standardised arrival weight
   - + 1.3 x rumination drop (daily against the animal's weekly average)
   - + 0.5 x activity drop (against the pen median)
   - + 0.25 x standardised count of low-rumination intervals
   - + random noise, N(0, 0.8)

   An intercept is tuned so about 3% of animals are cases, then each animal's case flag is a random (Bernoulli) draw from the resulting probability.

Expected printout: 8,693 animals, 73 pens, 291 simulated cases (3.3%).

## 3. Run the ML models

    python brd_beef_tool.py beef_feedlot_SYNTHETIC.csv

Writes `beef_model_metrics.csv`, `beef_brd_scores.csv` and `beef_brd_model.joblib`.

### Features (one row per animal)
- Daily rumination, weekly rumination average, daily activity, days on feed, arrival weight, estimated current weight.
- Mean, minimum, maximum and standard deviation across the animal's two-hourly readings for five sensor measures: activity change, activity change by 2 hours, raw activity, rumination deviation by 2 hours, raw rumination.
- Engineered: rumination deficit and ratio (daily against weekly), low-rumination intervals, activity against pen median, log days on feed.
- One-hot: sex, breed type, source, diet phase.

### Models compared
| Model | Settings |
| --- | --- |
| Logistic regression | median imputation, standardised, class_weight balanced |
| Random forest | 400 trees, class_weight balanced_subsample, min leaf 5 |
| Gradient boosting (HistGradientBoosting) | depth 3, learning rate 0.05, 200 iterations, class_weight balanced |

### Evaluation
5-fold StratifiedGroupKFold with whole pens held out, so no pen appears in both training and test folds. Scores are out-of-fold predictions. The model with the highest PR-AUC is selected, because only about 3% of animals are cases.

### Results
| Model | CV AUROC | CV PR-AUC | Selected |
| --- | --- | --- | --- |
| Logistic regression | 0.814 | 0.315 | Yes |
| Random forest | 0.816 | 0.289 | No |
| Gradient boosting | 0.797 | 0.259 | No |

Random forest has the highest AUROC by a hair (0.816 against 0.814), but logistic regression ranks the rare cases better (PR-AUC), and it is simpler to explain.

### Scores and tiers
- `BRD Probability` is from class-balanced training, so it is a relative ranking value, not a calibrated probability.
- `BRD Risk Score` is the out-of-fold probability's percentile rank within the herd (0 to 100).
- Tiers: High = top 2% (score above 98), Moderate = next 8% (above 90), Low = the rest.
- Result: High 170 animals (82 simulated cases), Moderate 695 (71), Low 7,824 (138).

## 4. Read the results with care
The outcome formula uses the same rumination and activity signals the models learn from, so the models partly rediscover the formula. These numbers show that the pipeline works end to end. Real accuracy needs outcome-labelled treatment records, with a plain rumination threshold and pen-rider pulls as the comparison.

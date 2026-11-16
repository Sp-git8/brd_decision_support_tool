# BRD Decision Lab

**Live dashboard:** https://brddecisionsupporttool.streamlit.app

Decision support for bovine respiratory disease (BRD) in feedlot cattle during the first 45 days after arrival.
The site combines two complementary tools:

| | Pen-level risk model | Animal-level screening |
|---|---|---|
| View | Macro: the whole lot | Individual: each animal |
| When | On arrival | Daily |
| Question | How risky is this lot, and which management option fits? | Which cattle should we examine today? |
| Inputs | Lot records, weather outlook | Collar sensor data, feedlot records |
| Method | System dynamics + Monte Carlo | Machine learning (logistic regression) |
| Output | Risk curve, option comparison, decision summary | Ranked check list, risk tiers |

## Run locally
```
pip install -r requirements.txt
streamlit run app.py
```
Opens at http://localhost:8501. No paid services are required. The live site redeploys automatically on every
push to `main`.

## Repository layout
```
app.py                      Entry point, theme, top navigation
brd_model.py                Pen-level model in Python (used by the dashboard)
brd_risk.mdl                Pen-level model in Vensim (same equations as brd_model.py)
pages/
  home.py                   Landing page
  risk_model.py             Pen-level risk model dashboard
  animal_screening.py       Animal-level screening dashboard
  about.py                  Methods and data for both models
ml_models/                  Data generation and model training for animal-level screening
                            (see ml_models/README_reproduce.md)
data/
  beef_brd_scores.csv       Animal-level scores and tiers (output of ml_models)
  beef_model_metrics.csv    Cross-validation metrics (output of ml_models)
.streamlit/config.toml      Theme
requirements.txt            Dashboard dependencies
```

## Pen-level risk model
A system dynamics model of one arriving lot over 45 days, with four stocks:
**Stress** (driven by transport, marketing channel, commingling, weaning, crowding and weather),
**Immunity** (built by vaccination and nutrition, suppressed by stress), **Nutrition deficit** (feed intake
below target), and **Cumulative hazard** (daily BRD risk with a ~7-day onset delay).

The current approach (pull and treat) is compared against vaccination, metaphylaxis and both, on cases,
deaths, antibiotic doses, cost and peak daily pulls, with checks against crew and chute capacity.
Uncertainty comes from 200 Monte Carlo runs per option, with parameters varied about ±15%. Unknown inputs are
sampled and flagged as low confidence.

**Data:** no dataset is used. Every scenario is a user input, the model structure follows published BRD risk
factors, and the parameter values are placeholders pending calibration.

## Animal-level screening
Scores every animal daily (0–100) from rumination and activity readings plus feedlot records. Three models
were compared with 5-fold cross-validation that holds out whole pens:

| Model | AUROC | PR-AUC | Selected |
|---|---|---|---|
| Logistic regression | 0.814 | 0.315 | Yes |
| Random forest | 0.816 | 0.289 | No |
| Gradient boosting | 0.797 | 0.259 | No |

Logistic regression was selected on PR-AUC, because cases are rare (~3%), and it is the simplest to explain.
Tiers: top 2% High, next 8% Moderate, the rest Low. In the demo data, High-tier cattle had a 48% simulated
BRD rate, against 1.8% for the Low tier.

**Data:** synthetic. Sensor patterns come from a public dairy collar export, rescaled to feedlot levels.
Pens, days on feed, weights, source and the BRD outcome are simulated (8,693 animals, 73 pens, 291 cases,
seed 42). The simulated outcome uses the same sensor signals the models learn from, so these figures show the
pipeline working end to end, not real-world accuracy. Full steps are in `ml_code/README_reproduce.md`.

## Data files
| File | Contents |
|---|---|
| `data/beef_brd_scores.csv` | One row per animal: ID, pen, days on feed, source, risk score, BRD probability (relative, not calibrated), rumination, weekly average, deficit, activity, simulated BRD pull |
| `data/beef_model_metrics.csv` | One row per model: AUROC, PR-AUC, selected |

Pen-level inputs, units and ranges are documented in `brd_model.py` and on the dashboard's Methods page.

## Limitations
- Pen-level parameters are uncalibrated, so outputs are directional.
- Animal-level accuracy is measured on simulated outcomes, not real treatment records.
- A rumination drop is not specific to BRD: other illness, lameness and stress look similar.

## Future work
- **Calibration:** fit pen-level parameters to published studies, and retrain the screening model on real
  treatment records.
- **Pen-rider reports:** let cowboys flag a sick-looking animal, which raises its risk score (it can never
  lower one).
- **Weigh-in temperatures:** add rectal temperature as a screening input.
- **Own data:** upload a yard's sensor export for scoring.

## Veterinary review
Both tools are planning and screening aids. Any metaphylaxis or treatment decision must be reviewed and
authorized by the herd veterinarian.

## References
- Cernicchiaro et al. (2012). *Journal of Animal Science* 90(6):1929–1939.
- Marchesini et al. (2018). *The Veterinary Journal* 231:41–47.

## External resources and AI use
Streamlit, Plotly, pandas, NumPy and scikit-learn; Vensim PLE for the pen-level model. Claude (Anthropic)
assisted with model structure, code and documentation. The team reviewed and verified all claims, citations
and results.

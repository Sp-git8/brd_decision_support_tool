"""BRD risk system dynamics model (lot level, first 45 days on feed).

Mirrors the Vensim stock-and-flow diagram:
  Stocks: Stress, Immunity, Nutrition deficit, Cumulative hazard
  Euler integration, dt = 0.25 day.

Website entry points:
  simulate(inputs)        -> one deterministic run (time series + summary)
  monte_carlo(inputs, n)  -> uncertainty bands (parameters + missing inputs sampled)
  compare(inputs)         -> current approach vs. alternatives, side by side

All numeric parameters are placeholders to be calibrated against literature.
"""
import numpy as np

# Calibration parameters (the only thing Monte Carlo varies). Placeholders.
PARAMS = {
    "stress_recovery_time": 5.0,     # days
    "transport_weight": 0.05,        # stress per hour in transit
    "immunity_build_rate": 0.05,     # per day
    "stress_suppression": 0.02,      # per stress unit per day
    "vaccine_strength": 0.2,         # immunity added over the delay
    "vaccine_delay": 12.0,           # days
    "deficit_recovery_time": 4.0,    # days
    "baseline_hazard": 0.0075,        # per day
    "stress_weight": 0.3,
    "immunity_weight": 2.0,
    "deficit_weight": 0.5,
    "metaphylaxis_efficacy": 0.5,
    "metaphylaxis_duration": 7.0,    # days
    "onset_delay": 7.0,              # days from risk exposure to clinical BRD
}

# Dropdown options -> model values
CHANNEL = {"sale_barn": (1.5, 0.15), "contract": (0.7, 0.0), "ranch_direct": (0.0, 0.0)}   # (stress, immunity penalty)
SOURCES = {"1": (0.0, 1.0), "2-5": (0.8, 1.3), "6+": (1.5, 1.6)}                          # (stress, exposure effect)
WEANING = {"fresh": (2.0, 0.2), "short": (1.0, 0.1), "preconditioned": (0.0, 0.0)}        # (stress, immunity penalty)

# What a blank field is sampled from in Monte Carlo (rough priors for Panhandle/KS yards)
PRIORS = {
    "channel": (["sale_barn", "contract", "ranch_direct"], [0.6, 0.25, 0.15]),
    "sources": (["1", "2-5", "6+"], [0.2, 0.3, 0.5]),
    "weaning": (["fresh", "short", "preconditioned"], [0.5, 0.3, 0.2]),
}

DAYS, DT = 45, 0.25


def _series(x, n):
    """Accept a scalar or a daily list (length >= 46) and return a daily array."""
    if x is None:
        return np.zeros(n)
    arr = np.atleast_1d(np.asarray(x, dtype=float))
    return np.full(n, arr[0]) if arr.size == 1 else np.resize(arr, n)


def simulate(inputs, params=None):
    """
    inputs (all from the website form):
      channel: 'sale_barn' | 'contract' | 'ranch_direct'
      sources: '1' | '2-5' | '6+'
      weaning: 'fresh' | 'short' | 'preconditioned'
      transport_hours: float
      arrival_weight: lb
      space_per_head: ft^2
      vaccinated: bool
      use_metaphylaxis: bool
      head_count: int
      temp_swing: daily high-low (F), scalar or list of 46 days
      wind: mph, scalar or list
      moisture: precipitation (in), scalar or list
    """
    p = {**PARAMS, **(params or {})}
    ch_stress, ch_imm = CHANNEL[inputs["channel"]]
    src_stress, exposure_effect = SOURCES[inputs["sources"]]
    wn_stress, wn_imm = WEANING[inputs["weaning"]]
    weight = inputs["arrival_weight"]

    temp = _series(inputs.get("temp_swing", 20), DAYS + 1)
    wind = _series(inputs.get("wind", 10), DAYS + 1)
    moist = _series(inputs.get("moisture", 0), DAYS + 1)

    arrival_stress = p["transport_weight"] * inputs["transport_hours"] + ch_stress + src_stress + wn_stress
    crowding_effect = (150 / inputs["space_per_head"]) ** 0.5
    target_intake = 0.02 * weight                                   # lb DM/day (2% of body weight)

    # Initial stock values
    S = 0.0
    I = float(np.clip(0.8 - ch_imm - wn_imm + 0.05 * (weight - 550) / 100, 0.1, 1.0))
    N = 0.005 * max(0.0, 550 - weight)                            # days-equivalent of missed intake
    H = 0.0
    vax = [0.0, 0.0, 0.0]                                           # DELAY3 stages (vaccine)
    onset = [0.0, 0.0, 0.0]                                         # DELAY3 stages (exposure -> clinical)

    steps = int(DAYS / DT)
    out = {k: np.zeros(steps + 1) for k in ("day", "stress", "immunity", "nutrition_deficit", "hazard", "brd_probability")}

    for k in range(steps + 1):
        t = k * DT
        d = int(t)
        P = 1 - np.exp(-H)

        # Auxiliaries
        weather_stress = 0.05 * max(0, temp[d] - 30) + 0.03 * max(0, wind[d] - 20) + 0.5 * (moist[d] > 0.1)
        stress_gain = crowding_effect * (arrival_stress * (t < 1) + weather_stress)
        stress_recovery = S / p["stress_recovery_time"]

        vax_in = p["vaccine_strength"] * inputs["vaccinated"] * (t < 1)
        stage_time = p["vaccine_delay"] / 3
        vaccination_boost = vax[2] / stage_time
        immunity_gain = vaccination_boost + p["immunity_build_rate"] * (1 - I) * (1 - min(N / 3, 1))
        immunity_loss = p["stress_suppression"] * S * I

        actual_intake = target_intake * (1 - 0.4 * S / (S + 3)) * (1 - 0.5 * P)
        deficit_growth = max(0.0, target_intake - actual_intake) / target_intake   # fraction of target missed per day
        deficit_recovery = N / p["deficit_recovery_time"]

        metaphylaxis_active = inputs["use_metaphylaxis"] * (t < p["metaphylaxis_duration"])
        exposure_hazard = (p["baseline_hazard"] * exposure_effect
                        * np.exp(p["stress_weight"] * S - p["immunity_weight"] * I + p["deficit_weight"] * N)
                        * (1 - p["metaphylaxis_efficacy"] * metaphylaxis_active))
        onset_time = p["onset_delay"] / 3
        daily_hazard = onset[2] / onset_time                        # Vensim: DELAY3(exposure hazard, onset delay)

        for key, val in zip(out, (t, S, I, N, daily_hazard, P)):
            out[key][k] = val

        # Integrate stocks
        S += DT * (stress_gain - stress_recovery)
        I += DT * (immunity_gain - immunity_loss)
        N += DT * (deficit_growth - deficit_recovery)
        H += DT * daily_hazard
        vax = [vax[0] + DT * (vax_in - vax[0] / stage_time),
               vax[1] + DT * (vax[0] / stage_time - vax[1] / stage_time),
               vax[2] + DT * (vax[1] / stage_time - vaccination_boost)]
        onset = [onset[0] + DT * (exposure_hazard - onset[0] / onset_time),
                 onset[1] + DT * (onset[0] / onset_time - onset[1] / onset_time),
                 onset[2] + DT * (onset[1] / onset_time - daily_hazard)]

    summary = outputs(out["brd_probability"][-1], inputs)
    summary["peak_risk_day"] = float(out["day"][np.argmax(out["hazard"])])
    return {**{k: v.tolist() for k, v in out.items()}, "summary": summary}


def outputs(brd_probability, inputs, dose_cost=25, treatment_cost=140, death_loss=1500):
    """Output layer: Head count -> cases, doses, deaths, cost."""
    head = inputs["head_count"]
    cases = head * brd_probability
    doses = head * inputs["use_metaphylaxis"] + cases
    deaths = cases * 0.07
    return {
        "brd_probability": float(brd_probability),
        "expected_cases": float(cases),
        "antibiotic_doses": float(doses),
        "expected_deaths": float(deaths),
        "total_cost": float(dose_cost * doses + treatment_cost * cases + death_loss * deaths),
    }


def monte_carlo(inputs, n=300, spread=0.15, seed=0):
    """Sample parameters (+/- spread, lognormal) and any blank categorical inputs."""
    rng = np.random.default_rng(seed)
    missing = [k for k in PRIORS if not inputs.get(k)]
    curves, summaries = [], []
    for _ in range(n):
        run_inputs = dict(inputs)
        for k in missing:
            options, weights = PRIORS[k]
            run_inputs[k] = rng.choice(options, p=weights)
        params = {k: v * rng.lognormal(0, spread) for k, v in PARAMS.items()}
        params["metaphylaxis_efficacy"] = min(params["metaphylaxis_efficacy"], 0.9)
        r = simulate(run_inputs, params)
        curves.append(r["brd_probability"])
        summaries.append(r["summary"])

    curves = np.array(curves)
    keys = summaries[0].keys()
    band = {k: [float(np.percentile([s[k] for s in summaries], q)) for q in (5, 50, 95)] for k in keys}
    lo, hi = band["brd_probability"][0], band["brd_probability"][2]
    return {
        "day": simulate(_fill(inputs))["day"],
        "brd_probability_p5": np.percentile(curves, 5, axis=0).tolist(),
        "brd_probability_p50": np.percentile(curves, 50, axis=0).tolist(),
        "brd_probability_p95": np.percentile(curves, 95, axis=0).tolist(),
        "summary_p5_p50_p95": band,
        "missing_inputs": missing,
        "low_confidence": bool(missing) or (hi - lo) > 0.25,
    }


def compare(inputs, n=300):
    """Current approach (pull and treat) vs. alternatives on the same lot."""
    options = {
        "Current: pull and treat": {"use_metaphylaxis": False},
        "Vaccinate on arrival": {"vaccinated": True, "use_metaphylaxis": False},
        "Metaphylaxis": {"use_metaphylaxis": True},
        "Vaccinate + metaphylaxis": {"vaccinated": True, "use_metaphylaxis": True},
    }
    return {name: monte_carlo({**inputs, **change}, n) for name, change in options.items()}


def _fill(inputs):
    """Most likely value for blank fields, for a single deterministic run."""
    return {**inputs, **{k: PRIORS[k][0][int(np.argmax(PRIORS[k][1]))] for k in PRIORS if not inputs.get(k)}}


if __name__ == "__main__":
    lot = {
        "channel": "sale_barn", "sources": "6+", "weaning": "fresh",
        "transport_hours": 12, "arrival_weight": 500, "space_per_head": 150,
        "vaccinated": False, "use_metaphylaxis": False, "head_count": 200,
        "temp_swing": 30, "wind": 12, "moisture": 0,
    }
    for name, res in compare(lot, n=200).items():
        b = res["summary_p5_p50_p95"]
        print(f"{name:28s} BRD {b['brd_probability'][1]:.1%} "
              f"({b['brd_probability'][0]:.1%}-{b['brd_probability'][2]:.1%})  "
              f"doses {b['antibiotic_doses'][1]:.0f}  cost ${b['total_cost'][1]:,.0f}")
    print()
    for lot2 in ({**lot, "channel": "ranch_direct", "sources": "1", "weaning": "preconditioned", "arrival_weight": 650},
                 {**lot, "sources": None, "weaning": None}):
        r = monte_carlo(lot2, 200)
        print(r["summary_p5_p50_p95"]["brd_probability"], "missing:", r["missing_inputs"], "low conf:", r["low_confidence"])

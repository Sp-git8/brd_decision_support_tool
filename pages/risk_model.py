"""Pen-level risk model page (system dynamics)."""
import json
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import brd_model as m

CHANNEL_LABELS = {"ranch_direct": "Ranch direct", "contract": "Video / contract", "sale_barn": "Sale barn", "unknown": "Unknown"}
SOURCE_LABELS = {"1": "1 source", "2-5": "2-5 sources", "6+": "6+ sources", "unknown": "Unknown"}
WEANING_LABELS = {"preconditioned": "Preconditioned (45+ d)", "short": "Short (7-44 d)", "fresh": "Fresh (<7 d)", "unknown": "Unknown"}
COLORS = {"Current: pull and treat": "#8A8F86", "Vaccinate on arrival": "#2E8B62",
          "Metaphylaxis": "#D0643A", "Vaccinate + metaphylaxis": "#5A4FB0"}
CHART = dict(height=360, margin=dict(l=10, r=10, t=40, b=10), legend=dict(orientation="h", y=-0.22),
             plot_bgcolor="#FFFFFF", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#1F2A24"))

BASELINE = {"channel": "sale_barn", "sources": "2-5", "weaning": "short", "transport": 10, "weight": 550,
            "vaccinated": False, "head": 200, "space": 150, "swing": 22, "wind": 12, "front": True, "front_day": 8}
PRESETS = {
    "Typical lot (baseline)": {},
    "High-risk sale barn calves": {"channel": "sale_barn", "sources": "6+", "weaning": "fresh", "transport": 18,
                                   "weight": 450, "space": 130},
    "Preconditioned yearlings": {"channel": "ranch_direct", "sources": "1", "weaning": "preconditioned",
                                 "transport": 5, "weight": 700, "vaccinated": True, "space": 200},
    "Unknown history": {"channel": "unknown", "sources": "unknown", "weaning": "unknown"},
}

for k, v in BASELINE.items():
    st.session_state.setdefault(k, v)


def apply_preset():
    for k, v in {**BASELINE, **PRESETS[st.session_state.preset]}.items():
        st.session_state[k] = v


@st.cache_data(show_spinner=False)
def run_compare(key, n):
    return m.compare(json.loads(key), n)


@st.cache_data(show_spinner=False)
def run_stocks(key):
    return m.simulate(m._fill(json.loads(key)))


# ================= Inputs (sidebar) =================
with st.sidebar:
    st.subheader(":material/tune: Lot inputs")
    st.selectbox("Start from a profile", list(PRESETS), key="preset", on_change=apply_preset)

    with st.expander("Cattle and arrival", expanded=True, icon=":material/pets:"):
        st.select_slider("Marketing channel", list(CHANNEL_LABELS), key="channel", format_func=CHANNEL_LABELS.get)
        st.select_slider("Source farms", list(SOURCE_LABELS), key="sources", format_func=SOURCE_LABELS.get)
        st.select_slider("Weaning status", list(WEANING_LABELS), key="weaning", format_func=WEANING_LABELS.get)
        st.slider("Transport hours", 0, 36, key="transport")
        st.slider("Arrival weight (lb)", 350, 850, key="weight", step=10)
        st.toggle("Vaccinated before arrival", key="vaccinated")

    with st.expander("Pen", expanded=True, icon=":material/fence:"):
        st.slider("Head count", 20, 500, key="head", step=10)
        st.slider("Pen space (ft²/head)", 80, 300, key="space", step=10)

    with st.expander("Weather outlook", icon=":material/thermostat:"):
        st.slider("Typical daily temp swing (°F)", 10, 40, key="swing")
        st.slider("Typical wind (mph)", 0, 35, key="wind")
        st.toggle("Cold front expected", key="front")
        st.slider("Front arrives on day", 1, 40, key="front_day", disabled=not st.session_state.front)

    with st.expander("Costs", icon=":material/payments:"):
        dose_cost = st.number_input("Metaphylaxis ($/head)", 0, 100, 25)
        vaccine_cost = st.number_input("Vaccine ($/head)", 0, 50, 8)
        treat_cost = st.number_input("Treatment + performance loss ($/case)", 0, 500, 140)
        death_loss = st.number_input("Death loss ($/head)", 0, 4000, 1500)

    with st.expander("Crew and facilities", icon=":material/groups:"):
        pull_capacity = st.number_input("Pull-and-treat capacity (head/day)", 1, 100, 8)
        process_capacity = st.number_input("Chute processing (head/day)", 10, 1000, 250)

    st.button("Reset to baseline", icon=":material/restart_alt:", width="stretch",
              on_click=lambda: [st.session_state.update(BASELINE), st.session_state.update(preset="Typical lot (baseline)")])

s = st.session_state
head, vaccinated = s.head, s.vaccinated
temps, winds, moist = [s.swing] * 46, [s.wind] * 46, [0.0] * 46
if s.front:
    for d in range(s.front_day, min(s.front_day + 3, 46)):
        temps[d], winds[d], moist[d] = 45, 30, 0.3

base = {
    "channel": None if s.channel == "unknown" else s.channel,
    "sources": None if s.sources == "unknown" else s.sources,
    "weaning": None if s.weaning == "unknown" else s.weaning,
    "transport_hours": s.transport, "arrival_weight": s.weight, "space_per_head": s.space,
    "head_count": head, "vaccinated": vaccinated, "use_metaphylaxis": False,
    "temp_swing": temps, "wind": winds, "moisture": moist,
}

with st.spinner("Running the model..."):
    results = run_compare(json.dumps(base), 200)


def costed(name, res):
    meta = "etaphylaxis" in name
    vax = "accinate" in name and not vaccinated
    q = res["summary_p5_p50_p95"]
    cases, deaths = q["expected_cases"][1], q["expected_deaths"][1]
    daily_new = np.diff(np.array(res["brd_probability_p50"])[::4]) * head
    issues = []
    if daily_new.max() > pull_capacity:
        issues.append(f"peak pulls {daily_new.max():.1f}/day exceed crew capacity ({pull_capacity})")
    if (meta or "accinate" in name) and head > process_capacity:
        issues.append(f"{head} head exceeds chute capacity ({process_capacity}/day)")
    return {
        "risk": q["brd_probability"][1], "lo": q["brd_probability"][0], "hi": q["brd_probability"][2],
        "cases": cases, "deaths": deaths, "doses": head * meta + cases,
        "cost": dose_cost * head * meta + vaccine_cost * head * vax + treat_cost * cases + death_loss * deaths,
        "peak": float(daily_new.max()), "peak_day": int(np.argmax(daily_new)) + 1,
        "issues": issues, "low_conf": res["low_confidence"], "missing": res["missing_inputs"],
    }


opts = {name: costed(name, res) for name, res in results.items()}
cur = opts["Current: pull and treat"]
pool = {n: o for n, o in opts.items() if not o["issues"]} or opts
cheapest = min(pool, key=lambda n: pool[n]["cost"])
fewest_doses = min(pool, key=lambda n: pool[n]["doses"])
best = pool[cheapest]
confidence = ("Low: " + ", ".join(cur["missing"]) + " unknown") if cur["missing"] else ("Low: wide range" if cur["low_conf"] else "Adequate")
level, badge = ("High", "high") if cur["risk"] >= 0.25 else ("Moderate", "mod") if cur["risk"] >= 0.10 else ("Low", "low")

# ================= Header =================
st.markdown(f"""
<style>
.band {{border-radius:20px; background:#16382A; color:#F4F1E8; padding:26px 32px; margin-bottom:14px;
  display:flex; justify-content:space-between; align-items:center; gap:16px; animation:fadeUp .5s ease-out both;}}
.band h1 {{color:#F4F1E8; margin:0; font-size:2rem; padding:0;}} .band p {{color:#D9E2D6; margin:4px 0 0;}}
.band .badge {{font-size:1rem; padding:8px 18px;}}
</style>
<div class="band">
  <div><h1>Pen-level risk model</h1><p>BRD risk over the first 45 days on feed, and what each option would change.</p></div>
  <span class="badge badge-{badge}">{level} risk · {cur['risk']:.0%}</span>
</div>
""", unsafe_allow_html=True)
chips = [f"{head} head", CHANNEL_LABELS[s.channel], SOURCE_LABELS[s.sources], WEANING_LABELS[s.weaning],
         f"{s.weight} lb", f"{s.transport} h transport", f"{s.space} ft²/head",
         "Vaccinated" if vaccinated else "Not vaccinated", f"Cold front day {s.front_day}" if s.front else "No front"]
st.markdown("".join(f'<span class="chip">{c}</span>' for c in chips), unsafe_allow_html=True)
st.write("")

if cur["missing"] or cur["low_conf"]:
    st.warning(f"**Confidence: {confidence}.** "
               + ("Missing records were filled with typical values. Confirm them before committing to a plan."
                  if cur["missing"] else "The risk range is wide. Treat the comparison as directional and monitor closely."),
               icon=":material/warning:")

k1, k2, k3, k4 = st.columns(4)
k1.metric("BRD risk by day 45", f"{cur['risk']:.0%}", help="Current approach (pull and treat), median of 200 runs")
k1.caption(f"Range {cur['lo']:.0%} – {cur['hi']:.0%}")
k2.metric("Expected cases", f"{cur['cases']:.0f}")
k2.caption(f"{cur['deaths']:.1f} expected deaths")
k3.metric("Peak pulls per day", f"{cur['peak']:.1f}")
k3.caption(f"Around day {cur['peak_day']} · crew capacity {pull_capacity}/day")
SHORT = {"Current: pull and treat": "Current", "Vaccinate on arrival": "Vaccinate",
         "Metaphylaxis": "Metaphylaxis", "Vaccinate + metaphylaxis": "Vax + meta"}
diff = best['cost'] - cur['cost']
k4.metric("Lowest-cost option", SHORT[cheapest], help=cheapest)
k4.caption("Same as current approach" if cheapest.startswith("Current")
           else f"{'−' if diff < 0 else '+'}${abs(diff):,.0f} vs current · {best['doses'] - cur['doses']:+.0f} doses")

tab_risk, tab_opts, tab_sum = st.tabs([":material/show_chart: Risk over time", ":material/compare_arrows: Compare options",
                                       ":material/description: Decision summary"])

with tab_risk:
    left, right = st.columns([3, 2])
    with left.container(border=True):
        fig = go.Figure()
        for name, res in results.items():
            day = res["day"]
            if name.startswith("Current"):
                fig.add_trace(go.Scatter(x=day + day[::-1], y=res["brd_probability_p95"] + res["brd_probability_p5"][::-1],
                                         fill="toself", fillcolor="rgba(138,143,134,0.18)", line=dict(width=0),
                                         name="Current: 5–95% range", hoverinfo="skip"))
            fig.add_trace(go.Scatter(x=day, y=res["brd_probability_p50"], name=name,
                                     line=dict(color=COLORS[name], width=3 if name.startswith("Current") else 2),
                                     hovertemplate="Day %{x:.0f}: %{y:.1%}<extra>" + name + "</extra>"))
        fig.update_layout(title="Share of lot with BRD", xaxis_title="Days on feed", yaxis_tickformat=".0%", **CHART)
        st.plotly_chart(fig, width="stretch")
    with right.container(border=True):
        stocks = run_stocks(json.dumps(base))
        fig2 = go.Figure()
        for k, lab, col in [("stress", "Stress", "#D0643A"), ("immunity", "Immunity", "#2E8B62"),
                            ("nutrition_deficit", "Nutrition deficit", "#B07A1E")]:
            fig2.add_trace(go.Scatter(x=stocks["day"], y=stocks[k], name=lab, line=dict(color=col),
                                      hovertemplate="Day %{x:.0f}: %{y:.2f}<extra>" + lab + "</extra>"))
        if s.front:
            fig2.add_vrect(x0=s.front_day, x1=s.front_day + 3, fillcolor="#378ADD", opacity=0.12, line_width=0,
                           annotation_text="cold front", annotation_position="top left")
        fig2.update_layout(title="What drives the risk", xaxis_title="Days on feed", **CHART)
        st.plotly_chart(fig2, width="stretch")
    st.caption("Stress spikes at arrival and with bad weather, suppresses immunity and feed intake, and risk follows "
               "about a week later.")

with tab_opts:
    comp = pd.DataFrame([{
        "Option": name,
        "BRD risk": o["risk"],
        "Range": f"{o['lo']:.0%}–{o['hi']:.0%}",
        "Cases avoided": round(cur["cases"] - o["cases"], 1),
        "Extra antibiotic doses": round(o["doses"] - cur["doses"]),
        "Cost vs current ($)": round(o["cost"] - cur["cost"]),
        "Feasible": "No: " + "; ".join(o["issues"]) if o["issues"] else "Yes",
    } for name, o in opts.items()])
    left, right = st.columns([3, 2])
    with left.container(border=True):
        st.dataframe(comp, hide_index=True, width="stretch", column_config={
            "BRD risk": st.column_config.ProgressColumn(format="percent", min_value=0, max_value=max(0.5, comp["BRD risk"].max())),
            "Cost vs current ($)": st.column_config.NumberColumn(format="dollar"),
        })
        st.caption("Compared with the current approach on the same lot. Negative cost means savings.")
        st.download_button("Download comparison (CSV)", comp.to_csv(index=False), file_name="brd_option_comparison.csv",
                           icon=":material/download:")
    with right.container(border=True):
        fig3 = go.Figure()
        for name, o in opts.items():
            fig3.add_trace(go.Scatter(x=[o["doses"]], y=[o["cases"]], mode="markers+text",
                                      text=[name.replace("Current: ", "")], textposition="top center",
                                      marker=dict(size=16, color=COLORS[name], line=dict(width=1, color="#FFFFFF")),
                                      showlegend=False,
                                      hovertemplate=f"{name}<br>%{{x:.0f}} doses, %{{y:.1f}} cases<extra></extra>"))
        fig3.update_layout(title="Antibiotic use vs. BRD cases (lower-left is better)",
                           xaxis_title="Antibiotic doses", yaxis_title="Expected cases", **CHART)
        st.plotly_chart(fig3, width="stretch")

with tab_sum:
    extra, avoided = best["doses"] - cur["doses"], cur["cases"] - best["cases"]
    dose_note = f"  (~{extra / avoided:.0f} extra doses per case avoided)" if avoided > 0.5 and extra > 0 else ""
    summary = f"""BRD DECISION SUMMARY
Lot: {' | '.join(chips)}
Weather: {s.swing}°F swing, {s.wind} mph wind{f', cold front day {s.front_day}' if s.front else ''}

Current approach (pull and treat): {cur['risk']:.0%} BRD risk ({cur['lo']:.0%}–{cur['hi']:.0%}) — {level} risk
  ~{cur['cases']:.0f} cases, {cur['deaths']:.1f} deaths, ${cur['cost']:,.0f}, peak {cur['peak']:.1f} pulls/day around day {cur['peak_day']}.

Lowest projected cost among feasible options: {cheapest}
  {best['risk']:.0%} risk, {avoided:.0f} cases avoided, {extra:+.0f} antibiotic doses, ${best['cost'] - cur['cost']:+,.0f} vs current.{dose_note}
Lowest antibiotic use among feasible options: {fewest_doses}

Confidence: {confidence}
Watch window: highest pull load around day {cur['peak_day']}{f'; cold front day {s.front_day} adds stress' if s.front else ''}.

Any metaphylaxis or treatment decision must be reviewed and authorized by the herd veterinarian.
"""
    with st.container(border=True):
        st.code(summary, language=None)
        st.download_button("Download summary", summary, file_name="brd_decision_summary.txt", icon=":material/download:")

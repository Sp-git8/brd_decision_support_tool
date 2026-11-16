from pathlib import Path

import pandas as pd
import streamlit as st

st.markdown("""
<style>
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], [data-testid="stExpandSidebarButton"] {display:none !important;}
.band {border-radius:20px; background:#16382A; color:#F4F1E8; padding:34px 40px; margin-bottom:22px; animation:fadeUp .5s ease-out both;}
.band h1 {color:#F4F1E8; margin:0 0 6px; font-size:2.3rem;} .band p {color:#D9E2D6; margin:0; font-size:1.02rem;}
.flow {width:100%; height:auto; margin:6px 0 4px;}
.flow .box {transition:transform .2s ease;} .flow .box:hover {transform:translateY(-3px);}
</style>
<div class="band">
  <h1>Methods and data</h1>
  <p>How each model works, what data it uses, and which numbers are still assumptions.</p>
</div>
""", unsafe_allow_html=True)

tab_pen, tab_animal = st.tabs([":material/monitoring: Pen-level risk model", ":material/sensors: Animal-level screening"])

with tab_pen:
    with st.container(border=True):
        st.markdown("#### Model structure")
        st.markdown("""
    <svg class="flow" viewBox="0 0 1000 190" xmlns="http://www.w3.org/2000/svg" font-family="DM Sans, sans-serif">
      <defs><marker id="a" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M1 1L9 5L1 9" fill="none" stroke="#5B6B61" stroke-width="1.6"/></marker></defs>
      <g class="box"><rect x="10" y="20" width="190" height="64" rx="12" fill="#EEF2EC" stroke="#B9C7B5"/>
        <text x="105" y="48" text-anchor="middle" font-size="15" font-weight="700" fill="#1F2A24">Arrival + weather</text>
        <text x="105" y="68" text-anchor="middle" font-size="12" fill="#5B6B61">transport, source, weaning</text></g>
      <g class="box"><rect x="270" y="20" width="160" height="64" rx="12" fill="#F9E2DC" stroke="#E5B3A2"/>
        <text x="350" y="48" text-anchor="middle" font-size="15" font-weight="700" fill="#8A2E17">Stress</text>
        <text x="350" y="68" text-anchor="middle" font-size="12" fill="#8A2E17">stock</text></g>
      <g class="box"><rect x="500" y="20" width="160" height="64" rx="12" fill="#E3F1E8" stroke="#A9D1B8"/>
        <text x="580" y="48" text-anchor="middle" font-size="15" font-weight="700" fill="#1E5C3A">Immunity</text>
        <text x="580" y="68" text-anchor="middle" font-size="12" fill="#1E5C3A">stock</text></g>
      <g class="box"><rect x="500" y="112" width="160" height="64" rx="12" fill="#FBF0D9" stroke="#E8CD8E"/>
        <text x="580" y="140" text-anchor="middle" font-size="15" font-weight="700" fill="#7A4E0B">Nutrition deficit</text>
        <text x="580" y="160" text-anchor="middle" font-size="12" fill="#7A4E0B">stock</text></g>
      <g class="box"><rect x="730" y="64" width="250" height="64" rx="12" fill="#16382A"/>
        <text x="855" y="92" text-anchor="middle" font-size="15" font-weight="700" fill="#F4F1E8">BRD risk</text>
        <text x="855" y="112" text-anchor="middle" font-size="12" fill="#D9E2D6">cumulative hazard, ~7 d onset</text></g>
      <g stroke="#5B6B61" stroke-width="1.6" fill="none" marker-end="url(#a)">
        <path d="M200 52 L266 52"/><path d="M430 52 L496 52"/><path d="M400 84 L400 144 L496 144"/>
        <path d="M580 112 L580 88"/><path d="M660 52 L700 52 L700 84 L726 84"/><path d="M660 144 L700 144 L700 110 L726 110"/>
        <path d="M350 20 L350 6 L855 6 L855 60"/>
      </g>
    </svg>
    """, unsafe_allow_html=True)
        st.markdown("""
    - **Stress** rises with transport, marketing channel, commingling, weaning, crowding and weather, and recovers over time.
    - **Immunity** is built by vaccination (about a 12-day lag) and good nutrition, and suppressed by stress.
    - **Nutrition deficit** grows when feed intake falls short of target; stress and illness lower intake.
    - **BRD risk** accumulates from the daily hazard set by all three, with a ~7-day delay to clinical signs.

    Two feedback loops drive the behavior: illness lowers intake, which weakens immunity (reinforcing), while stress
    recovers over time (balancing).
    """)

    c1, c2 = st.columns(2)
    with c1.container(border=True):
        st.markdown("#### Uncertainty")
        st.markdown("Each option is run 200 times with every parameter varied about ±15%. Inputs marked **Unknown** are "
                    "sampled from typical values. Results show the median and the 5–95% range, and the tool flags low "
                    "confidence when inputs are missing or the range is wide.")
    with c2.container(border=True):
        st.markdown("#### Status of the numbers")
        st.markdown("""
    | Item | Status |
    |---|---|
    | Model structure | Based on published BRD risk factors |
    | Parameter values | **Placeholders**, pending calibration |
    | Costs | User-editable assumptions |
    | Data | No producer data; all scenarios are user inputs |
    """)

    with st.container(border=True):
        st.markdown("#### Key references")
        st.markdown("""
    - Cernicchiaro et al. (2012). Distance traveled from sale barns and BRD risk in feeder cattle. *Journal of Animal Science* 90(6):1929–1939.
    - Marchesini et al. (2018). Rumination and activity as health indicators in beef cattle. *The Veterinary Journal* 231:41–47.
    """)

    with st.container(border=True):
        st.markdown("#### Future work")
        st.markdown("- **Check against pen riders.** Compare the model's predicted BRD rate with the share of animals pen "
                    "riders flag each day, and use the gap to recalibrate pen-level risk over time.")


with tab_animal:
    with st.container(border=True):
        st.markdown("#### What this model is")
        st.markdown("A screening tool that gives every animal a BRD risk score from 0 to 100 using one day of sensor readings "
                    "(activity and rumination recorded every two hours) plus feedlot records: days on feed, arrival weight, "
                    "sex, breed type and source.")
    with st.container(border=True):
        st.markdown("#### How it works")
        st.markdown("""
        1. **Summarise each animal.** Two-hourly readings become one row per animal: daily rumination against the weekly
           average, counts of low-rumination periods, activity against the pen median, swings in activity, plus feedlot records.
        2. **Learn the alert.** Logistic regression, random forest and gradient boosting were trained to predict the BRD pull
           and compared with 5-fold cross-validation that holds out whole pens.
        3. **Score.** The risk score is the model's BRD probability ranked within the herd, 0 to 100.
        4. **Tier.** Top 2% of scores are High, the next 8% Moderate, the rest Low.
        """)
    with st.container(border=True):
        st.markdown("#### Models compared")
        st.caption("5-fold cross-validation, holding out whole pens. PR-AUC weighs performance on the rare BRD cases and "
                   "was used to select the model.")
        metrics_path = next((f for root in [Path(__file__).resolve().parent.parent, Path.cwd()]
                             for f in sorted(root.rglob("*.csv")) if f.name.lower() == "beef_model_metrics.csv"), None)
        if metrics_path is not None:
            st.dataframe(pd.read_csv(metrics_path), hide_index=True, width="stretch")
        else:
            st.info("No metrics file found. Put `beef_model_metrics.csv` in the `data/` folder.")
    c1, c2 = st.columns(2)
    with c1.container(border=True):
        st.markdown("#### Data")
        st.markdown("""
        | Item | Status |
        |---|---|
        | Sensor patterns | Real dairy readings, rescaled to feedlot levels |
        | Pens, days on feed, weights, source | Synthetic |
        | BRD outcome | Simulated |
        """)
    with c2.container(border=True):
        st.markdown("#### Limits")
        st.markdown("""
        - Accuracy figures describe the simulation, not real BRD detection.
        - A rumination drop is not specific to BRD: other illness, lameness and stress look similar.
        - Use it to decide which cattle to examine, never to decide treatment on its own.
        """)
    with st.container(border=True):
        st.markdown("#### Future work")
        st.markdown("""
        - **Pen-rider reports.** Let cowboys flag an animal that looks sick (depressed, off feed, laboured breathing, nasal
          discharge) directly from the dashboard. A report acts as extra evidence and raises that animal's risk score, so
          visually obvious cases move to the top of the check list even when sensor data is borderline. Riders won't see
          every animal, so a missing report never lowers a score.
        - **Weigh-in temperatures.** Many yards take rectal temperatures at weigh-ins. Adding temperature as a model input,
          with fever (around 104 °F / 40 °C) as a flag, gives the model a direct clinical sign alongside rumination and activity.
        - **Model refresh.** Once real reports and temperatures are logged with BRD outcomes, retrain the model on real cases
          instead of simulated pulls.
        """)
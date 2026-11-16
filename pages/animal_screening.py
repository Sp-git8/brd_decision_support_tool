"""Animal-level screening page: daily sensor-based BRD risk scores."""
import re
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

def find_file(pattern):
    """Find a CSV by exact name near the app, wherever the repo is launched from."""
    roots = [Path(__file__).resolve().parent.parent, Path.cwd()]
    for root in roots:
        for f in sorted(root.rglob("*.csv")):
            if f.name.lower() == pattern and ".venv" not in f.parts:
                return f
    return None

# Accepted column names (lowercase, letters/digits only) -> internal name
ALIASES = {
    "animal": ["animal", "animalid", "id", "cowid", "tag"],
    "pen": ["pen", "penid"],
    "dof": ["daysonfeed", "dof", "days"],
    "source": ["source", "origin", "marketingchannel"],
    "score": ["riskscore", "score", "brdriskscore"],
    "prob": ["brdprobability", "probability", "prob", "predictedprobability"],
    "rumination": ["dailyrumination", "rumination", "ruminationmin"],
    "weekly": ["weeklyaverage", "weeklyavg", "ruminationweeklyaverage"],
    "deficit": ["deficit", "ruminationdeficit"],
    "activity": ["dailyactivity", "activity", "activitymin"],
    "pull": ["simulatedbrdpull", "brdpull", "pull", "pulled", "label"],
    "tier": ["tier", "risktier"],
}
LABELS = {"animal": "Animal", "pen": "Pen", "dof": "Days on feed", "source": "Source", "score": "Risk score",
          "prob": "BRD probability", "rumination": "Daily rumination (min)", "weekly": "Weekly average (min)",
          "deficit": "Rumination deficit (min)", "activity": "Daily activity (min)", "pull": "Simulated BRD pull"}
TIER_COLORS = {"High": "#D0643A", "Moderate": "#378ADD", "Low": "#B4B2A9"}


def key(c):
    return re.sub(r"[^a-z0-9]", "", c.lower())


@st.cache_data(show_spinner=False)
def load_scores(path):
    raw = pd.read_csv(path)
    found = {key(c): c for c in raw.columns}
    df = pd.DataFrame(index=raw.index)
    for name, opts in ALIASES.items():
        col = next((found[a] for a in opts if a in found), None)
        if col is not None:
            df[name] = raw[col]
    if "pull" in df:
        df["pull"] = df["pull"].map(lambda v: str(v).strip().lower() in ("1", "yes", "true", "y"))
    if "deficit" not in df and {"rumination", "weekly"} <= set(df):
        df["deficit"] = df["rumination"] - df["weekly"]
    if "tier" not in df:
        rank = df["score"] if "score" in df else df["prob"].rank(pct=True) * 100
        df["tier"] = pd.cut(rank, [-1, 90, 98, 101], labels=["Low", "Moderate", "High"]).astype(str)
    df["tier"] = df["tier"].astype(str).str.capitalize()
    return df


# ================= Page style =================
st.markdown("""
<style>
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], [data-testid="stExpandSidebarButton"] {display:none !important;}
.band {border-radius:20px; background:#16382A; color:#F4F1E8; padding:26px 32px; margin-bottom:14px;
  display:flex; justify-content:space-between; align-items:center; gap:16px; animation:fadeUp .5s ease-out both;}
.band h1 {color:#F4F1E8; margin:0; font-size:2rem; padding:0;} .band p {color:#D9E2D6; margin:4px 0 0;}
.demo {background:rgba(244,241,232,.12); border:1px solid rgba(244,241,232,.3); color:#F4F1E8; border-radius:999px;
  padding:6px 14px; font-size:.85rem; white-space:nowrap;}
</style>
<div class="band">
  <div><h1>Animal-level screening</h1><p>Daily BRD risk score for every animal from collar sensor data. Use it to decide which cattle to examine first.</p></div>
  <span class="demo">Demo data · synthetic feedlot dataset</span>
</div>
""", unsafe_allow_html=True)


@st.dialog("Use your own dataset")
def upload_info():
    st.markdown("**Coming soon.** You'll be able to upload a daily sensor export and see every animal scored, "
                "tiered and listed here in the same way.")
    st.markdown("Planned format: one row per animal per day with")
    st.markdown("- animal ID, pen, days on feed, source, arrival weight, sex, breed type\n"
                "- rumination and activity (minutes, two-hourly or daily totals)")
    st.caption("For now this page shows the synthetic demonstration dataset.")


@st.dialog("Report a sick animal")
def report_info():
    st.markdown("**Coming soon.** Pen riders will be able to flag an animal that looks sick, and the report will raise "
                "that animal's risk score so it moves up the check list.")
    st.markdown("Planned report:")
    st.markdown("- animal ID and pen\n- signs seen: depressed, off feed, laboured breathing, nasal discharge, cough\n"
                "- rectal temperature, if taken at weigh-in (fever around 104 °F / 40 °C)")
    st.caption("A report only raises a score. Animals nobody looked at are not marked down.")


top_l, top_r = st.columns([4, 1], vertical_alignment="center")
top_r.button("Report a sick animal", icon=":material/flag:", on_click=report_info, width="stretch",
             help="Coming soon: pen-rider reports raise an animal's risk score")
top_r.button("Upload your dataset", icon=":material/upload_file:", on_click=upload_info, width="stretch",
             help="Coming soon: score your own sensor export")

path = find_file("beef_brd_scores.csv")
if path is None:
    st.info("No scores file found. Put `beef_brd_scores.csv` in the `data/` folder.",
            icon=":material/folder_open:")
    st.stop()
df = load_scores(path)

# ================= Filters =================
with top_l:
    f1, f2, f3 = st.columns(3)
    max_dof = int(df["dof"].max()) if "dof" in df else 45
    dof_limit = f1.slider("Days on feed up to", 1, max(max_dof, 45), min(45, max_dof), disabled="dof" not in df,
                          help="The challenge covers the first 45 days after arrival")
    pens = f2.multiselect("Pens", sorted(df["pen"].unique()), placeholder="All pens") if "pen" in df else []
    sources = f3.multiselect("Source", sorted(df["source"].dropna().unique()), placeholder="All sources") if "source" in df else []

view = df.copy()
if "dof" in view:
    view = view[view["dof"] <= dof_limit]
if pens:
    view = view[view["pen"].isin(pens)]
if sources:
    view = view[view["source"].isin(sources)]

if view.empty:
    st.warning("No cattle match these filters.")
    st.stop()

n_high = int((view["tier"] == "High").sum())
n_mod = int((view["tier"] == "Moderate").sum())

if n_high:
    st.error(f"**{n_high} cattle are in the High risk tier.** Examine them today for fever and respiratory signs "
             f"before treating: the score is a screening flag, not a diagnosis.", icon=":material/notifications_active:")

k1, k2, k3, k4 = st.columns(4)
k1.metric("Cattle scored", f"{len(view):,}")
k2.metric("High risk tier", f"{n_high:,}", help="Top 2% of scores")
k3.metric("Moderate risk tier", f"{n_mod:,}", help="Next 8% of scores")
if "pull" in view:
    k4.metric("Simulated BRD pulls", f"{int(view['pull'].sum()):,}")
else:
    k4.metric("Average risk score", f"{view['score'].mean():.0f}" if "score" in view else "–")

CHART = dict(height=380, margin=dict(l=10, r=10, t=40, b=10), plot_bgcolor="#FFFFFF", paper_bgcolor="rgba(0,0,0,0)",
             font=dict(color="#1F2A24"), legend=dict(orientation="h", y=-0.2))

tab_check, tab_pattern, tab_perf = st.tabs([":material/checklist: Check today", ":material/scatter_plot: Sensor patterns",
                                            ":material/target: How well it flags"])

with tab_check:
    cols = [c for c in ["animal", "pen", "dof", "source", "score", "prob", "rumination", "weekly", "deficit", "activity", "pull"] if c in view]
    sort_col = "score" if "score" in view else "prob"
    for tier, note in [("High", "Examine today: temperature, breathing, nasal discharge, appetite."),
                       ("Moderate", "Re-check tomorrow instead of pulling immediately.")]:
        sub = view[view["tier"] == tier].sort_values(sort_col, ascending=False)[cols]
        with st.container(border=True):
            st.markdown(f"**{tier} tier · {len(sub):,} cattle**")
            st.caption(note)
            st.dataframe(sub.rename(columns=LABELS), hide_index=True, width="stretch", height=min(420, 38 + 35 * len(sub)),
                         column_config={"Risk score": st.column_config.ProgressColumn(format="%.1f", min_value=0, max_value=100),
                                        "BRD probability": st.column_config.NumberColumn(format="%.3f")})
            st.download_button(f"Download {tier.lower()} tier list (CSV)", sub.rename(columns=LABELS).to_csv(index=False),
                               file_name=f"brd_{tier.lower()}_tier.csv", icon=":material/download:", key=f"dl_{tier}")

with tab_pattern:
    left, right = st.columns([3, 2])
    with left.container(border=True):
        if {"deficit", "activity"} <= set(view):
            flagged = view[view["tier"].isin(["High", "Moderate"])]
            fig = go.Figure()
            for tier in ["Moderate", "High"]:
                t = flagged[flagged["tier"] == tier]
                fig.add_trace(go.Scatter(x=t["deficit"], y=t["activity"], mode="markers", name=f"{tier} tier",
                                         marker=dict(size=7, color=TIER_COLORS[tier], opacity=.75,
                                                     line=dict(width=1.5, color=["#1F2A24" if p else "rgba(0,0,0,0)" for p in t["pull"]]) if "pull" in t else None),
                                         text=t["animal"] if "animal" in t else None,
                                         hovertemplate="Animal %{text}<br>Deficit %{x:.0f} min<br>Activity %{y:.0f} min<extra></extra>"))
            fig.add_vline(x=0, line_dash="dot", line_color="#8A8F86")
            fig.update_layout(title="Flagged cattle: rumination drop against activity", xaxis_title="Rumination deficit (min, today minus weekly average)",
                              yaxis_title="Daily activity (min)", **CHART)
            st.plotly_chart(fig, width="stretch")
            st.caption("Far left and low means a large rumination drop with little movement, the pattern that fits illness. "
                       "Dark outline = simulated BRD pull.")
        else:
            st.info("Rumination and activity columns are needed for this chart.")
    with right.container(border=True):
        if "prob" in view:
            fig2 = go.Figure()
            for tier in ["Low", "Moderate", "High"]:
                t = view[view["tier"] == tier]
                fig2.add_trace(go.Histogram(x=t["prob"], name=tier, marker_color=TIER_COLORS[tier], xbins=dict(start=0, end=1, size=0.025)))
            fig2.update_layout(barmode="stack", title="Distribution of BRD probability", xaxis_title="Model BRD probability (relative)",
                               yaxis_title="Cattle", yaxis_type="log", **CHART)
            st.plotly_chart(fig2, width="stretch")
            st.caption("Most cattle sit near zero; the High tier is the thin tail on the right. Log scale.")

with tab_perf:
    if "pull" in view:
        perf = (view.groupby("tier")["pull"].agg(Cattle="size", Pulls="sum").reindex(["High", "Moderate", "Low"]).dropna())
        perf["BRD rate"] = perf["Pulls"] / perf["Cattle"]
        perf["Share of all pulls"] = perf["Pulls"] / perf["Pulls"].sum()
        left, right = st.columns([3, 2])
        with left.container(border=True):
            st.markdown("**Where the simulated BRD cases landed**")
            st.dataframe(perf.reset_index().rename(columns={"tier": "Tier"}), hide_index=True, width="stretch",
                         column_config={"BRD rate": st.column_config.ProgressColumn(format="percent", min_value=0, max_value=1),
                                        "Share of all pulls": st.column_config.NumberColumn(format="percent")})
            hi, lo = perf["BRD rate"].get("High", 0), perf["BRD rate"].get("Low", 0)
            if lo:
                st.caption(f"High-tier cattle got BRD {hi / lo:.0f}× as often as Low-tier cattle in the simulation.")
        with right.container(border=True):
            fig3 = go.Figure(go.Bar(x=perf.index, y=perf["BRD rate"], marker_color=[TIER_COLORS[t] for t in perf.index],
                                    text=[f"{v:.1%}" for v in perf["BRD rate"]], textposition="outside"))
            fig3.update_layout(title="BRD rate by tier", yaxis_tickformat=".0%", **{**CHART, "height": 300})
            st.plotly_chart(fig3, width="stretch")
        st.caption("The BRD outcome is simulated, so these figures show how the tool works, not how well it detects real BRD. "
                   "Model comparison is on the Methods and data page.")
    else:
        st.info("A simulated BRD pull column is needed to show performance by tier.")
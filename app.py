"""BRD Decision Lab: entry point and top navigation.

Run:  streamlit run app.py
Add a new model later: create pages/<name>.py and add one st.Page line below.
"""
import streamlit as st

st.set_page_config(page_title="BRD Decision Lab", page_icon=":material/pets:", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,700&family=Fraunces:opsz,wght@9..144,600;9..144,700&display=swap');

.stApp {font-family:'DM Sans', sans-serif;}
h1, h2, h3, h4 {font-family:'Fraunces', serif !important; letter-spacing:-0.01em;}

@keyframes fadeUp {from {opacity:0; transform:translateY(14px);} to {opacity:1; transform:none;}}
@keyframes fadeIn {from {opacity:0;} to {opacity:1;}}
@keyframes draw {to {stroke-dashoffset:0;}}
@keyframes drift {0%,100% {transform:translateX(0);} 50% {transform:translateX(6px);}}
@keyframes spin {to {transform:rotate(360deg);}}

.block-container {padding-top:4.2rem; animation:fadeIn .4s ease-out;}

[data-testid="stMetric"] {background:#FFFFFF; border:1px solid #DDE3DA; border-radius:14px; padding:16px 18px;
  box-shadow:0 1px 2px rgba(31,42,36,.04); transition:transform .2s ease, box-shadow .2s ease; animation:fadeUp .5s ease-out both;}
[data-testid="stMetric"]:hover {transform:translateY(-3px); box-shadow:0 8px 20px rgba(31,42,36,.08);}
[data-testid="stColumn"]:nth-child(2) [data-testid="stMetric"] {animation-delay:.06s;}
[data-testid="stColumn"]:nth-child(3) [data-testid="stMetric"] {animation-delay:.12s;}
[data-testid="stColumn"]:nth-child(4) [data-testid="stMetric"] {animation-delay:.18s;}
[data-testid="stMetricLabel"] p {font-size:.95rem; color:#5B6B61; text-transform:uppercase; letter-spacing:.04em;}
[data-testid="stMetricValue"] {font-family:'Fraunces', serif; font-size:1.9rem;}

[data-testid="stVerticalBlockBorderWrapper"] {border-radius:14px !important; transition:box-shadow .2s ease; animation:fadeUp .5s ease-out both;}
[data-testid="stVerticalBlockBorderWrapper"]:hover {box-shadow:0 8px 24px rgba(31,42,36,.07);}

.stTabs [data-baseweb="tab-list"] {gap:6px;}
.stTabs [data-baseweb="tab"] {font-weight:500; border-radius:10px 10px 0 0; padding:8px 16px; transition:background .2s ease;}
.stTabs [data-baseweb="tab"]:hover {background:#EEF2EC;}
.stTabs [data-baseweb="tab-panel"] {animation:fadeIn .35s ease-out;}

.stButton button, .stDownloadButton button {border-radius:10px; transition:all .2s ease;}
.stButton button:hover, .stDownloadButton button:hover {transform:translateY(-1px); box-shadow:0 4px 12px rgba(46,107,79,.18);}
[data-testid="stExpander"] details {border-radius:12px; transition:box-shadow .2s ease;}
[data-testid="stExpander"] details:hover {box-shadow:0 2px 10px rgba(31,42,36,.06);}

.badge {display:inline-block; padding:5px 14px; border-radius:999px; font-size:.85rem; font-weight:700; animation:fadeIn .4s ease-out;}
.badge-low {background:#E3F1E8; color:#1E5C3A;} .badge-mod {background:#FBF0D9; color:#7A4E0B;} .badge-high {background:#F9E2DC; color:#8A2E17;}
.chip {display:inline-block; background:#FFFFFF; border:1px solid #DDE3DA; color:#2E3B33; border-radius:999px;
  padding:4px 13px; margin:3px 6px 3px 0; font-size:.95rem; animation:fadeIn .4s ease-out both;}
.muted {color:#5B6B61;}
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p {font-size:1.1rem !important; color:#4A5A50 !important; line-height:1.5;}
[data-testid="stWidgetLabel"] p {font-size:1rem !important;}
.muted, .band p {font-size:1.08rem !important;}
</style>
""", unsafe_allow_html=True)

pages = [
    st.Page("pages/home.py", title="Home", icon=":material/home:", default=True),
    st.Page("pages/risk_model.py", title="Pen-level risk model", icon=":material/monitoring:", url_path="risk-model"),
    st.Page("pages/animal_screening.py", title="Animal-level screening", icon=":material/sensors:", url_path="animal-screening"),
    st.Page("pages/about.py", title="Methods and data", icon=":material/menu_book:", url_path="methods"),
]
st.navigation(pages, position="top").run()
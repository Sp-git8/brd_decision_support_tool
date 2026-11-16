import streamlit as st

st.markdown("""
<style>
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], [data-testid="stExpandSidebarButton"] {display:none !important;}

.hero {position:relative; border-radius:22px; overflow:hidden; background:#16382A; color:#F4F1E8;
  min-height:420px; animation:fadeIn .6s ease-out;}
.hero svg.scene {position:absolute; inset:0; width:100%; height:100%;}
.hero .copy {position:relative; z-index:2; padding:56px 56px 40px; max-width:620px; animation:fadeUp .7s ease-out .1s both;}
.hero .eyebrow {display:inline-block; font-size:.78rem; letter-spacing:.14em; text-transform:uppercase;
  background:rgba(244,241,232,.12); border:1px solid rgba(244,241,232,.25); padding:5px 12px; border-radius:999px;}
.hero h1 {font-family:'Fraunces', serif; font-size:3.1rem; line-height:1.05; margin:18px 0 14px; color:#F4F1E8;}
.hero p {font-size:1.08rem; line-height:1.6; color:#D9E2D6; margin:0 0 26px;}
.cta {display:inline-block; background:#E9B44C; color:#1F2A24 !important; text-decoration:none !important; font-weight:700;
  padding:13px 24px; border-radius:12px; transition:transform .2s ease, box-shadow .2s ease;}
.cta:hover {transform:translateY(-2px); box-shadow:0 10px 24px rgba(0,0,0,.25);}
.cta.ghost {background:transparent; color:#F4F1E8 !important; border:1px solid rgba(244,241,232,.4); margin-left:10px;}
.risk-line {stroke-dasharray:900; stroke-dashoffset:900; animation:draw 2.4s ease-out .5s forwards;}
.cow {animation:drift 6s ease-in-out infinite;} .cow.b {animation-delay:-2s;} .cow.c {animation-delay:-4s;}
.blades {transform-origin:1012px 160px; animation:spin 9s linear infinite;}

.stats {display:flex; gap:14px; margin:22px 0 8px; flex-wrap:wrap;}
.stat {flex:1; min-width:180px; background:#FFFFFF; border:1px solid #DDE3DA; border-radius:16px; padding:18px 20px;
  animation:fadeUp .6s ease-out both;}
.stat:nth-child(2) {animation-delay:.08s;} .stat:nth-child(3) {animation-delay:.16s;} .stat:nth-child(4) {animation-delay:.24s;}
.stat b {display:block; font-family:'Fraunces', serif; font-size:1.7rem; color:#2E6B4F;}
.stat span {color:#5B6B61; font-size:.9rem;}

.cards {display:grid; grid-template-columns:repeat(3, minmax(0,1fr)); gap:16px; margin:26px 0;}
.card {background:#FFFFFF; border:1px solid #DDE3DA; border-radius:18px; padding:24px; transition:transform .25s ease, box-shadow .25s ease;
  animation:fadeUp .6s ease-out both;}
.card:nth-child(2) {animation-delay:.1s;} .card:nth-child(3) {animation-delay:.2s;}
.card:hover {transform:translateY(-5px); box-shadow:0 14px 30px rgba(31,42,36,.10);}
.card .icon {width:52px; height:52px; border-radius:14px; display:flex; align-items:center; justify-content:center; margin-bottom:14px;}
.card h3 {font-size:1.2rem; margin:0 0 8px;}
.card p {color:#5B6B61; margin:0; line-height:1.55;}

.steps {display:grid; grid-template-columns:repeat(4, minmax(0,1fr)); gap:14px; margin:10px 0 26px;}
.models {display:grid; grid-template-columns:repeat(2, minmax(0,1fr)); gap:18px; margin:28px 0 10px;}
.model {display:block; background:#FFFFFF; border:1px solid #DDE3DA; border-radius:20px; padding:28px; text-decoration:none !important;
  color:#1F2A24 !important; transition:transform .25s ease, box-shadow .25s ease, border-color .25s ease; animation:fadeUp .6s ease-out both;}
.model:nth-child(2) {animation-delay:.12s;}
.model:hover {transform:translateY(-5px); box-shadow:0 16px 34px rgba(31,42,36,.10); border-color:#2E6B4F;}
.model .tag {display:inline-block; font-size:.75rem; letter-spacing:.1em; text-transform:uppercase; background:#E3F1E8; color:#1E5C3A;
  padding:4px 10px; border-radius:999px;}
.model .tag.alt {background:#E6F1FB; color:#0C447C;}
.model h3 {font-size:1.5rem; margin:14px 0 8px;}
.model p {color:#5B6B61; line-height:1.6; margin:0 0 16px;}
.model .uses span {display:inline-block; border:1px solid #DDE3DA; border-radius:999px; padding:3px 10px; margin:0 6px 6px 0; font-size:.82rem; color:#2E3B33;}
.model .go {display:inline-block; margin-top:12px; font-weight:700; color:#2E6B4F;}
@media (max-width:900px) {.models {grid-template-columns:1fr;}}
.step {position:relative; padding:20px; border-radius:16px; background:#EEF2EC; animation:fadeUp .6s ease-out both;}
.step:nth-child(2) {animation-delay:.08s;} .step:nth-child(3) {animation-delay:.16s;} .step:nth-child(4) {animation-delay:.24s;}
.step .n {font-family:'Fraunces', serif; font-size:1.9rem; color:#2E6B4F; line-height:1;}
.step p {margin:8px 0 0; color:#2E3B33; line-height:1.5;}
.note {display:flex; gap:12px; align-items:flex-start; background:#FFF8E8; border:1px solid #F0DDB0; border-radius:14px; padding:16px 18px; color:#5A4410;}
@media (max-width:900px) {.cards, .steps {grid-template-columns:1fr;} .hero h1 {font-size:2.2rem;} .hero .copy {padding:36px 28px;}}
</style>

<div class="hero">
  <svg class="scene" viewBox="0 0 1200 420" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
    <defs>
      <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#16382A"/><stop offset="1" stop-color="#2E6B4F"/></linearGradient>
      <linearGradient id="field" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#C9A55C"/><stop offset="1" stop-color="#9C7B3C"/></linearGradient>
      <linearGradient id="fade" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#16382A" stop-opacity=".95"/><stop offset=".55" stop-color="#16382A" stop-opacity=".35"/><stop offset="1" stop-color="#16382A" stop-opacity="0"/></linearGradient>
    </defs>
    <rect width="1200" height="420" fill="url(#sky)"/>
    <circle cx="1030" cy="62" r="34" fill="#E9B44C" opacity=".9"/>
    <circle cx="1030" cy="62" r="58" fill="#E9B44C" opacity=".12"/>
    <path d="M0 300 C200 270 360 285 520 275 C700 262 860 290 1200 268 L1200 420 L0 420Z" fill="#3E7A58" opacity=".8"/>
    <path d="M0 325 C220 305 420 318 640 308 C860 298 1000 318 1200 305 L1200 420 L0 420Z" fill="url(#field)"/>
    <g stroke="#6B5229" stroke-width="5" stroke-linecap="round">
      <line x1="560" y1="300" x2="560" y2="352"/><line x1="680" y1="296" x2="680" y2="350"/><line x1="800" y1="300" x2="800" y2="352"/>
      <line x1="920" y1="302" x2="920" y2="354"/><line x1="1040" y1="300" x2="1040" y2="352"/><line x1="1160" y1="298" x2="1160" y2="350"/>
    </g>
    <g stroke="#6B5229" stroke-width="3"><path d="M560 315 L1200 312"/><path d="M560 335 L1200 332"/></g>
    <g fill="#5A4A3A"><rect x="1008" y="160" width="8" height="150"/><path d="M996 310 L1012 160 L1028 310Z" fill="none" stroke="#5A4A3A" stroke-width="4"/></g>
    <g class="blades" fill="#F4F1E8" opacity=".9">
      <rect x="1008" y="110" width="8" height="50" rx="2"/><rect x="1008" y="160" width="8" height="50" rx="2"/>
      <rect x="962" y="156" width="50" height="8" rx="2"/><rect x="1012" y="156" width="50" height="8" rx="2"/>
    </g>
    <g class="cow" fill="#2B211A">
      <rect x="640" y="318" width="74" height="34" rx="14"/><rect x="706" y="308" width="26" height="22" rx="7"/>
      <rect x="648" y="346" width="7" height="22"/><rect x="664" y="346" width="7" height="22"/><rect x="690" y="346" width="7" height="22"/><rect x="704" y="346" width="7" height="22"/>
    </g>
    <g class="cow b" fill="#7A3E22">
      <rect x="770" y="326" width="70" height="32" rx="14"/><rect x="832" y="316" width="24" height="20" rx="7"/>
      <rect x="778" y="352" width="7" height="20"/><rect x="793" y="352" width="7" height="20"/><rect x="818" y="352" width="7" height="20"/><rect x="830" y="352" width="7" height="20"/>
      <rect x="790" y="330" width="22" height="12" rx="6" fill="#F4F1E8"/>
    </g>
    <g class="cow c" fill="#2B211A">
      <rect x="1080" y="322" width="64" height="30" rx="13"/><rect x="1060" y="313" width="24" height="20" rx="7"/>
      <rect x="1086" y="346" width="7" height="20"/><rect x="1100" y="346" width="7" height="20"/><rect x="1122" y="346" width="7" height="20"/><rect x="1134" y="346" width="7" height="20"/>
    </g>
    <rect width="1200" height="420" fill="url(#fade)"/>
    <path class="risk-line" d="M520 250 C600 245 640 120 720 95 C790 75 840 150 900 205 C960 255 1060 262 1200 258"
          fill="none" stroke="#E9B44C" stroke-width="4" stroke-linecap="round"/>
    <circle cx="720" cy="95" r="7" fill="#E9B44C" opacity="0"><animate attributeName="opacity" from="0" to="1" begin="2.2s" dur=".4s" fill="freeze"/></circle>
    <text x="736" y="88" fill="#F4F1E8" font-size="15" font-family="DM Sans, sans-serif" opacity="0">peak risk · week 1–3<animate attributeName="opacity" from="0" to="1" begin="2.3s" dur=".4s" fill="freeze"/></text>
  </svg>
  <div class="copy">
    <span class="eyebrow">Feedlot arrival health · first 45 days</span>
    <h1>See BRD risk coming before it shows up in the pen.</h1>
    <p>Two tools for the first 45 days on feed: a pen-level model that plans each arriving lot, and an animal-level
       screen that flags which cattle to examine every day.</p>
    <a class="cta" href="risk-model" target="_self">Pen-level risk model →</a>
    <a class="cta ghost" href="animal-screening" target="_self">Animal-level screening →</a>
  </div>
</div>

<div class="models">
  <a class="model" href="risk-model" target="_self">
    <span class="tag">Macro view · on arrival</span>
    <h3>Pen-level risk model</h3>
    <p>Simulates BRD risk for a whole lot over 45 days from arrival conditions, and compares pull and treat,
       vaccination and metaphylaxis on cases, antibiotic use, cost and crew load.</p>
    <div class="uses"><span>Lot records</span><span>Weather outlook</span><span>System dynamics</span></div>
    <span class="go">Open model →</span>
  </a>
  <a class="model" href="animal-screening" target="_self">
    <span class="tag alt">Individual view · daily</span>
    <h3>Animal-level screening</h3>
    <p>Scores every animal from collar sensor data and ranks who to examine today, with a re-check list for
       borderline cattle.</p>
    <div class="uses"><span>Rumination</span><span>Activity</span><span>Machine learning</span></div>
    <span class="go">Open screening →</span>
  </a>
</div>
""", unsafe_allow_html=True)
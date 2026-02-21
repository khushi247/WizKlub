# pages/1_Dashboard.py — WizKlub CRM Dashboard
# Accessed via the "📊 CRM Dashboard" button on the chat page

import streamlit as st
from scoring import score_label

st.set_page_config(
    page_title="WizKlub CRM",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Outfit', sans-serif !important; }
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stSidebarNav"] { display: none; }
section[data-testid="stSidebar"] { display: none; }
.stApp { background: #f7f5f0; }
.block-container { padding-top: 1.2rem !important; }

.m-card { background:#fff; border:1px solid #e5e0d8; border-radius:14px;
          padding:20px 16px; text-align:center; box-shadow:0 2px 8px rgba(0,0,0,0.04); }
.m-num  { font-size:36px; font-weight:700; line-height:1; }
.m-lbl  { font-size:10px; font-weight:600; text-transform:uppercase;
          letter-spacing:1.2px; color:#9a9189; margin-top:6px; }

.tbl { width:100%; border-collapse:collapse; font-size:13px; }
.tbl th { text-align:left; padding:8px 12px; font-size:10px; font-weight:700;
          text-transform:uppercase; letter-spacing:1px; color:#9a9189;
          border-bottom:2px solid #e5e0d8; }
.tbl td { padding:10px 12px; border-bottom:1px solid #f0ece6; vertical-align:middle; }
.tbl tr:hover td { background:#faf8f4; }

.badge { display:inline-block; padding:3px 10px; border-radius:50px;
         font-size:11px; font-weight:600; }
.hot    { background:rgba(239,68,68,0.10);  color:#dc2626; }
.warm   { background:rgba(251,146,60,0.12); color:#ea6c0a; }
.cool   { background:rgba(99,102,241,0.10); color:#4f46e5; }
.parent { background:rgba(45,106,79,0.10);  color:#2d6a4f; }
.school { background:rgba(231,111,81,0.10); color:#c0502d; }
.demo-y { background:rgba(45,106,79,0.10);  color:#2d6a4f; }
.demo-n { background:#f0ece6; color:#9a9189; }

.sec-lbl { font-size:11px; font-weight:700; text-transform:uppercase;
           letter-spacing:1.2px; color:#9a9189;
           border-bottom:1px solid #e5e0d8; padding-bottom:8px; margin-bottom:14px; }
.pipe-row { display:flex; justify-content:space-between; align-items:center;
            padding:9px 0; border-bottom:1px solid #f5f2ee; font-size:13px; }
.pipe-row:last-child { border:none; }

.stButton > button {
    background: #2d6a4f !important; color: white !important;
    border: none !important; border-radius: 50px !important;
    padding: 8px 20px !important; font-size: 13px !important;
    font-weight: 600 !important; font-family: 'Outfit', sans-serif !important;
}
.stButton > button:hover { background: #235e43 !important; }
</style>
""", unsafe_allow_html=True)

# Init state guard
if "all_leads" not in st.session_state:
    st.session_state.all_leads  = []
    st.session_state.demo_count = 0

all_leads = st.session_state.all_leads
total     = len(all_leads)
hot       = sum(1 for l in all_leads if l["score"] >= 70)
warm      = sum(1 for l in all_leads if 45 <= l["score"] < 70)
cool      = sum(1 for l in all_leads if l["score"] < 45)
demos     = st.session_state.get("demo_count", 0)
parents   = sum(1 for l in all_leads if l["type"] == "Parent")
schools   = sum(1 for l in all_leads if l["type"] == "School")
conv_rate = round(demos / total * 100) if total else 0
avg_score = round(sum(l["score"] for l in all_leads) / total) if total else 0


# ── Page header ───────────────────────────────────────────────────────────────
hc, bc = st.columns([3, 1])
with hc:
    st.markdown("""
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:4px;">
        <div style="font-size:26px">📊</div>
        <div>
            <div style="font-size:20px;font-weight:700;color:#1a1a2e;letter-spacing:-0.4px">
                WizKlub CRM Dashboard</div>
            <div style="font-size:12px;color:#9a9189;margin-top:2px">
                Session leads · auto-scored · real-time</div>
        </div>
    </div>""", unsafe_allow_html=True)

with bc:
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    if st.button("← Back to Chat"):
        st.switch_page("app.py")


st.markdown("<br>", unsafe_allow_html=True)

# ── Stat cards ────────────────────────────────────────────────────────────────
c1, c2, c3, c4, c5, c6 = st.columns(6)
for col, val, color, label in [
    (c1, total,       "#2d6a4f", "Total Leads"),
    (c2, hot,         "#dc2626", "🔥 Hot"),
    (c3, warm,        "#ea6c0a", "🟠 Warm"),
    (c4, demos,       "#2d6a4f", "Demo Requests"),
    (c5, f"{conv_rate}%", "#4f46e5", "Conversion"),
    (c6, avg_score,   "#1a1a2e", "Avg Score"),
]:
    col.markdown(f"""
    <div class="m-card">
        <div class="m-num" style="color:{color}">{val}</div>
        <div class="m-lbl">{label}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Main layout ───────────────────────────────────────────────────────────────
left, right = st.columns([2.2, 1], gap="large")

with left:
    st.markdown('<div class="sec-lbl">Captured Leads</div>', unsafe_allow_html=True)

    if not all_leads:
        st.markdown("""
        <div style="text-align:center;padding:50px;background:#faf8f4;
                    border-radius:14px;border:1px dashed #e5e0d8;color:#b0a89e;">
            <div style="font-size:36px;margin-bottom:10px">💬</div>
            <div style="font-size:14px">No leads yet — go chat with the bot first!</div>
        </div>""", unsafe_allow_html=True)
    else:
        rows = ""
        for l in reversed(all_leads):
            sl     = score_label(l["score"])
            t_cls  = "school" if l["type"] == "School" else "parent"
            i_cls  = "demo-y" if l["wants_demo"] else "demo-n"
            intent = "📅 Demo" if l["wants_demo"] else "📩 Info"
            detail = l.get("child_age") or l.get("school_size") or "—"
            prog   = _program(l)
            rows  += f"""
            <tr>
              <td>
                <strong>{l['name']}</strong><br>
                <span style="font-size:11px;color:#9a9189">{l['email']}</span><br>
                <span style="font-size:11px;color:#b0a89e">{l['phone']}</span>
              </td>
              <td><span class="badge {t_cls}">{l['type']}</span></td>
              <td style="color:#6b6560;font-size:12px">{detail}</td>
              <td style="font-size:12px;color:#6b6560">{prog}</td>
              <td><span class="badge {sl['cls']}">{sl['text']} {l['score']}</span></td>
              <td><span class="badge {i_cls}">{intent}</span></td>
            </tr>"""

        st.markdown(f"""
        <div style="background:white;border:1px solid #e5e0d8;
                    border-radius:14px;padding:16px;overflow-x:auto;">
        <table class="tbl">
          <thead><tr>
            <th>Contact</th><th>Type</th><th>Profile</th>
            <th>Recommended Program</th><th>Score</th><th>Intent</th>
          </tr></thead>
          <tbody>{rows}</tbody>
        </table></div>""", unsafe_allow_html=True)

with right:
    st.markdown('<div class="sec-lbl">Pipeline Summary</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div style="background:white;border:1px solid #e5e0d8;border-radius:14px;padding:16px 18px;">
      <div class="pipe-row"><span style="color:#6b6560">Total leads</span><strong>{total}</strong></div>
      <div class="pipe-row"><span style="color:#6b6560">Demo conversion</span>
        <strong style="color:#2d6a4f">{conv_rate}%</strong></div>
      <div class="pipe-row"><span style="color:#6b6560">Avg lead score</span>
        <strong>{avg_score} / 100</strong></div>
      <div class="pipe-row"><span style="color:#6b6560">Parent leads</span><strong>{parents}</strong></div>
      <div class="pipe-row"><span style="color:#6b6560">School leads</span><strong>{schools}</strong></div>
      <div class="pipe-row"><span style="color:#6b6560">Hot (call now 🔥)</span>
        <strong style="color:#dc2626">{hot}</strong></div>
      <div class="pipe-row"><span style="color:#6b6560">Warm (follow up 🟠)</span>
        <strong style="color:#ea6c0a">{warm}</strong></div>
      <div class="pipe-row"><span style="color:#6b6560">Cool (nurture 🔵)</span>
        <strong style="color:#4f46e5">{cool}</strong></div>
    </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown('<div class="sec-lbl">Scoring Breakdown</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="background:white;border:1px solid #e5e0d8;border-radius:14px;
                padding:16px 18px;font-size:12px;color:#6b6560;line-height:1.9;">
      <div><strong style="color:#1a1a2e">What earns points:</strong></div>
      <div>School type &nbsp;+20 &nbsp;|&nbsp; Parent &nbsp;+10</div>
      <div>School size (1000+) &nbsp;+20</div>
      <div>Budget ₹3000+ &nbsp;+15</div>
      <div>Demo request &nbsp;+25</div>
      <div>Sweet-spot age (8–13) &nbsp;+15</div>
      <div>Coding/competitive goal &nbsp;+10</div>
      <div>Valid email + phone &nbsp;+5 each</div>
      <br>
      <span class="badge hot">🔥 70-100</span> Call within 1hr<br>
      <span class="badge warm">🟠 45-69</span> Same-day follow-up<br>
      <span class="badge cool">🔵 0-44</span> Email nurture
    </div>""", unsafe_allow_html=True)


def _program(lead: dict) -> str:
    if lead.get("type") == "School":
        return "SmartTech for Schools"
    goals = lead.get("goals", "")
    age   = lead.get("child_age", "")
    if "Coding" in goals:       return "SmartTech / YPDP"
    if "Competitive" in goals:  return "HOTS Program"
    if "thinking" in goals.lower(): return "HOTS Program"
    if age == "5–7 years":      return "WizBlock Basics"
    return "HOTS / SmartTech"

import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
import time

# 1. Setup Connection
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="Hybrid-45 Pro", page_icon="none", layout="wide")

# --- UI STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa !important; }
    h1, h2, h3, p, span, label { color: #2d3436 !important; font-family: 'Inter', sans-serif; }
    div.stButton > button {
        background-color: #4834d4 !important;
        color: #ffffff !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 0.8rem !important;
        font-weight: 700 !important;
        width: 100% !important;
        text-transform: uppercase;
    }
    .goal-card {
        background: #ffffff;
        border: 1px solid #e1e8ed;
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.02);
    }
    </style>
    """, unsafe_allow_html=True)

# --- DATA ENGINE ---
@st.cache_data(ttl=2)
def load_data():
    try:
        res = supabase.table("gym_logs").select("*").order("created_at", desc=True).execute()
        data = pd.DataFrame(res.data) if res.data else pd.DataFrame()
        if not data.empty:
            data['created_at'] = pd.to_datetime(data['created_at'])
            data['vol'] = data['weight'] * data['reps']
            data['e1rm'] = round(data['weight'] / (1.0278 - (0.0278 * data['reps'])), 1)
        return data
    except:
        return pd.DataFrame()

df = load_data()

st.title("Hybrid-45 Performance")

# --- TOP WIDGETS ---
if not df.empty:
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown('<div class="goal-card">', unsafe_allow_html=True)
        today_vol = df[df['created_at'].dt.date == datetime.now().date()]['vol'].sum()
        st.metric("Session Volume", f"{int(today_vol)}kg")
        st.progress(min(float(today_vol) / 5000.0, 1.0))
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="goal-card">', unsafe_allow_html=True)
        st.metric("Peak Strength", f"{df['e1rm'].max()}")
        st.markdown('</div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="goal-card">', unsafe_allow_html=True)
        st.metric("Total Sessions", len(df['created_at'].dt.date.unique()))
        st.markdown('</div>', unsafe_allow_html=True)

# --- TABS ---
t_log, t_sesh, t_lab, t_hall = st.tabs(["LOG", "ANALYSIS", "LAB", "HALL"])

with t_log:
    with st.form("gym_form", clear_on_submit=True):
        st.subheader("Entry")
        exs = ["DB Bench Press", "Hack Squat", "Lat Pulldown", "Lateral Raises", "Tricep Push Down", "Seated Cable Row", "Leg Press", "Bicep Curls", "Pull Ups", "Face Pulls", "Machine Crunch"]
        if not df.empty:
            exs = sorted(list(set(exs + df['exercise'].unique().tolist())))
        ex = st.selectbox("Exercise", exs)
        cw, cr = st.columns(2)
        with cw: wt = st.number_input("Weight (kg)", min_value=0.0, step=2.5)
        with cr: rp = st.number_input("Reps", min_value=0, step=1)
        note = st.text_area("Notes", placeholder="Seat Pos...")
        if st.form_submit_button("SAVE SET"):
            payload = {"exercise": ex, "weight": wt, "reps": rp, "notes": note}
            supabase.table("gym_logs").insert(payload).execute()
            st.cache_data.clear()
            st.rerun()
    if st.button("START 90s REST"):
        ph = st.empty()
        for i in range(90, 0, -1):
            ph.metric("REMAINING", f"{i}s")
            time.sleep(1)
        st.success("REST DONE")

with t_sesh:
    if not df.empty:
        today_dt = datetime.now().date()
        today_df = df[df['created_at'].dt.date == today_dt]
        if not today_df.empty:
            st.subheader("Today vs Last")
            for item in sorted(today_df['exercise'].unique()):
                past = df[(df['exercise'] == item) & (df['created_at'].dt.date < today_dt)].head(1)
                curr = today_df[today_df['exercise'] == item].head(1)
                with st.expander(item, expanded=True):
                    sc1, sc2 = st.columns(2)
                    sc1.metric("Today", f"{curr.iloc[0]['weight']}kg")
                    if not past.empty:
                        d = curr.iloc[0]['weight'] - past.iloc[0]['weight']
                        sc2.metric("Last", f"{past.iloc[0]['weight']}kg", delta=f"{d}kg")
        else:
            st.subheader("Last Session")
            last_dt = df['created_at'].dt.date.iloc[0]
            last_df = df[df['created_at'].dt.date == last_dt]
            st.dataframe(last_df[['exercise', 'weight', 'reps', 'notes']], hide_index=True)
    else:
        st.info("Log a set to start.")

with t_lab:
    if not df.empty:
        sel = st.selectbox("Analysis", sorted(df['exercise'].unique()))
        h = df[df['exercise'] == sel].sort_values('created_at').tail(10)
        st.line_chart(h.set_index('created_at')[['weight', 'e1rm']], color=["#4834d4", "#686de0"])
        st.bar_chart(h.set_index('created_at')['vol'], color="#4834d4")

with t_hall:
    if not df.empty:
        prs = df.sort_values('weight', ascending=False).drop_duplicates('exercise')
        st.dataframe(prs[['exercise', 'weight', 'reps', 'e1rm']].reset_index(drop=True), use_container_width=True)
        if st.button("DELETE LAST"):
            l_id = df.iloc[0]['id']
            supabase.table("gym_logs").delete().eq("id", l_id).execute()
            st.cache_data.clear()
            st.rerun()
            

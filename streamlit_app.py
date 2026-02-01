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

# --- MINIMALIST MODERN UI STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa !important; }
    h1, h2, h3, p, span, label { 
        color: #2d3436 !important; 
        font-family: 'Inter', -apple-system, sans-serif; 
    }
    div.stButton > button {
        background-color: #4834d4 !important;
        color: #ffffff !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 0.8rem !important;
        font-weight: 700 !important;
        width: 100% !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .goal-card {
        background: #ffffff;
        border: 1px solid #e1e8ed;
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.02);
    }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #ffffff;
        border: 1px solid #e1e8ed;
        border-radius: 8px;
        color: #636e72 !important;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        color: #4834d4 !important;
        border-bottom: 3px solid #4834d4 !important;
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
            # Brzycki 1RM formula
            data['e1rm'] = round(data['weight'] / (1.0278 - (0.0278 * data['reps'])), 1)
        return data
    except: return pd.DataFrame()

df = load_data()

# --- TOP LEVEL WIDGETS ---
st.title("Hybrid-45 Performance")

if not df.empty:
    col_w1, col_w2, col_w3 = st.columns(3)
    with col_w1:
        st.markdown('<div class="goal-card">', unsafe_allow_html=True)
        today_vol = df[df['created_at'].dt.date == datetime.now().date()]['vol'].sum()
        st.metric("Session Volume", f"{int(today_vol)}kg")
        st.progress(min(today_vol / 5000, 1.0))
        st.markdown('</div>', unsafe_allow_html=True)
    with col_w2:
        st.markdown('<div class="goal-card">', unsafe_allow_html=True)
        st.metric("Peak Strength", f"{df['e1rm'].max()}")
        st.markdown('</div>', unsafe_allow_html=True)
    with col_w3:
        st.markdown('<div class="goal-card">', unsafe_allow_html=True)
        st.metric("Total Sessions", len(df['created_at'].dt.date.unique()))
        st.markdown('</div>', unsafe_allow_html=True)

# --- NAVIGATION TABS ---
t_log, t_sesh, t_lab, t_hall = st.tabs(["LOG", "ANALYSIS", "LAB", "HALL"])

# --- TAB 1: LOGGING ---
with t_log:
    with st.form("gym_form", clear_on_submit=True):
        st.subheader("Entry")
        exercises = ["DB Bench Press", "Hack Squat", "Lat Pulldown", "Lateral Raises", "Tricep Push Down", "Seated Cable Row", "Leg Press", "Bicep Curls", "Pull Ups", "Face Pulls", "Machine Crunch"]
        if not df.empty:
            exercises = sorted(list(set(exercises + df['exercise'].unique().tolist())))
        
        ex = st.selectbox("Exercise", exercises)
        c1, c2 = st.columns(2)
        with c1: wt = st.number_input("Weight (kg)", step=2.5)
        with c2: rp = st.number_input("Reps", step=1)
        note = st.text_area("Notes", placeholder="Seat Position, Tempo...")
        
        if st.form_submit_button("SAVE SET"):
            payload = {"exercise": ex, "weight": wt, "reps": rp, "notes": note}
            supabase.table("gym_logs").insert(payload).execute()
            st.cache_data.clear()
            st.rerun()

    st.divider()
    if st.button("START 90s REST"):
        ph = st.empty()
        for i in range(90, 0, -1):
            ph.metric("REMAINING", f"{i}s")
            time.sleep(1)
        st.success("REST COMPLETED")

# --- TAB 2: ANALYSIS (Always Persistent) ---
with t_sesh:
    if not df.empty:
        today_date = datetime.now().date()
        today_df = df[df['created_at'].dt.date == today_date]
        
        if not today_df.empty:
            st.subheader("Current Session vs Previous")
            for item in sorted(today_df['exercise'].
                               

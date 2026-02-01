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
    except Exception:
        return pd.DataFrame()

df = load_data()

# --- TOP LEVEL WIDGETS ---
st.title("Hybrid-45 Performance")

if not df.empty:
    col_w1, col_w2, col_w3 = st.columns(3)
    with col_w1:
        st.markdown('<div class="goal-card">', unsafe_allow_html=True)
        today_vol = df[df['created_at'].dt.date == datetime.now().date()]['vol'].sum()
        st.metric("Session Volume", f"{int(today_vol)}kg")
        st.progress(min(float(today_vol) / 5000.0, 1.0))
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
            existing_ex = sorted(df['exercise'].unique().tolist())
            exercises = sorted(list(set(exercises + existing_ex)))
        
        ex = st.selectbox("Exercise", exercises)
        c1, c2 = st.columns(2)
        with c1: wt = st.number_input("Weight (kg)", min_value=0.0, step=2.5)
        with c2: rp = st.number_input("Reps", min_value=0, step=1)
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

# --- TAB 2: ANALYSIS ---
with t_sesh:
    if not df.empty:
        today_date = datetime.now().date()
        today_df = df[df['created_at'].dt.date == today_date]
        
        if not today_df.empty:
            st.subheader("Current Session vs Previous")
            unique_today = sorted(today_df['exercise'].unique())
            for item in unique_today:
                past = df[(df['exercise'] == item) & (df['created_at'].dt.date < today_date)].head(1)
                curr = today_df[today_df['exercise'] == item].head(1)
                with st.expander(item, expanded=True):
                    sc1, sc2 = st.columns(2)
                    sc1.metric("Today", f"{curr.iloc[0]['weight']}kg")
                    if not past.empty:
                        p_wt = past.iloc[0]['weight']
                        diff = curr.iloc[0]['weight'] - p_wt
                        sc2.metric("Last Time", f"{p_wt}kg", delta=f"{diff}kg")
                    else:
                        st.info("New movement for today!")
        else:
            st.subheader("Last Session Overview")
            last_date = df['created_at'].dt.date.iloc[0]
            last_sesh = df[df['created_at'].dt.date == last_date]
            st.info(f"Summary from {last_date.strftime('%d %b')}")
            st.dataframe(last_sesh[['exercise', 'weight', 'reps', 'notes']], hide_index=True, use_container_width=True)
    else:
        st.info("Log your first set to unlock data analysis.")

# --- TAB 3: LAB ---
with t_lab:
    if not df.

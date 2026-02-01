import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
import time

# 1. Initialize Supabase
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="H-45 DATA PRO", page_icon="📊", layout="wide")

# CUSTOM CSS: HIGH CONTRAST & MOBILE OPTIMIZATION
st.markdown("""
    <style>
    .stApp { background-color: #05070a !important; }
    h1, h2, h3, p, span, label, .stMarkdown { color: #FFFFFF !important; }
    
    /* STARK WHITE BUTTON TEXT */
    .stButton>button {
        background-color: #ff4b4b !important;
        color: white !important;
        font-weight: 800 !important;
        border: none !important;
        text-transform: uppercase;
    }
    
    /* METRIC CARDS */
    [data-testid="stMetricValue"] { color: #FFD700 !important; font-weight: 800; }
    .stMetric { background: #161b22 !important; border: 1px solid #30363d !important; padding: 15px; border-radius: 15px; }
    
    /* TABS STYLING */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #161b22;
        border-radius: 5px 5px 0px 0px;
        color: white !important;
        padding: 10px 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- DATA ENGINE ---
@st.cache_data(ttl=2)
def load_data():
    try:
        response = supabase.table("gym_logs").select("*").order("created_at", desc=True).execute()
        df = pd.DataFrame(response.data) if response.data else pd.DataFrame()
        if not df.empty:
            df['created_at'] = pd.to_datetime(df['created_at'])
            # Calc Estimated 1RM: Weight * (1 + Reps/30)
            df['e1rm'] = round(df['weight'] * (1 + df['reps'] / 30), 1)
            df['volume'] = df['weight'] * df['reps']
        return df
    except: return pd.DataFrame()

full_df = load_data()

st.title("⚡ HYBRID-45 DATA PRO")

# --- TABS INTERFACE ---
tab_log, tab_session, tab_lab, tab_history = st.tabs(["⚡ LOG", "📊 SESSION", "📈 LAB", "🏆 PRs"])

# --- TAB 1: LOGGING ---
with tab_log:
    with st.form("entry_form", clear_on_submit=True):
        ex_list = ["Hack Squat", "DB Bench Press", "Lat Pulldown", "Lateral Raises", "Tricep Push Down", "Seated Cable Row", "Leg Press", "Bicep Curls", "Pull Ups", "Face Pulls", "Machine Crunch"]
        if not full_df.empty:
            ex_list = sorted(list(set(ex_list + full_df['exercise'].unique().tolist())))
        
        ex_choice = st.selectbox("Exercise", ex_list)
        c1, c2 = st.columns(2)
        with c1: wt = st.number_input("Weight (kg)", step=2.5)
        with c2: reps = st.number_input("Reps", step=1)
        
        diff = st.select_slider("Intensity", options=["Easy", "Mod", "Hard", "Fail"])
        notes = st.text_area("Notes (Seat, Tempo)", placeholder="Pos 3, 3s descent...")
        
        if st.form_submit_button("SAVE SET 🚀"):
            data = {"exercise": ex_choice, "weight": wt, "reps": reps, "difficulty": diff, "notes": notes}
            supabase.table("gym_logs").insert(data).execute()
            st.cache_data.clear()
            st.rerun()

# --- TAB 2: SESSION COMPARISON ---
with tab_session:
    if not full_df.empty:
        today = datetime.now().date()
        today_data = full_df[full_df['created_at'].dt.date == today]
        
        if not today_data.empty:
            st.subheader("🔥 Current Session Progress")
            col1, col2 = st.columns(2)
            col1.metric("Current Vol", f"{int(today_data['volume'].sum())} kg")
            col2.metric("Sets Done", len(today_data))
            
            st.markdown("### Head-to-Head (Today vs Last)")
            for ex

import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
import time

# 1. Initialize Supabase
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="H-45 COMMAND", page_icon="⚡", layout="wide")

# --- FORCED DARK THEME & HIGH CONTRAST CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #05070a !important; }
    h1, h2, h3, p, span, label, .stMarkdown { color: #FFFFFF !important; }
    
    /* BUTTONS: Forced white text on red background */
    div.stButton > button:first-child {
        background-color: #ff4b4b !important;
        color: white !important;
        font-weight: 800 !important;
        border: none !important;
        border-radius: 10px;
        width: 100%;
        height: 3.5em;
        text-transform: uppercase;
    }
    
    /* METRIC CARDS: Gold numbers for max visibility */
    [data-testid="stMetricValue"] { color: #FFD700 !important; font-weight: 800; font-size: 2rem; }
    [data-testid="stMetricLabel"] { color: #E0E0E0 !important; }
    .stMetric { 
        background: #161b22 !important; 
        border: 1px solid #30363d !important; 
        padding: 15px; 
        border-radius: 15px; 
    }
    
    /* TABS: Clean navigation */
    .stTabs [data-baseweb="tab-list"] { background-color: transparent; }
    .stTabs [data-baseweb="tab"] { color: #888 !important; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { color: #fff !important; border-bottom-color: #ff4b4b !important; }
    
    /* INPUT BOXES */
    input, select, textarea { background-color: #0d1117 !important; color: white !important; border: 1px solid #30363d !important; }
    </style>
    """, unsafe_allow_html=True)

# --- DATA ENGINE ---
@st.cache_data(ttl=2)
def load_all_data():
    try:
        response = supabase.table("gym_logs").select("*").order("created_at", desc=True).execute()
        df = pd.DataFrame(response.data) if response.data else pd.DataFrame()
        if not df.empty:
            df['created_at'] = pd.to_datetime(df['created_at'])
            df['volume'] = df['weight'] * df['reps']
            # Brzycki 1RM Estimate: Weight / (1.0278 - 0.0278 * Reps)
            df['e1rm'] = round(df['weight'] / (1.0278 - (0.0278 * df['reps'])), 1)
        return df
    except:
        return pd.DataFrame()

full_df = load_all_data()

# --- EXERCISE LIST CONFIG ---
base_list = ["DB Bench Press", "Hack Squat", "Lat Pulldown", "Lateral Raises", "Tricep Push Down", "Seated Cable Row", "Leg Press", "Bicep Curls", "Pull Ups", "Face Pulls", "Machine Crunch"]
if not full_df.empty:
    logged_list = full_df['exercise'].unique().tolist()
    final_exercises = sorted(list(set(base_list + logged_list)))
else:
    final_exercises = sorted(base_list)

st.title("⚡ HYBRID-45 COMMAND")

# --- NAVIGATION ---
tab_log, tab_session, tab_lab, tab_history = st.tabs(["📝 LOG", "📊 SESSION", "📈 LAB", "🏆 HALL OF FAME"])

# --- TAB 1: LOGGING ---
with tab_log:
    with st.form("entry_form", clear_on_submit=True):
        ex = st.selectbox("Exercise", final_exercises)
        c1, c2 = st.columns(2)
        with c1: wt = st.number_input("Weight (kg)", min_value=0.0, step=2.5)
        with c2: reps = st.number_input("Reps", min_value=0, step=1)
        
        diff = st.select_slider("Intensity", options=["Easy", "Moderate", "Hard", "Failure"])
        notes = st.text_area("Notes (Seat
        

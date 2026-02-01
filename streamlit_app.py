import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
import time

# 1. Initialize Supabase
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="H-45 COMMAND", page_icon="💪", layout="wide")

# FORCED HIGH-CONTRAST DARK THEME + BUTTON FIXES
st.markdown("""
    <style>
    .stApp { background-color: #05070a !important; }
    h1, h2, h3, p, span, label { color: #FFFFFF !important; }
    
    /* FIX BUTTON VISIBILITY */
    .stButton>button {
        background-color: #ff4b4b !important;
        color: white !important;
        font-weight: bold !important;
        border: none !important;
        width: 100%;
    }
    .stButton>button:active, .stButton>button:focus {
        color: white !important;
        background-color: #cc0000 !important;
    }

    /* METRIC CARDS */
    [data-testid="stMetricValue"] { color: #FFD700 !important; font-weight: 800; }
    .stMetric { background: #161b22 !important; border: 1px solid #30363d !important; padding: 10px; border-radius: 12px; }
    
    /* TABLE STYLING */
    [data-testid="stTable"] { background-color: #161b22; color: white; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- DATA LOADING ---
@st.cache_data(ttl=2)
def load_data():
    try:
        response = supabase.table("gym_logs").select("*").order("created_at", desc=True).execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except:
        return pd.DataFrame()

full_df = load_data()

st.title("💪 H-45 COMMAND")

# --- TOP SKILL: PERSONAL RECORDS ---
if not full_df.empty:
    st.subheader("🏆 Personal Records (PRs)")
    # Find max weight for each exercise
    pr_df = full_df.groupby('exercise')['weight'].max().reset_index()
    pr_cols = st.columns(len(pr_df.head(4))) # Show top 4
    for i, col in enumerate(pr_cols):
        if i < len(pr_df):
            col.metric(pr_df.iloc[i]['exercise'], f"{pr_df.iloc[i]['weight']}kg")

# --- LOGGING FORM ---
with st.container():
    st.subheader("🏋️ Log Next Set")
    with st.form("entry_form", clear_on_submit=True):
        ex_list = ["Hack Squat", "DB Bench Press", "Lat Pulldown", "Lateral Raises", "Tricep Push Down", "Seated Cable Row", "Leg Press", "Bicep Curls", "Pull Ups", "Face Pulls", "Machine Crunch"]
        
        # Merge logged exercises for dynamic dropdown
        if not full_df.empty:
            ex_list = sorted(list(set(ex_list + full_df['exercise'].unique().tolist())))

        ex_choice = st.selectbox("Exercise", ex_list)
        c1, c2, c3 = st.columns(3)
        with c1: wt = st.number_input("Weight (kg)", step=2.5)
        with c2: reps = st.number_input("Reps", step=1)
        with c3: diff = st.select_slider("Intensity", options=["Easy", "Mod", "Hard", "Fail"])
        
        notes = st.text_area("Notes (Seat, Tempo, etc.)", placeholder="Seat pos 3...")
        
        if st.form_submit_button("SAVE TO DATABASE 🚀"):
            data = {"exercise": ex_choice, "weight": wt, "reps": reps, "difficulty": diff, "notes": notes}
            supabase.table("gym_logs").insert(data).execute()
            st.cache_data.clear()
            st.rerun()

# --- DUPLICATE PREVENTION: RECENT HISTORY ---
st.divider()
st.subheader("🕒 Last 5 Sets (Prevention View)")
if not full_df.empty:
    # We only show the most relevant columns for mobile glance
    recent_view = full_df[['exercise', 'weight', 'reps', 'notes']].head(5)
    st.table(recent_view)
else:
    st.info("No sets logged yet.")

# --- PROGRESS MONITORING ---
if not full_df.empty:
    st.divider()
    view_ex = st.selectbox("🔍 Analysis Mode", sorted(full_df['exercise'].unique()))
    
    ex_history = full_df[full_df['exercise'] == view_ex].copy()
    ex_history['date'] = pd.to_datetime(ex_history['created_at'])
    
    # Advanced Metric: Volume Trend
    ex_history['volume'] = ex_history['weight'] * ex_history['reps']
    
    t1, t2 = st.tabs(["📈 Weight Graph", "📊 Volume Progress"])
    with t1:
        st.area_chart(ex_history.set_index('date')['weight'], color="#ff4b4b")
    with t2:
        st.bar_chart(ex_history.set_index('date')['volume'], color="#FFD700")

    if st.button("🗑️ Undo Last Mistake"):
        last_id = full_df.iloc[0]['id']
        supabase.table("gym_logs").delete().eq("id", last_id).execute()
        st.cache_data.clear()
        st.rerun()
        

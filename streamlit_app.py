import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
import time

# 1. Initialize Supabase
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="Hybrid-45 PRO", page_icon="⚡", layout="wide")

# FORCED HIGH-CONTRAST DARK THEME (Overrides Browser Settings)
st.markdown("""
    <style>
    /* Force background to be dark */
    .stApp {
        background-color: #05070a !important;
    }
    
    /* Force ALL text to be stark white */
    h1, h2, h3, p, span, label, .stMarkdown {
        color: #FFFFFF !important;
    }

    /* Metric Cards Styling */
    [data-testid="stMetricValue"] {
        color: #FFD700 !important; /* Gold for numbers */
        font-weight: 800 !important;
    }
    
    [data-testid="stMetricLabel"] {
        color: #FFFFFF !important;
        font-size: 1.1rem !important;
    }

    .stMetric {
        background: #161b22 !important;
        border: 2px solid #30363d !important;
        padding: 20px;
        border-radius: 12px;
    }

    /* Make buttons and inputs visible */
    .stButton>button {
        background-color: #ff4b4b !important;
        color: white !important;
        border-radius: 8px;
    }
    
    input, select, textarea {
        background-color: #0d1117 !important;
        color: white !important;
        border: 1px solid #30363d !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("⚡ Hybrid-45 PRO")

# --- DATA LOADING ---
response = supabase.table("gym_logs").select("*").order("created_at", desc=True).execute()
full_df = pd.DataFrame(response.data) if response.data else pd.DataFrame()

# --- WORKOUT DEFINITIONS ---
ex_list = {
    "A: Foundation": ["Hack Squat (Moderate)", "DB Bench Press", "Lat Pulldowns", "Lateral Raises", "Tricep Rope Pushdown"],
    "B: Hypertrophy": ["Incline Machine Press", "Seated Cable Row", "Leg Press (High Foot)", "DB Bicep Curls", "Plank"],
    "C: Peak Intensity": ["Hack Squat (Intensity)", "Chest Fly Machine", "Pull-Ups / Assisted", "Face Pulls", "Overhead Tricep Extension"]
}

# --- LOGGING FORM ---
with st.container():
    st.subheader("➕ LOG NEXT SET")
    with st.form("entry_form", clear_on_submit=True):
        day_type = st.radio("Workout Day", list(ex_list.keys()), horizontal=True)
        ex_choice = st.selectbox("Select Exercise", ex_list[day_type])
        
        c1, c2, c3 = st.columns(3)
        with c1: wt = st.number_input("Weight (kg)", step=2.5)
        with c2: reps = st.number_input("Reps", step=1)
        with c3: diff = st.select_slider("Intensity", options=["Easy", "Mod", "Hard", "Fail"])
        
        if st.form_submit_button("SAVE SET 🚀"):
            data = {"exercise": ex_choice, "weight": wt, "reps": reps, "difficulty": diff, "workout_day": day_type}
            supabase.table("gym_logs").insert(data).execute()
            st.rerun()

# --- COMPARISON DASHBOARD ---
if not full_df.empty:
    st.divider()
    selected_ex = st.selectbox("🔍 REVIEW PROGRESS", sorted(full_df['exercise'].unique()))
    
    history = full_df[full_df['exercise'] == selected_ex].head(2)
    
    if not history.empty:
        col1, col2 = st.columns(2)
        with col1:
            row1 = history.iloc[0]
            st.metric("LATEST WEIGHT", f"{row1['weight']} kg")
            st.metric("LATEST REPS", f"{row1['reps']}")
        
        with col2:
            if len(history) > 1:
                row2 = history.iloc[1]
                w_delta = float(row1['weight'] - row2['weight'])
                st.metric("PREVIOUS WEIGHT", f"{row2['weight']} kg", delta=f"{w_delta} kg")
                st.metric("PREVIOUS REPS", f"{row2['reps']}", delta=int(row1['reps'] - row2['reps']))
            else:
                st.info("Log another session for comparison.")

    # --- EXTRA SKILLS: DELETE & REST ---
    st.divider()
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("❌ Delete Last Entry"):
            last_id = full_df.iloc[0]['id']
            supabase.table("gym_logs").delete().eq("id", last_id).execute()
            st.warning("Last entry deleted.")
            time.sleep(1)
            st.rerun()
            
    with col_b:
        if st.button("⏲️ 90s Rest Timer"):
            t = st.empty()
            for i in range(90, 0, -1):
                t.metric("RESTING...", f"{i}s")
                time.sleep(1)
            st.balloons()

    st.subheader("📈 Weight History")
    chart_data = full_df[full_df['exercise'] == selected_ex].copy()
    chart_data['date'] = pd.to_datetime(chart_data['created_at'])
    st.area_chart(chart_data.set_index('date')['weight'], color="#ff4b4b")

else:
    st.info("No data yet. Log your first set!")
    

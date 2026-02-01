import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime

# Initialize Supabase
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="Hybrid-45 Pro", page_icon="⚡", layout="wide")

# Custom CSS for a cleaner look
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="metric-container"] {
        background-color: #1e2130;
        border: 1px solid #4a4a4a;
        padding: 15px;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("⚡ Hybrid-45 Tracker")

# --- DATA LOADING ---
response = supabase.table("gym_logs").select("*").order("created_at", desc=True).execute()
full_df = pd.DataFrame(response.data) if response.data else pd.DataFrame()

# --- HEADER METRICS ---
if not full_df.empty:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Workouts", len(full_df['workout_day'].unique()))
    with col2:
        total_kg = (full_df['weight'] * full_df['reps']).sum()
        st.metric("Total Lifted", f"{int(total_kg):,} kg")
    with col3:
        last_date = pd.to_datetime(full_df['created_at']).iloc[0].strftime("%d %b")
        st.metric("Last Session", last_date)

# --- LOGGING FORM ---
st.subheader("🏋️ Log New Set")
with st.expander("Open Entry Form", expanded=True):
    with st.form("gym_form", clear_on_submit=True):
        day = st.radio("Workout Day", ["A: Foundation", "B: Hypertrophy", "C: Peak Intensity"], horizontal=True)
        
        ex_list = {
            "A: Foundation": ["Hack Squat", "DB Bench Press", "Lat Pulldowns", "Lateral Raises", "Tricep Rope Pushdown"],
            "B: Hypertrophy": ["Incline Machine Press", "Seated Cable Row", "Leg Press", "DB Bicep Curls", "Plank"],
            "C: Peak Intensity": ["Hack Squat", "Chest Fly Machine", "Pull-Ups", "Face Pulls", "Overhead Tricep Extension"]
        }
        
        ex = st.selectbox("Exercise", ex_list[day])
        
        c1, c2, c3 = st.columns(3)
        with c1: wt = st.number_input("Weight (kg)", step=2.5)
        with c2: reps = st.number_input("Reps", step=1)
        with c3: diff = st.select_slider("Feel", options=["Easy", "Mod", "Hard", "Fail"])
        
        if st.form_submit_button("Save Set 🚀"):
            data = {
                "exercise": ex, "weight": wt, "reps": reps, 
                "difficulty": diff, "workout_day": day
            }
            supabase.table("gym_logs").insert(data).execute()
            st.rerun()

# --- VISUALS ---
if not full_df.empty:
    st.divider()
    st.subheader(f"📈 {ex} Analysis")
    
    # Filter for selected exercise
    chart_data = full_df[full_df['exercise'] == ex].copy()
    chart_data['volume'] = chart_data['weight'] * chart_data['reps']
    chart_data['date'] = pd.to_datetime(chart_data['created_at'])
    
    tab1, tab2 = st.tabs(["Weight Progress", "Volume Progress"])
    
    with tab1:
        st.area_chart(chart_data.set_index('date')['weight'], color="#ff4b4b")
    with tab2:
        st.bar_chart(chart_data.set_index('date')['volume'], color="#29b5e8")

    st.subheader("📋 Recent History")
    st.dataframe(full_df[['created_at', 'exercise', 'weight', 'reps', 'difficulty']], hide_index=True)
    

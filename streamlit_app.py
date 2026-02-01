import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime

# 1. Initialize Supabase
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="Hybrid-45 Gym", page_icon="🏋️", layout="wide")

# Custom Styling
st.markdown("""
    <style>
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #4a4a4a; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏋️ Hybrid-45 Gym Tracker")

# --- DATA LOADING ---
response = supabase.table("gym_logs").select("*").order("created_at", desc=True).execute()
full_df = pd.DataFrame(response.data) if response.data else pd.DataFrame()

# --- LOGGING FORM ---
with st.expander("➕ Log New Set", expanded=True):
    with st.form("entry_form", clear_on_submit=True):
        ex_list = {
            "A: Foundation": ["Hack Squat (Moderate)", "DB Bench Press", "Lat Pulldowns", "Lateral Raises", "Tricep Rope Pushdown"],
            "B: Hypertrophy": ["Incline Machine Press", "Seated Cable Row", "Leg Press (High Foot)", "DB Bicep Curls", "Plank"],
            "C: Peak Intensity": ["Hack Squat (Intensity)", "Chest Fly Machine", "Pull-Ups / Assisted", "Face Pulls", "Overhead Tricep Extension"]
        }
        
        day_type = st.radio("Select Workout", list(ex_list.keys()), horizontal=True)
        ex_choice = st.selectbox("Exercise", ex_list[day_type])
        
        c1, c2, c3 = st.columns(3)
        with c1: wt = st.number_input("Weight (kg)", step=2.5)
        with c2: reps = st.number_input("Reps", step=1)
        with c3: diff = st.select_slider("Intensity", options=["Easy", "Mod", "Hard", "Fail"])
        
        if st.form_submit_button("Save Set 🚀"):
            data = {"exercise": ex_choice, "weight": wt, "reps": reps, "difficulty": diff, "workout_day": day_type}
            supabase.table("gym_logs").insert(data).execute()
            st.rerun()

# --- COMPARISON & CHART DASHBOARD ---
if not full_df.empty:
    st.divider()
    
    # Dropdown to select exercise for comparison
    unique_exercises = sorted(full_df['exercise'].unique())
    selected_ex = st.selectbox("🔍 Compare History For:", unique_exercises)

    # Get last 2 entries for comparison
    compare_df = full_df[full_df['exercise'] == selected_ex].head(2)
    
    if not compare_df.empty:
        col_new, col_old = st.columns(2)
        
        # Latest Workout
        with col_new:
            st.write("### 🥇 Latest Session")
            row1 = compare_df.iloc[0]
            st.metric("Weight", f"{row1['weight']} kg")
            st.metric("Reps", f"{row1['reps']}")
            st.metric("Vol", f"{row1['weight'] * row1['reps']} kg")

        # Previous Workout with Comparison
        with col_old:
            st.write("### 🥈 Previous Session")
            if len(compare_df) > 1:
                row2 = compare_df.iloc[1]
                w_delta = float(row1['weight'] - row2['weight'])
                r_delta = int(row1['reps'] - row2['reps'])
                st.metric("Weight", f"{row2['weight']} kg", delta=f"{w_delta} kg")
                st.metric("Reps", f"{row2['reps']}", delta=f"{r_delta}")
                st.metric("Vol", f"{row2['weight'] * row2['reps']} kg")
            else:
                st.info("Log one more session to see comparison data.")

        # PROGRESSION ALERT (Hybrid-45 Logic)
        if len(compare_df) > 1:
            if row1['weight'] == row2['weight'] and row1['reps'] >= row2['reps']:
                target = round(row1['weight'] * 1.025, 1)
                st.success(f"📈 **Progression Target:** Hit {row1['weight']}kg twice? Try **{target}kg** next!")

    # THE CHART
    chart_data = full_df[full_df['exercise'] == selected_ex].copy()
    chart_data['date'] = pd.to_datetime(chart_data['created_at'])
    st.area_chart(chart_data.set_index('date')['weight'], color="#ff4b4b")
else:
    st.info("No gym data found yet. Log a set above!")
    

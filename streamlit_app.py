import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Hybrid-45 Tracker", page_icon="⚡")
st.title("⚡ Hybrid-45 Progress")

# Connect to Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Read the data - TTL=0 ensures we always get the latest from the sheet
df = conn.read(ttl=0)

# LOG GYM WORKOUT
st.subheader("🏋️ Log Workout")
with st.form("gym_form", clear_on_submit=True):
    workout_type = st.radio("Workout Day", ["A: Foundation", "B: Hypertrophy", "C: Peak Intensity"])
    
    exercise_options = {
        "A: Foundation": ["Hack Squat", "DB Bench Press", "Lat Pulldowns", "Lateral Raises", "Tricep Rope Pushdown"],
        "B: Hypertrophy": ["Incline Machine Press", "Seated Cable Row", "Leg Press", "DB Bicep Curls", "Plank"],
        "C: Peak Intensity": ["Hack Squat", "Chest Fly Machine", "Pull-Ups", "Face Pulls", "Overhead Tricep Extension"]
    }
    
    ex = st.selectbox("Exercise", exercise_options[workout_type])
    
    col1, col2 = st.columns(2)
    with col1:
        wt = st.number_input("Weight (kg)", min_value=0.0, step=2.5)
    with col2:
        reps = st.number_input("Reps", min_value=1, step=1)
        
    diff = st.select_slider("Intensity/Feel", options=["Easy", "Moderate", "Hard", "Failure"])
    
    submitted = st.form_submit_button("Save Set")

if submitted:
    new_entry = pd.DataFrame([{
        "Date": datetime.now().strftime("%Y-%m-%d"),
        "Exercise": ex,
        "Weight": wt,
        "Reps": reps,
        "Difficulty": diff,
        "Time": datetime.now().strftime("%H:%M")
    }])
    
    # NEW SAVE METHOD: Combining dataframes
    updated_df = pd.concat([df, new_entry], ignore_index=True)
    
    # Force the update
    try:
        conn.update(data=updated_df)
        st.success(f"Logged {ex} to Google Sheets!")
        st.balloons()
        st.rerun() # Refresh to show new data
    except Exception as e:
        st.error(f"Save failed. Error: {e}")
        

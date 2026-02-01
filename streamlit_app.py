import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Hybrid-45 Tracker", page_icon="⚡")
st.title("⚡ Hybrid-45 Progress")

# Connect to Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(ttl=0)

# 1. LOG STEPS & ACTIVITY
with st.expander("👟 Log Daily Steps & Cardio", expanded=False):
    daily_steps = st.number_input("Steps Today", min_value=0, step=500)
    activity = st.selectbox("Activity Type", ["Gym", "Cycle Commute", "Active Recovery", "Rest"])
    if st.button("Log Daily Activity"):
        # Logic to save steps could go here or in a separate sheet
        st.success(f"Logged {daily_steps} steps!")

# 2. LOG GYM WORKOUT
st.subheader("🏋️ Log Workout")
with st.form("gym_form", clear_on_submit=True):
    # Exercise List based on your Hybrid-45 Plan
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
    updated_df = pd.concat([df, new_entry], ignore_index=True)
    conn.update(data=updated_df)
    st.balloons()

# 3. DATA & PROGRESS
if not df.empty:
    st.divider()
    # Your 2.5% - 5% increase logic
    hist = df[df['Exercise'] == ex]
    if len(hist) >= 2:
        last_two = hist.tail(2)['Weight'].tolist()
        if last_two[0] == last_two[1]:
            increase = round(wt * 1.025, 1)
            st.warning(f"🎯 **Progression Alert:** You've hit {wt}kg twice. Aim for **{increase}kg** today (2.5% increase)!")

    st.subheader(f"Progress: {ex}")
    st.line_chart(hist.set_index('Date')['Weight'])
    

import streamlit as st
import pandas as pd
from datetime import datetime

# Set up the file for storage
DATA_FILE = "gym_stats.csv"

def load_data():
    try:
        return pd.read_csv(DATA_FILE)
    except FileNotFoundError:
        return pd.DataFrame(columns=["Date", "Exercise", "Weight", "Reps", "Difficulty", "Time"])

st.title("💪 Personal Gainz Tracker")

# --- INPUT SECTION ---
with st.expander("Add New Set", expanded=True):
    exercise = st.selectbox("Exercise", ["Bench Press", "Squat", "Deadlift", "Shoulder Press", "Rows"])
    weight = st.number_input("Weight (kg/lbs)", min_value=0.0, step=2.5)
    reps = st.number_input("Reps", min_value=0, step=1)
    difficulty = st.select_slider("How did it feel?", options=["Easy", "Moderate", "Hard", "Very Hard"])
    workout_time = st.time_input("Workout Time", datetime.now().time())
    
    if st.button("Log Set"):
        new_data = pd.DataFrame([[datetime.now().date(), exercise, weight, reps, difficulty, workout_time]], 
                                columns=["Date", "Exercise", "Weight", "Reps", "Difficulty", "Time"])
        df = load_data()
        df = pd.concat([df, new_data], ignore_index=True)
        df.to_csv(DATA_FILE, index=False)
        st.success("Set Logged!")

# --- SMART PROMPT LOGIC ---
df = load_data()
if not df.empty:
    exercise_history = df[df['Exercise'] == exercise].tail(2)
    
    if len(exercise_history) == 2:
        weights = exercise_history['Weight'].tolist()
        if weights[0] == weights[1]:
            st.warning(f"🚀 Recommendation: You've hit {weights[1]} twice in a row. Time to increase the weight or reps!")

# --- VISUALS ---
st.header("Progress History")
st.dataframe(df.sort_values(by="Date", ascending=False))

# Simple Efficiency Chart
if not df.empty:
    st.subheader("Efficiency: Weight over Time")
    st.line_chart(df[df['Exercise'] == exercise].set_index('Date')['Weight'])
  

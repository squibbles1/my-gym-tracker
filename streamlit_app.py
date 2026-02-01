import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime

# Initialize Supabase
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.title("⚡ Hybrid-45: Supabase Edition")

# --- LOGGING FORM ---
with st.form("gym_form", clear_on_submit=True):
    day = st.radio("Workout Day", ["A: Foundation", "B: Hypertrophy", "C: Peak Intensity"])
    
    # Map exercises to your plan
    ex_list = {
        "A: Foundation": ["Hack Squat", "DB Bench Press", "Lat Pulldowns", "Lateral Raises", "Tricep Rope Pushdown"],
        "B: Hypertrophy": ["Incline Machine Press", "Seated Cable Row", "Leg Press", "DB Bicep Curls", "Plank"],
        "C: Peak Intensity": ["Hack Squat", "Chest Fly Machine", "Pull-Ups", "Face Pulls", "Overhead Tricep Extension"]
    }
    
    ex = st.selectbox("Exercise", ex_list[day])
    wt = st.number_input("Weight (kg)", step=2.5)
    reps = st.number_input("Reps", step=1)
    diff = st.select_slider("Intensity", options=["Easy", "Moderate", "Hard", "Failure"])
    
    if st.form_submit_button("Save to Database"):
        data = {
            "exercise": ex,
            "weight": wt,
            "reps": reps,
            "difficulty": diff,
            "workout_day": day
        }
        # Save to Supabase
        response = supabase.table("gym_logs").insert(data).execute()
        st.success(f"Logged {ex}!")
        st.balloons()

# --- DATA VIEWING ---
st.divider()
st.subheader("Progress History")

# Pull fresh data from Supabase
response = supabase.table("gym_logs").select("*").order("created_at", desc=True).execute()
if response.data:
    full_df = pd.DataFrame(response.data)
    
    # Show chart for current exercise
    chart_df = full_df[full_df['exercise'] == ex]
    if not chart_df.empty:
        st.line_chart(chart_df.set_index('created_at')['weight'])
    
    st.dataframe(full_df)
else:
    st.info("No data logged yet. Let's get to work!")
    

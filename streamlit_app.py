import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Gym Tracker", page_icon="💪")
st.title("🏋️ My Gym Progress")

# Connect to Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Read existing data
df = conn.read(ttl=0)

# Input Section
with st.form("log_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        ex = st.selectbox("Exercise", ["Bench Press", "Squat", "Deadlift", "Shoulder Press", "Rows"])
        wt = st.number_input("Weight (kg)", min_value=0.0, step=2.5)
    with col2:
        reps = st.number_input("Reps", min_value=1, step=1)
        diff = st.select_slider("How did it feel?", options=["Easy", "Moderate", "Hard", "Very Hard"])
    
    submitted = st.form_submit_button("Log Set")

if submitted:
    new_data = pd.DataFrame([{
        "Date": datetime.now().strftime("%Y-%m-%d"),
        "Exercise": ex,
        "Weight": wt,
        "Reps": reps,
        "Difficulty": diff,
        "Time": datetime.now().strftime("%H:%M")
    }])
    
    # Merge and update
    updated_df = pd.concat([df, new_data], ignore_index=True)
    conn.update(data=updated_df)
    st.success(f"Saved {ex} set!")
    st.balloons()

# Smart Prompt: Check for progression
if not df.empty:
    history = df[df['Exercise'] == ex].tail(2)
    if len(history) == 2 and history.iloc[0]['Weight'] == history.iloc[1]['Weight']:
        st.info(f"🚀 You've hit {wt}kg twice in a row. Time to try for a PR!")

# Visualization
st.subheader("Progress Chart")
if not df.empty:
    chart_data = df[df['Exercise'] == ex]
    st.line_chart(chart_data.set_index('Date')['Weight'])

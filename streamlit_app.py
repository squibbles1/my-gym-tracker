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

# CUSTOM CSS FOR HIGH CONTRAST & READABILITY
st.markdown("""
    <style>
    /* Force high-contrast white text */
    [data-testid="stMetricValue"] { color: #FFFFFF !important; font-weight: 800 !important; font-size: 2.2rem !important; }
    [data-testid="stMetricLabel"] { color: #E0E0E0 !important; font-size: 1.1rem !important; }
    h1, h2, h3, p { color: white !important; }
    
    /* Modern Card Look */
    .stMetric {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.2);
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
    }
    
    /* Custom Progress Bar Color */
    .stProgress > div > div > div > div { background-color: #ff4b4b; }
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

# --- SESSION PROGRESS ---
if not full_df.empty:
    today = datetime.now().strftime("%Y-%m-%d")
    today_data = full_df[full_df['created_at'].str.contains(today)]
    completed_count = len(today_data['exercise'].unique())
    progress = min(completed_count / 5, 1.0)
    st.write(f"**Session Progress: {completed_count}/5 Exercises Done**")
    st.progress(progress)

# --- LOGGING FORM ---
with st.expander("➕ LOG NEXT SET", expanded=True):
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

# --- COACHING & COMPARISON ---
if not full_df.empty:
    st.divider()
    selected_ex = st.selectbox("🔍 SELECT EXERCISE TO REVIEW", sorted(full_df['exercise'].unique()))
    
    history = full_df[full_df['exercise'] == selected_ex].head(2)
    
    if not history.empty:
        col1, col2 = st.columns(2)
        
        # Latest Workout (Stark White)
        with col1:
            st.subheader("🥇 Latest Session")
            row1 = history.iloc[0]
            st.metric("Weight", f"{row1['weight']} kg")
            st.metric("Reps", f"{row1['reps']}")
            st.metric("Total Vol", f"{int(row1['weight'] * row1['reps'])} kg")
        
        # Comparison with Arrows
        with col2:
            st.subheader("🥈 Previous Session")
            if len(history) > 1:
                row2 = history.iloc[1]
                w_delta = float(row1['weight'] - row2['weight'])
                r_delta = int(row1['reps'] - row2['reps'])
                st.metric("Weight", f"{row2['weight']} kg", delta=f"{w_delta} kg")
                st.metric("Reps", f"{row2['reps']}", delta=f"{r_delta}")
                st.metric("Total Vol", f"{int(row2['weight'] * row2['reps'])} kg")
            else:
                st.info("Log one more session for comparison data.")

        # AUTOMATED HYBRID-45 COACH
        if len(history) > 1:
            if row1['weight'] == row2['weight']:
                target = round(row1['weight'] * 1.025, 1)
                st.success(f"🎯 **COACH:** You hit {row1['weight']}kg twice. Today's Goal: **{target}kg**")
            elif row1['weight'] > row2['weight']:
                st.info("🔥 **COACH:** New weight record! Focus on maintaining form today.")

    # --- TOOLS & CHARTS ---
    st.divider()
    t1, t2 = st.tabs(["📈 Progress Chart", "⏲️ Rest Timer"])
    
    with t1:
        chart_data = full_df[full_df['exercise'] == selected_ex].copy()
        chart_data['date'] = pd.to_datetime(chart_data['created_at'])
        st.area_chart(chart_data.set_index('date')['weight'], color="#ff4b4b")
        
    with t2:
        if st.button("Start 90s Rest"):
            placeholder = st.empty()
            for i in range(90, 0, -1):
                placeholder.metric("Rest Remaining", f"{i}s")
                time.sleep(1)
            st.balloons()
            st.warning("⏱️ REST OVER: GET TO THE NEXT SET!")

else:
    st.info("Welcome to Hybrid-45! Log your first set above to see your dashboard.")

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

# FORCED HIGH-CONTRAST DARK THEME & BUTTON FIXES
st.markdown("""
    <style>
    .stApp { background-color: #05070a !important; }
    h1, h2, h3, p, span, label, .stMarkdown { color: #FFFFFF !important; }
    
    /* FIX BUTTON VISIBILITY */
    div.stButton > button {
        background-color: #ff4b4b !important;
        color: white !important;
        font-weight: 800 !important;
        border: none !important;
        width: 100% !important;
        text-transform: uppercase;
    }

    /* METRIC CARDS */
    [data-testid="stMetricValue"] { color: #FFD700 !important; font-weight: 800; }
    .stMetric { background: #161b22 !important; border: 1px solid #30363d !important; padding: 15px; border-radius: 12px; }
    
    /* TABS STYLING */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# --- DATA ENGINE ---
@st.cache_data(ttl=2)
def load_data():
    try:
        response = supabase.table("gym_logs").select("*").order("created_at", desc=True).execute()
        df = pd.DataFrame(response.data) if response.data else pd.DataFrame()
        if not df.empty:
            df['created_at'] = pd.to_datetime(df['created_at'])
            # Brzycki 1RM Formula
            df['e1rm'] = round(df['weight'] / (1.0278 - (0.0278 * df['reps'])), 1)
            df['volume'] = df['weight'] * df['reps']
        return df
    except: return pd.DataFrame()

full_df = load_data()

st.title("💪 HYBRID-45 COMMAND")

# --- NAVIGATION TABS ---
tab_log, tab_session, tab_analysis, tab_history = st.tabs(["⚡ LOG SET", "📊 SESSION", "📈 PROGRESS LAB", "🏆 HALL OF FAME"])

# --- TAB 1: LOGGING ---
with tab_log:
    with st.form("entry_form", clear_on_submit=True):
        # The list we use for the dropdown
        exercise_options = ["DB Bench Press", "Hack Squat", "Lat Pulldown", "Lateral Raises", "Tricep Push Down", "Seated Cable Row", "Leg Press", "Bicep Curls", "Pull Ups", "Face Pulls", "Machine Crunch"]
        
        # Merge with any custom ones logged previously
        if not full_df.empty:
            logged_list = full_df['exercise'].unique().tolist()
            exercise_options = sorted(list(set(exercise_options + logged_list)))
        
        ex_choice = st.selectbox("Select Exercise", exercise_options)
        new_ex = st.text_input("OR Add New Exercise Type")
        
        c1, c2 = st.columns(2)
        with c1: wt = st.number_input("Weight (kg)", step=2.5)
        with c2: reps = st.number_input("Reps", step=1)
        
        notes = st.text_area("Notes (Seat Position, Tempo, etc.)", placeholder="e.g. Seat Pos 4, 3s descent...")
        
        # Decide which name to save
        final_ex = new_ex if new_ex else ex_choice
        
        if st.form_submit_button("SAVE TO DATABASE 🚀"):
            data = {
                "exercise": final_ex, 
                "weight": wt, 
                "reps": reps, 
                "notes": notes,
                "workout_day": "Logged" # Fallback to keep DB happy
            }
            supabase.table("gym_logs").insert(data).execute()
            st.cache_data.clear()
            st.rerun()

# --- TAB 2: SESSION SUMMARY (Head-to-Head Comparison) ---
with tab_session:
    if not full_df.empty:
        today = datetime.now().date()
        today_df = full_df[full_df['created_at'].dt.date == today]
        
        if not today_df.empty:
            st.subheader(f"Today's Session: {today.strftime('%d %b')}")
            col1, col2 = st.columns(2)
            col1.metric("Exercises Done", len(today_df['exercise'].unique()))
            col2.metric("Total Volume", f"{int(today_df['volume'].sum())} kg")
            
            st.divider()
            st.markdown("### 🆚 Today vs Last Time")
            for ex in sorted(today_df['exercise'].unique()):
                # Get last set from BEFORE today
                past_set = full_df[(full_df['exercise'] == ex) & (full_df['created_at'].dt.date < today)].head(1)
                curr_set = today_df[today_df['exercise'] == ex].head(1)
                
                with st.expander(f"📌 {ex}", expanded=True):
                    sc1, sc2 = st.columns(2)
                    sc1.write(f"**Today:** {curr_set.iloc[0]['weight']}kg x {curr_set.iloc[0]['reps']}")
                    if not past_set.empty:
                        p_wt = past_set.iloc[0]['weight']
                        delta = curr_set.iloc[0]['weight'] - p_wt
                        sc2.write(f"**Previous:** {p_wt}kg")
                        if delta > 0: 
                            st.success(f"📈 +{delta}kg Increase!")
                        elif delta == 0 and curr_set.iloc[0]['reps'] > past_set.iloc[0]['reps']:
                            st.success(f"🔥 +{curr_set.iloc[0]['reps'] - past_set.iloc[0]['reps']} Reps!")
        else:
            

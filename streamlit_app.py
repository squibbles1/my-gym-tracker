import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
import time

# 1. Initialize Supabase
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="Hybrid-45 ULTRA", page_icon="⚡", layout="wide")

# FORCED HIGH-CONTRAST DARK THEME
st.markdown("""
    <style>
    .stApp { background-color: #05070a !important; }
    h1, h2, h3, p, span, label { color: #FFFFFF !important; }
    [data-testid="stMetricValue"] { color: #FFD700 !important; font-weight: 800; }
    .stMetric { background: #161b22 !important; border: 1px solid #30363d !important; padding: 15px; border-radius: 12px; }
    .stTextArea textarea { background-color: #0d1117 !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# --- DATA LOADING ---
@st.cache_data(ttl=5) # Refresh every 5 seconds
def load_data():
    response = supabase.table("gym_logs").select("*").order("created_at", desc=True).execute()
    return pd.DataFrame(response.data) if response.data else pd.DataFrame()

full_df = load_data()

# --- DYNAMIC EXERCISE LIST ---
# Default list based on your plan
base_exercises = [
    "DB Bench Press", "Hack Squat", "Lat Pulldown", "Lateral Raises", 
    "Tricep Push Down", "Seated Cable Row", "Leg Press", 
    "Bicep Curls", "Pull Ups", "Face Pulls", "Machine Crunch"
]

# Get any custom exercises you've logged in the past
if not full_df.empty:
    logged_exercises = full_df['exercise'].unique().tolist()
    combined_exercises = list(set(base_exercises + logged_exercises))
else:
    combined_exercises = base_exercises
combined_exercises.sort()

st.title("⚡ Hybrid-45 ULTRA")

# --- TODAY'S SUMMARY ---
if not full_df.empty:
    today_str = datetime.now().strftime("%Y-%m-%d")
    today_df = full_df[full_df['created_at'].str.contains(today_str)]
    
    if not today_df.empty:
        st.subheader("📋 Today's Session")
        s1, s2, s3 = st.columns(3)
        with s1: st.metric("Exercises", len(today_df['exercise'].unique()))
        with s2: 
            vol = (today_df['weight'] * today_df['reps']).sum()
            st.metric("Total Vol", f"{int(vol)} kg")
        with s3: st.metric("Sets", len(today_df))
        st.divider()

# --- LOGGING FORM ---
with st.container():
    st.subheader("🏋️ Log Set")
    with st.form("entry_form", clear_on_submit=True):
        col_ex, col_new = st.columns([2,1])
        with col_ex:
            ex_choice = st.selectbox("Exercise", combined_exercises)
        with col_new:
            new_ex = st.text_input("OR Add New Type")

        c1, c2, c3 = st.columns(3)
        with c1: wt = st.number_input("Weight (kg)", step=2.5)
        with c2: reps = st.number_input("Reps", step=1)
        with c3: diff = st.select_slider("Feel", options=["Easy", "Mod", "Hard", "Fail"])
        
        notes = st.text_area("Notes (e.g. Seat Pos 4, slow tempo)", placeholder="Notes...")
        
        # Determine which exercise name to use
        final_ex = new_ex if new_ex else ex_choice

        if st.form_submit_button("SAVE SET 🚀"):
            data = {
                "exercise": final_ex, 
                "weight": wt, 
                "reps": reps, 
                "difficulty": diff, 
                "notes": notes
            }
            supabase.table("gym_logs").insert(data).execute()
            st.cache_data.clear()
            st.rerun()

# --- COMPARISON & HISTORY ---
if not full_df.empty:
    st.divider()
    view_ex = st.selectbox("🔍 View Progress", combined_exercises)
    
    history = full_df[full_df['exercise'] == view_ex].head(2)
    
    if not history.empty:
        col_a, col_b = st.columns(2)
        with col_a:
            r1 = history.iloc[0]
            st.metric("LATEST", f"{r1['weight']}kg x {r1['reps']}")
            if r1['notes']: st.caption(f"📝 {r1['notes']}")
            
        with col_b:
            if len(history) > 1:
                r2 = history.iloc[1]
                st.metric("PREVIOUS", f"{r2['weight']}kg x {r2['reps']}", 
                          delta=f"{float(r1['weight']-r2['weight'])}kg")
                if r2['notes']: st.caption(f"📝 {r2['notes']}")

    # --- TOOLS ---
    tab1, tab2 = st.tabs(["📈 Chart", "🗑️ Manage"])
    with tab1:
        chart_data = full_df[full_df['exercise'] == view_ex].copy()
        chart_data['date'] = pd.to_datetime(chart_data['created_at'])
        st.area_chart(chart_data.set_index('date')['weight'], color="#ff4b4b")
    with tab2:
        if st.button("Delete Last Entry"):
            last_id = full_df.iloc[0]['id']
            supabase.table("gym_logs").delete().eq("id", last_id).execute()
            st.cache_data.clear()
            st.rerun()
            

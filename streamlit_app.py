import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
import time

# 1. Setup Connection
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="H-45 PRO", page_icon="⚡", layout="wide")

# --- UI OVERHAUL: CLEAN, FRESH & MODERN LIGHT THEME ---
st.markdown("""
    <style>
    /* Clean Light Background */
    .stApp { background-color: #f8f9fa !important; }
    
    /* Dark Slate Text for Readability */
    h1, h2, h3, p, span, label, .stMarkdown { 
        color: #2d3436 !important; 
        font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; 
    }

    /* THE BUTTON FIX: Vibrant Indigo with Stark White Text */
    div.stButton > button {
        background-color: #4834d4 !important; /* Professional Indigo */
        color: #ffffff !important;           /* GUARANTEED WHITE TEXT */
        border-radius: 10px !important;
        border: none !important;
        padding: 0.8rem 1rem !important;
        font-weight: 700 !important;
        font-size: 1.1rem !important;
        width: 100% !important;
        box-shadow: 0 4px 12px rgba(72, 52, 212, 0.2) !important;
        transition: all 0.3s ease;
    }
    
    /* Button Hover/Active State */
    div.stButton > button:hover, div.stButton > button:active, div.stButton > button:focus {
        background-color: #3c2bb3 !important;
        color: #ffffff !important;
        box-shadow: 0 2px 6px rgba(72, 52, 212, 0.4) !important;
    }

    /* Modern Card Styling for Metrics */
    [data-testid="stMetric"] {
        background: #ffffff !important;
        border: 1px solid #e1e8ed !important;
        padding: 20px !important;
        border-radius: 16px !important;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05) !important;
    }
    [data-testid="stMetricValue"] { color: #4834d4 !important; font-weight: 800; }

    /* Input Fields styling */
    input, select, textarea {
        background-color: #ffffff !important;
        color: #2d3436 !important;
        border: 1px solid #dcdde1 !important;
        border-radius: 8px !important;
    }
    
    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] { background-color: transparent; gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #ffffff;
        border: 1px solid #e1e8ed;
        border-radius: 8px 8px 0 0;
        color: #636e72 !important;
        padding: 8px 16px;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        color: #4834d4 !important;
        border-bottom: 3px solid #4834d4 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- DATA ENGINE ---
@st.cache_data(ttl=2)
def load_data():
    try:
        res = supabase.table("gym_logs").select("*").order("created_at", desc=True).execute()
        data = pd.DataFrame(res.data) if res.data else pd.DataFrame()
        if not data.empty:
            data['created_at'] = pd.to_datetime(data['created_at'])
            data['vol'] = data['weight'] * data['reps']
            data['e1rm'] = round(data['weight'] / (1.0278 - (0.0278 * data['reps'])), 1)
        return data
    except: return pd.DataFrame()

df = load_data()

# --- HEADER ---
st.title("⚡ Hybrid-45 Tracker")

# --- TOP SUMMARY ---
if not df.empty:
    c1, c2, c3 = st.columns(3)
    with c1: st.metric("Personal Best", f"{df['weight'].max()} kg")
    with c2: 
        today_vol = df[df['created_at'].dt.date == datetime.now().date()]['vol'].sum()
        st.metric("Today's Volume", f"{int(today_vol)} kg")
    with c3:
        total_sessions = len(df['created_at'].dt.date.unique())
        st.metric("Total Sessions", total_sessions)

# --- NAVIGATION ---
t_log, t_sesh, t_lab, t_hall = st.tabs(["📝 LOG SET", "📊 SESSION", "📈 PROGRESS", "🏆 HALL"])

# --- TAB 1: LOGGING ---
with t_log:
    with st.form("gym_form", clear_on_submit=True):
        st.subheader("Add New Set")
        exercises = ["DB Bench Press", "Hack Squat", "Lat Pulldown", "Lateral Raises", "Tricep Push Down", "Seated Cable Row", "Leg Press", "Bicep Curls", "Pull Ups", "Face Pulls", "Machine Crunch"]
        if not df.empty:
            exercises = sorted(list(set(exercises + df['exercise'].unique().tolist())))
        
        ex = st.selectbox("Exercise Name", exercises)
        
        col_w, col_r = st.columns(2)
        with col_w: wt = st.number_input("Weight (kg)", min_value=0.0, step=2.5)
        with col_r: rp = st.number_input("Reps", min_value=0, step=1)
        
        note = st.text_area("Notes", placeholder="Seat Pos 4, Tempo 3-0-1...")
        
        # This button is now hard-coded Indigo Blue with White text
        if st.form_submit_button("SAVE TO CLOUD 🚀"):
            payload = {"exercise": ex, "weight": wt, "reps": rp, "notes": note}
            supabase.table("gym_logs").insert(payload).execute()
            st.cache_data.clear()
            st.rerun()

    st.subheader("🕒 Recent Activity")
    if not df.empty:
        st.dataframe(df[['exercise', 'weight', 'reps', 'notes']].head(5), hide_index=True, use_container_width=True)

# --- TAB 2: SESSION ANALYSIS ---
with t_sesh:
    if not df.empty:
        today_date = datetime.now().date()
        today_df = df[df['created_at'].dt.date == today_date]
        if not today_df.empty:
            st.subheader("Today's Performance vs. Previous")
            for item in sorted(today_df['exercise'].unique()):
                past = df[(df['exercise'] == item) & (df['created_at'].dt.date < today_date)].head(1)
                curr = today_df[today_df['exercise'] == item].head(1)
                with st.expander(f"📌 {item}", expanded=True):
                    sc1, sc2 = st.columns(2)
                    sc1.metric("Today's Weight", f"{curr.iloc[0]['weight']}kg")
                    if not past.empty:
                        diff = curr.iloc[0]['weight'] - past.iloc[0]['weight']
                        sc2.metric("Previous Best", f"{past.iloc[0]['weight']}kg", delta=f"{diff}kg")
        else:
            st.info("Log a set to see your session comparison.")

# --- TAB 3: PROGRESS LAB ---
with t_lab:
    if not df.empty:
        sel_ex = st.selectbox("Choose Exercise", sorted(df['exercise'].unique()))
        h = df[df['exercise'] == sel_ex].sort_values('created_at')
        st.subheader(f"Growth: {sel_ex}")
        
        # Strength Chart
        st.write("Strength Trend (Est. 1RM)")
        st.line_chart(h.set_index('created_at')['e1rm'], color="#4834d4")
        
        # Volume Chart
        st.write("Session Volume (Total kg)")
        st.bar_chart(h.set_index('created_at')['vol'], color="#686de0")

# --- TAB 4: HALL OF FAME ---
with t_hall:
    if not df.empty:
        st.subheader("🏆 Your All-Time PRs")
        prs = df.sort_values('weight', ascending=False).drop_duplicates('exercise')
        st.dataframe(prs[['exercise', 'weight', 'reps', 'e1rm']].reset_index(drop=True), use_container_width=True)
        
        st.divider()
        if st.button("🗑️ DELETE LAST ENTRY"):
            last_id = df.iloc[0]['id']
            supabase.table("gym_logs").delete().eq("id", last_id).execute()
            st.cache_data.clear()
            st.rerun()

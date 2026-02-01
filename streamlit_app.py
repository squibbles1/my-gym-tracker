import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
import time

# 1. Setup Connection
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="H-45 COMMAND", page_icon="⚡", layout="wide")

# --- UI OVERHAUL: STARK CONTRAST ---
st.markdown("""
    <style>
    /* Force Deep Background */
    .stApp { background-color: #0e1117 !important; }
    
    /* Global White Text */
    h1, h2, h3, p, span, label, .stMarkdown { color: #ffffff !important; font-family: 'Inter', sans-serif; }

    /* THE BUTTON FIX: Forced Blue Background & White Text */
    .stButton > button {
        background-color: #1e88e5 !important;
        color: #ffffff !important;
        border-radius: 12px !important;
        border: none !important;
        padding: 0.75rem 1rem !important;
        font-weight: 700 !important;
        font-size: 1.1rem !important;
        width: 100% !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3) !important;
    }
    
    /* Ensure text stays white even when hovered/clicked on Android */
    .stButton > button:hover, .stButton > button:focus, .stButton > button:active {
        color: #ffffff !important;
        background-color: #1565c0 !important;
    }

    /* Metric Glass-Cards */
    [data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 15px;
        border-radius: 15px;
    }
    [data-testid="stMetricValue"] { color: #00e5ff !important; font-weight: 800; }

    /* Hide standard streamlit footers for a cleaner look */
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- DATA ENGINE ---
@st.cache_data(ttl=2)
def load_data():
    try:
        res = supabase.table("gym_logs").select("*").order("created_at", desc=True).execute()
        df = pd.DataFrame(res.data) if res.data else pd.DataFrame()
        if not df.empty:
            df['created_at'] = pd.to_datetime(df['created_at'])
            df['vol'] = df['weight'] * df['reps']
            # Brzycki 1RM Estimate
            df['e1rm'] = round(df['weight'] / (1.0278 - (0.0278 * df['reps'])), 1)
        return df
    except: return pd.DataFrame()

df = load_data()

# --- TOP DASHBOARD ---
st.title("⚡ HYBRID-45")
if not df.empty:
    c1, c2 = st.columns(2)
    with c1: st.metric("Best Lift", f"{df['weight'].max()} kg")
    with c2: 
        today_vol = df[df['created_at'].dt.date == datetime.now().date()]['vol'].sum()
        st.metric("Today's Vol", f"{int(today_vol)} kg")

# --- NAVIGATION ---
t_log, t_sesh, t_lab, t_pr = st.tabs(["📝 LOG", "📊 SESSION", "📈 PROGRESS", "🏆 HALL"])

# --- TAB 1: LOGGING ---
with t_log:
    with st.form("gym_form", clear_on_submit=True):
        exercises = ["DB Bench Press", "Hack Squat", "Lat Pulldown", "Lateral Raises", "Tricep Push Down", "Seated Cable Row", "Leg Press", "Bicep Curls", "Pull Ups", "Face Pulls", "Machine Crunch"]
        if not df.empty:
            exercises = sorted(list(set(exercises + df['exercise'].unique().tolist())))
        
        ex = st.selectbox("Exercise Name", exercises)
        
        col_w, col_r = st.columns(2)
        with col_w: wt = st.number_input("Weight (kg)", min_value=0.0, step=2.5)
        with col_r: rp = st.number_input("Reps", min_value=0, step=1)
        
        note = st.text_area("Notes", placeholder="Seat Pos 4, Tempo 3-0-1...")
        
        # This button text is now hard-coded to stay white
        if st.form_submit_button("SAVE SET 🚀"):
            payload = {"exercise": ex, "weight": wt, "reps": rp, "notes": note}
            supabase.table("gym_logs").insert(payload).execute()
            st.cache_data.clear()
            st.rerun()

    st.subheader("🕒 Recent Activity")
    if not df.empty:
        st.dataframe(df[['exercise', 'weight', 'reps', 'notes']].head(5), hide_index=True)

# --- TAB 2: SESSION COMPARISON ---
with t_sesh:
    if not df.empty:
        today_date = datetime.now().date()
        today_df = df[df['created_at'].dt.date == today_date]
        if not today_df.empty:
            st.subheader("🆚 Today vs Previous")
            for item in sorted(today_df['exercise'].unique()):
                past = df[(df['exercise'] == item) & (df['created_at'].dt.date < today_date)].head(1)
                curr = today_df[today_df['exercise'] == item].head(1)
                with st.expander(f"📌 {item}", expanded=True):
                    sc1, sc2 = st.columns(2)
                    sc1.metric("Today", f"{curr.iloc[0]['weight']}kg")
                    if not past.empty:
                        diff = curr.iloc[0]['weight'] - past.iloc[0]['weight']
                        sc2.metric("Last", f"{past.iloc[0]['weight']}kg", delta=f"{diff}kg")
        else:
            st.info("Log a set to see your session comparison.")

# --- TAB 3: PROGRESS LAB ---
with t_lab:
    if not df.empty:
        sel_ex = st.selectbox("Select Movement", sorted(df['exercise'].unique()))
        h = df[df['exercise'] == sel_ex].sort_values('created_at')
        st.write("#### Strength Growth (Est. 1RM)")
        st.line_chart(h.set_index('created_at')['e1rm'], color="#00e5ff")
        st.write("#### Volume per Set")
        st.bar_chart(h.set_index('created_at')['vol'], color="#1e88e5")

# --- TAB 4: HALL OF FAME ---
with t_pr:
    if not df.empty:
        st.subheader("🏆 Personal Records")
        prs = df.sort_values('weight', ascending=False).drop_duplicates('exercise')
        st.table(prs[['exercise', 'weight', 'reps', 'e1rm']].reset_index(drop=True))
        
        if st.button("🗑️ DELETE LAST ENTRY"):
            last_id = df.iloc[0]['id']
            supabase.table("gym_logs").delete().eq("id", last_id).execute()
            st.cache_data.clear()
            st.rerun()
            

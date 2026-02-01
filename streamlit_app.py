import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
import time

# 1. Setup Connection
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="H-45 COMMAND", page_icon="💪", layout="wide")

# --- MODERN NEON THEME & BUTTON OVERRIDES ---
st.markdown("""
    <style>
    /* Force Dark Background */
    .stApp { background-color: #0a0e14 !important; }
    
    /* Global Text Color */
    h1, h2, h3, p, span, label, .stMarkdown { color: #ffffff !important; }

    /* MODERN BUTTONS: Fixed White Text, No Hover Issues */
    div.stButton > button {
        background-color: #007bff !important; /* Electric Blue */
        color: #ffffff !important;
        font-weight: 700 !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 15px !important;
        width: 100% !important;
        text-transform: uppercase;
        box-shadow: 0px 4px 10px rgba(0, 123, 255, 0.3);
    }
    
    /* Ensure text stays white even when clicked */
    div.stButton > button:hover, div.stButton > button:active, div.stButton > button:focus {
        color: #ffffff !important;
        background-color: #0056b3 !important;
        border: none !important;
    }

    /* Metric Card Modern Look */
    [data-testid="stMetricValue"] { color: #FFD700 !important; font-weight: 800; font-size: 2.5rem !important; }
    .stMetric {
        background: #1c222d !important;
        border: 1px solid #2d3646 !important;
        padding: 20px !important;
        border-radius: 15px !important;
    }

    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] { background-color: transparent; }
    .stTabs [data-baseweb="tab"] { color: #94a3b8 !important; font-weight: 600; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { color: #ffffff !important; border-bottom-color: #007bff !important; }
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
            # Strength Est (1RM)
            df['e1rm'] = round(df['weight'] / (1.0278 - (0.0278 * df['reps'])), 1)
        return df
    except Exception:
        return pd.DataFrame()

f_df = load_data()

st.title("💪 HYBRID-45 COMMAND")

# --- TOP STATS BAR ---
if not f_df.empty:
    m1, m2, m3 = st.columns(3)
    with m1: st.metric("Workouts Logged", len(f_df))
    with m2: 
        total_vol = int(f_df['vol'].sum())
        st.metric("All-Time Volume", f"{total_vol:,}kg")
    with m3:
        best_lift = f_df['weight'].max()
        st.metric("Max Weight", f"{best_lift}kg")

# --- MAIN TABS ---
t_log, t_sesh, t_lab, t_pr = st.tabs(["⚡ LOG SET", "📊 SESSION", "📈 PROGRESS", "🏆 HALL OF FAME"])

# --- TAB 1: LOGGING ---
with t_log:
    with st.form("entry_form", clear_on_submit=True):
        opts = ["Hack Squat", "DB Bench Press", "Lat Pulldown", "Lateral Raises", "Tricep Push Down", "Seated Cable Row", "Leg Press", "Bicep Curls", "Pull Ups", "Face Pulls", "Machine Crunch"]
        if not f_df.empty:
            opts = sorted(list(set(opts + f_df['exercise'].unique().tolist())))
        
        ex = st.selectbox("Exercise", opts)
        
        c1, c2 = st.columns(2)
        with c1: wt = st.number_input("Weight (kg)", step=2.5)
        with c2: rp = st.number_input("Reps", step=1)
        
        note = st.text_area("Notes", placeholder="Seat pos, tempo, tempo...")
        
        if st.form_submit_button("SAVE TO CLOUD 🚀"):
            payload = {"exercise": ex, "weight": wt, "reps": rp, "notes": note}
            supabase.table("gym_logs").insert(payload).execute()
            st.cache_data.clear()
            st.rerun()

# --- TAB 2: SESSION SUMMARY ---
with t_sesh:
    if not f_df.empty:
        today = datetime.now().date()
        t_df = f_df[f_df['created_at'].dt.date == today]
        if not t_df.empty:
            st.subheader(f"Session: {today.strftime('%d %b')}")
            for item in sorted(t_df['exercise'].unique()):
                past = f_df[(f_df['exercise'] == item) & (f_df['created_at'].dt.date < today)].head(1)
                curr = t_df[t_df['exercise'] == item].head(1)
                with st.expander(f"📌 {item}", expanded=True):
                    sc1, sc2 = st.columns(2)
                    sc1.metric("Current", f"{curr.iloc[0]['weight']}kg")
                    if not past.empty:
                        p_wt = past.iloc[0]['weight']
                        diff = curr.iloc[0]['weight'] - p_wt
                        sc2.metric("Last Time", f"{p_wt}kg", delta=f"{diff}kg")
        else:
            st.info("Log a set to see your session comparison.")
    else:
        st.info("No data yet.")

# --- TAB 3: PROGRESS LAB ---
with t_lab:
    if not f_df.empty:
        sel = st.selectbox("Select Exercise", sorted(f_df['exercise'].unique()))
        h = f_df[f_df['exercise'] == sel].sort_values('created_at')
        
        st.write("#### Strength Trend (Est. 1RM)")
        st.line_chart(h.set_index('created_at')['e1rm'], color="#FFD700")
        
        st.write("#### Total Workload (Volume)")
        st.bar_chart(h.set_index('created_at')['vol'], color="#007bff")
    else:
        st.info("Analyze your growth here once you've logged data.")

# --- TAB 4: HALL OF FAME ---
with t_pr:
    if not f_df.empty:
        st.subheader("🏆 Personal Bests")
        prs = f_df.sort_values('weight', ascending=False).drop_duplicates('exercise')
        st.table(prs[['exercise', 'weight', 'reps', 'e1rm']].reset_index(drop=True))
        
        st.divider()
        if st.button("🗑️ DELETE LAST ENTRY"):
            l_id = f_df.iloc[0]['id']
            supabase.table("gym_logs").delete().eq("id", l_id).execute()
            st.cache_data.clear()
            st.rerun()
            

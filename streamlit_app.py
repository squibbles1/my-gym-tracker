import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
import time

# 1. Setup Connection
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="H-45 ULTRA", page_icon="⚡", layout="wide")

# --- PREMIUM MODERN UI STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa !important; }
    
    /* Clean Typography */
    h1, h2, h3, p, span, label { 
        color: #2d3436 !important; 
        font-family: 'Inter', -apple-system, sans-serif; 
    }

    /* THE INDIGO BUTTON: High Contrast & Modern */
    div.stButton > button {
        background-color: #4834d4 !important;
        color: #ffffff !important;
        border-radius: 12px !important;
        border: none !important;
        padding: 1rem !important;
        font-weight: 700 !important;
        width: 100% !important;
        box-shadow: 0 4px 15px rgba(72, 52, 212, 0.2) !important;
    }

    /* GOAL WIDGET STYLE */
    .goal-card {
        background: #ffffff;
        border: 1px solid #e1e8ed;
        padding: 20px;
        border-radius: 20px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
    }

    /* TAB STYLING */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #ffffff;
        border: 1px solid #e1e8ed;
        border-radius: 10px;
        color: #636e72 !important;
        padding: 10px 20px;
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

# --- TOP LEVEL WIDGETS (Goal Tracking) ---
st.title("⚡ Performance Command")

col_w1, col_w2, col_w3 = st.columns(3)
with col_w1:
    st.markdown('<div class="goal-card">', unsafe_allow_html=True)
    st.metric("Session Volume", f"{int(df[df['created_at'].dt.date == datetime.now().date()]['vol'].sum())}kg")
    st.write("Target: 5,000kg")
    st.progress(min(df[df['created_at'].dt.date == datetime.now().date()]['vol'].sum() / 5000, 1.0))
    st.markdown('</div>', unsafe_allow_html=True)

with col_w2:
    st.markdown('<div class="goal-card">', unsafe_allow_html=True)
    total_reps = df['reps'].sum()
    st.metric("Lifetime Reps", f"{int(total_reps):,}")
    st.write("Goal: 10,000")
    st.progress(min(total_reps / 10000, 1.0))
    st.markdown('</div>', unsafe_allow_html=True)

with col_w3:
    st.markdown('<div class="goal-card">', unsafe_allow_html=True)
    st.metric("Strength Score", f"{df['e1rm'].max() if not df.empty else 0}")
    st.write("Peak Performance")
    st.markdown('</div>', unsafe_allow_html=True)

# --- NAVIGATION ---
t_log, t_sesh, t_lab, t_hall = st.tabs(["📝 LOG", "📊 ANALYSIS", "📈 LAB", "🏆 HALL"])

# --- TAB 1: LOGGING ---
with t_log:
    with st.form("gym_form", clear_on_submit=True):
        st.subheader("Add Performance Data")
        exercises = ["DB Bench Press", "Hack Squat", "Lat Pulldown", "Lateral Raises", "Tricep Push Down", "Seated Cable Row", "Leg Press", "Bicep Curls", "Pull Ups", "Face Pulls", "Machine Crunch"]
        if not df.empty:
            exercises = sorted(list(set(exercises + df['exercise'].unique().tolist())))
        
        ex = st.selectbox("Select Exercise", exercises)
        
        c1, c2 = st.columns(2)
        with c1: wt = st.number_input("Weight (kg)", step=2.5)
        with c2: rp = st.number_input("Reps", step=1)
        
        note = st.text_area("Session Notes", placeholder="Seat Pos 4, Tempo 3-0-1...")
        
        if st.form_submit_button("SAVE SET 🚀"):
            payload = {"exercise": ex, "weight": wt, "reps": rp, "notes": note}
            supabase.table("gym_logs").insert(payload).execute()
            st.cache_data.clear()
            st.rerun()

    # REST TIMER WIDGET
    st.divider()
    st.subheader("⏲️ Rest Protocol")
    if st.button("START 90s RECOVERY"):
        ph = st.empty()
        for i in range(90, 0, -1):
            ph.metric("RECOVERING...", f"{i}s")
            time.sleep(1)
        st.balloons()
        st.success("REST OVER: GO AGAIN!")

# --- TAB 3: THE LAB (Interactive Charts) ---
with t_lab:
    if not df.empty:
        sel_ex = st.selectbox("Analyze History", sorted(df['exercise'].unique()))
        h = df[df['exercise'] == sel_ex].sort_values('created_at')
        
        # Interactive Slider for Chart Zoom
        zoom = st.slider("View Last X Sessions", 5, len(h) if len(h) > 5 else 10, 10)
        h_zoom = h.tail(zoom)
        
        st.subheader(f"Insights: {sel_ex}")
        
        # INTERACTIVE LINE CHART
        st.write("Strength Velocity (Est. 1RM)")
        st.line_chart(h_zoom.set_index('created_at')[['weight', 'e1rm']], color=["#4834d4", "#686de0"])
        
        # STYLISH BAR CHART
        st.write("Total Volume Trend")
        st.bar_chart(h_zoom.set_index('created_at')['vol'], color="#4834d4")

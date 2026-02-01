import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime, timedelta
import time

# 1. SETUP & CONFIG
st.set_page_config(page_title="Hybrid-45 Onyx", page_icon="⚡", layout="wide")

url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# --- MODERN CLEAN CSS (Indigo & White) ---
st.markdown("""
    <style>
    /* Global Reset */
    .stApp { background-color: #f8f9fa !important; }
    h1, h2, h3, p, span, label, .stMarkdown { 
        color: #2d3436 !important; 
        font-family: -apple-system, BlinkMacSystemFont, sans-serif !important; 
    }

    /* CARD STYLING */
    .metric-card {
        background: #ffffff;
        border: 1px solid #e1e8ed;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
        text-align: center;
    }

    /* BUTTON STYLING (Simple & Clean) */
    div.stButton > button {
        background-color: #4834d4 !important; /* Indigo */
        color: #ffffff !important;           /* White Text */
        border: none !important;
        border-radius: 8px !important;
        padding: 0.8rem 1rem !important;
        font-weight: 700 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        width: 100% !important;
        transition: all 0.2s;
    }
    div.stButton > button:active { transform: scale(0.98); }

    /* INPUT FIELDS */
    .stSelectbox, .stNumberInput, .stTextArea { margin-bottom: 10px; }
    
    /* PROGRESS BAR */
    .stProgress > div > div > div > div { background-color: #4834d4 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- DATA ENGINE ---
@st.cache_data(ttl=5)
def get_data():
    try:
        res = supabase.table("gym_logs").select("*").order("created_at", desc=True).execute()
        df = pd.DataFrame(res.data) if res.data else pd.DataFrame()
        if not df.empty:
            df['created_at'] = pd.to_datetime(df['created_at'])
            df['date'] = df['created_at'].dt.date
            df['vol'] = df['weight'] * df['reps']
            df['e1rm'] = df['weight'] / (1.0278 - (0.0278 * df['reps']))
        return df
    except: return pd.DataFrame()

df = get_data()

# --- WEEKLY GOAL WIDGET ---
st.title("Hybrid-45 Tracker")

if not df.empty:
    # Calculate current week stats
    today = datetime.now().date()
    start_week = today - timedelta(days=today.weekday()) # Monday
    this_week_df = df[df['date'] >= start_week]
    sessions_this_week = len(this_week_df['date'].unique())
    
    # Display Widgets
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Weekly Goal", f"{sessions_this_week} / 3 Sessions")
        st.progress(min(sessions_this_week / 3.0, 1.0))
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        week_vol = int(this_week_df['vol'].sum())
        st.metric("Weekly Volume", f"{week_vol:,} kg")
        st.markdown('</div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        best_lift = df['weight'].max()
        st.metric("Best Lift", f"{best_lift} kg")
        st.markdown('</div>', unsafe_allow_html=True)

# --- MAIN TABS ---
t_log, t_analytics, t_history = st.tabs(["LOG DATA", "ANALYTICS", "HISTORY"])

# --- TAB 1: SMART LOGGING ---
with t_log:
    st.subheader("New Entry")
    with st.form("log_form", clear_on_submit=True):
        # 1. Exercise Selector
        base_list = ["Hack Squat", "DB Bench Press", "Lat Pulldown", "Lateral Raises", "Tricep Push Down", "Seated Cable Row", "Leg Press", "Bicep Curls", "Pull Ups", "Face Pulls", "Machine Crunch"]
        if not df.empty:
            base_list = sorted(list(set(base_list + df['exercise'].unique().tolist())))
        
        ex = st.selectbox("Select Movement", base_list)
        
        # 2. Smart Suggestion (Last Weight)
        last_stats = "No previous data"
        if not df.empty:
            last_entry = df[df['exercise'] == ex].head(1)
            if not last_entry.empty:
                w = last_entry.iloc[0]['weight']
                r = last_entry.iloc[0]['reps']
                last_stats = f"Last: {w}kg x {r} reps"
        st.caption(f"💡 {last_stats}")

        # 3. Inputs
        c1, c2 = st.columns(2)
        with c1: wt = st.number_input("Weight (kg)", step=2.5, min_value=0.0)
        with c2: rp = st.number_input("Reps", step=1, min_value=0)
        
        note = st.text_area("Notes", placeholder="Seat Position, Tempo...")
        
        if st.form_submit_button("SAVE ENTRY"):
            payload = {"exercise": ex, "weight": wt, "reps": rp, "notes": note}
            supabase.table("gym_logs").insert(payload).execute()
            st.cache_data.clear()
            st.rerun()

    # Recovery Timer (Simple Button)
    st.divider()
    if st.button("START 90s REST TIMER"):
        bar = st.progress(0)
        status = st.empty()
        for i in range(90):
            status.text(f"Recovering... {90-i}s remaining")
            bar.progress((i+1)/90)
            time.sleep(1)
        status.success("READY FOR NEXT SET!")

# --- TAB 2: DEEP ANALYTICS ---
with t_analytics:
    if not df.empty:
        # A. Head-to-Head (Today vs Last)
        today = datetime.now().date()
        today_data = df[df['date'] == today]
        
        st.subheader("Daily Performance")
        if not today_data.empty:
            for x in today_data['exercise'].unique():
                curr = today_data[today_data['exercise'] == x].iloc[0]
                prev = df[(df['exercise'] == x) & (df['date'] < today)].head(1)
                
                with st.expander(f"{x}: {curr['weight']}kg x {curr['reps']}", expanded=True):
                    c_a, c_b = st.columns(2)
                    c_a.metric("Today", f"{curr['weight']}kg")
                    if not prev.empty:
                        diff = curr['weight'] - prev.iloc[0]['weight']
                        c_b.metric("Prev", f"{prev.iloc[0]['weight']}kg", delta=diff)
                    else:
                        c_b.write("First Log")
        else:
            st.info("Log your first set today to see the Head-to-Head comparison.")

        st.divider()
        
        # B. Weekly Volume Trend (Consistency Check)
        st.subheader("Weekly Volume Consistency")
        df['week_start'] = df['created_at'].dt.to_period('W').apply(lambda r: r.start_time)
        weekly_vol = df.groupby('week_start')['vol'].sum()
        st.bar_chart(weekly_vol, color="#4834d4")
        
        # C. Strength Curve
        st.subheader("Strength Progression")
        target_ex = st.selectbox("Analyze Exercise", df['exercise'].unique())
        ex_trend = df[df['exercise'] == target_ex].sort_values('created_at')
        st.line_chart(ex_trend.set_index('created_at')['e1rm'], color="#4834d4")

# --- TAB 3: HISTORY ---
with t_history:
    if not df.empty:
        st.subheader("Logbook")
        st.dataframe(df[['date', 'exercise', 'weight', 'reps', 'notes']], hide_index=True, use_container_width=True)
        
        if st.button("Delete Most Recent Entry"):
            last_id = df.iloc[0]['id']
            supabase.table("gym_logs").delete().eq("id", last_id).execute()
            st.cache_data.clear()
            st.rerun()
        

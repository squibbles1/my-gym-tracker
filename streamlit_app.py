import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime, timedelta
import time

# 1. SETUP
st.set_page_config(page_title="Hybrid-45 Onyx", page_icon="⚡", layout="wide")

# 2. CSS STYLING (Clean & Modern)
onyx_css = """
    <style>
    /* Global Background */
    .stApp { background-color: #f8f9fa; }
    
    /* Fonts & Text */
    h1, h2, h3, h4, p, span, label, div { 
        color: #2d3436; 
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; 
    }

    /* Cards */
    .metric-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #e1e8ed;
        box-shadow: 0 2px 5px rgba(0,0,0,0.03);
        text-align: center;
        margin-bottom: 10px;
    }
    .metric-val { font-size: 1.8rem; font-weight: 800; color: #2d3436; }
    .metric-lbl { font-size: 0.9rem; color: #636e72; text-transform: uppercase; letter-spacing: 0.5px; }

    /* Buttons - Indigo Theme */
    div.stButton > button {
        background-color: #4834d4;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.7rem 1rem;
        font-weight: 700;
        width: 100%;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    div.stButton > button:hover { background-color: #3c2bb3; color: white; }

    /* Radio/Select Styling */
    .stRadio > div { flex-direction: row; gap: 20px; }
    </style>
"""
st.markdown(onyx_css, unsafe_allow_html=True)

# 3. DATABASE CONNECTION
@st.cache_resource
def init_db():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        return None

supabase = init_db()

# 4. DATA LOADER
@st.cache_data(ttl=5)
def get_data():
    if not supabase: return pd.DataFrame()
    try:
        res = supabase.table("gym_logs").select("*").order("created_at", desc=True).execute()
        df = pd.DataFrame(res.data) if res.data else pd.DataFrame()
        if not df.empty:
            df['created_at'] = pd.to_datetime(df['created_at'])
            df['date'] = df['created_at'].dt.date
            df['vol'] = df['weight'] * df['reps']
            # Brzycki 1RM
            df['e1rm'] = df.apply(lambda x: x['weight'] / (1.0278 - (0.0278 * x['reps'])) if x['reps'] < 30 else 0, axis=1)
        return df
    except: return pd.DataFrame()

def card(label, value):
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-lbl">{label}</div>
            <div class="metric-val">{value}</div>
        </div>
    """, unsafe_allow_html=True)

# --- APP START ---
df = get_data()

st.title("Hybrid-45 Onyx")

# --- WEEKLY WIDGET ---
if not df.empty:
    today = datetime.now().date()
    # Find start of week (Monday)
    start_week = today - timedelta(days=today.weekday())
    this_week = df[df['date'] >= start_week]
    
    sessions = len(this_week['date'].unique())
    vol = int(this_week['vol'].sum())
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.caption("Weekly Goal (3 Sessions)")
        st.progress(min(sessions/3.0, 1.0))
        st.write(f"**{sessions} / 3 Completed**")
    with c2:
        card("Weekly Vol", f"{vol:,}")
    with c3:
        best = df['weight'].max()
        card("Best Lift", f"{best}kg")
else:
    st.info("👋 Welcome! Log your first set below.")

# --- NAVIGATION ---
t_log, t_anl, t_hist = st

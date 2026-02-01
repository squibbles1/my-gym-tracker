import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime, timedelta
import time

# 1. SETUP
st.set_page_config(page_title="Hybrid-45 Onyx", page_icon="⚡", layout="wide")

# Connect to Database
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
except:
    st.error("Database connection failed. Check your secrets.")

# 2. CSS STYLING (Separated for safety)
# We define the style in a variable first to avoid syntax errors
onyx_css = """
    <style>
    /* Global Background */
    .stApp { background-color: #f8f9fa; }
    
    /* Fonts & Text */
    h1, h2, h3, p, span, label, div { 
        color: #2d3436; 
        font-family: -apple-system, BlinkMacSystemFont, sans-serif; 
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
    .metric-lbl { font-size: 0.9rem; color: #636e72; text-transform: uppercase; }

    /* Buttons - Indigo Theme */
    div.stButton > button {
        background-color: #4834d4;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.7rem 1rem;
        font-weight: 700;
        width: 100%;
    }
    div.stButton > button:hover { background-color: #3c2bb3; color: white; }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: white;
        border-radius: 6px;
        border: 1px solid #e1e8ed;
        color: #636e72;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: #4834d4;
        color: white;
    }
    </style>
"""
st.markdown(onyx_css, unsafe_allow_html=True)

# 3. HELPER FUNCTIONS
@st.cache_data(ttl=5)
def get_data():
    try:
        res = supabase.table("gym_logs").select("*").order("created_at", desc=True).execute()
        df = pd.DataFrame(res.data) if res.data else pd.DataFrame()
        if not df.empty:
            df['created_at'] = pd.to_datetime(df['created_at'])
            df['date'] = df['created_at'].dt.date
            df['vol'] = df['weight'] * df['reps']
            # Simple 1RM calc
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

# 4. MAIN APP
df = get_data()

st.title("Hybrid-45 Onyx")

# --- WEEKLY WIDGET ---
if not df.empty:
    today = datetime.now().date()
    #
    

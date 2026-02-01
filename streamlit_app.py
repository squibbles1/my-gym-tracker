import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
import time

# 1. Setup Connection
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="Hybrid-45 Pro", page_icon="none", layout="wide")

# --- MINIMALIST MODERN UI STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa !important; }
    h1, h2, h3, p, span, label { 
        color: #2d3436 !important; 
        font-family: 'Inter', -apple-system, sans-serif; 
    }
    div.stButton > button {
        background-color: #4834d4 !important;
        color: #ffffff !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 0.8rem !important;
        font-weight: 700 !important;
        width: 100% !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .goal-card {
        background: #ffffff;
        border: 1px solid #e1e8ed;
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.02);
    }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #ffffff;
        border: 1px solid #e1e8ed;
        border-radius: 8px;
        color: #636e72 !important;
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
            data['created_
            

import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime, timedelta
import time

# 1. SETUP & CONFIGURATION
st.set_page_config(page_title="Hybrid-45 Onyx", page_icon="⚡", layout="wide")

# Connect to Database
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
except:
    st.error("Supabase connection failed. Please check your secrets.")

# --- MODERN CLEAN CSS (Fixes Text Overlay Issues) ---
st.markdown("""
    <style>
    /* 1. Global Background & Fonts */
    .stApp { background-color: #f8f9fa; }
    
    /* Target only specific text elements to avoid breaking icons */
    h1, h2, h3, h4, p, label, .stMarkdown div { 
        color: #2d3436; 
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }

    /* 2. CARD STYLING (For Metrics & Widgets) */
    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #e1e8ed;
        box-shadow: 0 4px 6px rgba(0,0,0,0.04);
        text-align: center;
        margin-bottom: 15px;
    }
    .metric-label { font-size: 0.9rem; color: #636e72; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px; }
    .metric-value { font-size: 2rem; color: #2d3436; font-weight: 800; }
    .metric-sub { font-size: 0.85rem; color: #4834d4; font-weight: 600; }

    /* 3. BUTTON STYLING (Indigo Theme) */
    div.stButton > button {
        background-color: #4834d4;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 1rem;
        font-weight: 700;
        width: 100%;
        transition: all 0.2s;
    }
    div.stButton > button:hover { background-color: #3c2bb3; color: white; }
    div.stButton > button:active { transform: scale(0.98); }

    /* 4. TABS STYLING */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; background-color: transparent; }
    .stTabs [data-baseweb="tab"] {
        background-color: white;
        border-radius: 6px;
        border: 1px solid #e1e8ed;
        color: #636e72;
        padding: 8px 16px;
        font-weight: 600;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: #4834d4;
        color: white
        

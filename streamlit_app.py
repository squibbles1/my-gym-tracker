import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
import time

# 1. Initialize Supabase
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="H-45 COMMAND", page_icon="💪", layout="wide")

# --- CUSTOM CSS: FORCED DARK MODE & HIGH VISIBILITY ---
st.markdown("""
    <style>
    .stApp { background-color: #05070a !important; }
    h1, h2, h3, p, span, label, .stMarkdown { color: #FFFFFF !important; }
    
    /* BUTTONS: Stark white text on red */
    div.stButton > button {
        background-color: #ff4b4b !important;
        color: white !important;
        font-weight: 800 !important;
        border: none !important;
        width: 100% !important;
        text-transform: uppercase;
    }

    /* METRIC CARDS: Gold numbers */
    [data-testid="stMetricValue"] { color: #FFD700 !important; font-weight: 800; }
    .stMetric { background: #161b22 !important; border: 1px solid #30363d !important; padding: 15px; border-radius: 12px; }
    
    /* INPUT BOXES */
    input, select, textarea { background-color: #0d1117 !important; color: white !important; border: 1px solid #30363d !important; }
    </style>
    """, unsafe_allow_html=True)

# --- DATA ENGINE ---
@st.cache_data(ttl=2)
def load_data():
    try:
        response = supabase.table("gym_logs").select("*").order("created_at", desc=True).execute()
        df = pd.DataFrame(response.data) if response.data else pd.DataFrame()
        if not df.empty:
            df['created_at'] = pd.to_datetime(df['created_at'])
            # Brzycki 1RM: Weight / (1.0278 - (0.0278 * Reps))
            df['e1rm'] = round(df['weight'] / (1.0278 - (0.0278 * df['reps'])), 1)
            df['volume'] = df['weight'] * df['reps']
        return df
    except:
        return pd.DataFrame()

full_df = load_data()

st.title("💪 HYBRID-45 COMMAND")

# --- TABS ---
tab_log, tab_session, tab_lab, tab_history = st.tabs(["📝 LOG", "📊 SESSION", "📈 LAB", "🏆 PRs"])

# --- TAB 1: LOGGING ---
with tab_log:
    with st.form("entry_form", clear_on_submit=True):
        opts = ["DB Bench Press", "Hack Squat", "Lat Pulldown", "Lateral Raises", "Tricep Push Down", "Seated Cable Row", "Leg Press", "Bicep Curls", "Pull Ups", "Face Pulls", "Machine Crunch"]
        if not full_df.empty:
            opts = sorted(list(set(opts + full_df['exercise'].unique().tolist())))
        
        ex_choice = st.selectbox("Select Exercise", opts)
        new_ex = st.text_input("OR Add New Type")
        
        c1, c2 = st.columns(2)
        with c1: wt = st.number_input("Weight (kg)", step=2.5)
        with c2: reps = st.number_input("Reps", step=1)
        
        notes = st.text_area("Notes (Seat, Tempo, etc.)", placeholder="Seat Pos 4...")
        
        final_ex = new_ex if new_ex else ex_choice
        
        if st.form_submit_button("SAVE TO DATABASE 🚀"):
            payload = {"exercise": final_ex, "weight": wt, "reps": reps, "notes": notes}
            supabase.table("gym_logs").insert(payload).execute()
            st.cache_data.clear()
            st.rerun()

# --- TAB 2: SESSION SUMMARY ---
with tab_session:
    if not full_df.empty:
        today = datetime.now().date()
        today_df = full_df[full_df['created_at'].dt.date == today]
        
        if not today_df.empty:
            st.subheader(f"Today: {today.strftime('%d %b')}")
            st.divider()
            for ex in sorted(today_df['exercise'].unique()):
                past = full_df[(full_df['exercise'] == ex) & (full_df['created_at'].dt.date < today)].head(1)
                curr = today_df[today_df['exercise'] == ex].head(1)
                
                with st.expander(f"📌 {ex}", expanded=True):
                    sc1, sc2 = st.columns(2)
                    sc1.write(f"**Today:** {curr.iloc[0]['weight']}kg x {curr.iloc[0]['reps']}")
                    if not past.empty:
                        p_wt = past.iloc[0]['weight']
                        delta = curr.iloc[0]['weight'] - p_wt
                        sc2.write(f"**Previous:** {p_wt}kg")
                        if delta > 0: st.success(f"📈 +{delta}kg Up!")
                    else:
                        sc2.caption("First time logging this!")
        else:
            st.info("No sets logged today yet.")
    else:
        st.info("Log your first set to see the summary!")

# --- TAB 3: PROGRESS LAB ---
with tab_lab:
    if not full_df.empty:
        sel_ex = st.selectbox("History Analysis", sorted(full_df['exercise'].unique()))
        ex_history = full_df[full_df['exercise'] == sel_ex].sort_values('created_at')
        
        st.write("#### Estimated 1RM (Strength Trend)")
        st.line_chart(ex_history.set_index('created_at')['e1rm'], color="#FFD700")
        
        st.write("#### Total Volume (Workload)")
        st.bar_chart(ex_history.set_index('created_at')['volume'], color="#29b

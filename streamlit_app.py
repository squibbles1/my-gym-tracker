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

# --- MODERN GLASS-MORPHIC THEME ---
st.markdown("""
    <style>
    /* Global App Background */
    .stApp { background-color: #0d1117 !important; }
    
    /* Clean White Text */
    h1, h2, h3, p, span, label, .stMarkdown { color: #ffffff !important; }

    /* BUTTONS: THE FIX */
    div.stButton > button {
        background-color: #2e7bff !important; /* Cobalt Blue */
        color: #ffffff !important;           /* STARK WHITE TEXT */
        font-weight: 800 !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 18px !important;
        width: 100% !important;
        text-transform: uppercase;
        letter-spacing: 1px;
        box-shadow: 0px 4px 15px rgba(46, 123, 255, 0.4);
    }
    
    /* Hover/Active states to keep text white */
    div.stButton > button:hover, div.stButton > button:active {
        color: #ffffff !important;
        background-color: #1a56b3 !important;
        box-shadow: none !important;
    }

    /* Metric Cards: Modern Glass Look */
    [data-testid="stMetricValue"] { color: #00d4ff !important; font-weight: 800; font-size: 2.2rem !important; }
    .stMetric {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        padding: 20px !important;
        border-radius: 20px !important;
    }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { 
        color: #8b949e !important; 
        font-weight: 600; 
        padding: 10px 15px;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { 
        color: #ffffff !important; 
        border-bottom-color: #2e7bff !important; 
    }
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
            # Brzycki 1RM for strength tracking
            df['e1rm'] = round(df['weight'] / (1.0278 - (0.0278 * df['reps'])), 1)
        return df
    except: return pd.DataFrame()

full_df = load_data()

st.title("⚡ HYBRID-45 COMMAND")

# --- TOP SUMMARY BAR ---
if not full_df.empty:
    m1, m2, m3 = st.columns(3)
    with m1: st.metric("Total Lifted", f"{int(full_df['vol'].sum()):,}kg")
    with m2: st.metric("Sessions", len(full_df['created_at'].dt.date.unique()))
    with m3: st.metric("Best Lift", f"{full_df['weight'].max()}kg")

# --- MAIN NAVIGATION ---
tab_log, tab_session, tab_lab, tab_history = st.tabs(["⚡ LOG SET", "📊 SESSION", "📈 PROGRESS", "🏆 HALL OF FAME"])

# --- TAB 1: LOGGING ---
with tab_log:
    with st.form("entry_form", clear_on_submit=True):
        exercises = ["DB Bench Press", "Hack Squat", "Lat Pulldown", "Lateral Raises", "Tricep Push Down", "Seated Cable Row", "Leg Press", "Bicep Curls", "Pull Ups", "Face Pulls", "Machine Crunch"]
        if not full_df.empty:
            exercises = sorted(list(set(exercises + full_df['exercise'].unique().tolist())))
        
        ex = st.selectbox("Exercise Name", exercises)
        
        c1, c2 = st.columns(2)
        with c1: wt = st.number_input("Weight (kg)", step=2.5)
        with c2: rp = st.number_input("Reps", step=1)
        
        notes = st.text_area("Notes (Seat Position / Tempo)", placeholder="e.g. Seat Pos 4, 3s descent...")
        
        if st.form_submit_button("SAVE TO DATABASE 🚀"):
            payload = {"exercise": ex, "weight": wt, "reps": rp, "notes": notes}
            supabase.table("gym_logs").insert(payload).execute()
            st.cache_data.clear()
            st.rerun()

    # --- DUPLICATE PREVENTION ---
    st.divider()
    st.subheader("🕒 Recent Activity")
    if not full_df.empty:
        st.dataframe(full_df[['exercise', 'weight', 'reps', 'notes']].head(5), hide_index=True, use_container_width=True)

# --- TAB 2: SESSION ANALYSIS ---
with tab_session:
    if not full_df.empty:
        today = datetime.now().date()
        today_df = full_df[full_df['created_at'].dt.date == today]
        if not today_df.empty:
            st.subheader(f"Session Summary: {today.strftime('%d %b')}")
            for item in sorted(today_df['exercise'].unique()):
                past = full_df[(full_df['exercise'] == item) & (full_df['created_at'].dt.date < today)].head(1)
                curr = today_df[today_df['exercise'] == item].head(1)
                with st.expander(f"📌 {item}", expanded=True):
                    sc1, sc2 = st.columns(2)
                    sc1.metric("Today", f"{curr.iloc[0]['weight']}kg")
                    if not past.empty:
                        p_wt = past.iloc[0]['weight']
                        diff = curr.iloc[0]['weight'] - p_wt
                        sc2.metric("Previous", f"{p_wt}kg", delta=f"{diff}kg")
                    else:
                        sc2.caption("New data point logged.")
        else:
            st.info("Log your first set to see the session comparison!")
    else:
        st.info("No data logged yet.")

# --- TAB 3: PROGRESS LAB ---
with tab_lab:
    if not full_df.empty:
        sel = st.selectbox("Select Movement", sorted(full_df['exercise'].unique()))
        h = full_df[full_df['exercise'] == sel].sort_values('created_at')
        
        st.write("#### Strength Trend (Estimated 1RM)")
        st.line_chart(h.set_index('created_at')['e1rm'], color="#00d4ff")
        
        st.write("#### Workload (Total Volume)")
        st.bar_chart(h.set_index('created_at')['vol'], color="#2e7bff")

# --- TAB 4: HALL OF FAME ---
with tab_history:
    if not full_df.empty:
        st.subheader("🏆 Personal Records")
        prs = full_df.sort_values('weight', ascending=False).drop_duplicates('exercise')
        st.table(prs[['exercise', 'weight', 'reps', 'e1rm']].reset_index(drop=True))
        
        st.divider()
        if st.button("🗑️ DELETE LAST ENTRY"):
            l_id = full_df.iloc[0]['id']
            supabase.table("gym_logs").delete().eq("id", l_id).execute()
            st.cache_data.clear()
            st.rerun()
            

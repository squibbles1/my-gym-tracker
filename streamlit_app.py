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

# --- CUSTOM CSS: FORCED DARK MODE & BUTTON FIXES ---
st.markdown("""
    <style>
    .stApp { background-color: #05070a !important; }
    h1, h2, h3, p, span, label, .stMarkdown { color: #FFFFFF !important; }
    
    /* STARK WHITE BUTTON TEXT */
    div.stButton > button {
        background-color: #ff4b4b !important;
        color: white !important;
        font-weight: 800 !important;
        border: none !important;
        text-transform: uppercase;
    }

    /* METRIC CARDS */
    [data-testid="stMetricValue"] { color: #FFD700 !important; font-weight: 800; }
    .stMetric { background: #161b22 !important; border: 1px solid #30363d !important; padding: 15px; border-radius: 12px; }
    
    /* INPUT BOX STYLING */
    input, select, textarea { background-color: #0d1117 !important; color: white !important; border: 1px solid #30363d !important; }
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
            # Brzycki 1RM Formula: Weight / (1.0278 - (0.0278 * Reps))
            df['e1rm'] = round(df['weight'] / (1.0278 - (0.0278 * df['reps'])), 1)
        return df
    except Exception:
        return pd.DataFrame()

f_df = load_data()

st.title("💪 HYBRID-45 COMMAND")

# --- NAVIGATION TABS ---
t_log, t_sesh, t_lab, t_pr = st.tabs(["📝 LOG", "📊 SESSION", "📈 LAB", "🏆 PRs"])

# --- TAB 1: LOGGING ---
with t_log:
    with st.form("entry_form", clear_on_submit=True):
        opts = ["Hack Squat", "DB Bench Press", "Lat Pulldown", "Lateral Raises", "Tricep Push Down", "Seated Cable Row", "Leg Press", "Bicep Curls", "Pull Ups", "Face Pulls", "Machine Crunch"]
        if not f_df.empty:
            opts = sorted(list(set(opts + f_df['exercise'].unique().tolist())))
        
        ex = st.selectbox("Exercise", opts)
        
        # Show PR for selected exercise immediately
        if not f_df.empty:
            ex_pr = f_df[f_df['exercise'] == ex]['weight'].max()
            if ex_pr > 0:
                st.caption(f"⭐ Personal Record for {ex}: {ex_pr} kg")

        c1, c2 = st.columns(2)
        with c1: wt = st.number_input("Weight (kg)", step=2.5)
        with c2: rp = st.number_input("Reps", step=1)
        
        note = st.text_area("Notes", placeholder="Seat pos, tempo, etc...")
        
        if st.form_submit_button("SAVE SET 🚀"):
            payload = {"exercise": ex, "weight": wt, "reps": rp, "notes": note}
            supabase.table("gym_logs").insert(payload).execute()
            st.cache_data.clear()
            st.rerun()

# --- TAB 2: SESSION ANALYSIS ---
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
                    sc1.metric("Today", f"{curr.iloc[0]['weight']}kg")
                    if not past.empty:
                        p_wt = past.iloc[0]['weight']
                        diff = curr.iloc[0]['weight'] - p_wt
                        sc2.metric("Last", f"{p_wt}kg", delta=f"{diff}kg")
                    else:
                        sc2.write("First entry!")
        else:
            st.info("No sets logged today.")
    else:
        st.info("Log your first set to begin.")

# --- TAB 3: PROGRESS LAB ---
with t_lab:
    if not f_df.empty:
        sel = st.selectbox("Analysis", sorted(f_df['exercise'].unique()))
        h = f_df[f_df['exercise'] == sel].sort_values('created_at')
        st.write("#### Strength Trend (Estimated 1RM)")
        st.line_chart(h.set_index('created_at')['e1rm'], color="#FFD700")
        st.write("#### Volume per Set")
        st.bar_chart(h.set_index('created_at')['vol'], color="#29b5e8")
    else:
        st.info("No data available.")

# --- TAB 4: HALL OF FAME ---
with t_pr:
    if not f_df.empty:
        st.subheader("🏆 Personal Records")
        prs = f_df.sort_values('weight', ascending=False).drop_duplicates('exercise')
        st.dataframe(prs[['exercise', 'weight', 'reps', 'e1rm']].reset_index(drop=True), hide_index=True)
        if st.button("🗑️ DELETE LAST"):
            l_id = f_df.iloc[0]['id']
            supabase.table("gym_logs").delete().eq("id", l_id).execute()
            st.cache_data.clear()
            st.rerun()
    else:
        st.info("Hall of Fame is empty.")
        

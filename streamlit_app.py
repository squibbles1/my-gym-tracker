import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime, timedelta
import time

# 1. SETUP
st.set_page_config(page_title="Hybrid-45 Onyx", page_icon="⚡", layout="wide")

# 2. CSS STYLING
onyx_css = """
    <style>
    .stApp { background-color: #f8f9fa; }
    h1, h2, h3, p, span, label, div { 
        color: #2d3436; 
        font-family: -apple-system, BlinkMacSystemFont, sans-serif; 
    }
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
        st.error(f"Database Error: {e}")
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
            df['e1rm'] = df.apply(lambda x: x['weight'] / (1.0278 - (0.0278 * x['reps'])) if x['reps'] < 30 else 0, axis=1)
        return df
    except Exception as e:
        st.error(f"Data Load Error: {e}")
        return pd.DataFrame()

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

# --- WEEKLY WIDGET (Only shows if data exists) ---
if not df.empty:
    today = datetime.now().date()
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
    st.info("👋 Welcome! Log your first set below to initialize your dashboard.")

# --- NAVIGATION (Always Visible) ---
t_log, t_anl, t_hist = st.tabs(["LOG", "ANALYTICS", "HISTORY"])

# --- TAB 1: LOGGING ---
with t_log:
    with st.container():
        with st.form("entry", clear_on_submit=True):
            # Dynamic Exercise List
            opts = ["Hack Squat", "DB Bench Press", "Lat Pulldown", "Lateral Raises", "Tricep Push Down", "Seated Cable Row", "Leg Press", "Bicep Curls", "Pull Ups", "Face Pulls", "Machine Crunch"]
            if not df.empty:
                opts = sorted(list(set(opts + df['exercise'].unique().tolist())))
            
            ex = st.selectbox("Exercise", opts)
            
            # Smart Suggestion
            hint = "New exercise"
            if not df.empty:
                last = df[df['exercise'] == ex].head(1)
                if not last.empty:
                    hint = f"Last: {last.iloc[0]['weight']}kg x {last.iloc[0]['reps']}"
            
            st.info(f"💡 {hint}")

            c1, c2 = st.columns(2)
            with c1: wt = st.number_input("Weight (kg)", step=2.5, min_value=0.0)
            with c2: rp = st.number_input("Reps", step=1, min_value=0)
            
            note = st.text_area("Notes", placeholder="Seat, Tempo...")
            
            if st.form_submit_button("SAVE SET"):
                if supabase:
                    data = {"exercise": ex, "weight": wt, "reps": rp, "notes": note}
                    supabase.table("gym_logs").insert(data).execute()
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error("Database not connected")

    st.divider()
    if st.button("START 90s REST"):
        bar = st.progress(0)
        t = st.empty()
        for i in range(90):
            t.write(f"Recovering... {90-i}s")
            bar.progress((i+1)/90)
            time.sleep(1)
        t.success("GO!")

# --- TAB 2: ANALYTICS ---
with t_anl:
    if not df.empty:
        today = datetime.now().date()
        today_df = df[df['date'] == today]
        
        st.subheader("Today vs Last Session")
        if not today_df.empty:
            for x in today_df['exercise'].unique():
                curr = today_df[today_df['exercise'] == x].iloc[0]
                prev = df[(df['exercise'] == x) & (df['date'] < today)].head(1)
                
                with st.container():
                    c_a, c_b = st.columns(2)
                    c_a.metric(f"{x} (Today)", f"{curr['weight']}kg")
                    if not prev.empty:
                        d = curr['weight'] - prev.iloc[0]['weight']
                        c_b.metric("Prev", f"{prev.iloc[0]['weight']}kg", delta=f"{d}kg")
                    else:
                        c_b.write("First Log")
                    st.divider()
        else:
            st.info("Log a set to see comparison.")

        st.subheader("Weekly Volume Trend")
        df['week'] = df['created_at'].dt.to_period('W').apply(lambda r: r.start_time)
        wk_stats = df.groupby('week')['vol'].sum()
        st.bar_chart(wk_stats, color="#4834d4")
    else:
        st.warning("No data available for analytics yet.")

# --- TAB 3: HISTORY ---
with t_hist:
    if not df.empty:
        st.dataframe(df[['date','exercise','weight','reps','notes']], use_container_width=True, hide_index=True)
        if st.button("DELETE LAST ENTRY"):
            if supabase:
                lid = df.iloc[0]['id']
                supabase.table("gym_logs").delete().eq("id", lid).execute()
                st.cache_data.clear()
                st.rerun()
    else:
        st.write("History is empty.")
        

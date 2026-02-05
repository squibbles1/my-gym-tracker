import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime, timedelta
import time
import altair as alt

# 1. CONFIGURATION
st.set_page_config(page_title="Hybrid-45 Onyx", page_icon="💎", layout="wide")

# 2. CSS STYLING (The Onyx Theme)
onyx_css = """
    <style>
    /* Global Reset */
    .stApp { background-color: #f8f9fa; }
    
    /* Typography */
    h1, h2, h3, h4, p, span, label, div { 
        color: #2d3436; 
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; 
    }

    /* Metric Cards */
    .stat-box {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #e1e8ed;
        box-shadow: 0 2px 8px rgba(0,0,0,0.03);
        text-align: center;
    }
    .stat-label { font-size: 0.85rem; color: #636e72; text-transform: uppercase; font-weight: 600; letter-spacing: 0.5px; }
    .stat-value { font-size: 1.6rem; color: #2d3436; font-weight: 800; margin: 5px 0; }
    .stat-delta { font-size: 0.9rem; font-weight: 600; }
    .pos { color: #00b894; } /* Green */
    .neg { color: #d63031; } /* Red */

    /* Indigo Buttons */
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
        transition: all 0.2s;
    }
    div.stButton > button:hover { background-color: #3c2bb3; transform: translateY(-1px); }
    
    /* Expander Styling */
    .streamlit-expanderHeader { background-color: white; border: 1px solid #dfe6e9; border-radius: 8px; }
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
    except: return None

supabase = init_db()

# 4. INTELLIGENCE ENGINE (Data Processing)
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
            
            # AUTO-TAGGING: Assign Muscle Groups
            def get_group(ex):
                ex = ex.lower()
                if any(x in ex for x in ['squat', 'leg', 'calf']): return 'Legs'
                if any(x in ex for x in ['bench', 'press', 'push', 'fly', 'lateral']): return 'Push'
                if any(x in ex for x in ['pull', 'row', 'curl', 'lat']): return 'Pull'
                return 'Core/Other'
            df['group'] = df['exercise'].apply(get_group)
            
        return df
    except: return pd.DataFrame()

# 5. UI COMPONENTS
def render_stat(label, value, delta_val, is_pct=False):
    color_class = "pos" if delta_val >= 0 else "neg"
    sign = "+" if delta_val >= 0 else ""
    suffix = "%" if is_pct else "kg"
    
    st.markdown(f"""
        <div class="stat-box">
            <div class="stat-label">{label}</div>
            <div class="stat-value">{value}</div>
            <div class="stat-delta {color_class}">
                {sign}{delta_val}{suffix} vs last wk
            </div>
        </div>
    """, unsafe_allow_html=True)

# --- APP START ---
df = get_data()

st.title("Hybrid-45 Onyx Pro")

# --- EXECUTIVE SUMMARY (Week vs Week) ---
if not df.empty:
    today = datetime.now().date()
    # Current Week (Mon-Sun)
    start_curr = today - timedelta(days=today.weekday())
    curr_df = df[df['date'] >= start_curr]
    
    # Previous Week
    start_prev = start_curr - timedelta(days=7)
    end_prev = start_curr - timedelta(days=1)
    prev_df = df[(df['date'] >= start_prev) & (df['date'] <= end_prev)]

    # Calculations
    curr_vol = int(curr_df['vol'].sum())
    prev_vol = int(prev_df['vol'].sum())
    vol_delta = curr_vol - prev_vol
    vol_pct = int(((curr_vol - prev_vol) / prev_vol * 100)) if prev_vol > 0 else 0
    
    curr_sess = len(curr_df['date'].unique())
    prev_sess = len(prev_df['date'].unique())
    sess_delta = curr_sess - prev_sess

    # Render Dashboard
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-label">Consistency Goal</div>
            <div class="stat-value">{curr_sess} / 3</div>
            <div class="stat-delta" style="color: #4834d4">Sessions this week</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        render_stat("Weekly Volume", f"{curr_vol:,}", vol_pct, is_pct=True)
    with c3:
        # Best lift this week vs last week
        curr_best = curr_df['weight'].max() if not curr_df.empty else 0
        prev_best = prev_df['weight'].max() if not prev_df.empty else 0
        render_stat("Peak Weight", f"{curr_best}kg", curr_best - prev_best, is_pct=False)

# --- NAVIGATION ---
t_log, t_anl, t_hist = st.tabs(["LOG", "ANALYTICS", "MANAGE HISTORY"])

# --- TAB 1: SMART LOG ---
with t_log:
    with st.container():
        with st.form("entry", clear_on_submit=True):
            # Exercise List
            defaults = ["Hack Squat", "DB Bench Press", "Lat Pulldown", "Lateral Raises", 
                        "Tricep Push Down", "Seated Cable Row", "Leg Press", "Bicep Curls", 
                        "Pull Ups", "Face Pulls", "Machine Crunch", 
                        "Chest Fly Machine", "Decline Press", "Overhead Tricep"]
            if not df.empty:
                defaults = sorted(list(set(defaults + df['exercise'].unique().tolist())))
            
            ex = st.selectbox("Exercise", defaults)
            
            # Suggestion
            hint = "New movement"
            if not df.empty:
                last = df[df['exercise'] == ex].head(1)
                if not last.empty:
                    hint = f"Last: {last.iloc[0]['weight']}kg x {last.iloc[0]['reps']}"
            st.info(f"💡 {hint}")

            c1, c2 = st.columns(2)
            with c1: wt = st.number_input("Weight (kg)", step=2.5, min_value=0.0)
            with c2: rp = st.number_input("Reps", step=1, min_value=0)
            
            st.write("---")
            c3, c4 = st.columns(2)
            with c3: intensity = st.radio("Intensity", ["Moderate", "Intense"], horizontal=True)
            with c4: feeling = st.select_slider("Feeling", ["Great", "Good", "OK", "Hard", "Grind"])
            
            note = st.text_area("Notes", placeholder="Seat pos...")
            
            if st.form_submit_button("SAVE ENTRY"):
                if supabase:
                    final_note = f"{note} | {intensity} | {feeling}"
                    data = {"exercise": ex, "weight": wt, "reps": rp, "notes": final_note}
                    supabase.table("gym_logs").insert(data).execute()
                    st.cache_data.clear()
                    st.rerun()

# --- TAB 2: ADVANCED ANALYTICS ---
with t_anl:
    if not df.empty:
        # 1. Muscle Split Donut Chart
        st.subheader("Training Split Balance")
        split_data = df.groupby('group')['vol'].sum().reset_index()
        base = alt.Chart(split_data).encode(theta=alt.Theta("vol", stack=True))
        pie = base.mark_arc(outerRadius=120).encode(
            color=alt.Color("group"),
            order=alt.Order("vol", sort="descending"),
            tooltip=["group", "vol"]
        )
        text = base.mark_text(radius=140).encode(
            text=alt.Text("vol", format=","),
            order=alt.Order("vol", sort="descending"),
            color=alt.value("black")  
        )
        st.altair_chart(pie + text, use_container_width=True)

        st.divider()

        # 2. Volume Trend
        st.subheader("Volume Trend (Last 8 Weeks)")
        df['week_start'] = df['created_at'].dt.to_period('W').apply(lambda r: r.start_time)
        wk_stats = df.groupby('week_start')['vol'].sum().tail(8)
        st.bar_chart(wk_stats, color="#4834d4")
    else:
        st.info("Log data to unlock visuals.")

# --- TAB 3: MANAGE HISTORY (Edit/Delete) ---
with t_hist:
    if not df.empty:
        st.subheader("Management Console")
        st.caption("Select an entry below to Edit or Delete it.")
        
        # 1. Select Entry to Manage
        # Create a display label for the dropdown
        df['label'] = df.apply(lambda x: f"{x['date']} | {x['exercise']} | {x['weight']}kg x {x['reps']}", axis=1)
        
        selected_label = st.selectbox("Search History", df['label'].tolist())
        
        # Get the full row data for the selection
        selection = df[df['label'] == selected_label].iloc[0]
        
        st.write("---")
        st.markdown(f"**Editing:** {selection['exercise']} on {selection['date']}")
        
        # 2. Edit Form
        with st.form("edit_form"):
            c1, c2 = st.columns(2)
            with c1: new_wt = st.number_input("Edit Weight", value=float(selection['weight']))
            with c2: new_rp = st.number_input("Edit Reps", value=int(selection['reps']))
            new_note = st.text_area("Edit Notes", value=selection['notes'])
            
            save_col, del_col = st.columns([1,1])
            with save_col:
                if st.form_submit_button("UPDATE ENTRY"):
                    if supabase:
                        supabase.table("gym_logs").update({
                            "weight": new_wt, "reps": new_rp, "notes": new_note
                        }).eq("id", selection['id']).execute()
                        st.success("Updated!")
                        st.cache_data.clear()
                        time.sleep(1)
                        st.rerun()
            
            with del_col:
                if st.form_submit_button("DELETE PERMANENTLY", type="primary"):
                    if supabase:
                        supabase.table("gym_logs").delete().eq("id", selection['id']).execute()
                        st.warning("Deleted!")
                        st.cache_data.clear()
                        time.sleep(1)
                        st.rerun()

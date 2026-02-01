# --- TAB 2: ANALYSIS (UPDATED FOR PERSISTENCE) ---
with t_sesh:
    if not df.empty:
        today_date = datetime.now().date()
        today_df = df[df['created_at'].dt.date == today_date]
        
        # Scenario A: You ARE currently working out
        if not today_df.empty:
            st.subheader("Current Session vs Previous")
            for item in sorted(today_df['exercise'].unique()):
                past = df[(df['exercise'] == item) & (df['created_at'].dt.date < today_date)].head(1)
                curr = today_df[today_df['exercise'] == item].head(1)
                with st.expander(item, expanded=True):
                    sc1, sc2 = st.columns(2)
                    sc1.metric("Today", f"{curr.iloc[0]['weight']}kg")
                    if not past.empty:
                        diff = curr.iloc[0]['weight'] - past.iloc[0]['weight']
                        sc2.metric("Last Time", f"{past.iloc[0]['weight']}kg", delta=f"{diff}kg")
        
        # Scenario B: You haven't started today yet - Show Last Session instead
        else:
            st.subheader("Last Session Overview")
            last_date = df['created_at'].dt.date.iloc[0]
            last_session_df = df[df['created_at'].dt.date == last_date]
            
            st.info(f"Showing data from your last session on {last_date.strftime('%d %b')}")
            
            for item in sorted(last_session_df['exercise'].unique()):
                set_data = last_session_df[last_session_df['exercise'] == item].iloc[0]
                with st.expander(item, expanded=False):
                    st.write(f"Weight: **{set_data['weight']}kg**")
                    st.write(f"Reps: **{set_data['reps']}**")
                    if set_data['notes']:
                        st.caption(f"Notes: {set_data['notes']}")
    else:
        st.info("No data found in database. Log your first set to begin.")

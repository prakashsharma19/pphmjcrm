import streamlit as st
import time

st.set_page_config(page_title="PPH CRM Migrated", layout="centered")

# Title and Message
st.title("📢 PPH CRM Software Migrated")
st.markdown("""
## The PPH CRM Software Has Migrated to Another Server

You will be redirected shortly to the new server:
🔗 [https://pphentry.onrender.com/](https://pphentry.onrender.com/)

**Redirecting in:** 
""")

# Countdown Timer
countdown = st.empty()
for i in range(5, 0, -1):
    countdown.markdown(f"# ⏳ {i}")
    time.sleep(1)

# JavaScript redirect after countdown
st.markdown(
    """
    <meta http-equiv="refresh" content="0; URL='https://pphentry.onrender.com/'" />
    """,
    unsafe_allow_html=True
)

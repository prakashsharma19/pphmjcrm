import streamlit as st
import time

st.set_page_config(page_title="PPH CRM Migrated", layout="centered")

# Static notice
st.markdown("""
<h1 style='text-align: center; font-size: 42px; color: #c0392b;'>🚨 PPH CRM Software Has Migrated</h1>
<h2 style='text-align: center; font-size: 26px;'>You will be redirected to the new server in <span id="countdown">10</span> seconds.</h2>
<h3 style='text-align: center; color: #2c3e50;'>New URL: <a href="https://pphentry.onrender.com" target="_blank">https://pphentry.onrender.com</a></h3>
<p style='text-align: center; font-size: 20px;'>Please update your bookmarks with this new address.</p>
""", unsafe_allow_html=True)

# Countdown (visible timer using Python)
for i in range(10, 0, -1):
    st.markdown(f"<h2 style='text-align: center;'>⏳ Redirecting in {i} seconds...</h2>", unsafe_allow_html=True)
    time.sleep(1)

# JavaScript for same-tab redirect
st.markdown("""
<script>
    window.location.href = "https://pphentry.onrender.com";
</script>
""", unsafe_allow_html=True)

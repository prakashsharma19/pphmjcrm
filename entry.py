import streamlit as st
import time

st.set_page_config(page_title="PPH CRM Migrated", layout="centered")

# Large, bold message
st.markdown("""
<h1 style='text-align: center; font-size: 40px; color: #d62728;'>🚨 PPH CRM Software Has Migrated</h1>
<h2 style='text-align: center; font-size: 28px; color: #333;'>You will be redirected to the new server in <span id="countdown">10</span> seconds.</h2>
<h3 style='text-align: center; color: #555;'>New URL: <a href="https://pphentry.onrender.com" target="_blank">https://pphentry.onrender.com</a></h3>
<p style='text-align: center; font-size: 20px;'>Please update your bookmarks with the new address.</p>
""", unsafe_allow_html=True)

# Countdown (for visual effect in Python)
for i in range(10, 0, -1):
    st.markdown(f"<h2 style='text-align: center;'>⏳ Redirecting in {i} seconds...</h2>", unsafe_allow_html=True)
    time.sleep(1)

# JavaScript to open in new tab after 10 seconds
st.markdown("""
<script>
    setTimeout(function() {
        window.open("https://pphentry.onrender.com", "_blank");
    }, 10000);
</script>
""", unsafe_allow_html=True)

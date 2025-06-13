import streamlit as st

st.set_page_config(page_title="PPH CRM Migrated", layout="centered")

st.markdown("""
<h1 style='text-align: center; font-size: 42px; color: #c0392b;'>🚨 PPH CRM Software Has Migrated</h1>
<h2 style='text-align: center; font-size: 26px;'>The application has been moved to a new server.</h2>
<h3 style='text-align: center; color: #2c3e50;'>🔗 <a href="https://pphentry.onrender.com" target="_blank">Click here to open the new app</a></h3>
<p style='text-align: center; font-size: 20px;'>📌 Please <strong>update your bookmarks</strong> to the new link above.</p>
""", unsafe_allow_html=True)

# Optional: Provide a "Bookmark This Page" hint button (opens link again, users manually bookmark)
col1, col2, col3 = st.columns([2, 2, 2])
with col2:
    st.markdown(
        """
        <a href="https://pphentry.onrender.com" target="_blank">
            <button style="padding: 10px 20px; font-size: 18px; background-color: #2e86de; color: white; border: none; border-radius: 6px; cursor: pointer;">
                🔖 Open & Bookmark
            </button>
        </a>
        """,
        unsafe_allow_html=True
    )

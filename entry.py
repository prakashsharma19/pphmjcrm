import streamlit as st

st.set_page_config(page_title="PPH CRM Migrated", layout="centered")

st.markdown("""
<h1 style='text-align: center; font-size: 42px; color: #2c3e50;'>📢 PPH CRM Software Has Migrated</h1>

<h2 style='text-align: center; font-size: 26px; color: #e74c3c;'>This application has moved to a new server with improved experience.</h2>

<h3 style='text-align: center; color: #2980b9; font-size: 22px;'>
🔗 <strong><a href="https://pphentry.onrender.com" target="_blank">https://pphentry.onrender.com</a></strong>
</h3>

<p style='text-align: center; font-size: 20px; color: #34495e;'>
👉 Please <strong>update your bookmark</strong> with this new link.
</p>

<p style='text-align: center; font-size: 18px; color: #7f8c8d;'>
Contact app administrator for any help <a href="mailto:contact@cpsharma.com">contact@cpsharma.com</a>
</p>
""", unsafe_allow_html=True)

# Centered Open & Bookmark Button
col1, col2, col3 = st.columns([2, 3, 2])
with col2:
    st.markdown(
        """
        <div style='text-align: center;'>
            <a href="https://pphentry.onrender.com" target="_blank">
                <button style="padding: 12px 30px; font-size: 18px; background-color: #2980b9; color: white; border: none; border-radius: 8px; cursor: pointer;">
                    🔖 Open & Bookmark
                </button>
            </a>
        </div>
        """,
        unsafe_allow_html=True
    )

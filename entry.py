import streamlit as st
import google.generativeai as genai
import firebase_admin
from firebase_admin import credentials, firestore
import os
from datetime import datetime
from io import StringIO
import time
from difflib import SequenceMatcher
from PIL import Image
import requests
from io import BytesIO
from dotenv import load_dotenv
import re

# Load environment variables from .env file
load_dotenv()

# ======================
# INITIALIZATION
# ======================
def init_session_state():
    session_vars = {
        'entries': [],
        'uploaded_entries': [],
        'upload_journal': "",
        'upload_filename': "",
        'show_files': False,
        'processing': False,
        'new_journal_name': "",
        'viewing_entries': None,
        'search_query': "",
        'editing_entry': None,
        'show_search_results': False,
        'search_results': [],
        'show_save_section': False,
        'deleting_entry': None,
        'deleting_file': None,
        'editing_current_entry': None,
        'deleting_current_entry': None,
        'available_journals': [],
        'current_edit_entry': None,
        'authenticated': False,
        'username': "",
        'font_size': 'Medium',
        'bg_color': '#ffffff',
        'theme': 'Light',
        'current_module': None,
        'cloud_status': 'Not checked',
        'ai_status': 'Not checked',
        'cloud_error': '',
        'ai_error': '',
        'show_all_entries': False,
        'manual_api_key': 'AIzaSyBIXgqTphaQq8u3W5A4HRHVhwBp_fbnfsg',
        'show_api_key_input': False,
        'delete_duplicates_mode': False,
        'show_connection_status': False,
        'app_mode': "✏️ Create Entries",
        'show_formatted_entries': False
    }
    
    for key, default_value in session_vars.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

# MUST BE FIRST STREAMLIT COMMAND
st.set_page_config(page_title="PPH CRM", layout="wide", initial_sidebar_state="expanded")
init_session_state()

# ======================
# REGEX PROCESSING FUNCTIONS
# ======================
def preprocess_with_regex(text):
    """Clean up text using regex patterns before sending to AI"""
    # Remove unwanted phrases
    patterns_to_remove = [
        r'View in Scopus',
        r'View the author\'s ORCID record',
        r'Corresponding author\.?',
        r'Corresponding authors at:.*',
        r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
        r'\([^)]*correspond[^)]*\)',  # Remove (corresponding author) notes
        r'\([^)]*\)',  # Remove all parenthetical notes
        r'\b\d{5,6}\b',  # Remove 5-6 digit numbers (like postal codes)
        r'\b[A-Z]{2}-\d{4,5}\b',  # Remove codes like BC-22860
        r'AP \d+',  # Remove AP numbers
        r'Km \d+',  # Remove Km numbers
        r'\b\d+\s*-\s*\d+\b',  # Remove number ranges
    ]
    
    for pattern in patterns_to_remove:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    # Clean up email formatting
    text = re.sub(r'\(at\)|\[at\]', '@', text, flags=re.IGNORECASE)
    text = re.sub(r'\(dot\)|\[dot\]', '.', text, flags=re.IGNORECASE)
    
    # Remove extra whitespace and empty lines
    text = '\n'.join([line.strip() for line in text.split('\n') if line.strip()])
    
    return text

def postprocess_with_regex(text):
    """Clean up AI output using regex patterns"""
    # Ensure each component is on its own line
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    # Standardize the format
    formatted_lines = []
    for line in lines:
        # Split lines that combine department and university
        if re.search(r'(.+),\s*(University|College|Instituto|Universidad|Institution)', line, re.IGNORECASE):
            parts = re.split(r',\s*(?=University|College|Instituto|Universidad|Institution)', line, flags=re.IGNORECASE)
            formatted_lines.extend(parts)
        else:
            formatted_lines.append(line)
    
    # Remove any remaining unwanted patterns
    clean_lines = []
    for line in formatted_lines:
        line = re.sub(r'\b(?:Department|Dept|Laboratory|Lab|School)\s*of\s*', '', line, flags=re.IGNORECASE)
        line = re.sub(r'\s{2,}', ' ', line).strip()
        if line:
            clean_lines.append(line)
    
    # Ensure we have exactly 5 lines (name, department, university, country, email)
    while len(clean_lines) < 5:
        clean_lines.append('')
    
    return '\n'.join(clean_lines[:5])

def extract_author_email(entry):
    """Extract name and email from entry"""
    lines = [line.strip() for line in entry.split('\n') if line.strip()]
    if not lines:
        return None, None
    
    # Name is first line
    name = lines[0].replace("Professor", "").strip()
    
    # Email is last line containing @
    email = ""
    for line in reversed(lines):
        if '@' in line:
            email = line.strip()
            break
    
    return name, email

# ======================
# FIREBASE INITIALIZATION
# ======================
def initialize_firebase():
    """Initialize Firebase with proper error handling and singleton pattern"""
    try:
        if firebase_admin._apps:
            st.session_state.cloud_status = "Connected"
            return True
            
        firebase_config = {
            "type": st.secrets["firebase"]["type"],
            "project_id": st.secrets["firebase"]["project_id"],
            "private_key_id": st.secrets["firebase"]["private_key_id"],
            "private_key": st.secrets["firebase"]["private_key"].replace('\\n', '\n'),
            "client_email": st.secrets["firebase"]["client_email"],
            "client_id": st.secrets["firebase"]["client_id"],
            "auth_uri": st.secrets["firebase"]["auth_uri"],
            "token_uri": st.secrets["firebase"]["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["firebase"]["auth_provider_x509_cert_url"],
            "client_x509_cert_url": st.secrets["firebase"]["client_x509_cert_url"],
            "universe_domain": st.secrets["firebase"]["universe_domain"]
        }

        cred = credentials.Certificate(firebase_config)
        firebase_admin.initialize_app(cred)
        
        st.session_state.cloud_status = "Connected"
        return True
        
    except Exception as e:
        st.session_state.cloud_status = "Error"
        st.session_state.cloud_error = str(e)
        return False

def get_firestore_db():
    if not initialize_firebase():
        st.error(f"Firebase initialization failed: {st.session_state.cloud_error}")
        return None
    return firestore.client()

# ======================
# UTILITY FUNCTIONS
# ======================
def load_logo():
    try:
        response = requests.get("https://github.com/prakashsharma19/hosted-images/raw/main/pphlogo.png")
        img = Image.open(BytesIO(response.content))
        return img
    except:
        return None

logo = load_logo()

def format_time(seconds):
    if seconds >= 60:
        return f"{int(seconds//60)} minute{'s' if seconds >= 120 else ''} {int(seconds%60)} second{'s' if seconds%60 != 1 else ''}"
    return f"{int(seconds)} second{'s' if seconds != 1 else ''}"

def normalize_text(text):
    return ' '.join(str(text).strip().lower().split())

def is_similar(text1, text2, threshold=0.85):
    return SequenceMatcher(None, normalize_text(text1), normalize_text(text2)).ratio() >= threshold

def get_journal_abbreviation(journal_name):
    common_words = ['and', 'of', 'the', 'in', 'journal', 'jp']
    words = [word for word in journal_name.split() if word.lower() not in common_words]
    
    if journal_name.startswith("JP "):
        return "JP" + journal_name.split()[1][0].upper()
    
    abbreviation = ''.join([word[0].upper() for word in words])
    
    if len(abbreviation) < 3:
        abbreviation = ''.join([word[:2].upper() for word in words[:2]])
    
    return abbreviation

def get_suggested_filename(journal_name):
    return f"{get_journal_abbreviation(journal_name)}_{datetime.now().strftime('%d%b%Y')}"

def process_uploaded_file(uploaded_file):
    try:
        stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
        content = stringio.read()
        return [entry.strip() for entry in content.split("\n\n") if entry.strip()]
    except Exception:
        return []

# ======================
# AI PROCESSING FUNCTIONS
# ======================
def format_entries_chunked(text, status_text):
    if st.session_state.ai_status != "Connected":
        st.error("AI service is not available. Cannot format entries.")
        return ""
        
    start_time = time.time()
    
    # First preprocess with regex
    preprocessed = preprocess_with_regex(text)
    entries = [entry.strip() for entry in preprocessed.split("\n\n") if entry.strip()]
    
    if not entries:
        return ""
    
    # Then refine with AI
    chunk_size = 10000
    chunks = ['\n\n'.join(entries[i:i+50]) for i in range(0, len(entries), 50)]
    formatted_parts = []
    total_chunks = len(chunks)
    
    progress_bar = st.progress(0)
    status_text.text("Starting AI processing...")
    
    for i, chunk in enumerate(chunks):
        elapsed = time.time() - start_time
        chunks_processed = i + 1
        avg_time_per_chunk = elapsed / chunks_processed
        remaining_time = (total_chunks - chunks_processed) * avg_time_per_chunk
        
        progress = int(chunks_processed / total_chunks * 100)
        progress_bar.progress(progress)
        status_text.text(f"Processing {chunks_processed}/{total_chunks} (Est. remaining: {format_time(remaining_time)})")
        
        prompt = f"""Refine these author entries to ensure consistent formatting:

Format each entry as:
Name
Department/Institute/Laboratory (most specific first)
University/Organization
Country
email@domain.com

RULES:
1. Keep only the most relevant institutional information
2. Remove all street addresses, postal codes, building numbers
3. Keep the most specific department/lab info on its own line
4. Keep university/organization on its own line
5. Keep country on its own line
6. Ensure email is clean and properly formatted on its own line
7. Remove any author notes, Scopus info, ORCID, etc.

Examples of correct formatting:
Manish Kumar
Experimental Research Laboratory, Department of Physics
ARSD College, University of Delhi
India
mkumar2@arsd.du.ac.in

Subhash Sharma
Centro de Nanociencias y Nanotecnología
Universidad Nacional Autónoma de México
México
subhash@ens.cnyn.unam.mx

Text to refine:
{chunk}
"""
        
        try:
            model = genai.GenerativeModel("gemini-1.5-flash-latest")
            response = model.generate_content(prompt)
            if response.text:
                # Post-process the AI output
                formatted_chunk = postprocess_with_regex(response.text)
                formatted_parts.append(formatted_chunk)
        except Exception as e:
            st.error(f"Error during formatting: {str(e)}")
            pass
    
    final_entries = []
    for entry in "\n\n".join(formatted_parts).split("\n\n"):
        lines = entry.split('\n')
        if len(lines) >= 2 and '@' in lines[-1]:
            final_entries.append(entry)
    
    processing_time = time.time() - start_time
    progress_bar.progress(100)
    status_text.text(f"Formatting complete! Time taken: {format_time(processing_time)}")
    return "\n\n".join(final_entries)

# [Rest of the code remains the same as in your original implementation]
# [Include all the database functions, UI components, and main app flow from the original code]
# [Make sure to update any function calls to use the new regex-based processing]

# ======================
# MAIN APP FLOW
# ======================
if not st.session_state.authenticated:
    show_login_page()
else:
    apply_theme_settings()
    
    with st.sidebar:
        show_connection_status()
        
        st.markdown("---")
        
        if st.button("🏠 Home", key="sidebar_home_btn"):
            st.session_state.current_module = None
            st.rerun()
        
        st.markdown("---")
        
        expander = st.expander("⚙️ Settings", expanded=False)
        with expander:
            st.subheader("Appearance")
            new_font_size = st.selectbox(
                "Font Size",
                ["Small", "Medium", "Large"],
                index=["Small", "Medium", "Large"].index(st.session_state.font_size),
                key="sidebar_font_size"
            )
            
            new_theme = st.selectbox(
                "Theme",
                ["Light", "Dark"],
                index=["Light", "Dark"].index(st.session_state.theme),
                key="sidebar_theme"
            )
            
            if st.button("Save Settings", key="save_settings_btn"):
                st.session_state.font_size = new_font_size
                st.session_state.theme = new_theme
                st.session_state.bg_color = "#ffffff" if new_theme == "Light" else "#1a1a1a"
                st.success("Settings saved successfully!")
                apply_theme_settings()
                st.rerun()
        
        st.markdown("---")
        st.markdown(f"Logged in as: **{st.session_state.username}**")
        
        if st.button("🚪 Logout", key="sidebar_logout_btn"):
            st.session_state.authenticated = False
            st.session_state.username = ""
            st.session_state.current_module = None
            st.rerun()

    if st.session_state.current_module is None:
        show_main_menu()
    elif st.session_state.current_module == "Entry":
        show_entry_module()
    elif st.session_state.current_module == "PPH Office Tools":
        st.header("🛠️ PPH Office Tools")
        st.info("Coming soon!")

st.markdown("---")
st.markdown("**PPH CRM - Contract App Administrator for any help at: [contact@cpspharma.com](mailto:contact@cpspharma.com)**")

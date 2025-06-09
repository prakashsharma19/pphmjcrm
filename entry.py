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
import math
import json

# Load environment variables
load_dotenv()

# Initialize session state
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
        'manual_api_key': 'AIzaSyCiUe8rCj4Ik7zWWTJ3I0aRCV1P_af6Y7Y',
        'show_api_key_input': False,
        'delete_duplicates_mode': False,
        'show_connection_status': False,
        'app_mode': "📝 Create Entries",
        'show_formatted_entries': False,
        'regex_filters': [],
        'ai_prompts': [],
        'show_regex_manager': False,
        'show_prompt_manager': False,
        'new_regex_filter': "",
        'new_prompt_name': "",
        'new_prompt_input': "",
        'new_prompt_output': "",
        'processing_start_time': None,
        'current_chunk': 0,
        'total_chunks': 0,
        'is_admin': False,
        'renaming_file': None,
        'new_filename': "",
        'moving_file': None,
        'target_journal': "",
        'last_activity_time': time.time(),
        'deleting_journal': None,
        'save_progress': 0,
        'save_status': "",
        'converting_journal': None,
        'show_journals_list': False,
        'resume_task_id': None,
        'resume_data_loaded': False,
        'create_entry_stage': 'format',
        'formatted_entries': [],
        'formatted_text': "",
        'show_formatting_results': False,
        'show_download_section': False,
        'deleting_keys_journal': None,
        'files_to_display': 3,
        'chunk_size': 50
    }
    for key, default_value in session_vars.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

st.set_page_config(page_title="PPH CRM 1", layout="wide", initial_sidebar_state="expanded")
init_session_state()

# Helper functions
def format_time(seconds):
    """Format time in seconds to human-readable format"""
    if seconds < 60:
        return f"{seconds:.1f} seconds"
    elif seconds < 3600:
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{int(minutes)} minutes {int(seconds)} seconds"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{int(hours)} hours {int(minutes)} minutes"

def get_suggested_filename(journal):
    """Generate a suggested filename based on journal name"""
    if not journal:
        return "entries.txt"
    abbreviation = ''.join([word[0].upper() for word in journal.split() if word[0].isalpha()])
    return f"{abbreviation} {datetime.now().strftime('%d-%m-%Y')}.txt"

def process_uploaded_file(uploaded_file):
    """Process uploaded file and return entries"""
    try:
        try:
            stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
            text = stringio.read()
        except UnicodeDecodeError:
            stringio = StringIO(uploaded_file.getvalue().decode("latin-1"))
            text = stringio.read()
        
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        entries = [entry.strip() for entry in text.split("\n\n") if entry.strip()]
        return entries
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
        return []

# Firebase initialization
def initialize_firebase():
    try:
        if firebase_admin._apps:
            st.session_state.cloud_status = "Connected"
            return True
            
        cred = credentials.Certificate({
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
        })
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

def get_available_journals():
    """Get list of available journals from Firestore"""
    all_journals = []
    db = get_firestore_db()
    if db:
        try:
            journals_ref = db.collection("journals").stream()
            all_journals = [journal.id for journal in journals_ref]
        except Exception as e:
            st.error(f"Error fetching journals: {str(e)}")
    return sorted(list(set([
        "Computer Science and Artificial Intelligence",
        "Advanced Studies in Artificial Intelligence",
        "Advances in Computer Science and Engineering",
        "Far East Journal of Experimental and Theoretical Artificial Intelligence",
        "Advances and Applications in Fluid Mechanics",
        "Advances in Fuzzy Sets and Systems",
        "Far East Journal of Electronics and Communications",
        "Far East Journal of Mechanical Engineering and Physics",
        "International Journal of Nutrition and Dietetics",
        "International Journal of Materials Engineering and Technology",
        "JP Journal of Solids and Structures",
        "Advances and Applications in Discrete Mathematics",
        "Advances and Applications in Statistics",
        "Far East Journal of Applied Mathematics",
        "Far East Journal of Dynamical Systems",
        "Far East Journal of Mathematical Sciences (FJMS)",
        "Far East Journal of Theoretical Statistics",
        "JP Journal of Algebra, Number Theory and Applications",
        "JP Journal of Biostatistics",
        "JP Journal of Fixed Point Theory and Applications",
        "JP Journal of Heat and Mass Transfer",
        "Surveys in Mathematics and Mathematical Sciences",
        "Universal Journal of Mathematics and Mathematical Sciences"
    ] + all_journals)))

def extract_author_email(entry):
    """Extract author name and email from entry"""
    lines = entry.split('\n')
    if len(lines) < 2:
        return None, None
    name = lines[0].replace("Professor", "").strip()
    email = lines[-1].strip()
    return name, email

def is_duplicate(name, email):
    """Check if an author is already in the system"""
    if not name or not email:
        return False
    db = get_firestore_db()
    if not db:
        return False
    key = f"{name.lower()}_{email.lower()}"
    doc = db.collection("author_keys").document(key).get()
    return doc.exists

def save_entries_with_progress(entries, journal, filename, status_text):
    """Save entries with progress tracking"""
    db = get_firestore_db()
    if not db:
        return False
        
    try:
        journal_ref = db.collection("journals").document(journal)
        if not journal_ref.get().exists:
            journal_ref.set({"created": datetime.now()})

        total_entries = len(entries)
        duplicates_found = 0
        unique_entries = []
        
        progress_bar = st.progress(0)
        status_text.text("Checking for duplicates...")
        
        batch_size = 50
        batch = db.batch()
        author_keys_batch = db.batch()
        
        for i, entry in enumerate(entries):
            progress = int((i + 1) / total_entries * 100)
            progress_bar.progress(progress)
            status_text.text(f"Processing {i+1}/{total_entries} ({progress}%) - {duplicates_found} duplicates found")
            
            name, email = extract_author_email(entry)
            if not name or not email:
                continue
                
            if is_duplicate(name, email):
                duplicates_found += 1
                continue
                
            unique_entries.append(entry)
            key = f"{name.lower()}_{email.lower()}"
            author_keys_batch.set(db.collection("author_keys").document(key), {
                "name": name,
                "email": email,
                "journal": journal,
                "filename": filename,
                "timestamp": datetime.now()
            })
            
            if i > 0 and i % batch_size == 0:
                batch.commit()
                author_keys_batch.commit()
                batch = db.batch()
                author_keys_batch = db.batch()
                
            st.session_state.last_activity_time = time.time()
        
        if len(unique_entries) > 0:
            doc_ref = db.collection("journals").document(journal).collection("files").document(filename)
            batch.set(doc_ref, {
                "entries": unique_entries,
                "last_updated": datetime.now(),
                "entry_count": len(unique_entries)
            })
            batch.commit()
            author_keys_batch.commit()
        
        progress_bar.progress(100)
        
        if duplicates_found:
            status_text.text(f"Completed! Saved {len(unique_entries)} entries, skipped {duplicates_found} duplicates")
        else:
            status_text.text(f"Completed! Saved {len(unique_entries)} entries")
            
        return True
        
    except Exception as e:
        st.error(f"Error saving entries: {str(e)}")
        return False

# AI processing function
def format_entries_chunked(text, status_text):
    if st.session_state.ai_status != "Connected":
        st.error("AI service is not available")
        return ""
        
    st.session_state.processing_start_time = time.time()
    preprocessed = preprocess_with_regex(text)
    entries = [entry.strip() for entry in preprocessed.split("\n\n") if entry.strip()]
    
    if not entries:
        return ""
    
    chunks = ['\n\n'.join(entries[i:i+st.session_state.chunk_size]) for i in range(0, len(entries), st.session_state.chunk_size)]
    st.session_state.total_chunks = len(chunks)
    st.session_state.current_chunk = 0
    formatted_parts = []
    
    progress_bar = st.progress(0)
    status_text.text("Initializing processing...")
    
    best_prompt = """You are an intelligent academic address refiner..."""  # Your full prompt here
    
    for i, chunk in enumerate(chunks):
        st.session_state.current_chunk = i + 1
        progress = int((i + 1) / len(chunks) * 100)
        progress_bar.progress(progress)
        
        st.session_state.last_activity_time = time.time()
        
        elapsed = time.time() - st.session_state.processing_start_time
        if i > 0:
            avg_time_per_chunk = elapsed / (i + 1)
            remaining_chunks = len(chunks) - (i + 1)
            estimated_remaining = avg_time_per_chunk * remaining_chunks
            
            status_text.text(
                f"Processing chunk {i+1}/{len(chunks)} "
                f"({progress}%) - "
                f"Estimated time remaining: {format_time(estimated_remaining)}\n"
                f"Processing speed: {avg_time_per_chunk:.1f} sec/chunk"
            )
        
        try:
            genai.configure(api_key=st.session_state.manual_api_key or os.getenv("GOOGLE_API_KEY"))
            model = genai.GenerativeModel("gemini-1.5-flash-latest")
            response = model.generate_content(best_prompt.format(chunk=chunk))
            
            if response.text:
                formatted_chunk = response.text.strip()
                formatted_chunk = '\n\n'.join([entry.strip() for entry in formatted_chunk.split('\n\n') if entry.strip()])
                formatted_parts.append(formatted_chunk)
        except Exception as e:
            st.error(f"Error processing chunk {i+1}: {str(e)}")
            continue
    
    processing_time = time.time() - st.session_state.processing_start_time
    progress_bar.progress(100)
    status_text.text(f"Completed in {format_time(processing_time)}")
    
    final_text = '\n\n'.join(formatted_parts)
    final_text = '\n\n'.join([entry.strip() for entry in final_text.split('\n\n') if entry.strip()])
    
    return final_text

# UI Components
def load_logo():
    try:
        response = requests.get("https://github.com/prakashsharma19/hosted-images/raw/main/pphlogo.png")
        img = Image.open(BytesIO(response.content))
        return img
    except:
        return None

logo = load_logo()

def show_connection_status():
    with st.sidebar.expander("🔌 Connection Status", expanded=False):
        if st.session_state.cloud_status == "Connected":
            st.success("☁️ Cloud: Connected")
        elif st.session_state.cloud_status == "Error":
            st.error("☁️ Cloud: Error")
            st.text_area("Cloud Error Details", 
                        value=st.session_state.cloud_error,
                        height=100,
                        disabled=True)
        else:
            st.warning("🔃 Cloud: Checking...")
        
        if st.session_state.ai_status == "Connected":
            st.success("🤖 AI: Connected")
        elif st.session_state.ai_status == "Error":
            st.error("🤖 AI: Error")
            st.text_area("AI Error Details",
                        value=st.session_state.ai_error,
                        height=100,
                        disabled=True)
        else:
            st.warning("🔃 AI: Checking...")
        
        if st.session_state.show_api_key_input or st.session_state.ai_status == "Error":
            with st.expander("🔑 Enter Gemini API Key"):
                st.session_state.manual_api_key = st.text_input(
                    "Gemini API Key:",
                    value=st.session_state.manual_api_key,
                    type="password"
                )
                if st.button("💾 Save API Key"):
                    if st.session_state.manual_api_key:
                        try:
                            genai.configure(api_key=st.session_state.manual_api_key)
                            test_service_connections()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Invalid API key: {str(e)}")
                    else:
                        st.error("Please enter an API key")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Refresh"):
                check_services_status()
                st.rerun()
        with col2:
            if st.button("🧪 Test Connections"):
                with st.spinner("Testing connections..."):
                    test_service_connections()
                    st.rerun()

def show_login_page():
    st.markdown("""
    <style>
        .login-container {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
        }
        .login-box {
            width: 400px;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            background-color: #f5f5f5;
        }
        .header {
            display: flex;
            justify-content: center;
            align-items: center;
            margin-bottom: 30px;
            flex-direction: column;
        }
        .app-title {
            font-size: 28px;
            font-weight: bold;
            color: #333;
            margin-top: 15px;
        }
        .stTextInput>div>div>input {
            padding: 10px;
            background-color: #fff;
            color: #333;
        }
        .stButton>button {
            width: 100%;
            padding: 10px;
            border-radius: 5px;
            border: none;
            background-color: #3498db;
            color: white;
            font-weight: bold;
        }
        .stButton>button:hover {
            background-color: #2980b9;
        }
    </style>
    """, unsafe_allow_html=True)

    with st.container():
        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown('<div class="header">', unsafe_allow_html=True)
            if logo:
                st.image(logo, width=150)
            st.markdown('<div class="app-title">PPH CRM</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with col2:
            st.markdown("### Login")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            
            if st.button("Login"):
                valid_users = {
                    "prakash": "PPHprakash123@",
                    "mangal": "mangal123@",
                    "manish": "mKPPH2025$",
                    "rajeev": "rajeev123@",
                    "ashish": "ashish123@",
                    "arun": "arunazad123@",
                    "admin": "admin123!@#"
                }
                
                if username.lower() in valid_users and password == valid_users[username.lower()]:
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.session_state.is_admin = (username.lower() == "prakash")
                    st.rerun()
                else:
                    st.error("Invalid username or password")

def apply_theme_settings():
    font_sizes = {
        "Small": "14px",
        "Medium": "16px",
        "Large": "18px"
    }
    
    current_font_size = font_sizes.get(st.session_state.font_size, "16px")
    
    st.markdown(f"""
    <style>
        .stApp {{
            background-color: #ffffff;
            color: #333333;
            font-size: {current_font_size};
        }}
        .css-1d391kg, .css-1y4p8pa {{
            background-color: #f5f5f5;
        }}
        .stTextInput>div>div>input, .stTextArea>div>div>textarea {{
            background-color: #ffffff;
            color: #333333;
            font-size: {current_font_size};
            border: 1px solid #ddd;
        }}
        .st-bb, .st-at, .st-ae, .st-af, .st-ag, .st-ah, .st-ai, .st-aj, .st-ak, .st-al {{
            font-size: {current_font_size};
            color: #333333;
        }}
        .sidebar .sidebar-content {{
            font-size: {current_font_size};
            background-color: #f5f5f5;
            color: #333333;
        }}
        .stButton>button {{
            color: #ffffff;
            background-color: #3498db;
        }}
        .stButton>button:hover {{
            background-color: #2980b9;
        }}
        .stAlert {{
            color: #333333;
        }}
        .st-expander {{
            background-color: #ffffff;
            border: 1px solid #ddd;
        }}
    </style>
    """, unsafe_allow_html=True)

def show_main_menu():
    st.markdown("""
    <style>
        .menu-container {
            display: flex;
            flex-direction: column;
            gap: 20px;
            margin-top: 50px;
        }
        .menu-item {
            padding: 30px;
            background-color: #f5f5f5;
            border-radius: 10px;
            display: flex;
            justify-content: center;
            align-items: center;
            cursor: pointer;
            transition: transform 0.3s;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            height: 120px;
        }
        .menu-item:hover {
            transform: scale(1.02);
            background-color: #e5e5e5;
        }
        .menu-icon {
            font-size: 40px;
            margin-right: 15px;
        }
        .menu-title {
            font-size: 28px;
            font-weight: bold;
        }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="header">', unsafe_allow_html=True)
    if logo:
        st.image(logo, width=150)
    st.markdown('<div class="app-title">PPH CRM</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="menu-container">', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📝 Entry Module", use_container_width=True):
            st.session_state.current_module = "Entry"
            st.rerun()
    
    with col2:
        if st.button("🛠️ PPH Office Tools", use_container_width=True):
            st.session_state.current_module = "PPH Office Tools"
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def show_entry_module():
    if not st.session_state.authenticated:
        show_login_page()
        return

    # Update available journals list
    st.session_state.available_journals = get_available_journals()
    
    st.title("📝 PPH CRM - Entry Module")
    
    if logo:
        st.image(logo, width=100)

    st.session_state.app_mode = st.radio(
        "Select Operation",
        ["📝 Create Entries", "📤 Upload Entries", "🔍 Search Database", "📚 Manage Journals"],
        horizontal=True
    )

    if st.session_state.app_mode == "📝 Create Entries":
        st.header("📝 Create Entries")
        
        with st.expander("⚙️ Processing Settings", expanded=False):
            st.session_state.chunk_size = st.slider(
                "Entries per chunk (adjust for performance):",
                min_value=10,
                max_value=100,
                value=50,
                step=10,
                help="Smaller chunks are more reliable but slower. Larger chunks are faster but may timeout."
            )
        
        uploaded_file = st.file_uploader("📄 Or upload a file to process", type=["txt"])
        if uploaded_file:
            uploaded_entries = process_uploaded_file(uploaded_file)
            if uploaded_entries:
                st.session_state.uploaded_entries = uploaded_entries
                st.text_area("Paste author entries here (one entry per paragraph):", 
                            value="\n\n".join(uploaded_entries), 
                            height=300,
                            key="create_entries_text")
        
        raw_text = st.text_area("Paste author entries here (one entry per paragraph):", height=300, key="create_entries_text")
        
        if st.session_state.create_entry_stage == 'format':
            if st.button("✨ Format Entries"):
                if raw_text.strip():
                    status_text = st.empty()
                    formatted = format_entries_chunked(raw_text, status_text)
                    
                    if formatted:
                        st.session_state.formatted_entries = formatted.split('\n\n')
                        st.session_state.formatted_text = formatted
                        st.session_state.show_formatting_results = True
                        st.session_state.create_entry_stage = 'download'
                        st.rerun()
        
        if st.session_state.show_formatting_results and st.session_state.formatted_text:
            st.subheader("Formatted Results")
            st.text_area("Formatted Entries", value=st.session_state.formatted_text, height=300, disabled=True)
            
            if st.session_state.create_entry_stage == 'download':
                st.subheader("Download Options")
                st.download_button(
                    "📥 Download Formatted Entries",
                    st.session_state.formatted_text,
                    file_name="formatted_entries.txt",
                    mime="text/plain"
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("➡️ Proceed to Save"):
                        st.session_state.create_entry_stage = 'save'
                        st.rerun()
                with col2:
                    if st.button("🔄 Restart Process"):
                        st.session_state.create_entry_stage = 'format'
                        st.session_state.show_formatting_results = False
                        st.session_state.formatted_entries = []
                        st.session_state.formatted_text = ""
                        st.rerun()
            
            if st.session_state.create_entry_stage == 'save':
                st.subheader("Save to Database")
                selected_journal = st.selectbox("Select Journal:", st.session_state.available_journals)
                filename = st.text_input("Filename:", get_suggested_filename(selected_journal))
                
                if st.button("💾 Save to Database"):
                    if selected_journal and filename:
                        status_text = st.empty()
                        if save_entries_with_progress(st.session_state.formatted_entries, selected_journal, filename, status_text):
                            st.session_state.create_entry_stage = 'format'
                            st.session_state.show_formatting_results = False
                            st.session_state.formatted_entries = []
                            st.session_state.formatted_text = ""
                            st.rerun()

# Main app flow
if __name__ == "__main__":
    if time.time() - st.session_state.last_activity_time > 30:
        st.session_state.last_activity_time = time.time()
    
    if not st.session_state.authenticated:
        show_login_page()
    else:
        apply_theme_settings()
        
        with st.sidebar:
            show_connection_status()
            
            st.markdown("---")
            
            if st.button("🏠 Home"):
                st.session_state.current_module = None
                st.rerun()
            
            st.markdown("---")
            
            expander = st.expander("⚙️ Settings", expanded=False)
            with expander:
                st.subheader("Appearance")
                new_font_size = st.selectbox(
                    "Font Size",
                    ["Small", "Medium", "Large"],
                    index=["Small", "Medium", "Large"].index(st.session_state.font_size)
                )
                
                new_theme = st.selectbox(
                    "Theme",
                    ["Light", "Dark"],
                    index=["Light", "Dark"].index(st.session_state.theme)
                )
                
                if st.button("💾 Save Settings"):
                    st.session_state.font_size = new_font_size
                    st.session_state.theme = new_theme
                    st.session_state.bg_color = "#ffffff" if new_theme == "Light" else "#1a1a1a"
                    st.success("Settings saved successfully!")
                    apply_theme_settings()
                    st.rerun()
            
            st.markdown("---")
            st.markdown(f"Logged in as: **{st.session_state.username}**")
            
            if st.button("🚪 Logout"):
                st.session_state.authenticated = False
                st.session_state.username = ""
                st.session_state.is_admin = False
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
    st.markdown("**PPH CRM - Contact App Administrator for any help at: [contact@cpsharma.com](mailto:contact@cpsharma.com)**")

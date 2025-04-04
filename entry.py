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
import json

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
        'bg_color': '#1a1a1a',
        'theme': 'Dark',
        'current_module': None,
        'cloud_status': 'Not checked',
        'ai_status': 'Not checked',
        'cloud_error': '',
        'ai_error': '',
        'show_all_entries': False,
        'manual_api_key': 'AIzaSyBIXgqTphaQq8u3W5A4HRHVhwBp_fbnfsg',
        'show_api_key_input': False,
        'delete_duplicates_mode': False
    }
    
    for key, default_value in session_vars.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

# MUST BE FIRST STREAMLIT COMMAND
st.set_page_config(page_title="PPH CRM", layout="wide", initial_sidebar_state="expanded")
init_session_state()

# ======================
# FIREBASE INITIALIZATION
# ======================
def initialize_firebase():
    """Initialize Firebase with proper error handling and singleton pattern"""
    try:
        # Check if already initialized
        if firebase_admin._apps:
            st.session_state.cloud_status = "Connected"
            return True
            
        # Load Firebase config from Streamlit secrets
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
    """Get Firestore client with initialization check"""
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

def extract_author_email(entry):
    """Extract author name and email from entry for duplicate detection"""
    lines = entry.split('\n')
    if len(lines) < 2:
        return None, None
    
    # First line is name (remove "Professor" prefix if present)
    name = lines[0].replace("Professor", "").strip()
    email = lines[-1].strip()
    
    return name, email

# ======================
# DATABASE FUNCTIONS
# ======================
def test_service_connections():
    """Test both Cloud and AI connections with retries"""
    max_retries = 3
    retry_delay = 2  # seconds
    
    # Test AI
    for attempt in range(max_retries):
        try:
            # Check if manual API key is provided
            api_key = st.session_state.manual_api_key if st.session_state.manual_api_key else os.getenv("GOOGLE_API_KEY")
            if not api_key:
                st.session_state.ai_status = "Error"
                st.session_state.ai_error = "No API key provided"
                break
                
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-2.0-flash")
            response = model.generate_content("Test connection")
            if response.text:
                st.session_state.ai_status = "Connected"
                st.session_state.ai_error = ""
                break
        except Exception as e:
            st.session_state.ai_status = "Error"
            st.session_state.ai_error = str(e)
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (attempt + 1))
    
    # Test Cloud
    for attempt in range(max_retries):
        try:
            db = get_firestore_db()
            if db:
                db.collection("test").document("test").get()
                st.session_state.cloud_status = "Connected"
                st.session_state.cloud_error = ""
                break
        except Exception as e:
            st.session_state.cloud_status = "Error"
            st.session_state.cloud_error = str(e)
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (attempt + 1))

def check_services_status():
    """Check and update the status of Cloud and AI services"""
    st.session_state.cloud_status = "Checking..."
    st.session_state.ai_status = "Checking..."
    st.session_state.cloud_error = ""
    st.session_state.ai_error = ""
    test_service_connections()

def initialize_services():
    # Get API key from environment variables or manual input
    API_KEY = st.session_state.manual_api_key if st.session_state.manual_api_key else os.getenv("GOOGLE_API_KEY")
    
    if not API_KEY:
        st.session_state.ai_status = "Error"
        st.session_state.ai_error = "No valid API key provided"
        st.session_state.show_api_key_input = True
        return False

    # AI Initialization
    try:
        genai.configure(api_key=API_KEY)
        st.session_state.ai_status = "Connected"
    except Exception as e:
        st.session_state.ai_status = "Error"
        st.session_state.ai_error = str(e)
        st.session_state.show_api_key_input = True
        return False

    # Firebase Initialization
    return initialize_firebase()

# Check services status on startup
if st.session_state.cloud_status == 'Not checked' and st.session_state.ai_status == 'Not checked':
    check_services_status()

services_initialized = initialize_services()

# Predefined journal list
JOURNAL_NAMES = [
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
]

def get_available_journals():
    all_journals = []
    db = get_firestore_db()
    if db:
        try:
            journals_ref = db.collection("journals").stream()
            all_journals = [journal.id for journal in journals_ref]
        except Exception as e:
            st.error(f"Error fetching journals: {str(e)}")
    return sorted(list(set(JOURNAL_NAMES + all_journals)))

st.session_state.available_journals = get_available_journals()

def check_duplicates(new_entries):
    """Check for duplicates across all journals and return only unique entries"""
    unique_entries = []
    duplicate_info = {}
    db = get_firestore_db()
    if not db:
        return unique_entries, duplicate_info
        
    # Create a dictionary to track the latest version of each author
    author_entries = {}
    
    # First check existing entries in database
    for journal in db.collection("journals").stream():
        for file in db.collection("journals").document(journal.id).collection("files").stream():
            existing_entries = file.to_dict().get("entries", [])
            for existing_entry in existing_entries:
                name, email = extract_author_email(existing_entry)
                if name and email:
                    key = f"{name.lower()}_{email.lower()}"
                    author_entries[key] = {
                        "entry": existing_entry,
                        "journal": journal.id,
                        "filename": file.id,
                        "timestamp": file.to_dict().get("last_updated", datetime.now())
                    }
    
    # Now check new entries against existing ones
    for new_entry in new_entries:
        name, email = extract_author_email(new_entry)
        if not name or not email:
            continue  # Skip invalid entries
            
        key = f"{name.lower()}_{email.lower()}"
        
        if key in author_entries:
            # This is a duplicate
            if key not in duplicate_info:
                duplicate_info[key] = []
            duplicate_info[key].append({
                "entry": new_entry,
                "journal": "NEW_UPLOAD",
                "filename": "NEW_UPLOAD",
                "timestamp": datetime.now()
            })
            # Keep the existing entry (don't add to unique_entries)
        else:
            # This is a new unique entry
            unique_entries.append(new_entry)
            # Add to author_entries to check against subsequent new entries
            author_entries[key] = {
                "entry": new_entry,
                "journal": "NEW_UPLOAD",
                "filename": "NEW_UPLOAD",
                "timestamp": datetime.now()
            }
    
    return unique_entries, duplicate_info

def delete_all_duplicates():
    """Delete all duplicate entries across the system, keeping only the latest version of each"""
    db = get_firestore_db()
    if not db:
        return False, "Database connection failed"
    
    try:
        # First collect all entries across all journals
        all_entries = {}
        journals_to_update = {}
        
        for journal in db.collection("journals").stream():
            journal_name = journal.id
            journals_to_update[journal_name] = {}
            
            for file in db.collection("journals").document(journal_name).collection("files").stream():
                file_name = file.id
                entries = file.to_dict().get("entries", [])
                last_updated = file.to_dict().get("last_updated", datetime.now())
                
                journals_to_update[journal_name][file_name] = {
                    "entries": entries,
                    "last_updated": last_updated
                }
                
                for entry in entries:
                    name, email = extract_author_email(entry)
                    if name and email:
                        key = f"{name.lower()}_{email.lower()}"
                        
                        if key not in all_entries:
                            all_entries[key] = []
                            
                        all_entries[key].append({
                            "entry": entry,
                            "journal": journal_name,
                            "filename": file_name,
                            "timestamp": last_updated
                        })
        
        # Now identify duplicates and keep only the latest version
        entries_to_keep = {}
        duplicates_found = 0
        
        for key, entries in all_entries.items():
            if len(entries) > 1:
                duplicates_found += len(entries) - 1
                # Sort by timestamp (newest first)
                sorted_entries = sorted(entries, key=lambda x: x["timestamp"], reverse=True)
                # Keep only the first (newest) entry
                entries_to_keep[key] = sorted_entries[0]
            else:
                entries_to_keep[key] = entries[0]
        
        if duplicates_found == 0:
            return True, "No duplicates found"
        
        # Now update all journals/files to remove duplicates
        for journal_name, files in journals_to_update.items():
            for file_name, file_data in files.items():
                original_entries = file_data["entries"]
                updated_entries = []
                
                for entry in original_entries:
                    name, email = extract_author_email(entry)
                    if name and email:
                        key = f"{name.lower()}_{email.lower()}"
                        # Only keep if this is the version we're keeping
                        if key in entries_to_keep and entries_to_keep[key]["entry"] == entry:
                            updated_entries.append(entry)
                
                # Update the file if entries changed
                if len(updated_entries) != len(original_entries):
                    doc_ref = db.collection("journals").document(journal_name).collection("files").document(file_name)
                    doc_ref.update({
                        "entries": updated_entries,
                        "entry_count": len(updated_entries),
                        "last_updated": datetime.now()
                    })
        
        return True, f"Removed {duplicates_found} duplicate entries, keeping only the latest versions"
    
    except Exception as e:
        return False, f"Error during duplicate removal: {str(e)}"

def format_entries_chunked(text, progress_bar, status_text):
    if st.session_state.ai_status != "Connected":
        st.error("AI service is not available. Cannot format entries.")
        return ""
        
    start_time = time.time()
    chunk_size = 10000
    chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
    formatted_parts = []
    total_chunks = len(chunks)
    
    progress_bar.progress(0)
    status_text.text("Starting AI processing...")
    
    for i, chunk in enumerate(chunks):
        elapsed = time.time() - start_time
        chunks_processed = i + 1
        avg_time_per_chunk = elapsed / chunks_processed
        remaining_time = (total_chunks - chunks_processed) * avg_time_per_chunk
        
        progress = int(chunks_processed / total_chunks * 100)
        progress_bar.progress(progress)
        status_text.text(f"Processing {chunks_processed}/{total_chunks} (Est. remaining: {format_time(remaining_time)})")
        
        prompt = f"""Format these author entries exactly like this example:

Professor John Smith
Computer Science Department
Artificial Intelligence Laboratory
Stanford University
353 Serra Mall, Palo Alto, CA 94305
United States
jsmith@stanford.edu

CRITICAL FORMATTING RULES:
1. MANDATORY: Exclude any entry that doesn't have both a name AND an email address
2. Always prefix the name with "Professor" (even if not explicitly mentioned)
3. PRESERVE ALL ADDRESS COMPONENTS (never delete city names or other location details)
4. Structure components with EXACTLY these line breaks:
   - Name (with "Professor" prefix)
   - Department (if exists)
   - Laboratory/Institute (if exists)
   - University/Organization
   - Full street address WITH city (e.g., "710049, AXZC Road, Xi'an")
   - Country (ONLY on its own line, remove duplicates)
   - Email (must be valid and present)

ADDRESS HANDLING SPECIFICS:
- Preserve the complete address, including street numbers, postal codes, and city names.
- If the country name appears within the street address line, remove it from there. Instead, place the country name on a separate line, just before the email line.
- Never delete city names or any other location identifiers.
- Format the postal code and city in this structure: "[Postal Code], [Street Address], [City]" Example: "710049, AXZC Road, Xi'an"
- Ensure consistency across all addresses while following these formatting rules.

EMAIL VALIDATION:
- Entry MUST have an email to be included
- Standardize email format: lowercase, no spaces
- Convert (at) to @ and (dot) to .
- Remove any non-email text from the email line

Example of correct formatting:
Professor Adil Murtaza
School of Physics
MOE Key Laboratory for Nonequilibrium Synthesis
State Key Laboratory for Materials Behavior
Xi'an Jiaotong University
710049, AXZC Road, Xi'an
China
adilmurtaza91@mail.xjtu.edu.cn

Text to format:
{chunk}
"""
        
        try:
            model = genai.GenerativeModel("gemini-1.5-flash-latest")
            response = model.generate_content(prompt)
            if response.text:
                formatted_parts.append(response.text.strip())
        except Exception as e:
            st.error(f"Error during formatting: {str(e)}")
            pass
    
    # Additional validation pass to ensure no entries without emails are included
    final_entries = []
    for entry in "\n\n".join(formatted_parts).split("\n\n"):
        lines = entry.split('\n')
        if len(lines) >= 2 and '@' in lines[-1]:  # Last line must contain email
            final_entries.append(entry)
    
    processing_time = time.time() - start_time
    progress_bar.progress(100)
    status_text.text(f"Formatting complete! Time taken: {format_time(processing_time)}")
    return "\n\n".join(final_entries)

def save_entries_with_progress(entries, journal, filename, progress_bar, status_text):
    db = get_firestore_db()
    if not db:
        return False
        
    start_time = time.time()
    total_entries = len(entries)
    
    try:
        journal_ref = db.collection("journals").document(journal)
        if not journal_ref.get().exists:
            journal_ref.set({"created": datetime.now()})

        # Check for duplicates and get only unique entries
        unique_entries, duplicates = check_duplicates(entries)
        
        if duplicates:
            st.warning(f"Found {len(duplicates)} duplicate entries that will not be saved")
            with st.expander("🔍 Duplicate Details"):
                for key, dup_list in duplicates.items():
                    name, email = extract_author_email(dup_list[0]["entry"])
                    st.write(f"**Author:** {name} ({email})")
                    st.write(f"- Found {len(dup_list)} duplicate(s)")
        
        if not unique_entries:
            st.error("No unique entries to save!")
            return False

        progress_bar.progress(0)
        status_text.text("Starting database save...")
        
        batch_size = 50
        for i in range(0, total_entries, batch_size):
            elapsed = time.time() - start_time
            entries_processed = i + 1
            avg_time_per_batch = elapsed / (entries_processed / batch_size)
            remaining_time = (total_entries - entries_processed) * (avg_time_per_batch / batch_size)
            
            progress = min(100, int(entries_processed / total_entries * 100))
            progress_bar.progress(progress)
            status_text.text(f"Saving {entries_processed}/{total_entries} (Est. remaining: {format_time(remaining_time)})")
            time.sleep(0.05)

        doc_ref = db.collection("journals").document(journal).collection("files").document(filename)
        doc_ref.set({
            "entries": unique_entries,
            "last_updated": datetime.now(),
            "entry_count": len(unique_entries)
        })
        
        processing_time = time.time() - start_time
        progress_bar.progress(100)
        status_text.text(f"✅ Saved {len(unique_entries)} unique entries in {format_time(processing_time)}")
        return True
    except Exception as e:
        st.error(f"Error saving entries: {str(e)}")
        return False

def get_journal_files(journal):
    db = get_firestore_db()
    if not db or not journal:
        return []
        
    files_ref = db.collection("journals").document(journal).collection("files")
    return [{
        "name": doc.id,
        "last_updated": doc.to_dict().get("last_updated", datetime.now()),
        "entry_count": doc.to_dict().get("entry_count", 0),
        "entries": doc.to_dict().get("entries", [])
    } for doc in files_ref.stream()]

def download_entries(journal, filename):
    db = get_firestore_db()
    if not db:
        return None
        
    doc = db.collection("journals").document(journal).collection("files").document(filename).get()
    return "\n\n".join(doc.to_dict().get("entries", [])) if doc.exists else None

def delete_file(journal, filename):
    db = get_firestore_db()
    if not db:
        return False
        
    try:
        db.collection("journals").document(journal).collection("files").document(filename).delete()
        return True
    except Exception:
        return False

def create_journal(journal_name):
    db = get_firestore_db()
    if not db:
        return False
        
    try:
        db.collection("journals").document(journal_name).set({"created": datetime.now()})
        st.session_state.available_journals = get_available_journals()
        return True
    except Exception:
        return False

def update_entry(journal, filename, old_entry, new_entry):
    db = get_firestore_db()
    if not db:
        return False
        
    try:
        doc_ref = db.collection("journals").document(journal).collection("files").document(filename)
        doc = doc_ref.get()
        if doc.exists:
            entries = doc.to_dict().get("entries", [])
            if old_entry in entries:
                entries[entries.index(old_entry)] = new_entry
                doc_ref.update({
                    "entries": entries,
                    "last_updated": datetime.now(),
                    "entry_count": len(entries)
                })
                return True
        return False
    except Exception:
        return False

def delete_entry(journal, filename, entry):
    db = get_firestore_db()
    if not db:
        return False
        
    try:
        doc_ref = db.collection("journals").document(journal).collection("files").document(filename)
        doc = doc_ref.get()
        if doc.exists:
            entries = doc.to_dict().get("entries", [])
            if entry in entries:
                entries.remove(entry)
                doc_ref.update({
                    "entries": entries,
                    "last_updated": datetime.now(),
                    "entry_count": len(entries)
                })
                return True
        return False
    except Exception:
        return False

def search_entries(query):
    results = []
    db = get_firestore_db()
    if not db or not query:
        return results
        
    query = query.lower()
    for journal in db.collection("journals").stream():
        for file in db.collection("journals").document(journal.id).collection("files").stream():
            if query in file.id.lower():
                results.append({
                    "journal": journal.id,
                    "filename": file.id,
                    "entry": f"File: {file.id}",
                    "full_path": f"{journal.id} > {file.id}",
                    "is_file": True
                })
            
            entries = file.to_dict().get("entries", [])
            for entry in entries:
                if query in entry.lower():
                    results.append({
                        "journal": journal.id,
                        "filename": file.id,
                        "entry": entry,
                        "full_path": f"{journal.id} > {file.id}",
                        "is_file": False
                    })
    return results

# ======================
# UI COMPONENTS
# ======================
def show_connection_status():
    """Show the connection status of Cloud and AI services"""
    with st.sidebar:
        st.markdown("### 🔌 Connection Status")
        
        # Cloud status
        if st.session_state.cloud_status == "Connected":
            st.success("✅ Cloud: Connected")
        elif st.session_state.cloud_status == "Error":
            st.error("❌ Cloud: Error")
            st.text_area("Cloud Error Details", 
                        value=st.session_state.cloud_error,
                        height=100,
                        disabled=True)
        else:
            st.warning("🔄 Cloud: Checking...")
        
        # AI status
        if st.session_state.ai_status == "Connected":
            st.success("✅ AI: Connected")
        elif st.session_state.ai_status == "Error":
            st.error("❌ AI: Error")
            st.text_area("AI Error Details",
                        value=st.session_state.ai_error,
                        height=100,
                        disabled=True)
        else:
            st.warning("🔄 AI: Checking...")
        
        # Manual API key input
        if st.session_state.show_api_key_input or st.session_state.ai_status == "Error":
            with st.expander("🔑 Enter Gemini API Key"):
                st.session_state.manual_api_key = st.text_input(
                    "Gemini API Key:",
                    value=st.session_state.manual_api_key,
                    type="password"
                )
                if st.button("Save API Key"):
                    if st.session_state.manual_api_key:
                        try:
                            genai.configure(api_key=st.session_state.manual_api_key)
                            test_service_connections()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Invalid API key: {str(e)}")
                    else:
                        st.error("Please enter an API key")
        
        # Action buttons
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
            background-color: #2d2d2d;
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
            color: white;
            margin-top: 15px;
        }
        .stTextInput>div>div>input {
            padding: 10px;
            background-color: #3d3d3d;
            color: white;
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
                if username == "admin" and password == "admin123":
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.rerun()
                else:
                    st.error("Invalid username or password")

def show_settings():
    st.header("⚙️ Settings")
    
    with st.form("settings_form"):
        st.subheader("Appearance")
        new_font_size = st.selectbox(
            "Font Size",
            ["Small", "Medium", "Large"],
            index=["Small", "Medium", "Large"].index(st.session_state.font_size)
        )
        
        new_theme = st.selectbox(
            "Theme",
            ["Dark", "Light", "System"],
            index=["Dark", "Light", "System"].index(st.session_state.theme)
        )
        
        new_bg_color = st.color_picker(
            "Background Color",
            st.session_state.bg_color
        )
        
        if st.form_submit_button("Save Settings"):
            st.session_state.font_size = new_font_size
            st.session_state.theme = new_theme
            st.session_state.bg_color = new_bg_color
            st.success("Settings saved successfully!")
            apply_theme_settings()

def apply_theme_settings():
    font_sizes = {
        "Small": "14px",
        "Medium": "16px",
        "Large": "18px"
    }
    
    current_font_size = font_sizes.get(st.session_state.font_size, "16px")
    
    # Apply theme
    if st.session_state.theme == "Dark":
        st.markdown(f"""
        <style>
            .stApp {{
                background-color: #1a1a1a;
                color: white;
                font-size: {current_font_size};
            }}
            .css-1d391kg, .css-1y4p8pa {{
                background-color: #2d2d2d;
            }}
            .stTextInput>div>div>input, .stTextArea>div>div>textarea {{
                background-color: #3d3d3d;
                color: white;
                font-size: {current_font_size};
            }}
            .st-bb, .st-at, .st-ae, .st-af, .st-ag, .st-ah, .st-ai, .st-aj, .st-ak, .st-al {{
                font-size: {current_font_size};
            }}
            .sidebar .sidebar-content {{
                font-size: {current_font_size};
            }}
        </style>
        """, unsafe_allow_html=True)
    elif st.session_state.theme == "Light":
        st.markdown(f"""
        <style>
            .stApp {{
                background-color: white;
                color: black;
                font-size: {current_font_size};
            }}
            .sidebar .sidebar-content {{
                font-size: {current_font_size};
            }}
        </style>
        """, unsafe_allow_html=True)
    else:  # System
        st.markdown(f"""
        <style>
            .stApp {{
                font-size: {current_font_size};
            }}
            .sidebar .sidebar-content {{
                font-size: {current_font_size};
            }}
        </style>
        """, unsafe_allow_html=True)
    
    # Apply background color
    st.markdown(f"""
    <style>
        .stApp {{
            background-color: {st.session_state.bg_color};
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
            background-color: #2d2d2d;
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
            background-color: #3d3d3d;
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
        if st.button("📝 Entry Module", key="entry_btn", use_container_width=True):
            st.session_state.current_module = "Entry"
            st.rerun()
    
    with col2:
        if st.button("🛠️ PPH Office Tools", key="tools_btn", use_container_width=True):
            st.session_state.current_module = "PPH Office Tools"
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def show_entry_module():
    if not st.session_state.authenticated:
        show_login_page()
        return

    st.title("📚 PPH CRM - Entry Module")
    
    if logo:
        st.image(logo, width=100)

    # Sidebar navigation for entry module
    app_mode = st.sidebar.radio("Select Operation", [
        "🔍 Search Database",
        "📤 Upload Entries",
        "✏️ Create Entries",
        "🗂 Manage Journals"
    ])

    if app_mode == "🔍 Search Database":
        st.header("🔍 Search Database")
        search_col1, search_col2 = st.columns([3, 1])
        with search_col1:
            search_query = st.text_input("Search for entries or filenames:", value=st.session_state.search_query)
        with search_col2:
            if st.button("Search"):
                if get_firestore_db():
                    st.session_state.search_query = search_query
                    st.session_state.search_results = search_entries(search_query)
                    st.session_state.show_search_results = True

        if st.session_state.show_search_results and st.session_state.search_results:
            st.subheader(f"Search Results ({len(st.session_state.search_results)} matches)")
            
            sort_col1, sort_col2 = st.columns(2)
            with sort_col1:
                sort_by = st.selectbox("Sort by", ["Relevance", "Journal", "Filename"])
            with sort_col2:
                sort_order = st.selectbox("Order", ["Descending", "Ascending"])
            
            if sort_by == "Journal":
                st.session_state.search_results.sort(key=lambda x: x["journal"], reverse=(sort_order == "Descending"))
            elif sort_by == "Filename":
                st.session_state.search_results.sort(key=lambda x: x["filename"], reverse=(sort_order == "Descending"))
            
            for result in st.session_state.search_results[:50]:
                with st.container():
                    st.markdown(f"**Journal:** {result['journal']}  \n**File:** {result['filename']}")
                    
                    if result.get("is_file", False):
                        st.text(f"File: {result['filename']}")
                        # Add download button for files
                        if st.button("📥 Download", key=f"dl_{result['journal']}_{result['filename']}"):
                            content = download_entries(result["journal"], result["filename"])
                            if content:
                                st.download_button(
                                    label="Download Now",
                                    data=content,
                                    file_name=f"{result['filename']}.txt",
                                    mime="text/plain"
                                )
                    else:
                        if st.session_state.current_edit_entry == result['entry']:
                            edited_entry = st.text_area("Edit entry:", value=result["entry"], height=150, 
                                                      key=f"edit_{result['journal']}_{result['filename']}_{hash(result['entry'])}")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("Save", key=f"save_{result['journal']}_{result['filename']}_{hash(result['entry'])}"):
                                    if update_entry(result["journal"], result["filename"], result["entry"], edited_entry):
                                        st.success("Entry updated successfully!")
                                        st.session_state.current_edit_entry = None
                                        st.session_state.search_results = search_entries(st.session_state.search_query)
                            with col2:
                                if st.button("Cancel", key=f"cancel_{result['journal']}_{result['filename']}_{hash(result['entry'])}"):
                                    st.session_state.current_edit_entry = None
                        else:
                            st.text_area("Entry:", value=result["entry"], height=150, 
                                        key=f"view_{result['journal']}_{result['filename']}_{hash(result['entry'])}", 
                                        disabled=True)
                    
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        if not result.get("is_file", False) and st.button("✏️ Edit", key=f"edit_btn_{result['journal']}_{result['filename']}_{hash(result['entry'])}"):
                            st.session_state.current_edit_entry = result['entry']
                    with col2:
                        if not result.get("is_file", False) and st.button("🗑️ Delete", key=f"delete_{result['journal']}_{result['filename']}_{hash(result['entry'])}"):
                            st.session_state.deleting_entry = result
                    st.markdown("---")

    elif app_mode == "📤 Upload Entries":
        st.header("📤 Upload Entries")
        
        # Add the "Delete Duplicate Entries" button at the top
        if st.button("✅ Delete Duplicate Entries", type="primary", 
                   help="Remove all duplicate entries from the entire system, keeping only the latest version of each"):
            st.session_state.delete_duplicates_mode = True
        
        if st.session_state.delete_duplicates_mode:
            with st.spinner("Searching for and removing duplicates..."):
                success, message = delete_all_duplicates()
                if success:
                    st.success(message)
                else:
                    st.error(message)
                st.session_state.delete_duplicates_mode = False
        
        uploaded_file = st.file_uploader("Upload TXT file with author entries", type=["txt"])
        
        if uploaded_file:
            st.session_state.upload_journal = st.selectbox(
                "Select Journal for Uploaded Entries:",
                st.session_state.available_journals
            )
            
            st.session_state.upload_filename = st.text_input(
                "Filename for uploaded entries:",
                get_suggested_filename(st.session_state.upload_journal)
            )
            
            uploaded_entries = process_uploaded_file(uploaded_file)
            if uploaded_entries:
                st.session_state.uploaded_entries = uploaded_entries
                st.success(f"Found {len(uploaded_entries)} raw entries in file")
                
                if st.button("Process Uploaded Entries"):
                    with st.spinner("Checking for duplicates..."):
                        unique_entries, duplicates = check_duplicates(st.session_state.uploaded_entries)
                        
                        if duplicates:
                            st.warning(f"Found {len(duplicates)} duplicate entries that will not be saved")
                            with st.expander("🔍 Duplicate Details"):
                                for key, dup_list in duplicates.items():
                                    name, email = extract_author_email(dup_list[0]["entry"])
                                    st.write(f"**Author:** {name} ({email})")
                                    st.write(f"- Found {len(dup_list)} duplicate(s)")
                        
                        st.session_state.entries = unique_entries
                        st.success(f"{len(unique_entries)} unique entries ready to save")
                        st.session_state.show_save_section = True

        if st.session_state.get('show_save_section', False) and st.session_state.entries:
            st.subheader("Processed Entries")
            st.info(f"Total unique entries ready to save: {len(st.session_state.entries)}")
            
            # Download option
            if st.button("Download Unique Entries"):
                entries_text = "\n\n".join(st.session_state.entries)
                st.download_button(
                    label="Download Now",
                    data=entries_text,
                    file_name=f"{st.session_state.upload_filename}_unique_entries.txt",
                    mime="text/plain"
                )
            
            if st.button("Save to Database"):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                if save_entries_with_progress(
                    st.session_state.entries,
                    st.session_state.upload_journal,
                    st.session_state.upload_filename,
                    progress_bar,
                    status_text
                ):
                    st.success("Unique entries saved successfully!")
                    st.session_state.show_save_section = False

    elif app_mode == "✏️ Create Entries":
        st.header("✏️ Create Entries")
        
        raw_text = st.text_area("Paste author entries here (one entry per paragraph):", height=300)
        
        if st.button("Format Entries"):
            if raw_text.strip():
                if st.session_state.ai_status != "Connected":
                    st.error("AI service is not available. Please check your API key in the sidebar.")
                else:
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    formatted = format_entries_chunked(raw_text, progress_bar, status_text)
                    if formatted:
                        entries = formatted.split("\n\n")
                        st.session_state.entries = entries
                        st.success(f"Formatted {len(entries)} entries!")
                        st.session_state.show_save_section = True
                        st.session_state.show_all_entries = False
                    else:
                        st.error("Formatting failed. Check your input.")
            else:
                st.warning("Please paste some content first")

        if st.session_state.get('show_save_section', False) and st.session_state.entries:
            st.subheader("Formatted Entries")
            st.info(f"Total formatted entries: {len(st.session_state.entries)}")
            
            if not st.session_state.show_all_entries:
                st.write("Showing first 30 entries:")
                for entry in st.session_state.entries[:30]:
                    st.text_area("", value=entry, height=150, disabled=True)
                
                if len(st.session_state.entries) > 30:
                    if st.button("Show All Entries"):
                        st.session_state.show_all_entries = True
                        st.rerun()
                    
                    if st.button("Download All Entries"):
                        entries_text = "\n\n".join(st.session_state.entries)
                        st.download_button(
                            label="Download All Entries",
                            data=entries_text,
                            file_name="formatted_entries.txt",
                            mime="text/plain"
                        )
            else:
                st.write("Showing all entries:")
                for entry in st.session_state.entries:
                    st.text_area("", value=entry, height=150, disabled=True)
                
                entries_text = "\n\n".join(st.session_state.entries)
                st.download_button(
                    label="Download All Entries",
                    data=entries_text,
                    file_name="formatted_entries.txt",
                    mime="text/plain"
                )
            
            selected_journal = st.selectbox("Select Journal:", st.session_state.available_journals)
            filename = st.text_input("Filename:", get_suggested_filename(selected_journal))
            
            if st.button("Save to Database"):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                if save_entries_with_progress(
                    st.session_state.entries,
                    selected_journal,
                    filename,
                    progress_bar,
                    status_text
                ):
                    st.success("Entries saved successfully!")
                    st.session_state.show_save_section = False

    elif app_mode == "🗂 Manage Journals":
        st.header("🗂 Manage Journals")
        
        tab1, tab2 = st.tabs(["View Journals", "Create New Journal"])
        
        with tab1:
            st.subheader("Available Journals")
            if not st.session_state.available_journals:
                st.info("No journals available. Create a new journal first.")
            else:
                selected_journal = st.selectbox("Select Journal:", st.session_state.available_journals)
                
                if selected_journal:
                    files = get_journal_files(selected_journal)
                    if files:
                        st.subheader(f"Files in {selected_journal}")
                        
                        for file in files:
                            with st.expander(f"{file['name']} ({file['entry_count']} entries)"):
                                col1, col2, col3 = st.columns([3, 1, 1])
                                with col1:
                                    last_updated = file["last_updated"]
                                    if isinstance(last_updated, datetime):
                                        st.write(f"Last updated: {last_updated.strftime('%d-%b-%Y %H:%M')}")
                                    else:
                                        st.write("Last updated: Unknown")
                                
                                with col2:
                                    if st.button("📥 Download", key=f"dl_{file['name']}"):
                                        content = download_entries(selected_journal, file['name'])
                                        if content:
                                            st.download_button(
                                                label="Download Now",
                                                data=content,
                                                file_name=f"{file['name']}.txt",
                                                mime="text/plain"
                                            )
                                
                                with col3:
                                    if st.button("🗑️ Delete", key=f"del_{file['name']}"):
                                        st.session_state.deleting_file = {
                                            "journal": selected_journal,
                                            "filename": file['name']
                                        }
                    else:
                        st.info(f"No files yet in {selected_journal}")
        
        with tab2:
            st.subheader("Create New Journal")
            with st.form(key="new_journal_form"):
                journal_name = st.text_input("Journal Name:")
                if st.form_submit_button("Create Journal"):
                    if journal_name.strip():
                        if create_journal(journal_name):
                            st.success(f"Journal '{journal_name}' created successfully!")
                        else:
                            st.error("Failed to create journal")
                    else:
                        st.warning("Please enter a journal name")

    # Handle modals and dialogs
    if st.session_state.deleting_entry:
        result = st.session_state.deleting_entry
        st.warning(f"Are you sure you want to delete this entry from {result['full_path']}?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Confirm Delete"):
                if delete_entry(result["journal"], result["filename"], result["entry"]):
                    st.success("Entry deleted successfully!")
                    st.session_state.deleting_entry = None
                    st.session_state.search_results = search_entries(st.session_state.search_query)
                else:
                    st.error("Failed to delete entry")
        with col2:
            if st.button("Cancel"):
                st.session_state.deleting_entry = None

    if st.session_state.deleting_file:
        file_info = st.session_state.deleting_file
        st.warning(f"Are you sure you want to delete '{file_info['filename']}' from {file_info['journal']}?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Yes, Delete"):
                if delete_file(file_info["journal"], file_info["filename"]):
                    st.success("File deleted successfully!")
                    st.session_state.deleting_file = None
                else:
                    st.error("Failed to delete file")
        with col2:
            if st.button("Cancel"):
                st.session_state.deleting_file = None

# ======================
# MAIN APP FLOW
# ======================
if not st.session_state.authenticated:
    show_login_page()
else:
    # Show connection status in sidebar
    show_connection_status()
    
    if st.session_state.current_module is None:
        show_main_menu()
    else:
        if st.session_state.current_module == "Entry":
            show_entry_module()
        elif st.session_state.current_module == "PPH Office Tools":
            st.header("🛠️ PPH Office Tools")
            st.info("Coming soon!")

    # Sidebar with logout button
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Logout"):
        st.session_state.authenticated = False
        st.session_state.username = ""
        st.session_state.current_module = None
        st.rerun()

    # Show user info
    st.sidebar.markdown(f"Logged in as: **{st.session_state.username}**")
    
    # Apply theme settings when authenticated
    apply_theme_settings()

# ======================
# FOOTER
# ======================
st.markdown("---")
st.markdown("**PPH CRM - Author Database Manager**")

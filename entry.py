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
import spacy
from spacy.matcher import Matcher
from spacy.language import Language

# Load environment variables from .env file
load_dotenv()

# Load multiple language models for spaCy
language_models = {
    'en': None,
    'es': None,
    'fr': None,
    'de': None,
    'it': None,
    'pt': None,
    'ru': None,
    'zh': None,
    'ja': None,
    'ar': None
}

def load_language_models():
    for lang in language_models:
        try:
            if lang == 'en':
                language_models[lang] = spacy.load("en_core_web_sm")
            elif lang == 'zh':
                language_models[lang] = spacy.load("zh_core_web_sm")
            elif lang == 'ja':
                language_models[lang] = spacy.load("ja_core_news_sm")
            else:
                try:
                    language_models[lang] = spacy.load(f"{lang}_core_news_sm")
                except:
                    # Fallback to blank model if specific model not available
                    language_models[lang] = spacy.blank(lang)
        except:
            from spacy.cli import download
            download(f"{lang}_core_news_sm")
            language_models[lang] = spacy.load(f"{lang}_core_news_sm")

load_language_models()

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
# ENHANCED NLP PROCESSING FUNCTIONS
# ======================
def detect_language(text):
    """Simple language detection based on common words"""
    text = text.lower()
    lang_scores = {
        'en': sum(1 for word in ['the', 'and', 'of', 'university', 'department'] if word in text),
        'es': sum(1 for word in ['y', 'de', 'universidad', 'departamento'] if word in text),
        'fr': sum(1 for word in ['et', 'de', 'université', 'département'] if word in text),
        'de': sum(1 for word in ['und', 'der', 'universität', 'abteilung'] if word in text),
        'it': sum(1 for word in ['e', 'di', 'università', 'dipartimento'] if word in text),
        'pt': sum(1 for word in ['e', 'de', 'universidade', 'departamento'] if word in text),
        'ru': sum(1 for word in ['и', 'университет', 'кафедра'] if word in text),
        'zh': sum(1 for word in ['大学', '系'] if word in text),
        'ja': sum(1 for word in ['大学', '学科'] if word in text),
        'ar': sum(1 for word in ['جامعة', 'قسم'] if word in text)
    }
    return max(lang_scores.items(), key=lambda x: x[1])[0]

def extract_institution_info(text):
    """Extract institution information from text in any language"""
    lang = detect_language(text)
    nlp = language_models[lang]
    doc = nlp(text)
    
    institution_types = [
        'university', 'college', 'institute', 'academy', 'school', 
        'université', 'universidad', 'universität', 'università', '大学', 'جامعة',
        'department', 'faculty', 'laboratory', 'institute', 'center', 'centre',
        'département', 'departamento', 'abteilung', 'dipartimento', '系', 'قسم'
    ]
    
    institution_info = {
        'name': '',
        'type': '',
        'department': '',
        'country': '',
        'email': ''
    }
    
    # Extract email
    for token in doc:
        if "@" in token.text:
            email = token.text.lower()
            email = email.replace("(at)", "@").replace("[at]", "@")
            email = email.replace("(dot)", ".").replace("[dot]", ".")
            email = email.replace(" ", "")
            institution_info['email'] = email
            break
    
    # Extract country (GPE = geopolitical entity)
    for ent in doc.ents:
        if ent.label_ == "GPE" and len(ent.text.split()) <= 3:
            institution_info['country'] = ent.text
            break
    
    # Extract institution name and type
    for token in doc:
        lower_token = token.text.lower()
        if any(inst_type in lower_token for inst_type in institution_types):
            # Get the full institution name
            start = token.i
            while start > 0 and doc[start-1].ent_type_ in ("", "ORG"):
                start -= 1
            end = token.i + 1
            while end < len(doc) and doc[end].ent_type_ in ("", "ORG"):
                end += 1
            
            institution_name = doc[start:end].text
            if not institution_info['name']:
                institution_info['name'] = institution_name
                institution_info['type'] = token.text
    
    # Extract department/school/faculty
    department_patterns = [
        [{"LOWER": {"IN": ["department", "dept", "departamento", "département", "abteilung", "系", "قسم"]}}],
        [{"LOWER": {"IN": ["school", "faculty", "escuela", "école", "fakultät", "学部"]}}],
        [{"LOWER": {"IN": ["laboratory", "lab", "laboratoire", "laboratorio"]}}],
        [{"LOWER": {"IN": ["institute", "institut", "instituto", "研究所"]}}],
        [{"LOWER": {"IN": ["center", "centre", "centro", "مركز"]}}]
    ]
    
    matcher = Matcher(nlp.vocab)
    for i, pattern in enumerate(department_patterns):
        matcher.add(f"DEPT_{i}", [pattern])
    
    matches = matcher(doc)
    for match_id, start, end in matches:
        span = doc[start:end]
        # Get the full department name
        while start > 0 and doc[start-1].ent_type_ in ("", "ORG"):
            start -= 1
        while end < len(doc) and doc[end].ent_type_ in ("", "ORG"):
            end += 1
        institution_info['department'] = doc[start:end].text
        break
    
    return institution_info

def format_with_nlp(entry):
    """Format entry using enhanced NLP processing"""
    lines = [line.strip() for line in entry.split('\n') if line.strip()]
    
    # Extract name (first line is usually name)
    name = lines[0].replace("Prof.", "").replace("Professor", "").strip()
    if not name:
        return None
    
    # Join all lines for processing
    full_text = " ".join(lines)
    
    # Extract components
    info = extract_institution_info(full_text)
    
    if not info['email']:
        return None
    
    # Build formatted entry
    formatted_lines = [f"Professor {name}"]
    if info['department']:
        formatted_lines.append(info['department'])
    if info['name']:
        formatted_lines.append(info['name'])
    if info['country']:
        formatted_lines.append(info['country'])
    formatted_lines.append(info['email'])
    
    return "\n".join(formatted_lines)

def preprocess_with_nlp(text):
    """Process raw text with NLP before AI formatting"""
    entries = [entry.strip() for entry in text.split("\n\n") if entry.strip()]
    formatted_entries = []
    
    for entry in entries:
        formatted = format_with_nlp(entry)
        if formatted:
            formatted_entries.append(formatted)
    
    return "\n\n".join(formatted_entries)

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

def extract_author_email(entry):
    lines = entry.split('\n')
    if len(lines) < 2:
        return None, None
    
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
            api_key = st.session_state.manual_api_key if st.session_state.manual_api_key else os.getenv("GOOGLE_API_KEY")
            if not api_key:
                st.session_state.ai_status = "Error"
                st.session_state.ai_error = "No API key provided"
                break
                
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-1.5-flash-latest")
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
    API_KEY = st.session_state.manual_api_key if st.session_state.manual_api_key else os.getenv("GOOGLE_API_KEY")
    
    if not API_KEY:
        st.session_state.ai_status = "Error"
        st.session_state.ai_error = "No valid API key provided"
        st.session_state.show_api_key_input = True
        return False

    try:
        genai.configure(api_key=API_KEY)
        st.session_state.ai_status = "Connected"
    except Exception as e:
        st.session_state.ai_status = "Error"
        st.session_state.ai_error = str(e)
        st.session_state.show_api_key_input = True
        return False

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
    unique_entries = []
    duplicate_info = {}
    db = get_firestore_db()
    if not db:
        return unique_entries, duplicate_info
        
    author_entries = {}
    
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
    
    for new_entry in new_entries:
        name, email = extract_author_email(new_entry)
        if not name or not email:
            continue
            
        key = f"{name.lower()}_{email.lower()}"
        
        if key in author_entries:
            if key not in duplicate_info:
                duplicate_info[key] = []
            duplicate_info[key].append({
                "entry": new_entry,
                "journal": "NEW_UPLOAD",
                "filename": "NEW_UPLOAD",
                "timestamp": datetime.now()
            })
        else:
            unique_entries.append(new_entry)
            author_entries[key] = {
                "entry": new_entry,
                "journal": "NEW_UPLOAD",
                "filename": "NEW_UPLOAD",
                "timestamp": datetime.now()
            }
    
    return unique_entries, duplicate_info

def delete_all_duplicates():
    db = get_firestore_db()
    if not db:
        return False, "Database connection failed"
    
    try:
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
        
        entries_to_keep = {}
        duplicates_found = 0
        
        for key, entries in all_entries.items():
            if len(entries) > 1:
                duplicates_found += len(entries) - 1
                sorted_entries = sorted(entries, key=lambda x: x["timestamp"], reverse=True)
                entries_to_keep[key] = sorted_entries[0]
            else:
                entries_to_keep[key] = entries[0]
        
        if duplicates_found == 0:
            return True, "No duplicates found"
        
        for journal_name, files in journals_to_update.items():
            for file_name, file_data in files.items():
                original_entries = file_data["entries"]
                updated_entries = []
                
                for entry in original_entries:
                    name, email = extract_author_email(entry)
                    if name and email:
                        key = f"{name.lower()}_{email.lower()}"
                        if key in entries_to_keep and entries_to_keep[key]["entry"] == entry:
                            updated_entries.append(entry)
                
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

def format_entries_chunked(text, status_text):
    if st.session_state.ai_status != "Connected":
        st.error("AI service is not available. Cannot format entries.")
        return ""
        
    start_time = time.time()
    
    # First process with NLP
    nlp_processed = preprocess_with_nlp(text)
    if not nlp_processed:
        return ""
    
    # Then refine with AI
    chunk_size = 10000
    chunks = [nlp_processed[i:i+chunk_size] for i in range(0, len(nlp_processed), chunk_size)]
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
        
        prompt = f"""Refine these pre-processed author entries to ensure consistent formatting:

Professor First Name Last Name
Department/Laboratory/School (if available)
University/Organization/Institution
Country
email@domain.com

RULES:
1. Keep only the corresponding address if multiple exist
2. Remove all street addresses, postal codes, etc. - keep only country
3. Keep all institution types (university, college, institute, etc.)
4. Keep all department types (department, school, faculty, laboratory, etc.)
5. Remove any additional information like phone numbers, ORCID, etc.
6. Ensure email is clean and properly formatted
7. Preserve original language of the address

Example of correct formatting:
Professor John Smith
Department of Computer Science
Stanford University
United States
jsmith@stanford.edu

Professor Maria García
Escuela de Ingeniería
Universidad de Barcelona
Spain
mgarcia@ub.edu

Text to refine:
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
    
    final_entries = []
    for entry in "\n\n".join(formatted_parts).split("\n\n"):
        lines = entry.split('\n')
        if len(lines) >= 2 and '@' in lines[-1]:
            final_entries.append(entry)
    
    processing_time = time.time() - start_time
    progress_bar.progress(100)
    status_text.text(f"Formatting complete! Time taken: {format_time(processing_time)}")
    return "\n\n".join(final_entries)

def save_entries_with_progress(entries, journal, filename, status_text):
    db = get_firestore_db()
    if not db:
        return False
        
    start_time = time.time()
    total_entries = len(entries)
    
    try:
        journal_ref = db.collection("journals").document(journal)
        if not journal_ref.get().exists:
            journal_ref.set({"created": datetime.now()})

        unique_entries, duplicates = check_duplicates(entries)
        
        if duplicates:
            st.warning(f"Found {len(duplicates)} duplicate entries that will not be saved")
            with st.expander("🔍 Duplicate Details", key=f"duplicates_{filename}"):
                for key, dup_list in duplicates.items():
                    name, email = extract_author_email(dup_list[0]["entry"])
                    st.write(f"**Author:** {name} ({email})")
                    st.write(f"- Found {len(dup_list)} duplicate(s)")
        
        if not unique_entries:
            st.error("No unique entries to save!")
            return False

        progress_bar = st.progress(0)
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
        
    try:
        files_ref = db.collection("journals").document(journal).collection("files")
        files = []
        for doc in files_ref.stream():
            file_data = doc.to_dict()
            files.append({
                "name": doc.id,
                "last_updated": file_data.get("last_updated", datetime.now()),
                "entry_count": file_data.get("entry_count", len(file_data.get("entries", []))),
                "entries": file_data.get("entries", [])
            })
        return files
    except Exception as e:
        st.error(f"Error fetching files: {str(e)}")
        return []

def download_entries(journal, filename):
    db = get_firestore_db()
    if not db:
        return None, 0
        
    try:
        doc = db.collection("journals").document(journal).collection("files").document(filename).get()
        if doc.exists:
            entries = doc.to_dict().get("entries", [])
            entry_count = doc.to_dict().get("entry_count", len(entries))
            return "\n\n".join(entries), entry_count
        return None, 0
    except Exception as e:
        st.error(f"Error downloading entries: {str(e)}")
        return None, 0

def delete_file(journal, filename):
    db = get_firestore_db()
    if not db:
        return False
        
    try:
        db.collection("journals").document(journal).collection("files").document(filename).delete()
        return True
    except Exception as e:
        st.error(f"Error deleting file: {str(e)}")
        return False

def create_journal(journal_name):
    db = get_firestore_db()
    if not db:
        return False
        
    try:
        db.collection("journals").document(journal_name).set({"created": datetime.now()})
        st.session_state.available_journals = get_available_journals()
        return True
    except Exception as e:
        st.error(f"Error creating journal: {str(e)}")
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
    except Exception as e:
        st.error(f"Error updating entry: {str(e)}")
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
    except Exception as e:
        st.error(f"Error deleting entry: {str(e)}")
        return False

def search_entries(query):
    results = []
    db = get_firestore_db()
    if not db or not query:
        return results
        
    try:
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
    except Exception as e:
        st.error(f"Error searching entries: {str(e)}")
        return []

# ======================
# UI COMPONENTS
# ======================
def show_connection_status():
    with st.sidebar.expander("📶 Connection Status", expanded=False):
        if st.session_state.cloud_status == "Connected":
            st.success("✅ Cloud: Connected")
        elif st.session_state.cloud_status == "Error":
            st.error("❌ Cloud: Error")
            st.text_area("Cloud Error Details", 
                        value=st.session_state.cloud_error,
                        height=100,
                        disabled=True,
                        key="cloud_error_details")
        else:
            st.warning("🔄 Cloud: Checking...")
        
        if st.session_state.ai_status == "Connected":
            st.success("✅ AI: Connected")
        elif st.session_state.ai_status == "Error":
            st.error("❌ AI: Error")
            st.text_area("AI Error Details",
                        value=st.session_state.ai_error,
                        height=100,
                        disabled=True,
                        key="ai_error_details")
        else:
            st.warning("🔄 AI: Checking...")
        
        if st.session_state.show_api_key_input or st.session_state.ai_status == "Error":
            with st.expander("🔑 Enter Gemini API Key", key="api_key_expander"):
                st.session_state.manual_api_key = st.text_input(
                    "Gemini API Key:",
                    value=st.session_state.manual_api_key,
                    type="password",
                    key="api_key_input"
                )
                if st.button("Save API Key", key="save_api_key"):
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
            if st.button("🔄 Refresh", key="refresh_connections"):
                check_services_status()
                st.rerun()
        with col2:
            if st.button("🧪 Test Connections", key="test_connections"):
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
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            
            if st.button("Login", key="login_button"):
                valid_users = {
                    "prakash": "prakash123@",
                    "mangal": "mangal123@",
                    "manish": "manish123@",
                    "rajeev": "rajeev123@",
                    "ashish": "ashish123@",
                    "arun": "arunazad123@",
                    "admin": "admin123"
                }
                
                if username.lower() in valid_users and password == valid_users[username.lower()]:
                    st.session_state.authenticated = True
                    st.session_state.username = username
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

    # Operation selector in main content area with unique key
    st.session_state.app_mode = st.radio(
        "Select Operation",
        ["✏️ Create Entries", "📤 Upload Entries", "🔍 Search Database", "🗂 Manage Journals"],
        key="operation_selector",
        horizontal=True
    )

    if st.session_state.app_mode == "✏️ Create Entries":
        st.header("✏️ Create Entries")
        
        raw_text = st.text_area("Paste author entries here (one entry per paragraph):", 
                              height=300, 
                              key="raw_entries_input")
        
        if st.button("Format Entries", key="format_entries_btn"):
            if raw_text.strip():
                if st.session_state.ai_status != "Connected":
                    st.error("AI service is not available. Please check your API key in the sidebar.")
                else:
                    status_text = st.empty()
                    formatted = format_entries_chunked(raw_text, status_text)
                    if formatted:
                        entries = formatted.split("\n\n")
                        st.session_state.entries = entries
                        st.success(f"Formatted {len(entries)} entries!")
                        st.session_state.show_save_section = True
                        st.session_state.show_formatted_entries = False
                    else:
                        st.error("Formatting failed. Check your input.")
            else:
                st.warning("Please paste some content first")

        if st.session_state.get('show_save_section', False) and st.session_state.entries:
            st.subheader("Formatted Entries")
            st.info(f"Total formatted entries: {len(st.session_state.entries)}")
            
            if st.button("👁️ Show Formatted Entries", key="toggle_formatted_entries"):
                st.session_state.show_formatted_entries = not st.session_state.show_formatted_entries
            
            if st.session_state.show_formatted_entries:
                st.write("Showing first 30 entries:")
                for i, entry in enumerate(st.session_state.entries[:30]):
                    st.text_area("", 
                               value=entry, 
                               height=150, 
                               disabled=True,
                               key=f"entry_{i}")
                
                if len(st.session_state.entries) > 30:
                    if st.button("Show All Entries", key="show_all_btn"):
                        st.session_state.show_all_entries = True
                        st.rerun()
                    
                    if st.button("Download All Entries", key="download_all_btn"):
                        entries_text = "\n\n".join(st.session_state.entries)
                        st.download_button(
                            label="Download All Entries",
                            data=entries_text,
                            file_name="formatted_entries.txt",
                            mime="text/plain",
                            key="download_all_entries_btn"
                        )
            
            entries_text = "\n\n".join(st.session_state.entries)
            st.download_button(
                label="Download All Entries",
                data=entries_text,
                file_name="formatted_entries.txt",
                mime="text/plain",
                key="download_full_entries_btn"
            )
            
            selected_journal = st.selectbox("Select Journal:", 
                                          st.session_state.available_journals,
                                          key="save_journal_select")
            filename = st.text_input("Filename:", 
                                   get_suggested_filename(selected_journal),
                                   key="save_filename_input")
            
            if st.button("Save to Database", key="final_save_btn"):
                status_text = st.empty()
                
                if save_entries_with_progress(
                    st.session_state.entries,
                    selected_journal,
                    filename,
                    status_text
                ):
                    st.success("Entries saved successfully!")
                    st.session_state.show_save_section = False

    elif st.session_state.app_mode == "📤 Upload Entries":
        st.header("📤 Upload Entries")
        
        if st.button("✅ Delete Duplicate Entries", 
                    type="primary", 
                    key="delete_duplicates_btn",
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
        
        uploaded_file = st.file_uploader("Upload TXT file with author entries", 
                                        type=["txt"], 
                                        key="file_uploader")
        
        if uploaded_file:
            st.session_state.upload_journal = st.selectbox(
                "Select Journal for Uploaded Entries:",
                st.session_state.available_journals,
                key="upload_journal_select"
            )
            
            st.session_state.upload_filename = st.text_input(
                "Filename for uploaded entries:",
                get_suggested_filename(st.session_state.upload_journal),
                key="upload_filename_input"
            )
            
            uploaded_entries = process_uploaded_file(uploaded_file)
            if uploaded_entries:
                st.session_state.uploaded_entries = uploaded_entries
                st.success(f"Found {len(uploaded_entries)} raw entries in file")
                
                if st.button("Process Uploaded Entries", key="process_upload_btn"):
                    with st.spinner("Checking for duplicates..."):
                        unique_entries, duplicates = check_duplicates(st.session_state.uploaded_entries)
                        
                        if duplicates:
                            st.warning(f"Found {len(duplicates)} duplicate entries that will not be saved")
                            with st.expander("🔍 Duplicate Details", key="duplicates_expander"):
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
            
            if st.button("Download Unique Entries", key="download_unique_btn"):
                entries_text = "\n\n".join(st.session_state.entries)
                st.download_button(
                    label="Download Now",
                    data=entries_text,
                    file_name=f"{st.session_state.upload_filename}_unique_entries.txt",
                    mime="text/plain",
                    key="download_unique_entries_btn"
                )
            
            if st.button("Save to Database", key="save_to_db_btn"):
                status_text = st.empty()
                
                if save_entries_with_progress(
                    st.session_state.entries,
                    st.session_state.upload_journal,
                    st.session_state.upload_filename,
                    status_text
                ):
                    st.success("Unique entries saved successfully!")
                    st.session_state.show_save_section = False

    elif st.session_state.app_mode == "🔍 Search Database":
        st.header("🔍 Search Database")
        search_col1, search_col2 = st.columns([3, 1])
        with search_col1:
            search_query = st.text_input("Search for entries or filenames:", 
                                       value=st.session_state.search_query,
                                       key="search_input")
        with search_col2:
            if st.button("Search", key="search_button"):
                if get_firestore_db():
                    st.session_state.search_query = search_query
                    st.session_state.search_results = search_entries(search_query)
                    st.session_state.show_search_results = True

        if st.session_state.show_search_results and st.session_state.search_results:
            st.subheader(f"Search Results ({len(st.session_state.search_results)} matches)")
            
            sort_col1, sort_col2 = st.columns(2)
            with sort_col1:
                sort_by = st.selectbox("Sort by", ["Relevance", "Journal", "Filename"], key="sort_by")
            with sort_col2:
                sort_order = st.selectbox("Order", ["Descending", "Ascending"], key="sort_order")
            
            if sort_by == "Journal":
                st.session_state.search_results.sort(key=lambda x: x["journal"], reverse=(sort_order == "Descending"))
            elif sort_by == "Filename":
                st.session_state.search_results.sort(key=lambda x: x["filename"], reverse=(sort_order == "Descending"))
            
            for i, result in enumerate(st.session_state.search_results[:50]):
                with st.container():
                    st.markdown(f"**Journal:** {result['journal']}  \n**File:** {result['filename']}")
                    
                    if result.get("is_file", False):
                        st.text(f"File: {result['filename']}")
                        if st.button("📥 Download", key=f"dl_{result['journal']}_{result['filename']}_{i}"):
                            content, entry_count = download_entries(result["journal"], result["filename"])
                            if content:
                                st.download_button(
                                    label="Download Now",
                                    data=content,
                                    file_name=f"{result['filename']} ({entry_count} entries).txt",
                                    mime="text/plain",
                                    key=f"download_{result['filename']}_{i}"
                                )
                    else:
                        if st.session_state.current_edit_entry == result['entry']:
                            edited_entry = st.text_area("Edit entry:", 
                                                       value=result["entry"], 
                                                       height=150, 
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
                            st.text_area("Entry:", 
                                        value=result["entry"], 
                                        height=150, 
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

    elif st.session_state.app_mode == "🗂 Manage Journals":
        st.header("🗂 Manage Journals")
        
        tab1, tab2 = st.tabs(["View Journals", "Create New Journal"])
        
        with tab1:
            st.subheader("Available Journals")
            if not st.session_state.available_journals:
                st.info("No journals available. Create a new journal first.")
            else:
                selected_journal = st.selectbox("Select Journal:", 
                                               st.session_state.available_journals,
                                               key="journal_select")
                
                if selected_journal:
                    files = get_journal_files(selected_journal)
                    if files:
                        st.subheader(f"Files in {selected_journal}")
                        
                        for i, file in enumerate(files):
                            try:
                                with st.expander(f"{file['name']} ({file['entry_count']} entries)", key=f"file_expander_{i}"):
                                    col1, col2, col3 = st.columns([3, 1, 1])
                                    with col1:
                                        last_updated = file["last_updated"]
                                        if isinstance(last_updated, datetime):
                                            st.write(f"Last updated: {last_updated.strftime('%d-%b-%Y %H:%M')}")
                                        else:
                                            st.write("Last updated: Unknown")
                                    
                                    with col2:
                                        if st.button("📥 Download", key=f"dl_{file['name']}_{i}"):
                                            content, entry_count = download_entries(selected_journal, file['name'])
                                            if content:
                                                st.download_button(
                                                    label="Download Now",
                                                    data=content,
                                                    file_name=f"{file['name']} ({entry_count} entries).txt",
                                                    mime="text/plain",
                                                    key=f"dl_btn_{file['name']}_{i}"
                                                )
                                    
                                    with col3:
                                        if st.button("🗑️ Delete", key=f"del_{file['name']}_{i}"):
                                            st.session_state.deleting_file = {
                                                "journal": selected_journal,
                                                "filename": file['name']
                                            }
                            except Exception as e:
                                st.error(f"Error displaying file: {str(e)}")
                                continue
                    else:
                        st.info(f"No files yet in {selected_journal}")
        
        with tab2:
            st.subheader("Create New Journal")
            with st.form(key="new_journal_form"):
                journal_name = st.text_input("Journal Name:", key="new_journal_name")
                submit_button = st.form_submit_button("Create Journal")
                
                if submit_button:
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
            if st.button("Confirm Delete", key="confirm_delete_entry"):
                if delete_entry(result["journal"], result["filename"], result["entry"]):
                    st.success("Entry deleted successfully!")
                    st.session_state.deleting_entry = None
                    st.session_state.search_results = search_entries(st.session_state.search_query)
                else:
                    st.error("Failed to delete entry")
        with col2:
            if st.button("Cancel", key="cancel_delete_entry"):
                st.session_state.deleting_entry = None

    if st.session_state.deleting_file:
        file_info = st.session_state.deleting_file
        st.warning(f"Are you sure you want to delete '{file_info['filename']}' from {file_info['journal']}?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Yes, Delete", key="confirm_delete_file"):
                if delete_file(file_info["journal"], file_info["filename"]):
                    st.success("File deleted successfully!")
                    st.session_state.deleting_file = None
                else:
                    st.error("Failed to delete file")
        with col2:
            if st.button("Cancel", key="cancel_delete_file"):
                st.session_state.deleting_file = None

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
st.markdown("**PPH CRM - Contract App Administrator for any help at: [contact@cpsharma.com](mailto:contact@cpsharma.com)**")

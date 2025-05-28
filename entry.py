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
        'app_mode': "?? Create Entries",
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
        'deleting_journal': None
    }
    for key, default_value in session_vars.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

st.set_page_config(page_title="PPH CRM", layout="wide", initial_sidebar_state="expanded")
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
    clean_name = re.sub(r'[^a-zA-Z0-9]', '_', journal)
    return f"{clean_name}_{datetime.now().strftime('%Y%m%d')}.txt"

def process_uploaded_file(uploaded_file):
    """Process uploaded file and return entries"""
    try:
        stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
        text = stringio.read()
        entries = [entry.strip() for entry in text.split("\n\n") if entry.strip()]
        return entries
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
        return []

# Regex processing functions
def preprocess_with_regex(text):
    """Clean up text before sending to AI using saved regex filters"""
    if not st.session_state.regex_filters:
        return text
    
    for pattern in st.session_state.regex_filters:
        try:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        except:
            continue
    
    return '\n'.join([line.strip() for line in text.split('\n') if line.strip()])

def load_regex_filters():
    """Load regex filters from Firestore"""
    db = get_firestore_db()
    if not db:
        return []
    
    try:
        filters_ref = db.collection("regex_filters")
        filters = []
        for doc in filters_ref.stream():
            filters.append(doc.to_dict().get("pattern", ""))
        return filters
    except Exception as e:
        st.error(f"Error loading regex filters: {str(e)}")
        return []

def save_regex_filter(pattern):
    """Save a new regex filter to Firestore"""
    db = get_firestore_db()
    if not db:
        return False
    
    try:
        doc_ref = db.collection("regex_filters").document()
        doc_ref.set({
            "pattern": pattern,
            "created_by": st.session_state.username,
            "created_at": datetime.now()
        })
        st.session_state.regex_filters = load_regex_filters()
        return True
    except Exception as e:
        st.error(f"Error saving regex filter: {str(e)}")
        return False

def delete_regex_filter(pattern):
    """Delete a regex filter from Firestore"""
    db = get_firestore_db()
    if not db:
        return False
    
    try:
        filters_ref = db.collection("regex_filters")
        for doc in filters_ref.where("pattern", "==", pattern).stream():
            doc.reference.delete()
        st.session_state.regex_filters = load_regex_filters()
        return True
    except Exception as e:
        st.error(f"Error deleting regex filter: {str(e)}")
        return False

def load_ai_prompts():
    """Load AI prompts from Firestore"""
    db = get_firestore_db()
    if not db:
        return []
    
    try:
        prompts_ref = db.collection("ai_prompts")
        prompts = []
        for doc in prompts_ref.stream():
            prompt_data = doc.to_dict()
            prompt_data["id"] = doc.id
            prompts.append(prompt_data)
        return prompts
    except Exception as e:
        st.error(f"Error loading AI prompts: {str(e)}")
        return []

def save_ai_prompt(name, input_text, output_text):
    """Save a new AI prompt example to Firestore"""
    db = get_firestore_db()
    if not db:
        return False
    
    try:
        doc_ref = db.collection("ai_prompts").document()
        doc_ref.set({
            "name": name,
            "input": input_text,
            "output": output_text,
            "created_by": st.session_state.username,
            "created_at": datetime.now()
        })
        st.session_state.ai_prompts = load_ai_prompts()
        return True
    except Exception as e:
        st.error(f"Error saving AI prompt: {str(e)}")
        return False

def delete_ai_prompt(prompt_id):
    """Delete an AI prompt from Firestore"""
    db = get_firestore_db()
    if not db:
        return False
    
    try:
        db.collection("ai_prompts").document(prompt_id).delete()
        st.session_state.ai_prompts = load_ai_prompts()
        return True
    except Exception as e:
        st.error(f"Error deleting AI prompt: {str(e)}")
        return False

# Firebase functions
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

def save_entries_with_progress(entries, journal, filename, status_text):
    db = get_firestore_db()
    if not db:
        return False
        
    try:
        journal_ref = db.collection("journals").document(journal)
        if not journal_ref.get().exists:
            journal_ref.set({"created": datetime.now()})

        # Check for duplicates and get only unique entries
        unique_entries, duplicates = check_duplicates(entries)
        
        if duplicates:
            st.warning(f"Found {len(duplicates)} duplicate entries that will not be saved")
            with st.expander("?? Duplicate Details"):
                for key, dup_list in duplicates.items():
                    name, email = extract_author_email(dup_list[0]["entry"])
                    st.write(f"**Author:** {name} ({email})")
                    st.write(f"- Found {len(dup_list)} duplicate(s)")
        
        if not unique_entries:
            st.error("No unique entries to save!")
            return False

        doc_ref = db.collection("journals").document(journal).collection("files").document(filename)
        doc_ref.set({
            "entries": unique_entries,
            "last_updated": datetime.now(),
            "entry_count": len(unique_entries)
        })
        return True
    except Exception as e:
        st.error(f"Error saving entries: {str(e)}")
        return False

def get_available_journals():
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
    """Extract author name and email from entry for duplicate detection"""
    lines = entry.split('\n')
    if len(lines) < 2:
        return None, None
    
    # First line is name (remove "Professor" prefix if present)
    name = lines[0].replace("Professor", "").strip()
    email = lines[-1].strip()
    
    return name, email

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

def delete_journal(journal_name):
    db = get_firestore_db()
    if not db:
        return False
        
    try:
        # First delete all files in the journal
        files_ref = db.collection("journals").document(journal_name).collection("files")
        for file in files_ref.stream():
            file.reference.delete()
        
        # Then delete the journal itself
        db.collection("journals").document(journal_name).delete()
        
        # Update available journals
        st.session_state.available_journals = get_available_journals()
        return True
    except Exception as e:
        st.error(f"Error deleting journal: {str(e)}")
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

def rename_file(journal, old_filename, new_filename):
    db = get_firestore_db()
    if not db:
        return False
        
    try:
        # Get the existing file data
        doc_ref = db.collection("journals").document(journal).collection("files").document(old_filename)
        doc = doc_ref.get()
        
        if not doc.exists:
            return False
            
        file_data = doc.to_dict()
        
        # Create new document with the same data
        db.collection("journals").document(journal).collection("files").document(new_filename).set(file_data)
        
        # Delete the old document
        doc_ref.delete()
        
        return True
    except Exception as e:
        st.error(f"Error renaming file: {str(e)}")
        return False

def move_file(source_journal, filename, target_journal):
    db = get_firestore_db()
    if not db:
        return False
        
    try:
        # Get the existing file data
        doc_ref = db.collection("journals").document(source_journal).collection("files").document(filename)
        doc = doc_ref.get()
        
        if not doc.exists:
            return False
            
        file_data = doc.to_dict()
        
        # Create new document in target journal
        db.collection("journals").document(target_journal).collection("files").document(filename).set(file_data)
        
        # Delete the old document
        doc_ref.delete()
        
        return True
    except Exception as e:
        st.error(f"Error moving file: {str(e)}")
        return False

# AI processing function with improved progress tracking and activity monitoring
def format_entries_chunked(text, status_text):
    if st.session_state.ai_status != "Connected":
        st.error("AI service is not available")
        return ""
        
    st.session_state.processing_start_time = time.time()
    preprocessed = preprocess_with_regex(text)
    entries = [entry.strip() for entry in preprocessed.split("\n\n") if entry.strip()]
    
    if not entries:
        return ""
    
    chunks = ['\n\n'.join(entries[i:i+50]) for i in range(0, len(entries), 50)]
    st.session_state.total_chunks = len(chunks)
    st.session_state.current_chunk = 0
    formatted_parts = []
    
    progress_bar = st.progress(0)
    status_text.text("Processing...")
    
    # Get the best available prompt
    best_prompt = """You are an intelligent academic address refiner. Given a raw academic author affiliation block, clean and format the address into exactly five lines according to the structure below:

Name  
Department (if available)  
University (most specific, if available)  
Country (if available)  
email@domain.com

Rules to Follow:

1. Include the Department only if explicitly mentioned (e.g., Department of Chemistry or School of Engineering).
2. Only include the most specific University or Institute name (e.g., Harbin Institute of Technology).
3. If both a College and a University are listed, retain only the University.
4. Remove all the following:
	- Postal codes, cities, buildings, room numbers, and internal unit codes.
	- Lab names, centers, or research groups unless no department or school is present.
	- Extra metadata like "View in Scopus", "Corresponding Author", "Authors at", their educational degree like Dr, Phd, etc.
5. Format with exactly one component per line (Name, Department, University, Country, Email) and no blank lines.
6. If multiple affiliations are given:
	- For multiple affiliations, list each author's full name, department, university, country, and email. Do not skip any authors, even if a corresponding author is marked.
7. Preserve proper capitalization, and avoid abbreviations unless officially part of the name.
8. Never include duplicate information, address fragments, or unrelated affiliations.
9. Take only "Corresponding authors at" address if given, in multiple address of single author.
10. Ensure there are no asterisks (**) or other unnecessary symbols in the resulted text. 
11. Do not write "Department not provided" or "email not provided" or anything similar in the formatted entries.
12. Do not merge or combine any entries. Separate each entry with a blank line. Only include entries in the result that contain at least one email address.
13. Exclude all postal addresses; only author affiliation, country, and email are required.
14. Convert UTF-8 texts into regular readable text.

Entries to format:
{chunk}"""
    
    if st.session_state.ai_prompts:
        # If we have saved prompts, use the most recent one as an example
        latest_prompt = st.session_state.ai_prompts[-1]
        best_prompt = f"""Format these author entries exactly like the following example:

EXAMPLE INPUT:
{latest_prompt['input']}

EXAMPLE OUTPUT:
{latest_prompt['output']}

Entries to format:
{{chunk}}"""
    
    for i, chunk in enumerate(chunks):
        st.session_state.current_chunk = i + 1
        progress = int((i + 1) / len(chunks) * 100)
        progress_bar.progress(progress)
        
        # Update activity time to prevent timeout
        st.session_state.last_activity_time = time.time()
        
        # Calculate estimated time remaining
        elapsed = time.time() - st.session_state.processing_start_time
        if i > 0:  # Only estimate after first chunk
            avg_time_per_chunk = elapsed / (i + 1)
            remaining_chunks = len(chunks) - (i + 1)
            estimated_remaining = avg_time_per_chunk * remaining_chunks
            status_text.text(
                f"Processing chunk {i+1}/{len(chunks)} "
                f"({progress}%) - "
                f"Estimated time remaining: {format_time(estimated_remaining)}"
            )
        
        try:
            genai.configure(api_key=st.session_state.manual_api_key or os.getenv("GOOGLE_API_KEY"))
            model = genai.GenerativeModel("gemini-1.5-flash-latest")
            response = model.generate_content(best_prompt.format(chunk=chunk))
            if response.text:
                formatted_parts.append(response.text)
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    processing_time = time.time() - st.session_state.processing_start_time
    progress_bar.progress(100)
    status_text.text(f"Completed in {format_time(processing_time)}")
    return '\n\n'.join(formatted_parts)

def test_service_connections():
    max_retries = 3
    retry_delay = 2
    
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

def load_logo():
    try:
        response = requests.get("https://github.com/prakashsharma19/hosted-images/raw/main/pphlogo.png")
        img = Image.open(BytesIO(response.content))
        return img
    except:
        return None

logo = load_logo()

def show_connection_status():
    with st.sidebar.expander("?? Connection Status", expanded=False):
        if st.session_state.cloud_status == "Connected":
            st.success("? Cloud: Connected")
        elif st.session_state.cloud_status == "Error":
            st.error("? Cloud: Error")
            st.text_area("Cloud Error Details", 
                        value=st.session_state.cloud_error,
                        height=100,
                        disabled=True)
        else:
            st.warning("?? Cloud: Checking...")
        
        if st.session_state.ai_status == "Connected":
            st.success("? AI: Connected")
        elif st.session_state.ai_status == "Error":
            st.error("? AI: Error")
            st.text_area("AI Error Details",
                        value=st.session_state.ai_error,
                        height=100,
                        disabled=True)
        else:
            st.warning("?? AI: Checking...")
        
        if st.session_state.show_api_key_input or st.session_state.ai_status == "Error":
            with st.expander("?? Enter Gemini API Key"):
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
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("?? Refresh"):
                check_services_status()
                st.rerun()
        with col2:
            if st.button("?? Test Connections"):
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
                    "manish": "manish123@",
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
        if st.button("?? Entry Module", use_container_width=True):
            st.session_state.current_module = "Entry"
            st.rerun()
    
    with col2:
        if st.button("??? PPH Office Tools", use_container_width=True):
            st.session_state.current_module = "PPH Office Tools"
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def show_regex_manager():
    st.subheader("?? Regex Filter Management")
    st.write("Add patterns to automatically filter before AI processing")
    
    # Display current filters
    st.write("**Current Filters:**")
    if not st.session_state.regex_filters:
        st.info("No regex filters saved yet")
    else:
        for i, pattern in enumerate(st.session_state.regex_filters):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.code(pattern)
            with col2:
                if st.button("???", key=f"del_regex_{i}"):
                    if delete_regex_filter(pattern):
                        st.success("Filter deleted successfully!")
                        st.rerun()
    
    # Add new filter
    with st.form(key="add_regex_form"):
        new_filter = st.text_input("New Regex Pattern:", value=st.session_state.new_regex_filter)
        if st.form_submit_button("Add Filter"):
            if new_filter.strip():
                if save_regex_filter(new_filter.strip()):
                    st.success("Filter added successfully!")
                    st.session_state.new_regex_filter = ""
                    st.rerun()
                else:
                    st.error("Failed to add filter")

def show_prompt_manager():
    st.subheader("?? AI Prompt Improvement")
    st.write("Add examples to improve the AI's formatting")
    
    # Display saved prompts
    st.write("**Saved Prompts:**")
    if not st.session_state.ai_prompts:
        st.info("No AI prompts saved yet")
    else:
        for prompt in st.session_state.ai_prompts:
            expander = st.expander(f"?? {prompt.get('name', 'Unnamed')}")
            with expander:
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Input:**")
                    st.text_area("", value=prompt.get("input", ""), height=150, disabled=True, key=f"input_{prompt['id']}")
                with col2:
                    st.write("**Output:**")
                    st.text_area("", value=prompt.get("output", ""), height=150, disabled=True, key=f"output_{prompt['id']}")
                
                if st.button("??? Delete", key=f"delete_{prompt['id']}"):
                    if delete_ai_prompt(prompt['id']):
                        st.success("Prompt deleted successfully!")
                        st.rerun()
    
    # Add new prompt example
    with st.form(key="add_prompt_form"):
        st.write("**Add New Example:**")
        name = st.text_input("Example Name:", value=st.session_state.new_prompt_name)
        col1, col2 = st.columns(2)
        with col1:
            input_text = st.text_area("Unformatted Input:", height=200, value=st.session_state.new_prompt_input)
        with col2:
            output_text = st.text_area("Formatted Output:", height=200, value=st.session_state.new_prompt_output)
        
        if st.form_submit_button("Save Example"):
            if name.strip() and input_text.strip() and output_text.strip():
                if save_ai_prompt(name.strip(), input_text.strip(), output_text.strip()):
                    st.success("Example saved successfully!")
                    st.session_state.new_prompt_name = ""
                    st.session_state.new_prompt_input = ""
                    st.session_state.new_prompt_output = ""
                    st.rerun()
                else:
                    st.error("Failed to save example")

def show_entry_module():
    if not st.session_state.authenticated:
        show_login_page()
        return

    # Load regex filters and AI prompts if admin
    if st.session_state.is_admin:
        if 'regex_filters' not in st.session_state or not st.session_state.regex_filters:
            st.session_state.regex_filters = load_regex_filters()
        if 'ai_prompts' not in st.session_state or not st.session_state.ai_prompts:
            st.session_state.ai_prompts = load_ai_prompts()

    st.title("?? PPH CRM - Entry Module")
    
    if logo:
        st.image(logo, width=100)

    # Show admin tools if logged in as admin
    if st.session_state.is_admin:
        admin_col1, admin_col2 = st.columns(2)
        with admin_col1:
            if st.button("?? Manage Regex Filters"):
                st.session_state.show_regex_manager = not st.session_state.show_regex_manager
        with admin_col2:
            if st.button("?? Improve AI Prompts"):
                st.session_state.show_prompt_manager = not st.session_state.show_prompt_manager
        
        if st.session_state.show_regex_manager:
            show_regex_manager()
            st.markdown("---")
        
        if st.session_state.show_prompt_manager:
            show_prompt_manager()
            st.markdown("---")

    # Update available journals list
    st.session_state.available_journals = get_available_journals()

    st.session_state.app_mode = st.radio(
        "Select Operation",
        ["?? Create Entries", "?? Upload Entries", "?? Search Database", "?? Manage Journals"],
        horizontal=True
    )

    if st.session_state.app_mode == "?? Create Entries":
        st.header("?? Create Entries")
        raw_text = st.text_area("Paste author entries here (one entry per paragraph):", height=300)
        
        if st.button("Format Entries"):
            if raw_text.strip():
                status_text = st.empty()
                formatted = format_entries_chunked(raw_text, status_text)
                if formatted:
                    st.session_state.entries = formatted.split('\n\n')
                    st.success(f"Formatted {len(st.session_state.entries)} entries!")
                    st.session_state.show_save_section = True
            
        if st.session_state.get('show_save_section', False) and st.session_state.entries:
            st.subheader("Formatted Entries")
            
            if st.button("Show Formatted Entries"):
                st.session_state.show_formatted_entries = not st.session_state.show_formatted_entries
            
            if st.session_state.show_formatted_entries:
                st.write("Showing first 30 entries:")
                for i, entry in enumerate(st.session_state.entries[:30]):
                    st.text_area("", value=entry, height=150, disabled=True, key=f"entry_{i}")
                
                if len(st.session_state.entries) > 30:
                    if st.button("Show All Entries"):
                        st.session_state.show_all_entries = True
                        st.rerun()
                    
                    if st.button("Download All Entries"):
                        entries_text = "\n\n".join(st.session_state.entries)
                        st.download_button(
                            label="Download Now",
                            data=entries_text,
                            file_name="formatted_entries.txt",
                            mime="text/plain"
                        )
            
            entries_text = "\n\n".join(st.session_state.entries)
            st.download_button(
                "Download All Entries",
                entries_text,
                "formatted_entries.txt"
            )
            
            selected_journal = st.selectbox("Select Journal:", st.session_state.available_journals)
            filename = st.text_input("Filename:", get_suggested_filename(selected_journal))
            
            if st.button("Save to Database"):
                status_text = st.empty()
                if save_entries_with_progress(st.session_state.entries, selected_journal, filename, status_text):
                    st.success("Entries saved successfully!")
                    st.session_state.show_save_section = False

    elif st.session_state.app_mode == "?? Upload Entries":
        st.header("?? Upload Entries")
        
        if st.button("? Delete Duplicate Entries", type="primary", help="Remove all duplicate entries from the entire system"):
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
                            with st.expander("?? Duplicate Details"):
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
            
            if st.button("Download Unique Entries"):
                entries_text = "\n\n".join(st.session_state.entries)
                st.download_button(
                    "Download Now",
                    entries_text,
                    f"{st.session_state.upload_filename}_unique_entries.txt"
                )
            
            if st.button("Save to Database"):
                status_text = st.empty()
                if save_entries_with_progress(
                    st.session_state.entries,
                    st.session_state.upload_journal,
                    st.session_state.upload_filename,
                    status_text
                ):
                    st.success("Unique entries saved successfully!")
                    st.session_state.show_save_section = False

    elif st.session_state.app_mode == "?? Search Database":
        st.header("?? Search Database")
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
            
            for i, result in enumerate(st.session_state.search_results[:50]):
                with st.container():
                    st.markdown(f"**Journal:** {result['journal']}  \n**File:** {result['filename']}")
                    
                    if result.get("is_file", False):
                        st.text(f"File: {result['filename']}")
                        # Direct download without additional button
                        content, entry_count = download_entries(result["journal"], result["filename"])
                        if content:
                            st.download_button(
                                "?? Download File",
                                content,
                                file_name=f"{result['filename']} ({entry_count} entries).txt",
                                mime="text/plain",
                                key=f"dl_{i}"
                            )
                    else:
                        if st.session_state.current_edit_entry == result['entry']:
                            edited_entry = st.text_area("Edit entry:", value=result["entry"], height=150, key=f"edit_{i}")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("Save", key=f"save_{i}"):
                                    if update_entry(result["journal"], result["filename"], result["entry"], edited_entry):
                                        st.success("Entry updated successfully!")
                                        st.session_state.current_edit_entry = None
                                        st.session_state.search_results = search_entries(st.session_state.search_query)
                            with col2:
                                if st.button("Cancel", key=f"cancel_{i}"):
                                    st.session_state.current_edit_entry = None
                        else:
                            st.text_area("Entry:", value=result["entry"], height=150, key=f"view_{i}", disabled=True)
                    
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        if not result.get("is_file", False) and st.button("?? Edit", key=f"edit_btn_{i}"):
                            st.session_state.current_edit_entry = result['entry']
                    with col2:
                        if not result.get("is_file", False) and st.button("??? Delete", key=f"delete_{i}"):
                            st.session_state.deleting_entry = result
                    st.markdown("---")

    elif st.session_state.app_mode == "?? Manage Journals":
        st.header("?? Manage Journals")
        
        tab1, tab2 = st.tabs(["View Journals", "Create New Journal"])
        
        with tab1:
            st.subheader("Available Journals")
            st.session_state.available_journals = get_available_journals()
            
            if not st.session_state.available_journals:
                st.info("No journals available. Create a new journal first.")
            else:
                for journal in st.session_state.available_journals:
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.write(f"?? {journal}")
                    with col2:
                        if st.button("???", key=f"del_journal_{journal}"):
                            st.session_state.deleting_journal = journal
                
                if st.session_state.deleting_journal:
                    st.warning(f"Are you sure you want to delete the journal '{st.session_state.deleting_journal}' and all its files?")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Yes, Delete Journal"):
                            if delete_journal(st.session_state.deleting_journal):
                                st.success("Journal deleted successfully!")
                                st.session_state.deleting_journal = None
                                st.rerun()
                    with col2:
                        if st.button("Cancel"):
                            st.session_state.deleting_journal = None
                
                st.markdown("---")
                
                selected_journal = st.selectbox("Select Journal to View Files:", st.session_state.available_journals)
                
                if selected_journal:
                    files = get_journal_files(selected_journal)
                    if files:
                        st.subheader(f"Files in {selected_journal}")
                        
                        for i, file in enumerate(files):
                            try:
                                expander = st.expander(f"{file['name']} ({file['entry_count']} entries)")
                                with expander:
                                    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                                    with col1:
                                        last_updated = file["last_updated"]
                                        if isinstance(last_updated, datetime):
                                            st.write(f"Last updated: {last_updated.strftime('%d-%b-%Y %H:%M')}")
                                        else:
                                            st.write("Last updated: Unknown")
                                    
                                    with col2:
                                        # Direct download without additional button
                                        content, entry_count = download_entries(selected_journal, file['name'])
                                        if content:
                                            st.download_button(
                                                "?? Download",
                                                content,
                                                file_name=f"{file['name']} ({entry_count} entries).txt",
                                                mime="text/plain",
                                                key=f"dl_file_{i}"
                                            )
                                    
                                    with col3:
                                        if st.button("?? Rename", key=f"rename_{i}"):
                                            st.session_state.renaming_file = {
                                                "journal": selected_journal,
                                                "filename": file['name']
                                            }
                                            st.session_state.new_filename = file['name']
                                    
                                    with col4:
                                        if st.button("??? Delete", key=f"del_file_{i}"):
                                            st.session_state.deleting_file = {
                                                "journal": selected_journal,
                                                "filename": file['name']
                                            }
                                    
                                    if st.button("?? Move to Another Journal", key=f"move_{i}"):
                                        st.session_state.moving_file = {
                                            "journal": selected_journal,
                                            "filename": file['name']
                                        }
                                        st.session_state.target_journal = ""
                            except Exception as e:
                                st.error(f"Error displaying file: {str(e)}")
                    else:
                        st.info(f"No files yet in {selected_journal}")
        
        with tab2:
            st.subheader("Create New Journal")
            with st.form(key="new_journal_form"):
                journal_name = st.text_input("Journal Name:")
                submit_button = st.form_submit_button("Create Journal")
                
                if submit_button:
                    if journal_name.strip():
                        if create_journal(journal_name):
                            st.success(f"Journal '{journal_name}' created successfully!")
                            st.session_state.available_journals = get_available_journals()
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
                    st.rerun()
        with col2:
            if st.button("Cancel"):
                st.session_state.deleting_file = None

    if st.session_state.renaming_file:
        file_info = st.session_state.renaming_file
        st.warning(f"Rename file '{file_info['filename']}' in {file_info['journal']}")
        new_name = st.text_input("New filename:", value=st.session_state.new_filename)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Confirm Rename"):
                if new_name.strip() and new_name != file_info['filename']:
                    if rename_file(file_info["journal"], file_info["filename"], new_name):
                        st.success("File renamed successfully!")
                        st.session_state.renaming_file = None
                        st.rerun()
                else:
                    st.warning("Please enter a new filename")
        with col2:
            if st.button("Cancel"):
                st.session_state.renaming_file = None

    if st.session_state.moving_file:
        file_info = st.session_state.moving_file
        st.warning(f"Move file '{file_info['filename']}' from {file_info['journal']} to another journal")
        target_journal = st.selectbox(
            "Select target journal:",
            [j for j in st.session_state.available_journals if j != file_info["journal"]]
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Confirm Move"):
                if target_journal:
                    if move_file(file_info["journal"], file_info["filename"], target_journal):
                        st.success("File moved successfully!")
                        st.session_state.moving_file = None
                        st.rerun()
                else:
                    st.warning("Please select a target journal")
        with col2:
            if st.button("Cancel"):
                st.session_state.moving_file = None

# Main app flow
if __name__ == "__main__":
    # Update last activity time periodically
    if time.time() - st.session_state.last_activity_time > 30:
        st.session_state.last_activity_time = time.time()
    
    if not st.session_state.authenticated:
        show_login_page()
    else:
        apply_theme_settings()
        
        with st.sidebar:
            show_connection_status()
            
            st.markdown("---")
            
            if st.button("?? Home"):
                st.session_state.current_module = None
                st.rerun()
            
            st.markdown("---")
            
            expander = st.expander("?? Settings", expanded=False)
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
                
                if st.button("Save Settings"):
                    st.session_state.font_size = new_font_size
                    st.session_state.theme = new_theme
                    st.session_state.bg_color = "#ffffff" if new_theme == "Light" else "#1a1a1a"
                    st.success("Settings saved successfully!")
                    apply_theme_settings()
                    st.rerun()
            
            st.markdown("---")
            st.markdown(f"Logged in as: **{st.session_state.username}**")
            
            if st.button("Logout"):
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
            st.header("??? PPH Office Tools")
            st.info("Coming soon!")

    st.markdown("---")
    st.markdown("**PPH CRM - Contact App Administrator for any help at: [contact@cpsharma.com](mailto:contact@cpsharma.com)**")


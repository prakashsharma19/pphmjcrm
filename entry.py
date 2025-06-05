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
        'create_entry_stage': 'format',  # 'format', 'download', 'save'
        'formatted_entries': [],
        'formatted_text': "",
        'show_formatting_results': False,
        'show_download_section': False
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
    # Extract journal abbreviation (first letters of each word)
    abbreviation = ''.join([word[0].upper() for word in journal.split() if word[0].isalpha()])
    return f"{abbreviation} {datetime.now().strftime('%d-%m-%Y')}.txt"

def process_uploaded_file(uploaded_file):
    """Process uploaded file and return entries"""
    try:
        # Try UTF-8 first
        try:
            stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
            text = stringio.read()
        except UnicodeDecodeError:
            # If UTF-8 fails, try latin-1
            stringio = StringIO(uploaded_file.getvalue().decode("latin-1"))
            text = stringio.read()
        
        # Clean up text
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        entries = [entry.strip() for entry in text.split("\n\n") if entry.strip()]
        return entries
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
        return []

# Firestore Resume Functions
def save_resume_data(task_type, data):
    """Save resume data to Firestore"""
    db = get_firestore_db()
    if not db:
        return None
    
    try:
        resume_ref = db.collection("resume_tasks")
        
        # Generate a task ID if we don't have one
        if not st.session_state.resume_task_id:
            st.session_state.resume_task_id = f"{st.session_state.username}_{int(time.time())}"
        
        resume_data = {
            "username": st.session_state.username,
            "task_type": task_type,
            "data": data,
            "timestamp": datetime.now(),
            "status": "incomplete",
            "current_chunk": st.session_state.current_chunk,
            "total_chunks": st.session_state.total_chunks,
            "app_mode": st.session_state.app_mode,
            "create_entry_stage": st.session_state.create_entry_stage
        }
        
        resume_ref.document(st.session_state.resume_task_id).set(resume_data)
        return st.session_state.resume_task_id
    except Exception as e:
        st.error(f"Error saving resume data: {str(e)}")
        return None

def load_resume_data(task_id):
    """Load resume data from Firestore"""
    db = get_firestore_db()
    if not db:
        return None
    
    try:
        doc = db.collection("resume_tasks").document(task_id).get()
        if doc.exists:
            return doc.to_dict()
        return None
    except Exception as e:
        st.error(f"Error loading resume data: {str(e)}")
        return None

def get_user_resume_tasks(username):
    """Get all resume tasks for a user"""
    db = get_firestore_db()
    if not db:
        return []
    
    try:
        tasks_ref = db.collection("resume_tasks").where("username", "==", username).where("status", "==", "incomplete")
        return [{"id": task.id, **task.to_dict()} for task in tasks_ref.stream()]
    except Exception as e:
        st.error(f"Error getting resume tasks: {str(e)}")
        return []

def mark_task_complete(task_id):
    """Mark a resume task as complete"""
    db = get_firestore_db()
    if not db:
        return False
    
    try:
        db.collection("resume_tasks").document(task_id).update({"status": "complete"})
        return True
    except Exception as e:
        st.error(f"Error marking task complete: {str(e)}")
        return False

def delete_resume_task(task_id):
    """Delete a resume task"""
    db = get_firestore_db()
    if not db:
        return False
    
    try:
        db.collection("resume_tasks").document(task_id).delete()
        return True
    except Exception as e:
        st.error(f"Error deleting resume task: {str(e)}")
        return False

def check_for_resume_tasks():
    """Check if there are resume tasks for the current user"""
    if st.session_state.resume_data_loaded:
        return False
    
    tasks = get_user_resume_tasks(st.session_state.username)
    if tasks:
        st.session_state.resume_tasks = tasks
        return True
    return False

def resume_task(task_id):
    """Resume a specific task"""
    task_data = load_resume_data(task_id)
    if not task_data:
        return False
    
    try:
        # Restore the application state
        st.session_state.app_mode = task_data.get("app_mode", "📝 Create Entries")
        st.session_state.current_chunk = task_data.get("current_chunk", 0)
        st.session_state.total_chunks = task_data.get("total_chunks", 0)
        st.session_state.create_entry_stage = task_data.get("create_entry_stage", "format")
        
        data = task_data.get("data", {})
        
        if task_data["task_type"] == "format_entries":
            st.session_state.entries = data.get("entries", [])
            st.session_state.formatted_entries = data.get("formatted_entries", [])
            st.session_state.formatted_text = data.get("formatted_text", "")
            st.session_state.upload_journal = data.get("journal", "")
            st.session_state.upload_filename = data.get("filename", "")
            st.session_state.show_formatting_results = data.get("show_formatting_results", False)
            st.session_state.show_download_section = data.get("show_download_section", False)
            st.session_state.show_save_section = data.get("show_save_section", False)
        
        elif task_data["task_type"] == "upload_entries":
            st.session_state.uploaded_entries = data.get("entries", [])
            st.session_state.upload_journal = data.get("journal", "")
            st.session_state.upload_filename = data.get("filename", "")
            st.session_state.duplicates = data.get("duplicates", {})
            st.session_state.processed_entries = data.get("processed_entries", [])
            st.session_state.show_save_section = True
        
        st.session_state.resume_task_id = task_id
        st.session_state.resume_data_loaded = True
        return True
    except Exception as e:
        st.error(f"Error resuming task: {str(e)}")
        return False

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

def is_duplicate(name, email):
    """Check if an author is already in the system using the author_keys collection"""
    if not name or not email:
        return False
        
    db = get_firestore_db()
    if not db:
        return False
        
    key = f"{name.lower()}_{email.lower()}"
    doc = db.collection("author_keys").document(key).get()
    return doc.exists

def save_entries_with_progress(entries, journal, filename, status_text):
    """Save entries with progress tracking and duplicate checking"""
    db = get_firestore_db()
    if not db:
        return False
        
    try:
        # Create journal if it doesn't exist
        journal_ref = db.collection("journals").document(journal)
        if not journal_ref.get().exists:
            journal_ref.set({"created": datetime.now()})

        # Initialize progress tracking
        total_entries = len(entries)
        processed_count = 0
        duplicates_found = 0
        unique_entries = []
        
        # Setup progress bar
        progress_bar = st.progress(0)
        status_text.text("Checking for duplicates...")
        
        # Process entries in batches
        batch_size = 50
        batch = db.batch()
        author_keys_batch = db.batch()
        
        for i, entry in enumerate(entries):
            # Update progress
            progress = int((i + 1) / total_entries * 100)
            progress_bar.progress(progress)
            status_text.text(f"Processing {i+1}/{total_entries} ({progress}%) - {duplicates_found} duplicates found")
            
            # Extract author info
            name, email = extract_author_email(entry)
            
            if not name or not email:
                continue  # Skip invalid entries
                
            # Check for duplicates using the optimized method
            if is_duplicate(name, email):
                duplicates_found += 1
                continue
                
            # Add to unique entries
            unique_entries.append(entry)
            
            # Create author key
            key = f"{name.lower()}_{email.lower()}"
            author_key_ref = db.collection("author_keys").document(key)
            author_keys_batch.set(author_key_ref, {
                "name": name,
                "email": email,
                "journal": journal,
                "filename": filename,
                "timestamp": datetime.now()
            })
            
            # Commit batches periodically
            if i > 0 and i % batch_size == 0:
                batch.commit()
                author_keys_batch.commit()
                batch = db.batch()
                author_keys_batch = db.batch()
                
            # Update last activity to prevent timeout
            st.session_state.last_activity_time = time.time()
        
        # Commit any remaining entries
        if len(unique_entries) > 0:
            # Save the entries to the journal file
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

def check_duplicates(new_entries):
    """Check for duplicates across all journals using author_keys collection"""
    unique_entries = []
    duplicate_info = {}
    db = get_firestore_db()
    
    if not db:
        return [], {}
    
    # Initialize progress tracking
    total_entries = len(new_entries)
    processed_count = 0
    duplicates_found = 0
    
    # Setup progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    status_text.text("Checking for duplicates...")
    
    for i, entry in enumerate(new_entries):
        # Update progress
        progress = int((i + 1) / total_entries * 100)
        progress_bar.progress(progress)
        status_text.text(f"Processing {i+1}/{total_entries} ({progress}%) - {duplicates_found} duplicates found")
        
        # Extract author info
        name, email = extract_author_email(entry)
        
        if not name or not email:
            continue  # Skip invalid entries
            
        key = f"{name.lower()}_{email.lower()}"
        
        # Check for duplicates using the optimized method
        if is_duplicate(name, email):
            # Get existing duplicate info from author_keys
            doc = db.collection("author_keys").document(key).get()
            if doc.exists:
                dup_data = doc.to_dict()
                if key not in duplicate_info:
                    duplicate_info[key] = []
                duplicate_info[key].append({
                    "entry": entry,
                    "journal": dup_data.get("journal", "Unknown"),
                    "filename": dup_data.get("filename", "Unknown"),
                    "timestamp": dup_data.get("timestamp", datetime.now())
                })
            duplicates_found += 1
        else:
            # This is a new unique entry
            unique_entries.append(entry)
    
    # Complete progress
    progress_bar.progress(100)
    if duplicates_found:
        status_text.text(f"Completed! Found {len(unique_entries)} unique entries, {duplicates_found} duplicates")
    else:
        status_text.text(f"Completed! Found {len(unique_entries)} unique entries")
    
    return unique_entries, duplicate_info

def convert_journal_to_author_keys(journal_name):
    """Convert all entries in a journal to author_keys collection"""
    db = get_firestore_db()
    if not db:
        return False, "Database connection failed"
    
    try:
        # Get all files in the journal
        files_ref = db.collection("journals").document(journal_name).collection("files")
        files = [doc.id for doc in files_ref.stream()]
        
        if not files:
            return False, f"No files found in journal '{journal_name}'"
        
        # Initialize progress
        progress_bar = st.progress(0)
        status_text = st.empty()
        total_files = len(files)
        processed_files = 0
        total_entries_processed = 0
        
        # Process each file
        for i, filename in enumerate(files):
            status_text.text(f"Processing file {i+1}/{total_files}: {filename}")
            progress_bar.progress(int((i + 1) / total_files * 50))  # First half for files
            
            # Get all entries in the file
            doc = files_ref.document(filename).get()
            if not doc.exists:
                continue
                
            entries = doc.to_dict().get("entries", [])
            batch = db.batch()
            entries_processed = 0
            
            # Process each entry
            for j, entry in enumerate(entries):
                # Update progress within file
                file_progress = int((j + 1) / len(entries) * 50) + 50  # Second half for entries
                progress_bar.progress(file_progress)
                status_text.text(
                    f"Processing file {i+1}/{total_files}: {filename}\n"
                    f"Entry {j+1}/{len(entries)} - Total processed: {total_entries_processed + j}"
                )
                
                name, email = extract_author_email(entry)
                if not name or not email:
                    continue
                    
                # Create author key
                key = f"{name.lower()}_{email.lower()}"
                author_key_ref = db.collection("author_keys").document(key)
                batch.set(author_key_ref, {
                    "name": name,
                    "email": email,
                    "journal": journal_name,
                    "filename": filename,
                    "timestamp": datetime.now()
                })
                
                entries_processed += 1
                
                # Commit in batches to avoid timeout
                if j > 0 and j % 100 == 0:
                    batch.commit()
                    batch = db.batch()
            
            # Commit remaining entries in this file
            batch.commit()
            total_entries_processed += entries_processed
            processed_files += 1
            
            # Update last activity to prevent timeout
            st.session_state.last_activity_time = time.time()
        
        progress_bar.progress(100)
        status_text.text(f"Completed! Processed {processed_files} files and {total_entries_processed} entries")
        return True, f"Successfully converted {processed_files} files with {total_entries_processed} entries"
    
    except Exception as e:
        return False, f"Error during conversion: {str(e)}"

def delete_author_keys_for_journal(journal_name):
    """Delete all author keys associated with a specific journal"""
    db = get_firestore_db()
    if not db:
        return False, "Database connection failed"
    
    try:
        # Get all author keys for this journal
        keys_ref = db.collection("author_keys").where("journal", "==", journal_name)
        keys_to_delete = [doc.id for doc in keys_ref.stream()]
        
        if not keys_to_delete:
            return True, f"No author keys found for journal '{journal_name}'"
        
        # Delete in batches
        batch_size = 500
        deleted_count = 0
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i in range(0, len(keys_to_delete), batch_size):
            batch = db.batch()
            for key in keys_to_delete[i:i+batch_size]:
                batch.delete(db.collection("author_keys").document(key))
            
            batch.commit()
            deleted_count += min(batch_size, len(keys_to_delete) - i)
            
            # Update progress
            progress = int((i + batch_size) / len(keys_to_delete) * 100)
            progress_bar.progress(progress)
            status_text.text(f"Deleted {deleted_count}/{len(keys_to_delete)} author keys")
            
            # Update last activity to prevent timeout
            st.session_state.last_activity_time = time.time()
        
        progress_bar.progress(100)
        return True, f"Successfully deleted {deleted_count} author keys for journal '{journal_name}'"
    
    except Exception as e:
        return False, f"Error during author key deletion: {str(e)}"

def delete_all_duplicates():
    """Delete all duplicate entries across the system, keeping only the latest version of each"""
    db = get_firestore_db()
    if not db:
        return False, "Database connection failed"
    
    try:
        # First collect all author keys
        author_keys_ref = db.collection("author_keys")
        author_keys = {}
        
        # Get all author keys to identify duplicates
        for doc in author_keys_ref.stream():
            data = doc.to_dict()
            key = doc.id
            author_keys[key] = data
        
        # Identify duplicates (same key but different documents)
        duplicates_to_remove = []
        unique_authors = set()
        
        for key, data in author_keys.items():
            if key in unique_authors:
                duplicates_to_remove.append((key, data))
            else:
                unique_authors.add(key)
        
        if not duplicates_to_remove:
            return True, "No duplicates found in author_keys collection"
        
        # Remove duplicates from author_keys
        batch = db.batch()
        for i, (key, data) in enumerate(duplicates_to_remove):
            doc_ref = author_keys_ref.document(key)
            batch.delete(doc_ref)
            
            # Commit in batches to avoid timeout
            if i > 0 and i % 100 == 0:
                batch.commit()
                batch = db.batch()
        
        batch.commit()
        
        return True, f"Removed {len(duplicates_to_remove)} duplicate author keys"
    
    except Exception as e:
        return False, f"Error during duplicate removal: {str(e)}"

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
        # First remove all author keys associated with this file
        entries, _ = download_entries(journal, filename)
        if entries:
            entries_list = entries.split('\n\n')
            batch = db.batch()
            
            for entry in entries_list:
                name, email = extract_author_email(entry)
                if name and email:
                    key = f"{name.lower()}_{email.lower()}"
                    doc_ref = db.collection("author_keys").document(key)
                    batch.delete(doc_ref)
            
            batch.commit()
        
        # Then delete the file itself
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
        # First delete all files in the journal (which will handle author_keys)
        files_ref = db.collection("journals").document(journal_name).collection("files")
        for file in files_ref.stream():
            delete_file(journal_name, file.id)
        
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
                # First update the author key if name/email changed
                old_name, old_email = extract_author_email(old_entry)
                new_name, new_email = extract_author_email(new_entry)
                
                if old_name != new_name or old_email != new_email:
                    # Delete old key
                    old_key = f"{old_name.lower()}_{old_email.lower()}"
                    db.collection("author_keys").document(old_key).delete()
                    
                    # Create new key
                    new_key = f"{new_name.lower()}_{new_email.lower()}"
                    db.collection("author_keys").document(new_key).set({
                        "name": new_name,
                        "email": new_email,
                        "journal": journal,
                        "filename": filename,
                        "timestamp": datetime.now()
                    })
                
                # Update the entry
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
                # Remove from author_keys
                name, email = extract_author_email(entry)
                if name and email:
                    key = f"{name.lower()}_{email.lower()}"
                    db.collection("author_keys").document(key).delete()
                
                # Remove from entries
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
        
        # Update all author_keys to point to new journal
        entries = file_data.get("entries", [])
        batch = db.batch()
        
        for entry in entries:
            name, email = extract_author_email(entry)
            if name and email:
                key = f"{name.lower()}_{email.lower()}"
                key_ref = db.collection("author_keys").document(key)
                batch.update(key_ref, {
                    "journal": target_journal
                })
        
        batch.commit()
        
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
                
                # Save progress to Firestore after each chunk
                save_resume_data("format_entries", {
                    "entries": entries,
                    "formatted_entries": formatted_parts,
                    "formatted_text": '\n\n'.join(formatted_parts),
                    "journal": st.session_state.upload_journal,
                    "filename": st.session_state.upload_filename,
                    "current_chunk": i + 1,
                    "total_chunks": len(chunks),
                    "show_formatting_results": True,
                    "show_download_section": False,
                    "show_save_section": False
                })
        except Exception as e:
            st.error(f"Error: {str(e)}")
            return ""
    
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
            st.markdown('<div class="app-title">PPH CRM - Test3</div>', unsafe_allow_html=True)
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
        if st.button("📝 Entry Module", use_container_width=True):
            st.session_state.current_module = "Entry"
            st.rerun()
    
    with col2:
        if st.button("🛠️ PPH Office Tools", use_container_width=True):
            st.session_state.current_module = "PPH Office Tools"
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def show_regex_manager():
    st.subheader("🔍 Regex Filter Management")
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
                if st.button("🗑️", key=f"del_regex_{i}"):
                    if delete_regex_filter(pattern):
                        st.success("Filter deleted successfully!")
                        st.rerun()
    
    # Add new filter
    with st.form(key="add_regex_form"):
        new_filter = st.text_input("New Regex Pattern:", value=st.session_state.new_regex_filter)
        if st.form_submit_button("➕ Add Filter"):
            if new_filter.strip():
                if save_regex_filter(new_filter.strip()):
                    st.success("Filter added successfully!")
                    st.session_state.new_regex_filter = ""
                    st.rerun()
                else:
                    st.error("Failed to add filter")

def show_prompt_manager():
    st.subheader("🤖 AI Prompt Improvement")
    st.write("Add examples to improve the AI's formatting")
    
    # Display saved prompts
    st.write("**Saved Prompts:**")
    if not st.session_state.ai_prompts:
        st.info("No AI prompts saved yet")
    else:
        for prompt in st.session_state.ai_prompts:
            expander = st.expander(f"📝 {prompt.get('name', 'Unnamed')}")
            with expander:
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Input:**")
                    st.text_area("", value=prompt.get("input", ""), height=150, disabled=True, key=f"input_{prompt['id']}")
                with col2:
                    st.write("**Output:**")
                    st.text_area("", value=prompt.get("output", ""), height=150, disabled=True, key=f"output_{prompt['id']}")
                
                if st.button("🗑️ Delete", key=f"delete_{prompt['id']}"):
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
        
        if st.form_submit_button("💾 Save Example"):
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

    st.title("📝 PPH CRM - Entry Module")
    
    if logo:
        st.image(logo, width=100)

    # Show admin tools if logged in as admin
    if st.session_state.is_admin:
        admin_col1, admin_col2 = st.columns(2)
        with admin_col1:
            if st.button("🔍 Manage Regex Filters"):
                st.session_state.show_regex_manager = not st.session_state.show_regex_manager
        with admin_col2:
            if st.button("🤖 Improve AI Prompts"):
                st.session_state.show_prompt_manager = not st.session_state.show_prompt_manager
        
        if st.session_state.show_regex_manager:
            show_regex_manager()
            st.markdown("---")
        
        if st.session_state.show_prompt_manager:
            show_prompt_manager()
            st.markdown("---")

    # Check for resume tasks on first load
    if not st.session_state.resume_data_loaded and st.session_state.authenticated:
        if check_for_resume_tasks():
            with st.expander("⚠️ Resume Incomplete Tasks", expanded=True):
                st.warning("You have incomplete tasks. Would you like to resume any of them?")
                
                for task in st.session_state.resume_tasks:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**Task Type:** {task['task_type']}")
                        st.write(f"**Started:** {task['timestamp'].strftime('%Y-%m-%d %H:%M') if isinstance(task['timestamp'], datetime) else 'Unknown'}")
                    with col2:
                        if st.button(f"Resume {task['id'][-6:]}", key=f"resume_{task['id']}"):
                            if resume_task(task['id']):
                                st.rerun()
                
                if st.button("Clear All Incomplete Tasks", key="clear_all_tasks"):
                    for task in st.session_state.resume_tasks:
                        delete_resume_task(task['id'])
                    st.session_state.resume_tasks = []
                    st.rerun()

    # Update available journals list
    st.session_state.available_journals = get_available_journals()

    st.session_state.app_mode = st.radio(
        "Select Operation",
        ["📝 Create Entries", "📤 Upload Entries", "🔍 Search Database", "📚 Manage Journals"],
        horizontal=True
    )

    if st.session_state.app_mode == "📝 Create Entries":
        st.header("📝 Create Entries")
        
        # File upload option for Create Entries
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
                        
                        # Save progress to Firestore
                        task_id = save_resume_data("format_entries", {
                            "entries": raw_text.split('\n\n'),
                            "formatted_entries": st.session_state.formatted_entries,
                            "formatted_text": st.session_state.formatted_text,
                            "show_formatting_results": True,
                            "show_download_section": False,
                            "show_save_section": False
                        })
                        
                        if task_id:
                            st.session_state.resume_task_id = task_id
                        st.rerun()
        
        if st.session_state.show_formatting_results and st.session_state.formatted_text:
            st.subheader("Formatted Results")
            st.text_area("Formatted Entries", value=st.session_state.formatted_text, height=300, disabled=True)
            
            if st.session_state.create_entry_stage == 'download':
                st.subheader("Download Options")
                if st.button("📥 Download Formatted Entries"):
                    st.download_button(
                        "💾 Download Now",
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
                        # Check for duplicates
                        with st.spinner("Checking for duplicates..."):
                            unique_entries, duplicates = check_duplicates(st.session_state.formatted_entries)
                            st.session_state.duplicates = duplicates
                            st.session_state.processed_entries = unique_entries
                            
                            if duplicates:
                                st.warning(f"Found {len(duplicates)} duplicate entries that will not be saved")
                                with st.expander("🔍 Duplicate Details"):
                                    for key, dup_list in duplicates.items():
                                        name, email = extract_author_email(dup_list[0]["entry"])
                                        st.write(f"**Author:** {name} ({email})")
                                        st.write(f"- Found in: {dup_list[0]['journal']} > {dup_list[0]['filename']}")
                                        st.write(f"- Original entry date: {dup_list[0]['timestamp'].strftime('%d-%b-%Y') if isinstance(dup_list[0]['timestamp'], datetime) else 'Unknown'}")
                                        st.write(f"- Number of duplicates: {len(dup_list)}")
                                        
                                        if st.button("👁️ View Original Entry", key=f"view_{key}"):
                                            original_content, _ = download_entries(dup_list[0]['journal'], dup_list[0]['filename'])
                                            if original_content:
                                                original_entries = original_content.split('\n\n')
                                                for orig_entry in original_entries:
                                                    if name in orig_entry and email in orig_entry:
                                                        st.text_area("Original Entry:", value=orig_entry, height=150, disabled=True)
                                                        break
                                        
                                        st.markdown("---")
                        
                        # Save to database
                        status_text = st.empty()
                        if save_entries_with_progress(unique_entries, selected_journal, filename, status_text):
                            st.success(f"Saved {len(unique_entries)} entries to {selected_journal}/{filename}")
                            st.session_state.show_save_section = True
                            
                            # Mark task as complete
                            if st.session_state.resume_task_id:
                                mark_task_complete(st.session_state.resume_task_id)
                                st.session_state.resume_task_id = None
                            
                            # Reset the process
                            st.session_state.create_entry_stage = 'format'
                            st.session_state.show_formatting_results = False
                            st.session_state.formatted_entries = []
                            st.session_state.formatted_text = ""
                            st.rerun()

    elif st.session_state.app_mode == "📤 Upload Entries":
        st.header("📤 Upload Entries")
        
        if st.button("⚠️ Delete Duplicate Entries", type="primary", help="Remove all duplicate entries from the entire system"):
            st.session_state.delete_duplicates_mode = True
        
        if st.session_state.delete_duplicates_mode:
            with st.spinner("Searching for and removing duplicates..."):
                success, message = delete_all_duplicates()
                if success:
                    st.success(message)
                else:
                    st.error(message)
                st.session_state.delete_duplicates_mode = False
        
        uploaded_file = st.file_uploader("📄 Upload TXT file with author entries", type=["txt"])
        
        if uploaded_file:
            st.session_state.upload_journal = st.selectbox(
                "Select Journal for Uploaded Entries:",
                st.session_state.available_journals
            )
            
            st.session_state.upload_filename = st.text_input(
                "Filename for uploaded entries:",
                get_suggested_filename(st.session_state.upload_journal)
            )
            
            if st.button("🔍 Process & Save Entries"):
                uploaded_entries = process_uploaded_file(uploaded_file)
                if uploaded_entries:
                    st.session_state.uploaded_entries = uploaded_entries
                    
                    # Save progress to Firestore
                    task_id = save_resume_data("upload_entries", {
                        "entries": uploaded_entries,
                        "journal": st.session_state.upload_journal,
                        "filename": st.session_state.upload_filename
                    })
                    
                    if task_id:
                        st.session_state.resume_task_id = task_id
                    
                    with st.spinner("Processing entries..."):
                        # Check duplicates and save in one go
                        status_text = st.empty()
                        unique_entries, duplicates = check_duplicates(st.session_state.uploaded_entries)
                        
                        if duplicates:
                            st.warning(f"Found {len(duplicates)} duplicate entries that will not be saved")
                            with st.expander("🔍 Duplicate Details"):
                                for key, dup_list in duplicates.items():
                                    name, email = extract_author_email(dup_list[0]["entry"])
                                    st.write(f"**Author:** {name} ({email})")
                                    st.write(f"- Found in: {dup_list[0]['journal']} > {dup_list[0]['filename']}")
                                    st.write(f"- Original entry date: {dup_list[0]['timestamp'].strftime('%d-%b-%Y') if isinstance(dup_list[0]['timestamp'], datetime) else 'Unknown'}")
                                    st.write(f"- Number of duplicates: {len(dup_list)}")
                                    
                                    if st.button("👁️ View Original Entry", key=f"view_{key}"):
                                        original_content, _ = download_entries(dup_list[0]['journal'], dup_list[0]['filename'])
                                        if original_content:
                                            original_entries = original_content.split('\n\n')
                                            for orig_entry in original_entries:
                                                if name in orig_entry and email in orig_entry:
                                                    st.text_area("Original Entry:", value=orig_entry, height=150, disabled=True)
                                                    break
                                    
                                    st.markdown("---")
                        
                        # Save to database
                        if save_entries_with_progress(
                            unique_entries,
                            st.session_state.upload_journal,
                            st.session_state.upload_filename,
                            status_text
                        ):
                            st.success(f"Saved {len(unique_entries)} entries to {st.session_state.upload_journal}/{st.session_state.upload_filename}")
                            
                            # Mark task as complete
                            if st.session_state.resume_task_id:
                                mark_task_complete(st.session_state.resume_task_id)
                                st.session_state.resume_task_id = None
                            
                            # Download options
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("📥 Download Formatted Entries Only"):
                                    entries_text = "\n\n".join(unique_entries)
                                    st.download_button(
                                        "💾 Download Now",
                                        entries_text,
                                        file_name="formatted_entries.txt",
                                        mime="text/plain"
                                    )
                            with col2:
                                if st.button("📥 Download Database Entries"):
                                    content, count = download_entries(st.session_state.upload_journal, st.session_state.upload_filename)
                                    if content:
                                        st.download_button(
                                            "💾 Download Now",
                                            content,
                                            file_name=f"{st.session_state.upload_filename} ({count} entries).txt",
                                            mime="text/plain"
                                        )

    elif st.session_state.app_mode == "🔍 Search Database":
        st.header("🔍 Search Database")
        search_col1, search_col2 = st.columns([3, 1])
        with search_col1:
            search_query = st.text_input("Search for entries or filenames:", value=st.session_state.search_query)
        with search_col2:
            if st.button("🔍 Search"):
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
                                "📥 Download File",
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
                                if st.button("💾 Save", key=f"save_{i}"):
                                    if update_entry(result["journal"], result["filename"], result["entry"], edited_entry):
                                        st.success("Entry updated successfully!")
                                        st.session_state.current_edit_entry = None
                                        st.session_state.search_results = search_entries(st.session_state.search_query)
                            with col2:
                                if st.button("❌ Cancel", key=f"cancel_{i}"):
                                    st.session_state.current_edit_entry = None
                        else:
                            st.text_area("Entry:", value=result["entry"], height=150, key=f"view_{i}", disabled=True)
                    
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        if not result.get("is_file", False) and st.button("✏️ Edit", key=f"edit_btn_{i}"):
                            st.session_state.current_edit_entry = result['entry']
                    with col2:
                        if not result.get("is_file", False) and st.button("🗑️ Delete", key=f"delete_{i}"):
                            st.session_state.deleting_entry = result
                    st.markdown("---")

    elif st.session_state.app_mode == "📚 Manage Journals":
        st.header("📚 Manage Journals")
        
        tab1, tab2 = st.tabs(["View Journals", "Create New Journal"])
        
        with tab1:
            # Collapsible journals list
            with st.expander("📚 Available Journals", expanded=st.session_state.show_journals_list):
                st.session_state.available_journals = get_available_journals()
                
                if not st.session_state.available_journals:
                    st.info("No journals available. Create a new journal first.")
                else:
                    for journal in st.session_state.available_journals:
                        col1, col2, col3, col4 = st.columns([4, 1, 1, 1])
                        with col1:
                            st.write(f"📖 {journal}")
                        with col2:
                            if st.button("🔄 Convert", key=f"convert_{journal}"):
                                st.session_state.converting_journal = journal
                        with col3:
                            if st.button("🗑️", key=f"del_journal_{journal}"):
                                st.session_state.deleting_journal = journal
                        with col4:
                            if st.button("🔑 Delete Keys", key=f"del_keys_{journal}"):
                                st.session_state.deleting_keys_journal = journal
                    
                    if st.session_state.converting_journal:
                        st.warning(f"Convert all entries in '{st.session_state.converting_journal}' to author_keys collection?")
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("✅ Yes, Convert"):
                                with st.spinner(f"Converting {st.session_state.converting_journal}..."):
                                    success, message = convert_journal_to_author_keys(st.session_state.converting_journal)
                                    if success:
                                        st.success(message)
                                    else:
                                        st.error(message)
                                    st.session_state.converting_journal = None
                                    st.rerun()
                        with col2:
                            if st.button("❌ Cancel"):
                                st.session_state.converting_journal = None
                    
                    if st.session_state.deleting_journal:
                        st.warning(f"Are you sure you want to delete the journal '{st.session_state.deleting_journal}' and all its files?")
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("✅ Yes, Delete"):
                                if delete_journal(st.session_state.deleting_journal):
                                    st.success("Journal deleted successfully!")
                                    st.session_state.deleting_journal = None
                                    st.rerun()
                        with col2:
                            if st.button("❌ Cancel"):
                                st.session_state.deleting_journal = None
                    
                    if st.session_state.deleting_keys_journal:
                        st.warning(f"Are you sure you want to delete all author keys for journal '{st.session_state.deleting_keys_journal}'?")
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("✅ Yes, Delete"):
                                with st.spinner(f"Deleting author keys for {st.session_state.deleting_keys_journal}..."):
                                    success, message = delete_author_keys_for_journal(st.session_state.deleting_keys_journal)
                                    if success:
                                        st.success(message)
                                    else:
                                        st.error(message)
                                    st.session_state.deleting_keys_journal = None
                                    st.rerun()
                        with col2:
                            if st.button("❌ Cancel"):
                                st.session_state.deleting_keys_journal = None
            
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
                                            "📥 Download",
                                            content,
                                            file_name=f"{file['name']} ({entry_count} entries).txt",
                                            mime="text/plain",
                                            key=f"dl_file_{i}"
                                        )
                                
                                with col3:
                                    if st.button("✏️ Rename", key=f"rename_{i}"):
                                        st.session_state.renaming_file = {
                                            "journal": selected_journal,
                                            "filename": file['name']
                                        }
                                        st.session_state.new_filename = file['name']
                                
                                with col4:
                                    if st.button("🗑️ Delete", key=f"del_file_{i}"):
                                        st.session_state.deleting_file = {
                                            "journal": selected_journal,
                                            "filename": file['name']
                                        }
                                
                                if st.button("➡️ Move to Another Journal", key=f"move_{i}"):
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
            st.subheader("➕ Create New Journal")
            with st.form(key="new_journal_form"):
                journal_name = st.text_input("Journal Name:")
                submit_button = st.form_submit_button("➕ Create Journal")
                
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
            if st.button("✅ Confirm Delete"):
                if delete_entry(result["journal"], result["filename"], result["entry"]):
                    st.success("Entry deleted successfully!")
                    st.session_state.deleting_entry = None
                    st.session_state.search_results = search_entries(st.session_state.search_query)
        with col2:
            if st.button("❌ Cancel"):
                st.session_state.deleting_entry = None

    if st.session_state.deleting_file:
        file_info = st.session_state.deleting_file
        st.warning(f"Are you sure you want to delete '{file_info['filename']}' from {file_info['journal']}?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Yes, Delete"):
                if delete_file(file_info["journal"], file_info["filename"]):
                    st.success("File deleted successfully!")
                    st.session_state.deleting_file = None
                    st.rerun()
        with col2:
            if st.button("❌ Cancel"):
                st.session_state.deleting_file = None

    if st.session_state.renaming_file:
        file_info = st.session_state.renaming_file
        st.warning(f"Rename file '{file_info['filename']}' in {file_info['journal']}")
        new_name = st.text_input("New filename:", value=st.session_state.new_filename)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Confirm Rename"):
                if new_name.strip() and new_name != file_info['filename']:
                    if rename_file(file_info["journal"], file_info["filename"], new_name):
                        st.success("File renamed successfully!")
                        st.session_state.renaming_file = None
                        st.rerun()
                else:
                    st.warning("Please enter a new filename")
        with col2:
            if st.button("❌ Cancel"):
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
            if st.button("✅ Confirm Move"):
                if target_journal:
                    if move_file(file_info["journal"], file_info["filename"], target_journal):
                        st.success("File moved successfully!")
                        st.session_state.moving_file = None
                        st.rerun()
                else:
                    st.warning("Please select a target journal")
        with col2:
            if st.button("❌ Cancel"):
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
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
        'manual_api_key': 'AIzaSyBIXgqTphaQq8u3W5A4HRHVhwBp_fbnfsg',
        'show_api_key_input': False,
        'delete_duplicates_mode': False,
        'show_connection_status': False,
        'app_mode': "✏️ Create Entries",
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
        'total_chunks': 0
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

def load_ai_prompts():
    """Load AI prompts from Firestore"""
    db = get_firestore_db()
    if not db:
        return []
    
    try:
        prompts_ref = db.collection("ai_prompts")
        prompts = []
        for doc in prompts_ref.stream():
            prompts.append(doc.to_dict())
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

        doc_ref = db.collection("journals").document(journal).collection("files").document(filename)
        doc_ref.set({
            "entries": entries,
            "last_updated": datetime.now(),
            "entry_count": len(entries)
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

# ... [keep all other existing Firebase functions unchanged] ...

# AI processing function with improved progress tracking
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
    status_text.text("Starting AI processing...")
    
    for i, chunk in enumerate(chunks):
        st.session_state.current_chunk = i + 1
        progress = int((i + 1) / len(chunks) * 100)
        progress_bar.progress(progress)
        
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
        
        # Use the best available prompt
        prompt = """Format these author entries exactly as:

Name
Department (if available)
University (if available)
Country (if available)
email@domain.com

RULES:
1. Only include department line if available
2. Only include most specific university name
3. Remove all addresses, postal codes, building numbers
4. Keep exactly one line per component
5. Remove all extra information

Example:
Manish Kumar
Department of Physics
University of Delhi
India
mkumar2@arsd.du.ac.in

Entries to format:
{chunk}"""
        
        try:
            genai.configure(api_key=st.session_state.manual_api_key or os.getenv("GOOGLE_API_KEY"))
            model = genai.GenerativeModel("gemini-1.5-flash-latest")
            response = model.generate_content(prompt.format(chunk=chunk))
            if response.text:
                formatted_parts.append(response.text)
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    processing_time = time.time() - st.session_state.processing_start_time
    progress_bar.progress(100)
    status_text.text(f"Completed in {format_time(processing_time)}")
    return '\n\n'.join(formatted_parts)

# ... [keep all other existing functions unchanged until show_entry_module] ...

def show_regex_manager():
    st.subheader("📝 Regex Filter Management")
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
                    # Implement delete functionality if needed
                    pass
    
    # Add new filter
    with st.form(key="add_regex_form"):
        new_filter = st.text_input("New Regex Pattern:", value=st.session_state.new_regex_filter)
        if st.form_submit_button("Add Filter"):
            if new_filter.strip():
                if save_regex_filter(new_filter.strip()):
                    st.success("Filter added successfully!")
                    st.session_state.new_regex_filter = ""
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
            with st.expander(f"📌 {prompt.get('name', 'Unnamed')}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Input:**")
                    st.text_area("", value=prompt.get("input", ""), height=150, disabled=True, key=f"input_{prompt['name']}")
                with col2:
                    st.write("**Output:**")
                    st.text_area("", value=prompt.get("output", ""), height=150, disabled=True, key=f"output_{prompt['name']}")
    
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
                else:
                    st.error("Failed to save example")

def show_entry_module():
    if not st.session_state.authenticated:
        show_login_page()
        return

    # Load regex filters and AI prompts if admin
    if st.session_state.username.lower() == "prakash":
        if 'regex_filters' not in st.session_state or not st.session_state.regex_filters:
            st.session_state.regex_filters = load_regex_filters()
        if 'ai_prompts' not in st.session_state or not st.session_state.ai_prompts:
            st.session_state.ai_prompts = load_ai_prompts()

    st.title("📚 PPH CRM - Entry Module")
    
    if logo:
        st.image(logo, width=100)

    # Show admin tools if logged in as Prakash
    if st.session_state.username.lower() == "prakash":
        admin_col1, admin_col2 = st.columns(2)
        with admin_col1:
            if st.button("⚙️ Manage Regex Filters"):
                st.session_state.show_regex_manager = not st.session_state.show_regex_manager
        with admin_col2:
            if st.button("🧠 Improve AI Prompts"):
                st.session_state.show_prompt_manager = not st.session_state.show_prompt_manager
        
        if st.session_state.show_regex_manager:
            show_regex_manager()
            st.markdown("---")
        
        if st.session_state.show_prompt_manager:
            show_prompt_manager()
            st.markdown("---")

    st.session_state.app_mode = st.radio(
        "Select Operation",
        ["✏️ Create Entries", "📤 Upload Entries", "🔍 Search Database", "🗂 Manage Journals"],
        horizontal=True
    )

    if st.session_state.app_mode == "✏️ Create Entries":
        st.header("✏️ Create Entries")
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
            
            if st.button("👁️ Show Formatted Entries"):
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

    elif st.session_state.app_mode == "📤 Upload Entries":
        st.header("📤 Upload Entries")
        
        if st.button("✅ Delete Duplicate Entries", type="primary", help="Remove all duplicate entries from the entire system"):
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
                                for email, dup_list in duplicates.items():
                                    st.write(f"**Email:** {email}")
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

    elif st.session_state.app_mode == "🔍 Search Database":
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
            
            for i, result in enumerate(st.session_state.search_results[:50]):
                with st.container():
                    st.markdown(f"**Journal:** {result['journal']}  \n**File:** {result['filename']}")
                    
                    if result.get("is_file", False):
                        st.text(f"File: {result['filename']}")
                        if st.button("📥 Download", key=f"dl_{i}"):
                            content, entry_count = download_entries(result["journal"], result["filename"])
                            if content:
                                st.download_button(
                                    "Download Now",
                                    content,
                                    f"{result['filename']} ({entry_count} entries).txt"
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
                        if not result.get("is_file", False) and st.button("✏️ Edit", key=f"edit_btn_{i}"):
                            st.session_state.current_edit_entry = result['entry']
                    with col2:
                        if not result.get("is_file", False) and st.button("🗑️ Delete", key=f"delete_{i}"):
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
                selected_journal = st.selectbox("Select Journal:", st.session_state.available_journals)
                
                if selected_journal:
                    files = get_journal_files(selected_journal)
                    if files:
                        st.subheader(f"Files in {selected_journal}")
                        
                        for i, file in enumerate(files):
                            try:
                                with st.expander(f"{file['name']} ({file['entry_count']} entries)", key=f"file_{i}"):
                                    col1, col2, col3 = st.columns([3, 1, 1])
                                    with col1:
                                        last_updated = file["last_updated"]
                                        if isinstance(last_updated, datetime):
                                            st.write(f"Last updated: {last_updated.strftime('%d-%b-%Y %H:%M')}")
                                        else:
                                            st.write("Last updated: Unknown")
                                    
                                    with col2:
                                        if st.button("📥 Download", key=f"dl_file_{i}"):
                                            content, entry_count = download_entries(selected_journal, file['name'])
                                            if content:
                                                st.download_button(
                                                    "Download Now",
                                                    content,
                                                    f"{file['name']} ({entry_count} entries).txt"
                                                )
                                    
                                    with col3:
                                        if st.button("🗑️ Delete", key=f"del_file_{i}"):
                                            st.session_state.deleting_file = {
                                                "journal": selected_journal,
                                                "filename": file['name']
                                            }
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
        with col2:
            if st.button("Cancel"):
                st.session_state.deleting_file = None

# Main app flow
if __name__ == "__main__":
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
                
                if st.button("Save Settings"):
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

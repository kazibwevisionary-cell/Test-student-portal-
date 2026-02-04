import streamlit as st
import pandas as pd
from supabase import create_client

# 1. DATABASE CONNECTION
# Connecting to your specific Supabase project
PROJECT_ID = "uxtmgdenwfyuwhezcleh"
SUPABASE_URL = f"https://{PROJECT_ID}.supabase.co"
SUPABASE_KEY = "sb_publishable_1BIwMEH8FVDv7fFafz31uA_9FqAJr0-"

try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error(f"Database Connection Failed: {e}")
    st.stop()

# 2. UI CONFIGURATION
st.set_page_config(page_title="KIU Study Portal", layout="wide", page_icon="🎓")

# Custom CSS for a professional look
st.markdown("""
<style>
    .stApp { background-color: #f8fafc; }
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; text-align: center; padding: 10px; background: white; border-top: 1px solid #e2e8f0; font-size: 12px; color: #64748b; }
    .video-container { position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; border-radius: 12px; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); }
    .video-container iframe { position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: 0; }
</style>
""", unsafe_allow_html=True)

# 3. AUTHENTICATION STATE
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# 4. LOGIN PAGE
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center; color: #1e40af; margin-top: 50px;'>KIU Q10 STUDY PORTAL</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        with st.container(border=True):
            st.subheader("Sign In")
            u = st.text_input("Registration Number / Email")
            p = st.text_input("Password", type="password")
            
            if st.button("Access Portal", use_container_width=True, type="primary"):
                st.session_state.logged_in = True
                st.rerun()
            
            st.divider()
            if st.button("Continue as Guest", use_container_width=True):
                st.session_state.logged_in = True
                st.rerun()
    st.stop()

# 5. NAVIGATION
st.sidebar.image("https://www.kiu.ac.ug/assets/images/logo.png", width=150) # Using KIU logo if available
menu = st.sidebar.radio("Main Menu", ["Student Portal", "Admin Dashboard", "Announcements"])

# --- STUDENT PORTAL ---
if menu == "Student Portal":
    st.title("📖 My Learning Resources")
    search_query = st.text_input("🔍 Search by Course Name (e.g. BIT, Law, BBA)", placeholder="Type here to filter...").strip()
    
    if search_query:
        # Fetching data from your Supabase 'materials' table
        try:
            response = supabase.table("materials").select("*").ilike("course_program", f"%{search_query}%").order("week").execute()
            
            if response.data:
                for item in response.data:
                    with st.container(border=True):
                        col_text, col_vid = st.columns([1, 2])
                        
                        with col_text:
                            st.subheader(f"Week {item['week']}")
                            st.write(f"**Topic:** {item['course_name']}")
                            st.link_button("📂 View Course Notes", item['notes_url'])
                        
                        with col_vid:
                            url = str(item.get('video_url', ""))
                            if "youtube.com" in url or "youtu.be" in url:
                                v_id = url.split("v=")[1].split("&")[0] if "v=" in url else url.split("/")[-1]
                                st.markdown(f'<div class="video-container"><iframe src="https://www.youtube.com/embed/{v_id}"></iframe></div>', unsafe_allow_html=True)
                            else:
                                st.info("No video preview available for this entry.")
            else:
                st.warning("No records found for that course. Please check your spelling.")
        except Exception as e:
            st.error(f"Error fetching data: {e}")

# --- ADMIN DASHBOARD ---
elif menu == "Admin Dashboard":
    st.title("🛠️ Admin Management")
    t1, t2, t3 = st.tabs(["Add Single Entry", "Bulk Excel Upload", "Manage Database"])
    
    with t1:
        with st.form("manual_entry"):
            prog = st.text_input("Course Program (e.g. BIT 2.1)")
            name = st.text_input("Topic Covered")
            wk = st.number_input("Week Number", 1, 15)
            vid = st.text_input("YouTube Link")
            note = st.text_input("Google Docs/Notes Link")
            if st.form_submit_button("Save Entry"):
                supabase.table("materials").insert({"course_program": prog, "course_name": name, "week": wk, "video_url": vid, "notes_url": note}).execute()
                st.success("Entry Saved Successfully!")

    with t2:
        course_label = st.text_input("Course Name for Bulk Upload")
        file = st.file_uploader("Upload Excel Template", type=["xlsx", "csv"])
        if file and course_label and st.button("Start Bulk Upload"):
            df = pd.read_excel(file) if "xlsx" in file.name else pd.read_csv(file)
            for _, row in df.iterrows():
                supabase.table("materials").insert({
                    "course_program": course_label,
                    "course_name": str(row.get('Topic Covered', '')),
                    "week": int(row.get('Week', 1)),
                    "video_url": str(row.get('Embeddable YouTube Video Link', '')),
                    "notes_url": str(row.get('link to Google docs Document', ''))
                }).execute()
            st.success("Database Updated via Excel!")

    with t3:
        all_data = supabase.table("materials").select("*").execute()
        st.write(f"Total Entries: {len(all_data.data)}")
        for entry in all_data.data:
            c1, c2 = st.columns([4, 1])
            c1.write(f"**{entry['course_program']}** | Wk {entry['week']}: {entry['course_name']}")
            if c2.button("🗑️ Delete", key=f"del_{entry['id']}"):
                supabase.table("materials").delete().eq("id", entry['id']).execute()
                st.rerun()

# --- ANNOUNCEMENTS ---
elif menu == "Announcements":
    st.title("📢 President's Notice Board")
    notices = supabase.table("notices").select("*").order("created_at", desc=True).execute()
    
    if notices.data:
        for n in notices.data:
            with st.chat_message("user"):
                st.write(f"**{n['title']}**")
                st.write(n['content'])
    else:
        st.info("No recent announcements.")

st.markdown('<div class="footer">KIU Study Portal | Developed by KMT Dynamics © 2026</div>', unsafe_allow_html=True)

import streamlit as st
import pandas as pd
from supabase import create_client

# 1. DATABASE CONNECTION
PROJECT_ID = "uxtmgdenwfyuwhezcleh"
SUPABASE_URL = f"https://{PROJECT_ID}.supabase.co"
SUPABASE_KEY = "sb_publishable_1BIwMEH8FVDv7fFafz31uA_9FqAJr0-"

try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception:
    st.error("Database Connection Failed.")
    st.stop()

# 2. UI CONFIG
st.set_page_config(page_title="KIU Q10 Portal", layout="wide")

st.markdown("""
<style>
.footer { position: fixed; left: 0; bottom: 0; width: 100%; text-align: center; padding: 10px; background: white; border-top: 1px solid #eee; z-index: 999; }
.video-container { position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; background: #000; border-radius: 8px; margin-bottom: 10px; }
.video-container iframe { position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: 0; }
</style>
""", unsafe_allow_html=True)

# 3. LOGIN PAGE
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'> KIU Q10 Portal</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,1.5,1])
    with col2:
        with st.container(border=True):
            st.subheader("Login Access")
            st.text_input("Username")
            st.text_input("Password", type="password")
            if st.button("Login", use_container_width=True) or st.button(" Skip & Browse", use_container_width=True):
                st.session_state.logged_in = True
                st.rerun()
    st.stop()

# 4. NAVIGATION
role = st.sidebar.radio("Navigation", ["Student Portal", "Admin Dashboard", "President Board"])

if role == "Admin Dashboard":
    st.header(" Management Console")
    t1, t2, t3 = st.tabs([" Add Entry", " Bulk Upload", "Delete Content"])
    
    with t1:
        with st.form("manual"):
            p = st.text_input("Course Name")
            t = st.text_input("Module Topic")
            w = st.number_input("Week", 1, 15)
            y = st.text_input("YouTube/Slide Link")
            n = st.text_input("Notes Link")
            if st.form_submit_button("Save"):
                supabase.table("materials").insert({"course_program": p, "course_name": t, "week": w, "video_url": y, "notes_url": n}).execute()
                st.success("Saved!")

    with t2:
        target = st.text_input("Target Course Name")
        f = st.file_uploader("Upload CSV/Excel", type=["xlsx", "csv"])
        if f and target and st.button("Start Upload"):
            df = pd.read_excel(f) if "xlsx" in f.name else pd.read_csv(f)
            for index, row in df.iterrows():
                supabase.table("materials").insert({
                    "course_program": target,
                    "course_name": str(row.get('Topic Covered', "")),
                    "week": int(row.get('Week', 1)),
                    "video_url": str(row.get('Embeddable YouTube Video Link', "")),
                    "notes_url": str(row.get('link to Google docs Document', ""))
                }).execute()
            st.success("Done!")

    with t3:
        # FIXED SECTION: This was likely where your SyntaxError occurred
        data = supabase.table("materials").select("*").execute()
        if data.data:
            for item in data.data:
                c1, c2 = st.columns([4, 1])
                c1.write(f"**{item['course_program']}** | Wk {item['week']}: {item['course_name']}")
                if c2.button("Delete", key=f"del_{item['id']}"):
                    supabase.table("materials").delete().eq("id", item['id']).execute()
                    st.rerun()

elif role == "President Board":
    with st.form("notice"):
        tt = st.text_input("Title")
        mm = st.text_area("Message")
        if st.form_submit_button("Publish"):
            supabase.table("notices").insert({"title": tt, "content": mm}).execute()
            st.success("Published!")

elif role == "Student Portal":
    search = st.text_input("Search Course").strip()
    if search:
        res = supabase.table("materials").select("*").ilike("course_program", f"%{search}%").order("week").execute()
        for item in res.data:
            with st.expander(f"Week {item['week']} - {item['course_name']}"):
                url = str(item.get('video_url', ""))
                if "youtube.com" in url or "youtu.be" in url:
                    v_id = url.split("v=")[1].split("&")[0] if "v=" in url else url.split("/")[-1]
                    st.markdown(f'<div class="video-container"><iframe src="https://www.youtube.com/embed/{v_id}"></iframe></div>', unsafe_allow_html=True)
                elif "docs.google.com" in url:
                    st.markdown(f'<div class="video-container"><iframe src="{url.replace("/edit", "/embed")}"></iframe></div>', unsafe_allow_html=True)
                st.link_button("Notes", item.get('notes_url', "#"))

st.markdown('<div class="footer">Built by KMT Dynamics</div>', unsafe_allow_html=True)

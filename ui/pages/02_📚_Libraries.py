import shutil
from pathlib import Path

import streamlit as st
from config import DATADIR, DEV, get_page_config, init_session
from tinydb import Query, TinyDB

# Set up page config & init session
st.set_page_config(**get_page_config())
init_session(st.session_state)

# Render session state if in dev mode
if DEV:
    with st.sidebar.expander("Session state"):
        st.write(st.session_state)

st.write("## 📚 &nbsp; Libraries")
st.write("---")

# Library creation & selection widget
# -----------------------------------
# Create a form to add a new library
with st.sidebar.form("create_library"):
    new_library = st.text_input("Create new library", help="Enter a new library name")
    add_library = st.form_submit_button(label="➕ Create")
    success_container = st.empty()

# If the form was submitted, create a new library
if add_library:
    if new_library:
        # Update session state
        init_session(st.session_state, library=new_library, reset=True)
        st.experimental_rerun()
    else:
        success_container.error("Please enter a library name")

existing_libraries = [p.name for p in Path(DATADIR).iterdir() if p.is_dir()]
selected_library = st.sidebar.selectbox(
    "📚 Select Library", options=existing_libraries, index=existing_libraries.index(st.session_state.library)
)
if selected_library != st.session_state.library:
    # Update session state
    init_session(st.session_state, library=selected_library, reset=True)
    st.experimental_rerun()


# Find all tinydb.json files in the datadir and display them as libraries
dbs = list(Path(DATADIR).glob("**/tinydb*.json"))
if len(dbs) == 1:
    st.info("🐸 &nbsp; Deleting the only remaining library will reset the app & recreate the default library")

# Sort dbs by creation dat
dbs = sorted(dbs, key=lambda x: x.stat().st_ctime, reverse=True)
for dbpath in dbs:
    libname = dbpath.parent.name
    db = TinyDB(dbpath)
    # Render library name & selected status
    st.write(f"#### `{libname}`")

    st.markdown(
        f"""
    <b>Path: `{dbpath.parent}`</b><br>
    <b>Media: `{len(db.table('Media'))}`</b>; &nbsp;
    <b>Captions: `{len(db.table('Captions'))}`</b>
    """,
        unsafe_allow_html=True,
    )

    # Button to select library. Render as disabled if already selected
    if libname == st.session_state.library:
        st.button("📌 &nbsp; Selected", disabled=True)
    else:
        # Button to select library
        if st.button("📌 &nbsp; Select", key=libname + "select"):
            init_session(st.session_state, library=libname, reset=True)
            st.experimental_rerun()

    # Button to delete library
    if st.button("🗑️ &nbsp; Delete", key=libname + "delete"):
        shutil.rmtree(dbpath.parent)
        init_session(st.session_state, reset=True)
        st.experimental_rerun()

    st.write("---")

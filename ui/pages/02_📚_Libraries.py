import shutil
from datetime import datetime
from pathlib import Path

import humanize
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

# Create a form to add a new library
with st.form("create_library"):
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


# Find all tinydb.json files in the datadir and display them as libraries
dbs = list(Path(DATADIR).glob("**/tinydb*.json"))
if len(dbs) == 1:
    st.info("🐸 &nbsp; Deleting the only remaining library will reset the app & recreate the default library")

# Sort dbs by creation date
dbs = sorted(dbs, key=lambda x: x.stat().st_ctime, reverse=True)
for dbpath in dbs:
    libname = dbpath.parent.name
    db = TinyDB(dbpath)
    # Render library name & selected status
    st.write(f"#### `{libname}`")

    st.markdown(
        f"""
    <b>Path: `{dbpath.parent}`</b> `[created: {humanize.naturaltime(datetime.fromtimestamp(dbpath.stat().st_ctime))}]`<br>
    <b>Media: `{len(db.table('Media'))}`</b>; &nbsp;
    <b>Captions: `{len(db.table('Captions'))}`</b>
    """,
        unsafe_allow_html=True,
    )

    # Button to delete library
    if st.button("🗑️ &nbsp; Delete", key=libname + "delete"):
        shutil.rmtree(dbpath.parent)
        init_session(st.session_state, reset=True)
        st.experimental_rerun()

    st.write("---")

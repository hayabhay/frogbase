import re
from datetime import datetime
from pathlib import Path

import streamlit as st
from config import DATADIR, DEV, TEMP_DIR, get_page_config, init_session
from tinydb import Query
from utils import get_formatted_media_info

# Set up page config & init session
st.set_page_config(**get_page_config())
init_session(st.session_state)

# Render session state if in dev mode
if DEV:
    with st.sidebar.expander("Session state"):
        st.write(st.session_state)

# Aliases for readability
# --------------------------------
fb = st.session_state.fb


# List view
# --------------------------------
if st.session_state.listview:  # noqa: C901
    # Reset detail view session state
    st.session_state.selected_media_offset = 0

    # Library selection widget
    # --------------------------------
    with st.sidebar.expander("📚 &nbsp; Libraries", expanded=False):
        existing_libraries = [p.name for p in Path(DATADIR).iterdir() if p.is_dir()]
        selected_library = st.selectbox(
            "Select Library", options=existing_libraries, index=existing_libraries.index(st.session_state.library)
        )
        if selected_library != st.session_state.library:
            # Update session state
            init_session(st.session_state, library=selected_library, reset=True)
            st.experimental_rerun()

    # Add Media widget
    # --------------------------------
    with st.sidebar.expander("➕ &nbsp; Add Media", expanded=False):
        # Render media type selection on the sidebar & the form
        source_type = st.radio("Media Source", ["Web", "Upload"], label_visibility="collapsed")
        with st.form("input_form"):
            # Add defaults for web_url & input_files to avoid pylance warnings
            web_url = None
            input_files = None
            if source_type == "Web":
                web_url = st.text_area("Web URLs (one per line)", help="Enter one URL per line")
                audio_only = st.checkbox("Audio Only", value=True)
                st.caption(
                    """
                    Supported sites: YouTube channels, playlists, videos; Vimeo etc.
                    [(view list)](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md)
                """
                )
            elif source_type == "Upload":
                input_files = st.file_uploader(
                    "Add one or more files",
                    type=["mp4", "avi", "mov", "mkv", "mp3", "wav"],
                    accept_multiple_files=True,
                )
            # TODO: Add record option later
            # elif source_type == "Record":
            #     pass
            add_media = st.form_submit_button(label="Add Media!")

        if add_media:
            if source_type == "Web":
                if web_url:
                    sources = [url.strip() for url in web_url.split("\n")]
                    opts = {"audio_only": audio_only}
                    st.success("Media downloading & processing in progress.")
                else:
                    st.error("Please enter URLs")
            elif source_type == "Upload":
                if input_files:
                    # Streamlit file uploader returns a list of BytesIO objects
                    # and frogbase does not support this yet. For now,
                    # bytes will first be saved to a temporary directory and
                    # then passed to frogbase as a list of file paths.
                    sources = []
                    # Move files from temp dir to libdir
                    opts = {"move": True}

                    for input_file in input_files:
                        # Destination path
                        dest_path = TEMP_DIR / input_file.name
                        # Save file to destination path
                        with open(dest_path, "wb") as f:
                            f.write(input_file.getvalue())
                        # Add to sources list
                        sources.append(str(dest_path.resolve()))
                else:
                    st.error("Please upload files")
            # elif source_type == "Record":
            #     pass

            if sources:
                fb.add(sources, **opts).transcribe(ignore_captioned=True)
                st.success("Media downloading & processing in progress.")

            # Set list mode to true
            st.session_state.listview = True
            st.experimental_rerun()

    # Filter widget
    # --------------------------------
    with st.sidebar.expander("🚫 &nbsp; Filters", expanded=False):
        # NOTE: Currently compound filters are supported using the tinydb query syntax
        # https://tinydb.readthedocs.io/en/latest/usage.html#queries
        # Here, the UI implies 'AND' operation between filters
        filters = None
        Media = Query()

        # Add a date range filter
        date_range = st.date_input("Date range", value=(), help="Filter by upload date. Leave blank to ignore.")
        if date_range:
            start_date = date_range[0].strftime("%Y%m%d")
            # Construct subfilter & add to filters
            subfilter = Media.upload_date >= start_date
            filters = filters & subfilter if filters else subfilter
            if len(date_range) == 2:
                end_date = date_range[1].strftime("%Y%m%d")
                # Construct subfilter & add to filters
                subfilter = Media.upload_date <= end_date
                filters = filters & subfilter if filters else subfilter

        # Add search filter
        title_contains = st.text_input(
            "Title contains",
            help="Search for media by keywords in the title (case insensitive)",
        )
        if title_contains:
            subfilter = Media.title.matches(f".*{title_contains}.*", flags=re.IGNORECASE)
            filters = filters & subfilter if filters else subfilter

        # Add uploader filter
        uploader_name = st.text_input("Uploader", help="Filter by uploader name/handle")
        if uploader_name:
            subfilter = Media.uploader_name.matches(f".*{uploader_name}.*", flags=re.IGNORECASE)
            filters = filters & subfilter if filters else subfilter

        # Add source type filter
        source = st.text_input(
            "Source", placeholder="youtube, vimeo, etc.", help="Filter by source of the original media"
        )

        if source:
            subfilter = Media.source.matches(f".*{source}.*", flags=re.IGNORECASE)
            filters = filters & subfilter if filters else subfilter

    # Main content
    # --------------------------------
    st.write(f"## 🐸 &nbsp; Library - `{st.session_state.library}`")
    st.write("---")
    query = st.sidebar.text_input(
        "Search",
        help="This is a Semantic Search Engine that searches your media library based on what is said & shown",
    )

    # Get list of media objects that match the filters
    media_objs = fb.media.search(filters) if filters else fb.media.all()

    if media_objs:
        # Render each media object
        for media_obj in media_objs:
            # Create 2 columns
            meta_col, media_col = st.columns([2, 1], gap="large")

            with meta_col:
                # Add a meta caption
                st.write(f"#### {media_obj.title}")
                # If dev mode is on, show the raw media object
                if DEV:
                    with st.expander("Raw media object", expanded=False):
                        st.json(media_obj.model_dump())

                st.markdown(get_formatted_media_info(media_obj), unsafe_allow_html=True)

                # Add nav buttons
                if st.button("🧐 &nbsp; Details", key=f"detail-{media_obj.id}"):
                    st.session_state.listview = False
                    st.session_state.selected_media = media_obj
                    st.experimental_rerun()

                if st.button("🗑️ &nbsp; Delete", key=f"delete-{media_obj.id}"):
                    media_obj.delete()
                    st.experimental_rerun()

            # Render the media
            with media_col:
                # YouTube videos can be directly embedded by streamlit
                if media_obj.src_name.lower() == "youtube":
                    st.video(media_obj.src)
                elif media_obj.is_video:
                    st.video(media_obj.loc)
                else:
                    st.audio(media_obj.loc)

            st.write("---")
    else:
        if filters:
            st.warning("No media found matching the filters. Try again with different filters.")
        else:
            st.info("No media found. Add some media to get started.")
            st.write("If you just want to test the app, click the button below to add some sample media.")
            if st.button("Add sample media"):
                fb.demo()
                st.experimental_rerun()


# Detail view
# -----------
if not st.session_state.listview:
    # Get the selected media object
    media_obj = st.session_state.selected_media

    MAX_TITLE_LEN = 80
    if len(media_obj.title) > MAX_TITLE_LEN:
        st.write(f"### {media_obj.title[:MAX_TITLE_LEN]}...")
    else:
        st.write(f"### {media_obj.title}")

    if DEV:
        with st.expander("Media object", expanded=False):
            st.write(media_obj.model_dump())

    # Render mini nav
    back_col, del_col = st.sidebar.columns(2)
    with back_col:
        # Add a button to show the list view
        if st.button("◀️ &nbsp; Back to list", key="back-to-list-main"):
            st.session_state.listview = True
            st.experimental_rerun()
    with del_col:
        if st.button("🗑️ Delete Media", key=f"delete-{media_obj.id}"):
            fb.media.delete(media_obj)
            st.session_state.listview = True
            st.experimental_rerun()

    # YouTube videos can be directly embedded by streamlit
    st.sidebar.audio(media_obj.loc, start_time=st.session_state.selected_media_offset)
    if media_obj.src_name.lower() == "youtube":
        st.sidebar.video(media_obj.src, start_time=st.session_state.selected_media_offset)
    elif media_obj.is_video:
        st.sidebar.video(media_obj.loc, start_time=st.session_state.selected_media_offset)

    with st.expander("📝 &nbsp; About"):
        st.markdown(get_formatted_media_info(media_obj, details=True), unsafe_allow_html=True)

    # Render captions
    captions = media_obj.captions.all()

    if captions:
        tabs = st.tabs([f"{c.lang} ({c.by[:7]})" for c in captions])

        # TODO: To speed up loading, paginate the captions
        for i, caption_obj in enumerate(captions):
            tab = tabs[i]
            with tab:
                with st.expander("📝 &nbsp; Caption Info", expanded=False):
                    st.json(caption_obj.model_dump())

                # Load the caption file
                captions_vtt = caption_obj.load()

                for caption in captions_vtt:
                    # Create 2 columns
                    meta_col, text_col = st.columns([1, 6], gap="small")

                    with meta_col:
                        if st.button(
                            f"▶️ &nbsp; {int(caption._start)} - {int(caption._end)}",
                            key=f"play-{caption._start}-{caption._end}",
                        ):
                            st.session_state.selected_media_offset = int(caption._start)
                            st.experimental_rerun()

                    with text_col:
                        st.write(f"##### `{caption.text}`")

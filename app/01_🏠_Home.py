from datetime import datetime
from pathlib import Path

import streamlit as st
from config import get_page_config, get_whisper_settings, save_whisper_settings
from core import MediaManager

st.set_page_config(**get_page_config())


# Session states
# --------------
# Set session state to toggle list & detail view
if "list_mode" not in st.session_state:
    st.session_state.list_mode = True
    st.session_state.selected_media = None
    st.session_state.selected_media_offset = 0

# Add whisper settings to session state
if "whisper_params" not in st.session_state:
    st.session_state.whisper_params = get_whisper_settings()

if "media_manager" not in st.session_state:
    st.session_state.media_manager = MediaManager()

# Alias for session state media manager
media_manager = st.session_state.media_manager


# Helper functions
# ----------------
def get_formatted_date(date_str: str) -> str:
    date_str = datetime.fromisoformat(date_str)
    date = date_str.strftime("%d %b %Y")
    time = date_str.strftime("%I:%M%p")
    return f"{time}, {date}"


# Add view
# ---------
with st.sidebar.expander("➕ &nbsp; Add Media", expanded=False):
    # # Render media type selection on the sidebar & the form
    source_type = st.radio("Media Source", ["YouTube", "Upload"], label_visibility="collapsed")
    with st.form("input_form"):
        if source_type == "YouTube":
            youtube_url = st.text_input("Youtube video or playlist URL")
        elif source_type == "Upload":
            input_files = st.file_uploader(
                "Add one or more files", type=["mp4", "avi", "mov", "mkv", "mp3", "wav"], accept_multiple_files=True
            )
        task_options = ["transcribe", "translate"]
        task = st.selectbox(
            "Task", options=task_options, index=task_options.index(st.session_state.whisper_params["task"])
        )
        add_media = st.form_submit_button(label="Add Media!")

    if add_media:
        source = None
        if source_type == "YouTube":
            if youtube_url and youtube_url.startswith("http"):
                source = youtube_url
            else:
                st.error("Please enter a valid YouTube URL")
        elif source_type == "Upload":
            if input_files:
                source = input_files
            else:
                st.error("Please upload files")

        # Lowercase the source type
        source_type = source_type.lower()

        # Update session state whisper params
        st.session_state.whisper_params["task"] = task

        if source:
            media_manager.add(
                source=source,
                source_type=source_type,
                **st.session_state.whisper_params,
            )
            # Render success message
            st.success("Media downloading & processing in progress.")

        # Set list mode to true
        st.session_state.list_mode = True
        st.experimental_rerun()

# Filters for media
# -----------------
with st.sidebar.expander("🔎 &nbsp; Search", expanded=st.session_state.list_mode):
    # Set a filter param set for media objects
    filters = {}

    # Add a date range filter
    date_range = st.date_input(
        "Date range",
        value=(),
    )
    if date_range:
        filters["start_date"] = date_range[0].strftime("%Y-%m-%d")
        if len(date_range) == 2:
            filters["end_date"] = date_range[1].strftime("%Y-%m-%d")

    # Add a media type filter
    media_type = st.selectbox("Media Source", options=["All", "YouTube", "Upload"], index=0)
    if media_type != "All":
        filters["source_type"] = media_type.lower()

    # Add search filter
    search_by_name = st.text_input("Search (by title)")
    if search_by_name:
        filters["search_by_name"] = search_by_name

    # Add search filter
    search_by_transcript = st.text_input("Search (by transcript)")
    if search_by_transcript:
        filters["search_by_transcript"] = search_by_transcript

    # Number of items per page
    limit = st.number_input("Items per page", min_value=1, max_value=100, value=10)
    filters["limit"] = limit


# List view
# ---------
if st.session_state.list_mode:
    # # Reset detail view session state
    st.session_state.selected_media_offset = 0

    st.write("## Media Library")

    if "search_by_transcript" in filters:
        # Create tabs for search by file & by transcript
        segment_tab, file_tab = st.tabs(["Segments", "Files"])
    else:
        file_tab = st.container()

    with file_tab:
        # Get all media with the filters
        media_objs = media_manager.get_list(**filters)

        # If no media objects are found
        if not media_objs:
            # Render a line only if search by transcript is not enabled
            if "search_by_transcript" not in filters:
                st.write("---")
            st.warning("No media found. Add some media or update filters and try again.")

        # Render media objects
        for media in media_objs:
            # Create 2 columns
            meta_col, media_col = st.columns([2, 1], gap="large")

            with meta_col:
                # Add a meta caption
                st.write(f"#### {media['source_name']}")

                source_type = "YouTube" if media["source_type"] == "youtube" else "upload"
                st.markdown(
                    f"""
                    <i>Source</i>: {source_type}<br/>
                    <i>Added</i>: {get_formatted_date(media["created"])}<br/>
                    <i>Generated by</i>: {media["generated_by"]}<br/>
                """,
                    unsafe_allow_html=True,
                )

                if st.button("🧐 Details", key=f"detail-{media['id']}"):
                    st.session_state.list_mode = False
                    st.session_state.selected_media = media["id"]
                    st.experimental_rerun()

                if st.button("🗑️ Delete", key=f"delete-{media['id']}"):
                    media_manager.delete(media["id"])
                    st.experimental_rerun()

            with media_col:
                # Render the media
                if media["source_type"] == "youtube":
                    st.video(media["source_link"])
                elif media["source_type"] == "upload":
                    st.audio(media["filepath"])

            st.write("---")

    if "search_by_transcript" in filters:
        with segment_tab:
            # Get all media with the filters
            segment_objs = media_manager.get_segments(**filters)

            # If no media objects are found
            if not segment_objs:
                st.warning("No segments found. Add some media or update filters and try again.")

            # Render media objects
            for segment in segment_objs:
                # Create 2 columns
                meta_col, media_col = st.columns([2, 1], gap="large")

                with meta_col:
                    # Add a meta caption
                    st.markdown(
                        f"""<h4><i>"{segment["text"]}</i>" - <code>[{int(segment['start'])}s - {int(segment['end'])}s]</code></h4>""",
                        unsafe_allow_html=True,
                    )

                    # Add a meta caption
                    source_type = "YouTube" if media["source_type"] == "youtube" else "uploaded"
                    st.markdown(
                        f"""
                        <i>Source</i>: <b>{media['source_name']}</b> ({source_type})<br/>
                        <i>Added</i>: {get_formatted_date(media["created"])}<br/>
                        <i>Generated by</i>: {media["generated_by"]}<br/>
                    """,
                        unsafe_allow_html=True,
                    )

                    if st.button("🧐 Details", key=f"segment-{segment['number']}-{segment['media']['id']}"):
                        st.session_state.list_mode = False
                        st.session_state.selected_media = segment["media"]["id"]
                        st.experimental_rerun()

                with media_col:
                    # NOTE: Adding video for youtube makes the list slow & ugly and is ignored here
                    st.audio(segment["media"]["filepath"], start_time=int(segment["start"]))

                st.write("---")


# Detail view
# -----------
else:
    # Get the selected media object
    media = media_manager.get_detail(media_id=st.session_state.selected_media)

    # Render mini nav
    back_col, del_col = st.sidebar.columns(2)
    with back_col:
        # Add a button to show the list view
        if st.button("◀️ &nbsp; Back to list", key="back-to-list-main"):
            st.session_state.list_mode = True
            st.experimental_rerun()
    with del_col:
        if st.button("🗑️ Delete Media", key=f"delete-{media['id']}"):
            media_manager.delete(media["id"])
            st.session_state.list_mode = True
            st.experimental_rerun()

    st.sidebar.write(f"""### {media["source_name"]}""")

    # Render the media. Use both audio & video for youtube
    if media["source_type"] == "youtube":
        st.sidebar.audio(media["filepath"], start_time=st.session_state.selected_media_offset)
        st.sidebar.video(media["source_link"])
    elif media["source_type"] == "upload":
        st.sidebar.audio(media["filepath"], start_time=st.session_state.selected_media_offset)

    st.write(f'## {media["source_name"]}')

    with st.expander("📝 &nbsp; Metadata"):
        # Add a meta caption
        source_type = "YouTube" if media["source_type"] == "youtube" else "uploaded"
        st.markdown(
            f"""
            <i>Source</i>: <b>{media['source_name']}</b> ({source_type})<br/>
            <i>Added</i>: {get_formatted_date(media["created"])}<br/>
            <i>Generated by</i>: {media["generated_by"]}<br/>
            <i>Audio directory</i>: `{Path(media["filepath"]).parent}`<br/>
            <i>Audio path</i>: `{media["filepath"]}`<br/>
            <i>Transcript path</i>: `{Path(media["filepath"]).parent / "transcript"}[(.srt, .vtt, .json, .txt, .tsv)]`<br/>
        """,
            unsafe_allow_html=True,
        )

    with st.expander("📝 &nbsp; Full Transcript"):
        st.markdown(media["transcript"])
        st.write("---")

    st.info(
        """Clicking on a segment will move start position to the segment (only audio player will continue playing while video will pause)"""
    )
    # Iterate over all segments in the transcript
    for segment in media["segments"]:
        # Create 2 columns
        meta_col, text_col = st.columns([1, 6], gap="small")

        with meta_col:
            if st.button(f"▶️ &nbsp; {int(segment['start'])}: {int(segment['end'])}", key=f"play-{segment['number']}"):
                st.session_state.selected_media_offset = int(segment["start"])
                st.experimental_rerun()

        with text_col:
            st.write(f'##### `{segment["text"]}`')

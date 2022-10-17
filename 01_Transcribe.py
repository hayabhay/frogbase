import streamlit as st

from transcriber import Transcription

# Set app wide config
st.set_page_config(
    page_title="Transcribe | Whisper UI",
    page_icon="🤖",
    layout="wide",
    menu_items={
        "Get Help": "https://twitter.com/hayabhay",
        "Report a bug": "https://github.com/hayabhay/whisper-ui/issues",
        "About": """This is a simple GUI for OpenAI's Whisper.
        Please report any bugs or issues on [Github](https://github.com/hayabhay/whisper-ui/). Thanks!""",
    },
)

# Render input type selection on the sidebar & the form
input_type = st.sidebar.selectbox("Input Type", ["YouTube", "Link", "File"])

with st.sidebar.form("input_form"):
    if input_type == "YouTube":
        youtube_url = st.text_input("URL (video works fine)")
    if input_type == "Link":
        url = st.text_input("URL (video works fine)")
    elif input_type == "File":
        input_file = st.file_uploader("File", type=["mp4", "avi", "mov", "mkv", "mp3", "wav"])

    # Create two options. Either Youtube or a local file
    name = st.text_input("Audio/Video Name", "some_cool_media")

    start = st.number_input("Start time for the media (sec)", min_value=0.0, step=1.0)
    duration = st.number_input("Duration (sec) - negative implies till the end", min_value=-1.0, step=1.0)

    whisper_model = st.selectbox("Whisper model", options=["tiny", "base", "small", "medium", "large"], index=1)
    extra_configs = st.expander("Extra Configs")
    with extra_configs:
        temperature = st.number_input("Temperature", min_value=0.0, max_value=1.0, value=0.0, step=0.1)
        temperature_increment_on_fallback = st.number_input(
            "Temperature Increment on Fallback", min_value=0.0, max_value=1.0, value=0.2, step=0.2
        )
        no_speech_threshold = st.slider("No Speech Threshold", min_value=0.0, max_value=1.0, value=0.6, step=0.05)
        logprob_threshold = st.slider("Logprob Threshold", min_value=-20.0, max_value=0.0, value=-1.0, step=0.1)
        compression_ratio_threshold = st.slider(
            "Compression Ratio Threshold", min_value=0.0, max_value=10.0, value=2.4, step=0.1
        )
        condition_on_previous_text = st.checkbox("Condition on previous text", value=True)
    transcribe = st.form_submit_button(label="Transcribe!")

if transcribe:
    if not name:
        st.error("Please enter a name for the audio/video")
    if input_type == "YouTube":
        if youtube_url and youtube_url.startswith("http"):
            st.session_state.transcription = Transcription(name, youtube_url, "youtube", start, duration)
        else:
            st.error("Please enter a valid YouTube URL")
    elif input_type == "Link":
        if url and url.startswith("http"):
            st.session_state.transcription = Transcription(name, url, "link", start, duration)
            downloaded = True
        else:
            st.error("Please enter a valid URL")
    elif input_type == "File":
        if input_file:
            st.session_state.transcription = Transcription(name, input_file, "file", start, duration)
        else:
            st.error("Please upload a file")

    # Transcribe on click
    st.session_state.transcription.transcribe(
        whisper_model,
        temperature,
        temperature_increment_on_fallback,
        no_speech_threshold,
        logprob_threshold,
        compression_ratio_threshold,
        condition_on_previous_text,
    )

# If there is a transcription, render it. If not, display instructions
if "transcription" in st.session_state:
    # Render transcriptions along with the audio & video if available
    transcription_col, media_col = st.columns(2, gap="large")

    transcription_col.markdown("#### Trimmed audio")
    with open(st.session_state.transcription.audio_path, "rb") as f:
        transcription_col.audio(f.read())
    transcription_col.markdown("---")
    transcription_col.markdown(f"#### Transcription (whisper model - `{whisper_model}`)")

    # Trim raw transcribed output off tokens to simplify

    raw_output = transcription_col.expander("Raw output")
    raw_output.write(st.session_state.transcription.raw_output)

    transcription_col.markdown(f"##### Language: `{st.session_state.transcription.language}`")
    # Show transcription in a slightly nicer format
    for segment in st.session_state.transcription.segments:
        transcription_col.markdown(
            f"""[{round(segment["start"], 1)} - {round(segment["end"], 1)}] - {segment["text"]}"""
        )

    media_col.markdown("#### Original audio")
    with open(st.session_state.transcription.og_audio_path, "rb") as f:
        media_col.audio(f.read())
    if input_type == "YouTube":
        media_col.markdown("---")
        media_col.markdown("#### Original YouTube Video")
        media_col.video(st.session_state.transcription.source)
else:
    with open("instructions.md", "r") as f:
        st.write(f.read())

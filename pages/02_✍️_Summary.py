import streamlit as st
from PIL import Image

# Set app wide config
st.set_page_config(
    page_title="OpenAI Whisper | Streamlit",
    page_icon="🤖",
    layout="wide",
    menu_items={
        "Get Help": "https://twitter.com/hayabhay",
        "Report a bug": "https://github.com/hayabhay/whisper-ui/issues",
        "About": """This is a simple GUI for OpenAI's Whisper.
        Please report any bugs or issues on [Github](https://github.com/hayabhay/whisper-ui/). Thanks!""",
    },
)

if "transcription" in st.session_state:
    with st.sidebar.form("summary_form"):
        model = st.text_input("🤗 Huggingface model name", "facebook/bart-large-cnn")
        min_length = st.number_input("Minimum length", min_value=50, max_value=250, value=50)
        max_length = st.number_input("Max length", min_value=100, max_value=5000, value=500, step=100)
        do_sample = st.checkbox("Sample", value=False)
        summarize = st.form_submit_button(label="Summarize!")

    if summarize:
        st.session_state.transcription.summarize(model, min_length, max_length, do_sample)

    st.write("## Original Text")
    st.write(st.session_state.transcription.text)
    st.write("---")

    if st.session_state.transcription.summarized:
        st.write("## Summary")
        st.write(st.session_state.transcription.summary)
else:
    st.error("Please upload an audio file to get started")

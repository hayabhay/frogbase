import streamlit as st

# Set app wide config
st.set_page_config(
    page_title="Help | Whisper UI",
    page_icon="🤖",
    layout="wide",
    menu_items={
        "Get Help": "https://twitter.com/hayabhay",
        "Report a bug": "https://github.com/hayabhay/whisper-ui/issues",
        "About": """This is a simple GUI for OpenAI's Whisper.
        Please report any bugs or issues on [Github](https://github.com/hayabhay/whisper-ui/). Thanks!""",
    },
)

with open("instructions.md", "r") as f:
    st.write(f.read())

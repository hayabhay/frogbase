import streamlit as st
from config import WHISPER_SETTINGS_FILE, get_page_config, get_whisper_settings, save_whisper_settings
from core import MediaManager

st.set_page_config(**get_page_config(layout="centered"))

# Session states
# --------------
# NOTE: This is repeated since direct landing on this page will throw an error
# Add whisper settings to session state
if "whisper_params" not in st.session_state:
    st.session_state.whisper_params = get_whisper_settings()

# Whisper config
# --------------
st.write("### ⚙️ Whisper Settings")
with st.form("whisper_settings_form"):
    model_options = ["tiny", "base", "small", "medium", "large"]
    selected_model = model_options.index(st.session_state.whisper_params["whisper_model"])
    whisper_model = st.selectbox("Model", options=model_options, index=selected_model)
    temperature = st.number_input(
        "Temperature", min_value=0.0, max_value=1.0, value=st.session_state.whisper_params["temperature"], step=0.1
    )
    temperature_increment_on_fallback = st.number_input(
        "Temperature Increment on Fallback",
        min_value=0.0,
        max_value=1.0,
        value=st.session_state.whisper_params["temperature_increment_on_fallback"],
        step=0.2,
    )
    no_speech_threshold = st.slider(
        "No Speech Threshold",
        min_value=0.0,
        max_value=1.0,
        value=st.session_state.whisper_params["no_speech_threshold"],
        step=0.05,
    )
    logprob_threshold = st.slider(
        "Logprob Threshold",
        min_value=-20.0,
        max_value=0.0,
        value=st.session_state.whisper_params["logprob_threshold"],
        step=0.1,
    )
    compression_ratio_threshold = st.slider(
        "Compression Ratio Threshold",
        min_value=0.0,
        max_value=10.0,
        value=st.session_state.whisper_params["compression_ratio_threshold"],
        step=0.1,
    )
    condition_on_previous_text = st.checkbox(
        "Condition on previous text", value=st.session_state.whisper_params["condition_on_previous_text"]
    )
    language_options = ['en', 'zh', 'de', 'es', 'ru', 'ko', 'fr', 'ja', 'pt', 'tr', 'pl', 'ca', 'nl', 'ar', 'sv', 'it', 'id', 'hi', 'fi', 'vi', 'he', 'uk', 'el', 'ms', 'cs', 'ro', 'da', 'hu', 'ta', 'no', 'th', 'ur', 'hr', 'bg', 'lt', 'la', 'mi', 'ml', 'cy', 'sk', 'te', 'fa', 'lv', 'bn', 'sr', 'az', 'sl', 'kn', 'et', 'mk', 'br', 'eu', 'is', 'hy', 'ne', 'mn', 'bs', 'kk', 'sq', 'sw', 'gl', 'mr', 'pa', 'si', 'km', 'sn', 'yo', 'so', 'af', 'oc', 'ka', 'be', 'tg', 'sd', 'gu', 'am', 'yi', 'lo', 'uz', 'fo', 'ht', 'ps', 'tk', 'nn', 'mt', 'sa', 'lb', 'my', 'bo', 'tl', 'mg', 'as', 'tt', 'haw', 'ln', 'ha', 'ba', 'jw', 'su']
    selected_language = language_options.index(st.session_state.whisper_params["language"])
    language = st.selectbox(
        "Language", options=language_options, index=selected_language
    )
    verbose = st.checkbox("Verbose", value=st.session_state.whisper_params["verbose"])

    save_settings = st.form_submit_button(label="💾 Save settings")
    success_container = st.empty()

    if save_settings:
        # Update session state
        updated_whisper_settings = {
            "whisper_model": whisper_model,
            "temperature": temperature,
            "temperature_increment_on_fallback": temperature_increment_on_fallback,
            "no_speech_threshold": no_speech_threshold,
            "logprob_threshold": logprob_threshold,
            "compression_ratio_threshold": compression_ratio_threshold,
            "condition_on_previous_text": condition_on_previous_text,
            "verbose": verbose,
            "language": language
        }
        # Commit to session & disk
        st.session_state.whisper_params = updated_whisper_settings
        save_whisper_settings(st.session_state.whisper_params)
        success_container.success("Settings saved!")

st.write(f"These settings are used for all media and will be saved to `{WHISPER_SETTINGS_FILE}`.")

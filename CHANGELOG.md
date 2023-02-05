# Changelog
All notable changes to this project will be documented in this file.

## `v1.0.0` (2023-02-09)
Since there was some apetite for this, I've rewritten this to make it a tad cleaner with a few additional features based on issues raised and personal preferences.
1. Ability to download entire YouTube playlists and upload multiple files at once
2. Ability browse, filter, and search through saved audio files (For now, this is done with a simple SQLite database & SQLAlchemy ORM)
3. Auto-export of transcriptions in multiple formats (was a feature request)
4. GPT-3 integration - Given the sudden increase in popularity of GPT-3, I've added a simple integration with the API. You can now set an API key and have GPT-3.5 summarize your transcriptions. Very likely, the next step will be to allow fine tuned models of transcription suites for modalities like question answering.
5. Live Transcription with Whisper - This is done by using the excellent [streamlit-webrtc](https://github.com/whitphx/streamlit-webrtc) library. This enables live transcription of audio from a microphone and can be used to take voice notes.


## `v0.0.1` (2022-10-17)
Initial release for demand testing ([PR #1](https://github.com/hayabhay/whisper-ui/pull/1)).

Features:
- Ability to process media from youtube & local files
- Whisper transcription
- Basic huggingface integration for summarization

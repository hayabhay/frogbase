
## Changelog
All notable changes to this project will be documented in this file.

### `v1.1.0` (2023-02-08)
- Merged feature from [@Eidenz](https://github.com/Eidenz) to add translation in addition to transcription

### `v1.0.0a` (2023-02-07)
Since there was some apetite for this, I've rewritten this to make it a tad cleaner with a few additional features based on issues raised and personal preferences.
1. Ability to download entire YouTube playlists and upload multiple files at once
2. Ability browse, filter, and search through saved audio files (For now, this is done with a simple SQLite database & SQLAlchemy ORM)
3. Auto-export of transcriptions in multiple formats (was a feature request)
4. Simple substring based search for transcript segments. This is done with a simple `LIKE` query on the SQLite database.
5. Fully reworked UI with a cleaner layout and more intuitive navigation.
6. Ability to save whisper configurations and reuse to prevent having to re-enter the same parameters every time.
7. Removed the ability to crop audio after download to simplify the codebase. Also, temporarily removed summarization until GPT-3 integration is complete.
### `v0.0.1` (2022-10-17)
Initial release for demand testing ([PR #1](https://github.com/hayabhay/whisper-ui/pull/1)).

Features:
- Ability to process media from youtube & local files
- Whisper transcription
- Basic huggingface integration for summarization


## Roadmap
[Planned]

1. Live Transcription with Whisper - Will [streamlit-webrtc](https://github.com/whitphx/streamlit-webrtc) library. This enables live transcription of audio from a microphone and can be used to take voice notes.
3. CLIP embeddings transcribed text segments + Faiss index for semantic search
2. GPT-3 integration - One approach is to simply allow for an instruct prompt to be entered for a transcript and save results. Will await feedback before implementing.
4. ...

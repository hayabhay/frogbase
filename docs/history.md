All notable changes to this project will be documented in this file.

## `2.0.0a0` `[2023-07-05]`

_⚠️ Breaking Changes_

A complete rewrite of the application. This is now split into two parts:

- A small Python utility package called `frogbase` that contains all the backend logic for the UI. This can be used as a standalone package or integrated into other applications.
- A slimmer Streamlit UI that provides a thin wrapper around the `frogbase` package built purely with self-hosted applications in mind.

**Features**s

- More content sources & formats

  - The use of `pytube` has been replaced with `yt_dlp`. This unlocks content download from a broad range of media platforms like YouTube (channels, playlists, videos), TikTok, Vimeo etc. [(full list)](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md)
  - Local files can now be ingested from a directory instead of just a single file.

  Sources can now be added in as a list of urls and/or local file paths.

- Semantic Search

  - The search functionality now includes semantic search over transcript contents instead of a simple substring search.
    This is done using [sentence-transformers](https://www.sbert.net/) and [hnswlib](https://github.com/nmslib/hnswlib)

- Updated Streamlit UI
  - The UI now includes the concept of Libraries to further organize media downloads. Libraries are simply subdirectories within the main data directory.
  - Filter & search functionality have been simplified and made more intuitive.

## `1.1.0` `[2023-02-08]`

- Merged feature from [@Eidenz](https://github.com/Eidenz) to add translation in addition to transcription

## `1.0.0` `[2023-02-07]`

Since there was some apetite for this, I've rewritten this to make it a tad cleaner with a few additional features based on issues raised and personal preferences.

1. Ability to download entire YouTube playlists and upload multiple files at once
2. Ability to browse, filter, and search through saved audio files (For now, this is done with a simple SQLite database & SQLAlchemy ORM)
3. Auto-export of transcriptions in multiple formats (was a feature request)
4. Simple substring based search for transcript segments. This is done with a simple `LIKE` query on the SQLite database.
5. Fully reworked UI with a cleaner layout and more intuitive navigation.
6. Ability to save whisper configurations and reuse to prevent having to re-enter the same parameters every time.
7. Removed the ability to crop audio after download to simplify the codebase. Also, temporarily removed summarization until GPT-3 integration is complete.

## `0.0.1` `[2022-10-17]`

Initial release for demand testing ([PR #1](https://github.com/hayabhay/whisper-ui/pull/1)).

Features:

- Ability to process media from YouTube & local files
- Whisper transcription
- Basic huggingface integration for summarization

---
title: Getting Started
description: Get started with FrogBase, a python package that lets you download, transcribe, index and search through multi-media content using a single interface.
---

🐸 **FrogBase** lets you create & navigate knowledge from multi-media content.

```python
from frogbase import FrogBase

fb = FrogBase()

sources = [
   "https://www.youtube.com/watch?v=HBxn56l9WcU",
   "https://www.youtube.com/@hayabhay"
]

fb.add(sources)

fb.search("squeaky frog")
```

[![PyPI](https://img.shields.io/pypi/v/frogbase.svg)][pypi_]
[![Status](https://img.shields.io/pypi/status/frogbase.svg)][status]
[![Python Version](https://img.shields.io/pypi/pyversions/frogbase)][python version]
[![License](https://img.shields.io/pypi/l/frogbase)][license]

[pypi_]: https://pypi.org/project/frogbase/
[status]: https://pypi.org/project/frogbase/
[python version]: https://pypi.org/project/frogbase
[license]: https://github.com/hayabhay/frogbase/blob/main/LICENSE

[Find FrogBase on Discord](https://discord.gg/e23YJWqu)

## Features

FrogBase currently provides functionality to:

- Download media files from a wide range of platforms (YouTube, TikTok, Vimeo, etc.) using [yt_dlp](https://github.com/yt-dlp/yt-dlp)
- Transcribe audio streams for downloaded & local files using [OpenAI's Whisper](https://openai.com/blog/whisper/)
- Embed transcribed text from corresponding video segments using [Sentence Transformers](https://www.sbert.net/)
- Index & search the embedded content using [hnswlib](https://github.com/nmslib/hnswlib)

FrogBase also includes a [Streamlit](https://streamlit.io/) UI to provide a simple GUI for the above functionality enabling a locally hosted, interactive experience.

### Non-technical Users

This section is for non-technical users who want to use FrogBase primarily through the accompanying Streamlit UI.

1. Download the latest release of FrogBase from [here](https://github.com/hayabhay/frogbase/archive/refs/heads/main.zip) and unzip it.
   Or, you can also clone the repository
   `console
git clone https://github.com/hayabhay/frogbase.git
`

2. Install FrogBase dependencies manually and run the UI.

   > Note: This also requires `ffmpeg` to be installed on your system. You can install it using `sudo apt install ffmpeg` on Ubuntu.

   1. Using pip

      ```console
      pip install frogbase streamlit
      streamlit run ui/01_🏠_Home.py
      ```

> [Coming soon] Instructions, environment for installation using Docker & Anaconda

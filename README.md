# 🐸 FrogBase

> _**Create navigable knowledge from multi-media content**_

**FrogBase** (previously whisper-ui) simplifies the `download-transcribe-embed-index` workflow for multi-media content.
It does so by linking content from various platforms
([yt_dlp](https://github.com/yt-dlp/yt-dlp))
with speech-to-text models ([OpenAI's Whisper](https://github.com/openai/whisper)),
image & text encoders ([SentenceTransformers](https://github.com/UKPLab/sentence-transformers)),
and embedding stores ([hnswlib](https://github.com/nmslib/hnswlib)).

> ⚠️ Warning: This is currently a pre-release version and is known to be very unstable. For stable releases, please use any 1.x versions.

```python
from frogbase import FrogBase
fb = FrogBase()
fb.demo()
fb.search("What is the name of the squeaky frog?")
```

> [Full Documentation](https://hayabhay.github.io/frogbase/) (WIP).

_FrogBase also comes with a **ready-to-use UI for non-technical users!**_

https://user-images.githubusercontent.com/6735526/216852681-53b6c3db-3e74-4c86-806f-6f6774a9003a.mp4

[![PyPI](https://img.shields.io/pypi/v/frogbase.svg)][pypi_]
[![Status](https://img.shields.io/pypi/status/frogbase.svg)][status]
[![Python Version](https://img.shields.io/pypi/pyversions/frogbase)][python version]
[![License](https://img.shields.io/pypi/l/frogbase)][license]

[pypi_]: https://pypi.org/project/frogbase/
[status]: https://pypi.org/project/frogbase/
[python version]: https://pypi.org/project/frogbase
[license]: https://github.com/hayabhay/frogbase/blob/main/LICENSE

## Features

FrogBase currently provides functionality to:

- Download media files from a wide range of platforms (YouTube, TikTok, Vimeo, etc.) using [yt_dlp](https://github.com/yt-dlp/yt-dlp)
- Transcribe audio streams for downloaded & local files using [OpenAI's Whisper](https://openai.com/blog/whisper/)
- Embed transcribed text from corresponding video segments using [Sentence Transformers](https://www.sbert.net/)
- Index & search the embedded content using [hnswlib](https://github.com/nmslib/hnswlib)

FrogBase also includes a [Streamlit](https://streamlit.io/) UI to provide a simple GUI for the above functionality enabling a locally hosted, interactive experience.

## Quickstart

- [Software Developers](###Developers)
- [Non-technical Users](###Non-technical-Users)

### Software Developers

This section is for software developers who want to use FrogBase as a python package.

1. Install `ffmpeg` and FrogBase

   ```console
   sudo apt install ffmpeg
   pip install frogbase
   ```

2. Import FrogBase and use it as follows -

   ```python
   from frogbase import FrogBase

   fb = FrogBase()

   sources = [
      "https://www.youtube.com/watch?v=HBxn56l9WcU",
      "https://www.youtube.com/@hayabhay"
   ]

   fb.add(sources)

   fb.search("What is the name of the squeaky frog?")
   ```

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

## Links

- [Documentation](https://hayabhay.github.io/frogbase/)
- [Issues](https://github.com/hayabhay/frogbase/issues) & [Discussions](https://github.com/hayabhay/frogbase/discussions)
- [Discord](https://discord.gg/HKkpnx8pU)
- [History](docs/history.md)
- [Roadmap](docs/roadmap.md)
- [Contributing Guide](docs/contributing.md)
- [License](LICENSE) (MIT)

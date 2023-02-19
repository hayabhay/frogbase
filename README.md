# Streamlit UI for OpenAI's Whisper

This is a simple [Streamlit UI](https://streamlit.io/) for [OpenAI's Whisper speech-to-text model](https://openai.com/blog/whisper/).
It let's you download and transcribe media from YouTube videos, playlists, or local files.
You can then browse, filter, and search through your saved audio files.
Feel free to raise an issue for bugs or feature requests or send a PR.

https://user-images.githubusercontent.com/6735526/216852681-53b6c3db-3e74-4c86-806f-6f6774a9003a.mp4

## Setup

This was built & tested on Python 3.11 but should also work on Python 3.9+ as with the original [Whisper repo](https://github.com/openai/whisper)).
You'll need to install `ffmpeg` on your system. Then, install the requirements with `pip`.

```
sudo apt install ffmpeg
pip install -r requirements.txt
```

If you're using conda, you can create a new environment with the following command:

```
conda env create -f environment.yml
```

Note: If you're using a CPU-only machine, your runtime can be sped-up by using quantization implemented by [@MicellaneousStuff](https://github.com/MiscellaneousStuff) by swapping out `pip install openai-whisper` from `requirements.txt` and replacing it with their fork `pip install git+https://github.com/MiscellaneousStuff/whisper.git` (See related discussion here - https://github.com/hayabhay/whisper-ui/issues/20)

## Usage

Once you're set up, you can run the app with:

```
streamlit run app/01_🏠_Home.py
```

This will open a new tab in your browser with the app. You can then select a YouTube URL or local file & click "Run Whisper" to run the model on the selected media.

## Docker

Alternatively, you can run the app containerized with Docker via the included docker-compose.yml. Simply run:

```
docker compose up
```

Then open up a new tab and navigate to [http://localhost:8501/](http://localhost:8501/)

NOTE: For existing users, this will break the database since absolute paths of files are saved. A future fix will be added to fix this.

## Changelog

All notable changes to this project alongside potential feature roadmap will be documented [in this file](CHANGELOG.md)

## License

Whisper is licensed under [MIT](https://github.com/openai/whisper/blob/main/LICENSE) while Streamlit is licensed under [Apache 2.0](https://github.com/streamlit/streamlit/blob/develop/LICENSE).
Everything else is licensed under [MIT](https://github.com/hayabhay/whisper-ui/blob/main/LICENSE).

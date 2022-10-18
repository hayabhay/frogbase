# Streamlit UI for OpenAI's Whisper transcription & analytics

https://user-images.githubusercontent.com/6735526/196173369-27c5ceec-733a-4928-8acb-17cbc2e77a04.mp4

This is a simple [Streamlit UI](https://streamlit.io/) for [OpenAI's Whisper speech-to-text model](https://openai.com/blog/whisper/).
It let's you automatically select media by YouTube URL or select local files & then runs Whisper on them.
Following that, it will display some basic analytics on the transcription.
Feel free to send a PR if you want to add any more analytics or features!

## Setup
This was built & tested on Python 3.9 but should also work on Python 3.7+ as with the original [Whisper repo](https://github.com/openai/whisper)).
You'll need to install `ffmpeg` on your system. Then, install the requirements with `pip`.

```
pip install -r requirements.txt
```
## Usage

Once you're set up, you can run the app with:

```
streamlit run 01_Transcribe.py
```

This will open a new tab in your browser with the app. You can then select a YouTube URL or local file & click "Run Whisper" to run the model on the selected media.

## License
Whisper is licensed under [MIT](https://github.com/openai/whisper/blob/main/LICENSE) while Streamlit is licensed under [Apache 2.0](https://github.com/streamlit/streamlit/blob/develop/LICENSE).
Everything else is licensed under [MIT](https://github.com/hayabhay/whisper-ui/blob/main/LICENSE).

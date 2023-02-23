# Sutitle generation using OpenAI's Whisper

This is a simple [Streamlit UI](https://streamlit.io/) for [OpenAI's Whisper speech-to-text model](https://openai.com/blog/whisper/).
It let's you download and transcribe media from YouTube videos, playlists, or local files with specific settings.
You can then browse, filter, and search through your saved audio files.
Feel free to raise an issue for bugs or feature requests or send a PR.

這是一個簡單的 [Streamlit UI](https://streamlit.io/) ，用於  [OpenAI的Whisper](https://openai.com/blog/whisper/) 語音轉文字模型。
它允許您從YouTube視頻、播放列表或本地文件下載和轉錄媒體 (一個檔案限制為200MB)。
然後，您可以瀏覽、過濾和搜索您保存的音頻文件。隨時歡迎提出錯誤或功能要求，或發送 PR。

[![Whisper Subtitle](https://i.ytimg.com/vi/JVCONXj6lgo/maxresdefault.jpg)](https://youtu.be/JVCONXj6lgo "Whisper Subtitle")

## Setup
This was built & tested on Python 3.11 but should also work on Python 3.8+ as with the original [Whisper repo](https://github.com/openai/whisper)).
You'll need to install `ffmpeg` on your system. Then, install the requirements with `pip`.

```
# Install pytorch if you don't have it
# sudo conda install pytorch
pip install -r requirements.txt
pip install git+https://github.com/openai/whisper.git
```

## Usage

1. Once you're set up, you can run the app with:

```
streamlit run app/01_🏠_Home.py
```

This will open a new tab in your browser with the app. You can then select a YouTube URL or local file & click "Run Whisper" to run the model on the selected media.

If the tab doesn't open, please use the URL: ```https://localhost:8501``` in your browser.

2. If you are not satisfied with the output, click on '⚙️Settings' on the left, then you can fine-tune the inference of Whisper model.

Important ⚙️Settings F.Y.I :
- Model: the model branch you want to use, defult: ```medium```
- language: the language of transcription, default: ```zh``` (中文)
- No Speech Threshold: how strictly we are in excluding non-speech detection, default ```0.4``` (lower level are more strict)
- Condition on previous text: whether the model will be affected by last text, default: ```True```


## Hosting

If you want to host it on a server with dynamic IP, you can install ```ngrok``` for forwarding your IP out. 
So you can access it anywhere via a random url like: ```https://b9f1-458-19-17-41.jp.ngrok.io``` 

1. Register for an account and get your own token from ngrok website: https://dashboard.ngrok.com/get-started/your-authtoken
2. Install NGROK
```
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
sudo tar xvzf ngrok-v3-stable-linux-amd64.tgz -C /usr/local/bin
rm ngrok-v3-stable-linux-amd64.tgz
```
4. Put your own ngrok token from [ngrok website](https://dashboard.ngrok.com/get-started/your-authtoken) to  ```forward_port.sh```
5. Expose your url to the public with ```bash forward_port.sh```
6. Inspect the random url by ```python inspect_url.py ``` and use the url in your browser

🚧 Under Construction:
1. Import redis for task queue

🔥You can try our demo [here](https://whispersubtitle.aiacademy.tw)

Special thanks to [<img src=https://i.imgur.com/bTHUPca.png width=300>](https://en.aiacademy.tw/) for the server.

## Changelog
See [Commits](https://github.com/ShuYuHuang/whisper-subtitle/commits) for detailed changes.

Version summary will be provided in [Release](https://github.com/ShuYuHuang/whisper-subtitle/releases).

The changelog of the original vertion can be found [in this file](https://github.com/hayabhay/whisper-ui/blob/main/CHANGELOG.md).

## License
- Whisper: [MIT](https://github.com/openai/whisper/blob/main/LICENSE)
- Streamlit: [Apache 2.0](https://github.com/streamlit/streamlit/blob/develop/LICENSE).
- else: [MIT](https://github.com/hayabhay/whisper-ui/blob/main/LICENSE).

## Reference
I forked the original version of the interfaces form https://github.com/hayabhay/whisper-ui. 

They actually did a great job for forming a manage systme of subtitles: search engine, transcript viewer, settings

The original version aims to demonstrate the power of Whisper, especially for short films in youtube for local use.

My goal is to provide a service for a bunch of clinets to make subtitles for long videos like meeting records, courses and movies.

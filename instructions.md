## Whisper UI - Transcriptions, Summaries & Analytics

> Feel free to [send a PR](https://github.com/hayabhay/whisper-ui/) if you want to add any more analytics or features!
---

#### Run Whisper
- Add a YouTube URL or select a local file on the left
- If you want to trim the clip, you can add a start timestamp and/or duration (leaving duration at a negative value will trim to the end of the clip)
- Select the right Whisper model supported by your machine (extra configs have other whisper params if you want to play around with them)
- Click "Transcribe"
This will replace these instructions with transcriptions along with A/V on the Transcribe page. Not to worry, they'll still be on the help page if needed.

Once a transcription is created, it will be retained as a session variable so you can navigate around.
However, if you refresh or add a new video, the old transcription will be replaced.

---

#### Run Summarizers
- On the Summary page, pick a summarization model from [Hugging Face](https://huggingface.co/models?pipeline_tag=summarization&sort=downloads) and click "Run Summarization"

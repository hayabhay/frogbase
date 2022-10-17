"""Simple module that holds a transcription along with all the metadata & analytics
"""
from typing import Union

import ffmpeg
import numpy as np
import requests
import torch
import whisper
from pytube import YouTube
from transformers import pipeline

from config import LOCAL_DIR


class Transcription:
    def __init__(self, name: str, source: Union[str, bytes], source_type: str, start: float, duration: float):
        self.name = name
        self.source = source
        self.source_type = source_type
        self.transcribed = False
        self.summarized = False

        # Create a save directory
        self.save_dir = LOCAL_DIR / self.name

        if self.source_type == "youtube":
            # TODO: Perhaps this can be stored in a file-like object in memory
            # itag = 140 is the audio only version
            # TODO: Skip handling extensions
            YouTube(self.source).streams.get_by_itag(140).download(self.save_dir, filename="audio")
        elif self.source_type == "link":
            r = requests.get(self.source, allow_redirects=True)
            with open(self.save_dir / "audio", "wb") as f:
                f.write(r.content)
        elif self.source_type == "file":
            # TODO: Check if ffmpeg can read directly from a file-like in memory container
            # For now, re-save it to the local directory
            with open(self.save_dir / "audio", "wb") as f:
                f.write(self.source.read())

        # Crop the audio as needed
        # Load the audio file. Python-ffmpeg is poorly documented so unsure how to cleanly do this but this works
        if duration > 0:
            audio = ffmpeg.input(f"{self.save_dir}/audio", ss=start, t=duration)
        else:
            audio = ffmpeg.input(f"{self.save_dir}/audio", ss=start)

        self.og_audio_path = self.save_dir / "audio"
        self.audio_path = self.save_dir / "audio_trimmed.mp4"

        # Check if whisper can directly read from a file-like object in memory
        audio = ffmpeg.output(audio, str(self.audio_path.resolve()), acodec="copy")
        ffmpeg.run(audio, overwrite_output=True)

    def transcribe(
        self,
        whisper_model: str,
        temperature: float,
        temperature_increment_on_fallback: float,
        no_speech_threshold: float,
        logprob_threshold: float,
        compression_ratio_threshold: float,
        condition_on_previous_text: bool,
        keep_model_in_memory: bool = True,
    ):

        # Get whisper model
        # NOTE: If mulitple models are selected, this may keep all of them in memory depending on the cache size
        transcriber = whisper.load_model(whisper_model)

        # Set configs & transcribe
        if temperature_increment_on_fallback is not None:
            temperature = tuple(np.arange(temperature, 1.0 + 1e-6, temperature_increment_on_fallback))
        else:
            temperature = [temperature]

        self.raw_output = transcriber.transcribe(
            str(self.audio_path.resolve()),
            temperature=temperature,
            no_speech_threshold=no_speech_threshold,
            logprob_threshold=logprob_threshold,
            compression_ratio_threshold=compression_ratio_threshold,
            condition_on_previous_text=condition_on_previous_text,
            verbose=True,
        )

        # For simpler access
        self.text = self.raw_output["text"]
        self.language = self.raw_output["language"]
        self.segments = self.raw_output["segments"]

        # Remove token ids from the output
        for segment in self.segments:
            del segment["tokens"]

        self.transcribed = True

        if not keep_model_in_memory:
            del transcriber
            torch.cuda.empty_cache()

    def summarize(self, model: str, min_length: int, max_length: int, do_sample: bool):
        if not self.transcribed:
            raise Exception("Transcription not yet done")

        # TODO: Validate model name & handle errors
        summarizer = pipeline("summarization", model=model)

        self.summary = summarizer(self.text, min_length=min_length, max_length=max_length, do_sample=do_sample)[0][
            "summary_text"
        ]
        self.summarized = True

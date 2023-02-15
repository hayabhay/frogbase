import json
import pathlib

# Project structure
# -----------------
APP_DIR = pathlib.Path(__file__).parent.absolute()
PROJECT_DIR = APP_DIR.parent.absolute()

# Create a data directory to save all local data files
DATA_DIR = PROJECT_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# Create a data directory
MEDIA_DIR = DATA_DIR / "media"
MEDIA_DIR.mkdir(exist_ok=True)

DEBUG = True


# Whisper config
# --------------
# Default settings
WHISPER_DEFAULT_SETTINGS = {
    "whisper_model": "medium",
    "temperature": 0.0,
    "temperature_increment_on_fallback": 0.2,
    "no_speech_threshold": 0.4,
    "logprob_threshold": -1.0,
    "compression_ratio_threshold": 2.4,
    "condition_on_previous_text": True,
    "verbose": False,
    "language": 'zh',
    "fp16": True,
    "without_timestamps" : False
}
WHISPER_SETTINGS_FILE = DATA_DIR / ".whisper_settings.json"


def save_whisper_settings(settings):
    with open(WHISPER_SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)


def get_whisper_settings():
    # Check if whisper settings are saved in data directory
    if WHISPER_SETTINGS_FILE.exists():
        with open(WHISPER_SETTINGS_FILE, "r") as f:
            whisper_settings = json.load(f)
    else:
        whisper_settings = WHISPER_DEFAULT_SETTINGS
        save_whisper_settings(WHISPER_DEFAULT_SETTINGS)
    return whisper_settings


# Common page configurations
# --------------------------
ABOUT = """
### 💬 Whisper Subtitle

This is a simple wrapper around Whisper to save, browse & search through transcripts for movie subtitles.

Please report any bugs or issues on [Github](https://github.com/ShuYuHuang/whisper-subtitle/). Thanks!
"""


def get_page_config(page_title_prefix="💬", layout="wide"):
    return {
        "page_title": f"{page_title_prefix}Whisper Subtitle",
        "page_icon": ":movie_camera:",
        "layout": layout,
        "menu_items": {
            "Get Help": "https://github.com/ShuYuHuang",
            "Report a bug": "https://github.com/ShuYuHuang/whisper-subtitle/issues",
            "About": ABOUT,
        },
    }

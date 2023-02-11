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

DEBUG = False


# Whisper config
# --------------
# Default settings
WHISPER_DEFAULT_SETTINGS = {
    "whisper_model": "base",
    "temperature": 0.0,
    "temperature_increment_on_fallback": 0.2,
    "no_speech_threshold": 0.6,
    "logprob_threshold": -1.0,
    "compression_ratio_threshold": 2.4,
    "condition_on_previous_text": True,
    "verbose": False,
    "task": "transcribe",
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
        # Check if all keys are present [for backward compatibility]
        for key in WHISPER_DEFAULT_SETTINGS.keys():
            if key not in whisper_settings:
                whisper_settings[key] = WHISPER_DEFAULT_SETTINGS[key]
    else:
        whisper_settings = WHISPER_DEFAULT_SETTINGS
        save_whisper_settings(WHISPER_DEFAULT_SETTINGS)
    return whisper_settings


# Common page configurations
# --------------------------
ABOUT = """
### Whisper UI

This is a simple wrapper around Whisper to save, browse & search through transcripts.

Please report any bugs or issues on [Github](https://github.com/hayabhay/whisper-ui/). Thanks!
"""


def get_page_config(page_title_prefix="", layout="wide"):
    return {
        "page_title": f"{page_title_prefix}Whisper UI",
        "page_icon": "🤖",
        "layout": layout,
        "menu_items": {
            "Get Help": "https://twitter.com/hayabhay",
            "Report a bug": "https://github.com/hayabhay/whisper-ui/issues",
            "About": ABOUT,
        },
    }

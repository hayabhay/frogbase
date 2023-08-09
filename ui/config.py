import os
import sys
import tempfile
from pathlib import Path

from dotenv import load_dotenv

# This will load the environment variables from .env file from whereever it is called
load_dotenv()

# Project structure
# -----------------
APP_DIR = Path(__file__).parent.absolute()
PROJECT_DIR = APP_DIR.parent.absolute()
TEMP_DIR = Path(tempfile.gettempdir())

# Site wide config can be set using environment variables
DEV = os.getenv("FROGBASE_DEV", False)
VERBOSE = os.getenv("FROGBASE_VERBOSE", False)
DATADIR = os.getenv("FROGBASE_DATADIR", APP_DIR / "data")
LIBRARY = os.getenv("FROGBASE_LIBRARY", "frogverse")
PERSIST = os.getenv("FROGBASE_PERSIST", True)

# Common page configurations
# --------------------------
ABOUT = """
### FrogBase UI

Discover, transcribe, and search media effortlessly with FrogBase.
Download from popular platforms like YouTube, TikTok, upload your own content, and enjoy a convenient Q&A interface.

Please report any bugs or issues on [Github](https://github.com/hayabhay/frogbase/issues). Thanks!
"""


def get_page_config(page_title_prefix="", layout="wide"):
    return {
        "page_title": f"{page_title_prefix}FrogBase UI",
        "page_icon": "🐸",
        "layout": layout,
        "initial_sidebar_state": "expanded",
        "menu_items": {
            "Get Help": "https://twitter.com/hayabhay",
            "Report a bug": "https://github.com/hayabhay/frogbase/issues",
            "About": ABOUT,
        },
    }


def init_session(session_state, library: str = LIBRARY, reset: bool = False):
    """Site wide function to intialize session state variables if they don't exist."""
    # Running in dev mode implies using the local frogbase modules instead of the pip installed version
    # if DEV:
    if True:  # TODO: Remove this when package is stable
        # Insert project directory into the head of the system path to override installed frogbase from pip
        sys.path.insert(0, str(PROJECT_DIR))

    # Now import frogbase
    from frogbase import FrogBase

    # Session states
    # --------------------------------
    # Create a frogbase instance
    if "fb" not in session_state or reset:
        session_state.library = library
        session_state.fb = FrogBase(datadir=DATADIR, library=library, verbose=VERBOSE, dev=DEV, persist=PERSIST)

    # Set session state to toggle list & detail view
    if "listview" not in session_state or reset:
        session_state.listview = True
        session_state.selected = None
        session_state.selected_media_offset = 0

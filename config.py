import pathlib

APP_DIR = pathlib.Path(__file__).parent.absolute()

LOCAL_DIR = APP_DIR / "local"
LOCAL_DIR.mkdir(exist_ok=True)

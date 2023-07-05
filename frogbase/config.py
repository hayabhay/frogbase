from pathlib import Path

from loguru._logger import Logger
from pydantic import BaseModel, ConfigDict, Field
from tinydb import TinyDB


class FrogBaseConfig(BaseModel):
    """Active config for the FrogBase instance at any given time."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)
    datadir: Path = Field(..., description="The path to the data directory.")
    libdir: Path = Field(..., description="The path to the library directory.")
    db: TinyDB = Field(..., repr=False, description="The TinyDB datastore from the FrogBase instance.")
    logger: Logger = Field(..., repr=False, description="The logger instance from the FrogBase instance.")
    verbose: bool = Field(False, description="Whether to print verbose logs.")
    dev: bool = Field(False, description="Whether to run in development mode.")
    download_archive: Path = Field(..., description="The path to the download archive used by yt-dlp.")

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

# TODO: It is unclear if webvtt-py is well maintained
# but since webvtt format is pretty standard the
# probability of it breaking is relatively low.
import webvtt
from pydantic import BaseModel, ConfigDict, Field
from tinydb import Query

from frogbase.config import FrogBaseConfig


class Captions(BaseModel):
    """Class to represent a media's captions. This is linked to a single media by the media's id.
    Additionally, multiple captions can be linked to a single media based on the environment the
    captions were generated in.
    """

    # Config & Private attrs
    model_config = ConfigDict(frozen=True)

    # Public attrs
    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="id is typically a function of media id & env in which it was generated",
    )
    media_id: str = Field(..., description="The id of the media to which the captions belong.")
    loc: str = Field(..., description="Relative location of the captions file. A '.vtt' file on disk for now")
    infoloc: str = Field(default="", description="Relative location where FrogBase saves this object as a json file.")
    fmt: str = Field(..., description="The format of the media's captions. Always 'vtt' for now")
    kind: str = Field(..., description="This is either 'captions' or 'subtitles'.")
    lang: str = Field(..., description="The language of the media's captions. Example: 'en', 'hi' etc.")
    by: str = Field(..., description="The source of the media's captions. Example: 'youtube', 'whisper' etc.")
    created: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="When this captions were either downloaded or generated by FrogBase.",
    )
    settings: dict | None = Field(default=None, description="The settings under which these captions were generated.")

    def __init__(self, config: FrogBaseConfig, **data: dict[str, Any]) -> None:
        """Initialize a Captions object.

        Args:
            config: The config object for FrogBase.
            **data: The data to initialize the Captions object with.
        """
        super().__init__(**data)
        self._config = config
        self._logger = config.logger
        self._table = config.db.table(self.__class__.__name__)
        # Set relative location of the captions file as Path object.
        self._loc = self._config.libdir / self.loc
        self._infoloc = self._config.libdir / self.infoloc

    def __repr__(self) -> str:
        """Return a string representation of the Captions instance."""
        return f"<Captions(lang={self.lang}, by={self.by}, loc={self._loc.name})>"

    def __str__(self) -> str:
        """Return a string representation of the Captions instance."""
        return self.__repr__()

    def _save(self, to_file: bool = True) -> None:
        """Write this media object to db and file."""
        # Convert media object to a dictionary & add to the media table.
        self._table.upsert(self.model_dump(), Query()["id"] == self.id)
        self._logger.info(f"Captions <{self.id}> metadata added to db.")

        # Additionally, save the media metadata to file.
        if to_file:
            self._infoloc.parent.mkdir(parents=True, exist_ok=True)
            with open(self._infoloc, "w") as f:
                f.write(self.model_dump_json())
            self._logger.info(f"Saved captions metadata to {self._infoloc.resolve()}")

    def load(self, fmt: str = "vtt") -> dict[str, Any]:
        """Load the captions data file into a standard dictionary.
        Can load .vtt, .srt or .json files if available.

        Args:
            captions: The captions object or id to load from the .vtt file.

        Returns:
            Dictionary containing the captions data in the form of a standard captions object.
            This is a subset of openai's transcript format.
        """
        if fmt == "vtt" or fmt == "srt":
            captions_reader = (
                webvtt.read(str(self._loc.resolve())) if fmt == "vtt" else webvtt.from_srt(str(self._loc.resolve()))
            )
            for segment_id, captions in enumerate(captions_reader):
                yield {
                    "id": segment_id,
                    "start": captions.start_in_seconds,
                    "end": captions.end_in_seconds,
                    "start_str": captions.start,
                    "end_str": captions.end,
                    "text": captions.text,
                }
        else:
            raise ValueError(f"Unsupported or missing captions for '{fmt}' format.")

    def _load_whisper_json(self) -> dict[str, Any]:
        """Internal method to load whisper's json dump if available."""
        json_fname = f"{self._loc.stem}.{json}"
        if not (self._loc.parent / json_fname).exists():
            raise ValueError(f"Missing whisper json file for {self._loc.name}")
        else:
            with open((self._loc.parent / json_fname).resolve()) as f:
                return json.load(f)

    def delete(self, bkup_files: bool = True) -> None:
        """Delete this captions object from db and file."""
        self._table.remove(Query().id == self.id)
        self._logger.info(f"Deleted captions from db: {id}")

        if bkup_files:
            # Remove the captions info file from disk.
            self._infoloc.unlink()
            # Get a glob of all files associated with the captions object.
            for caption_file in self._loc.parent.glob(f"{self._loc.stem}*"):
                # Delete the files
                caption_file.unlink()
                self._logger.info(f"Deleted file: {caption_file}")


class CaptionsManager:
    """
    Manager class for Captions objects. This typically triggers creation, deletion,
    and retrieval of one or more Captions objects.
    NOTE: Caption managers operate within the context of a single media object.
    """

    def __init__(self, media_id: str, config: FrogBaseConfig) -> None:
        """Initializes a MediaManager object. This is typically triggered by a FrogBase instance.

        Args:
            media_id: The id of the media to which the captions belong.
            config: The config object for the FrogBase instance.
        """
        # Set the library directory and the db.
        self.media_id = media_id
        self._config = config
        self._logger = config.logger
        self._table = config.db.table(Captions.__name__)

    # ----------------------- CRUD Operations - Read ------------------------
    def get(self, id: str) -> Captions:
        """Get a captions object from db.

        Args:
            id: The id of the captions object to retrieve.

        Returns:
            The captions object with the given id.
        """
        captions_dict = self._table.get((Query().id == id) & (Query().media_id == self.media_id))
        return Captions(config=self._config, **captions_dict) if captions_dict else None

    def all(self) -> list[Captions]:
        """Get all captions objects from db for the given media.

        Returns:
            A list of all captions objects.
        """
        captions_dicts = self._table.search(Query().media_id == self.media_id)
        captions_dicts = sorted(captions_dicts, key=lambda x: x["created"], reverse=True)
        return [Captions(config=self._config, **captions_dict) for captions_dict in captions_dicts]

    # TODO: Fix this.
    def latest(self, prefer_subtitles=True) -> Captions:
        """Get the latest captions object from db for the given media.

        Returns:
            The latest captions object.
        """
        captions_dicts = self._table.search(Query().media_id == self.media_id)
        captions_dicts = sorted(captions_dicts, key=lambda x: x["created"], reverse=True)
        captions_dict = None
        if prefer_subtitles:
            for captions_dict in captions_dicts:
                if captions_dict["kind"] == "subtitles":
                    break
        # Else pick the first one if it exists.
        captions_dict = captions_dict or captions_dicts[0]
        return Captions(config=self._config, **captions_dict) if captions_dict else None

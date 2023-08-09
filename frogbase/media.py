import hashlib
import json
import platform
import re
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from subprocess import CalledProcessError, run
from typing import Any
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field
from tinydb import Query
from tinydb.queries import QueryInstance
from yt_dlp import YoutubeDL

from frogbase.captions import Captions, CaptionsManager
from frogbase.config import FrogBaseConfig


class Media(BaseModel):
    """Class to represent a Media object in FrogBase. This typically represents a single
    audio or video file and is the primarily access point for all media sources."""

    # NOTE: Ideally this should be frozen but it isn't possible to create
    # a captions manager object as a public attribute in that case.
    # Instead, save() is made private to prevent accidental changes.
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Core media attributes
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="The id of the media source.")
    loc: str = Field(..., description="Relative location of the media file in the library (path on disk for now)")
    ext: str = Field(..., description="Media format extension. Example: 'webm', 'mp4' etc.")
    is_video: bool = Field(..., description="Whether the media source is a video or not.")
    infoloc: str = Field(default="", description="Relative location where this object is saved in the library")
    title: str = Field(default="", description="The title of the media.")

    # Source information
    src: str = Field(default="", description="The location of the media source (url or path on disk)")
    src_name: str = Field(default="", description="The name of the media source. Example: 'youtube', 'disk' etc.")
    src_domain: str = Field(default="", description="The domain of the media source. Example: 'youtube.com' etc.")

    # Uploader information
    uploader_id: str = Field(default="", description="The id of the media uploader.")
    uploader_name: str = Field(default="", description="The name of the media uploader.")
    uploader_url: str = Field(default="", description="The url of the media uploader.")
    upload_date: str = Field(default="", description="The date when the media was uploaded to the source.")

    # Optional core attributes
    thumbnail: str = Field(default="", description="The url of the thumbnail of the media source.")
    description: str = Field(default="", repr=False, description="The description of the media source.")
    duration: float | None = Field(default=None, description="The duration of the media source in seconds.")
    filesize: int | None = Field(default=None, description="The filesize of the media source in bytes.")
    tags: list[str] = Field(default_factory=list, description="Typically keywords for the media source.")
    created: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="When this media object was created by FrogBase.",
    )
    rawinfoloc: str = Field(default="", description="Additional metadata (yt-dlp for now.)")

    captions: CaptionsManager = Field(default=None, exclude=True, description="The captions manager instance.")

    def __init__(self, config: FrogBaseConfig, **data: dict[str, Any]) -> None:
        """Initialize a Media object.

        Args:
            config: FrogBaseConfig object
            **data: The data to initialize the Media object with.
        """
        # Initialize the BaseModel
        super().__init__(**data)
        self._config = config
        self._logger = config.logger
        self._table = config.db.table(self.__class__.__name__)

        # Set path objects for the media source and info file.
        self._loc = self._config.libdir / self.loc
        self._infoloc = self._config.libdir / self.infoloc

        # Captions for any media source can be accessed via the captions manager.
        self.captions = CaptionsManager(media_id=self.id, config=self._config)

    # Override repr to make it more readable.
    def __repr__(self) -> str:
        """Return a string representation of this media object."""
        title_repr = f"{self.title[:30]}..." if len(self.title) > 30 else self.title
        return f"<Media: {title_repr} | {self.src}>"

    def __str__(self) -> str:
        """Return a string representation of this media object."""
        return self.__repr__()

    def _save(self, to_file: bool = True) -> None:
        """Write this media object to db and file."""
        # Convert media object to a dictionary & add to the media table.
        self._table.upsert(self.model_dump(), Query().id == self.id)
        self._logger.info(f"Media <{self.id}> metadata added to db.")

        # Additionally, save the media metadata to file.
        if to_file:
            self._infoloc.parent.mkdir(parents=True, exist_ok=True)
            with open(self._infoloc, "w") as f:
                f.write(self.model_dump_json())
            self._logger.info(f"Saved media metadata to {self._infoloc.resolve()}")

    def delete(self, bkup_files: bool = True) -> None:
        """Delete this media object from db and file."""
        self._table.remove(Query().id == self.id)
        self._logger.info(f"Deleted media from db: {id}")

        # Delete all captions from the db.
        # NOTE: Backup files will be removed by the media manager.
        for captions_obj in self.captions.all():
            captions_obj.delete(bkup_files=False)

        # Delete the media subdirectory
        if bkup_files:
            shutil.rmtree(self._loc.parent, ignore_errors=False, onerror=None)
            self._logger.info(f"Deleted media directory: {self._loc.parent}")

        # Delete the media id from downloaded media list if it exists.
        if Path(self._config.download_archive).exists():
            with open(self._config.download_archive) as f:
                downloaded_archive = [line.strip().split() for line in f.readlines() if line.strip()]
            # Remove the media id from the downloaded media list.
            downloaded_archive = [" ".join(line) for line in downloaded_archive if line[1] != self.id]
            # Write the updated downloaded media list to the archive file.
            with open(self._config.download_archive, "w") as f:
                f.write("\n".join(downloaded_archive))

    def has_captions(self) -> bool:
        """Check if this media has captions."""
        return len(self.captions.all()) > 0


class MediaManager:
    """Manager class for Media objects. This typically triggers creation, deletion,
    and retrieval of one or more Media objects."""

    def __init__(self, config: FrogBaseConfig) -> None:
        """Initializes a MediaManager object. This is typically triggered by a FrogBase instance.

        Args:
            config: The config object for the FrogBase instance.
        """
        # Initalize the manager
        self._config = config
        self._logger = config.logger
        self._table = self._config.db.table(Media.__name__)

    # ---------------------------- Utilities --------------------------------
    @classmethod
    def get_media_info(cls, file_path: str) -> dict[str, Any]:
        """Call ffmpeg probe within a python subprocess to get metadata about a media file.

        Args:
            file_path: The path of the file to check.
        """
        if not Path(file_path).exists():
            raise FileNotFoundError(f"{file_path} does not exist.")

        try:
            ffmpeg = run(
                ["ffprobe", "-v", "error", "-print_format", "json", "-show_format", file_path],
                capture_output=True,
                text=True,
            )
            # Parse the output into a dict
            output = json.loads(ffmpeg.stdout)["format"]
            return output
        except CalledProcessError:
            raise Exception("ffprobe not found. Please install ffmpeg.")

    @classmethod
    def is_video(cls, file_path: str) -> bool:
        """Call ffmpeg probe within a python subprocess to check if the file is a video.

        Args:
            file_path: The path of the file to check.
        """
        if not Path(file_path).exists():
            raise FileNotFoundError(f"{file_path} does not exist.")
        try:
            ffmpeg = run(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-select_streams",
                    "v:0",
                    "-show_entries",
                    "stream=codec_type",
                    "-of",
                    "default=noprint_wrappers=1:nokey=1",
                    file_path,
                ],
                capture_output=True,
                text=True,
            )
            return ffmpeg.stdout.strip() == "video"
        except CalledProcessError:
            raise Exception("ffprobe not found. Please install ffmpeg.")

    # ----------------------- CRUD Operations - Create ----------------------
    def _add_from_web(self, url: str, **opts: dict[str, Any]) -> list[Media]:
        """Add a youtube video to the FrogBase. This is a thin wrapper around
        yt_dlp to download youtube videos.

        Args:
            url: The url of the youtube video, playlist, or channel.
            **opts: Supported options are:
                1. low_quality: Whether to download the media in low quality.
                2. audio_only: Whether to download the audio only.
                3. ydl_opts: Config params passed directly to yt_dlp superceding the
                    above options.
        """
        low_quality = opts.get("low_quality", True)
        audio_only = opts.get("audio_only", True)

        # Standardize output template regardless of yt_dlp options.
        outtmpl = str(self._config.libdir / "%(title).50B::%(id)s" / "media.%(ext)s")

        # If opts is provided use it directly
        if opts and "ydl_opts" in opts:
            self._logger.info(f"Using provided ydl_opts: {opts['ydl_opts']}")
            ydl_opts = opts["ydl_opts"]
            # Set the output template to the standard one.
            ydl_opts["outtmpl"] = outtmpl
        else:
            self._logger.info(f"Constructing ydl_opts for video: {url}")
            self._logger.info(f"low_quality: {low_quality}, audio_only: {audio_only}")
            # Construct the ydl_opts.
            ydl_opts = {
                "writeinfojson": True,
                "writesubtitles": True,
                "writeautomaticsub": True,
                "subtitleslangs": ["en"],
                "quiet": not self._config.verbose,
                "outtmpl": outtmpl,
                "download_archive": self._config.download_archive,
            }
            # Set a/v formats
            if audio_only:
                ydl_opts["format"] = "249/250/251/bestaudio/best" if low_quality else "bestaudio/best"
                ydl_opts["postprocessors"] = [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "128" if low_quality else "256",
                    }
                ]
            else:
                ydl_opts["format"] = "18/22/best" if low_quality else "best"

            # Log the ydl_opts.
            self._logger.info(f"Starting download using ydl_opts: {ydl_opts}")

        # Download the media.
        # NOTE: yt_dlp will NOT download the same media twice as long as the download_archive
        # is set. If this is deleted, files will be overwritten.
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download(url)

        # Maintain a list of media objects that were added.
        added_media = []

        # For each newly downloaded media, process infojson and add to the FrogBase.
        for infojson in self._config.libdir.glob("**/media.info.json"):
            # Get the media id from the infojson.
            media_id = infojson.parent.stem.split("::")[-1]
            # Load the infojson
            # NOTE: If the same link is downloaded twice but with additional captions (eg. different languages),
            # there will be additional .vtt files that need to be processed even if the media is already in the db.
            # So, infodict will be loaded even if the media is already in the db.
            with open(infojson) as f:
                infodict = json.load(f)

            # Check if the media is already in the db.
            media_obj = self.get(media_id)

            # If media exists, load it. If not, create it
            if not media_obj:
                self._logger.info(f"Adding new media: {infojson}")
                # If the media is not a video, skip it.
                # NOTE: This happens when channels, playlists, etc. are downloaded and channel/playlist
                # info is downloaded as well (separate directories)
                if infodict["_type"] != "video":
                    self._logger.info(f"Directory is not a video: {infojson}")
                    continue

                # Get media location from infojson & check if it exists.
                # TODO: When post-processing is manually overridden, assuming mp3 for audio_only
                # as ext is incorrect. Need to fix this but not a priority for now.
                media_ext = "mp3" if audio_only else infodict["ext"]
                media_loc = infojson.parent / f"media.{media_ext}"

                if not media_loc.exists():
                    self._logger.warning(f"Media file not found: {media_loc}")
                    continue

                # Get media fmt info from ffprobe.
                media_fmt = self.get_media_info(str(media_loc.resolve()))

                # Create a media source instance.
                media_obj = Media(
                    id=infodict["id"],
                    loc=str(media_loc.relative_to(self._config.libdir)),
                    ext=media_ext,
                    is_video=self.is_video(str(media_loc.resolve())),
                    infoloc=str(
                        (infojson.parent / ".bkup" / f"{media_id}.media.fb.json").relative_to(self._config.libdir)
                    ),
                    title=infodict["title"],
                    src=infodict["webpage_url"],
                    src_name=infodict["extractor"],
                    src_domain=infodict["webpage_url_domain"],
                    uploader_id=infodict.get("uploader_id", ""),
                    uploader_name=infodict.get("uploader", ""),
                    uploader_url=infodict.get("uploader_url", ""),
                    upload_date=infodict.get("upload_date", ""),
                    thumbnail=infodict.get("thumbnail", ""),
                    description=infodict.get("description", ""),
                    duration=media_fmt.get("duration"),
                    filesize=media_fmt.get("size"),
                    tags=infodict.get("tags", []),
                    rawinfoloc=str(infojson),
                    # Additional private fields
                    config=self._config,
                )
                media_obj._save()

                # Add the media to the list of added media.
                added_media.append(media_obj)

            # Next, process all downloaded captions
            # NOTE: Currently it is assumed that only .vtt files are downloaded by yt_dlp
            # Get .vtt files in the infojson directory.
            # NOTE: At some point it is possible that for a mix of new & existing files to co-exist
            # and need to be processed separately. All existing files are assumed to have a standard
            # filename format so they can be identified. New files have the same name as the media
            # file so they can be identified. (see yt_dlp params above)
            vtt_files = list(infojson.parent.glob("media.*.vtt"))
            # Process each .vtt file.
            for vtt_file in vtt_files:
                self._logger.info(f"Processing captions file: {vtt_file}")
                # Parse information from the filename.
                lang = vtt_file.stem.split(".")[-1]
                by = infodict["uploader"] if lang in infodict["subtitles"] else infodict["extractor"]
                kind = "subtitles" if lang in infodict["subtitles"] else "captions"
                id_str = f"{media_id}{kind}{by}{lang}"
                self._logger.info(f"hashing {id_str}")
                captions_id = hashlib.sha256(id_str.encode()).hexdigest()[:16]

                # Check if captions file already exists in the db
                captions_dict = self._config.db.get(Query().captions.id == captions_id)
                if captions_dict:
                    self._logger.info(f"Captions with id <{captions_id}> already exists in db.")
                else:
                    self._logger.info(f"Captions with id <{captions_id}> not found in db. Adding..")
                    # Create a new filename for the captions file in a standard format.
                    # The <lang>.vtt suffix will remain while the rest of the filename will be
                    # updated since yt_dlp names the files differently.
                    newfilename = f"{kind}::{by}::{lang}::{captions_id}.vtt"
                    newfilepath = vtt_file.parent / newfilename
                    # Rename captions file.
                    vtt_file.rename(newfilepath)

                    # Add captions to FrogBase.
                    captions_obj = Captions(
                        id=captions_id,
                        media_id=media_id,
                        loc=str(newfilepath.relative_to(self._config.libdir)),
                        infoloc=str(
                            (infojson.parent / ".bkup" / f"{captions_id}.captions.fb.json").relative_to(
                                self._config.libdir
                            )
                        ),
                        fmt="vtt",
                        kind=kind,
                        lang=lang,
                        by=by,
                        config=self._config,
                    )
                    self._logger.info(f"Added <{lang}> captions provided by {by}")
                    # Add captions to the media object & save to db.
                    captions_obj._save()

        # Return the list of added media.
        return added_media

    def _add_from_disk(self, source: str, **opts: dict[str, Any]) -> list[Media]:
        """Add a single local media object to the FrogBase library.
        Local media objects are unaltered and added to the FrogBase as is.

        Args:
            source: The location of the media source. This is a local file path.
                Supported file formats are: mp3, mp4, mpeg, mpga, wav, webm.
            **opts: Supported options are:
                1. recursive: If true, the source directory is searched recursively.
                2. move: If true, the source files are moved to the output directory instead of copying.
        """
        recursive = opts.get("recursive", False)
        move = opts.get("move", False)

        # Check if path is a directory.
        if Path(source).is_dir():
            self._logger.info(f"Directory found: {source}. Adding all supported files in directory.")
            # Get all supported files in the source directory
            if recursive:
                supported_files = list(Path(source).glob("**/*.{mp3,mp4,mpeg,mpga,wave,webm}"))
            else:
                supported_files = list(Path(source).glob("*.{mp3,mp4,mpeg,mpga,wave,webm}"))
            self._logger.info(f"Found {len(supported_files)} supported files in: {source}")
        else:
            supported_files = [Path(source)]

        # Maintain a list of media objects that were added.
        added_media = []

        # For each file, add it to the FrogBase library.
        for media_file in supported_files:
            # First, get details about the source media file.
            media_fmt = self.get_media_info(str(media_file.resolve()))
            # Next, create a media id using hash value of the full source path, duration and size.
            id_str = str(media_file.resolve()) + str(media_fmt.get("duration")) + str(media_fmt.get("size"))
            media_id = hashlib.sha256(id_str.encode()).hexdigest()[:16]

            # Check if the media is already in the db.
            media_obj = self.get(media_id)
            if media_obj:
                self._logger.info(f"Media already in FrogBase: {media_file}")
                continue

            # Next, create a new subdirectory for the media and copy/move the file to it.
            # The subdirectory name is the name without the extension and the media id.
            # Eg: media_file = /home/user/funnyaudio.mp3
            #    media_dir = /home/user/funnyaudio::02e2e89f0fb8f666
            media_dirname = media_file.stem + f"::{media_id}"
            # Create the subdirectory in the output directory.
            media_dir = Path(self._config.libdir) / media_dirname
            media_dir.mkdir(parents=True, exist_ok=True)
            dest_file = media_dir / media_file.name
            # Get stat about the source media file
            media_stat = media_file.stat()

            # Copy/move the media file to the subdirectory.
            if move:
                shutil.move(str(media_file.resolve()), str(dest_file.resolve()))
            else:
                shutil.copy(str(media_file.resolve()), str(dest_file.resolve()))

            # Create a media source instance.
            media_obj = Media(
                id=media_id,
                loc=str(dest_file.relative_to(self._config.libdir)),
                ext=media_file.suffix,
                is_video=self.is_video(str(dest_file.resolve())),
                infoloc=str((media_dir / ".bkup" / f"{media_id}.media.fb.json").relative_to(self._config.libdir)),
                title=media_file.stem,
                src=str(media_file.resolve()),
                src_name="disk",
                uploader_id=platform.node(),
                uploader_name=platform.node(),
                upload_date=datetime.fromtimestamp(media_stat.st_ctime).strftime("%Y%m%d"),
                duration=media_fmt.get("duration"),
                filesize=media_fmt.get("size"),
                config=self._config,
            )
            # Dump media metadata to the save location & add to the database.
            media_obj._save()

            # Add the media to the list of added media.
            added_media.append(media_obj)

        return added_media

    def add(self, sources: str | list[str], **opts: dict[str, Any]) -> list[Media]:
        """Adds a one or more media objects to the FrogBase library.

        Args:
            sources: One or more media sources to add. Allowed sources are urls or filepaths on disk.
               Single source can be passed as a string instead of a list as a convenience.
            **opts: Source type specific options. Check the source type specific methods for more info.
        """
        # If a single source is passed, convert it to a list.
        if not isinstance(sources, list):
            sources = [sources]

        added_media = []
        for source in sources:
            if isinstance(source, str):
                source = source.strip()
                # Attempt to parse the location as a url.
                parsed_loc = urlparse(source)

                # If the location is a url, then the scheme will not be empty.
                if parsed_loc.scheme:
                    self._logger.info(f"Source is a url: {source}")
                    added_media += self._add_from_web(source, **opts)
                else:
                    # Check if the location is a local file path.
                    if Path(source).exists():
                        self._logger.info(f"Source is a local path: {source}")
                        added_media += self._add_from_disk(source, **opts)
                    else:
                        # Print anerror that the source is not a valid url or file path.
                        self._logger.error(f"Invalid source: {source}")
            else:
                self._logger.error(f"Invalid source type: {type(source)}")

        # Return the list of added media.
        return added_media

    # ----------------------- CRUD Operations - Read ------------------------
    def get(self, id: str) -> Media:
        """Get a media object by its id.

        Args:
            id: The id of the media object to retrieve or the url/filepath
        """
        # First check if the id exists in the database.
        media_dict = self._table.get(Query().id == id)
        # If not, check against the media source. This is atypical but is supported
        # for convenience.
        if not media_dict:
            media_dict = self._table.get(Query().src == id)
        return Media(config=self._config, **media_dict) if media_dict else None

    def all(self) -> list[Media]:
        """Get all media objects."""
        media_dicts = self._table.all()
        media_dicts = sorted(media_dicts, key=lambda x: x["created"], reverse=True)
        return [Media(config=self._config, **media_dict) for media_dict in media_dicts]

    def count(self) -> int:
        """Get the number of media objects in the database."""
        return len(self.all())

    # TODO: Add native support for filtering by different criteria based on usage patterns
    def search(self, query: QueryInstance) -> list[Media]:
        """Filter media entries by a list of different criteria.
        As of now, this is simply a wrapper around tinydb's search method
        and requires knowledge of the underlying query syntax & db structure.

        Args:
            query: A tinydb query object.
        """
        self._logger.info(f"Searching for media with query: {query}")
        media_dicts = self._table.search(query)
        media_dicts = sorted(media_dicts, key=lambda x: x["created"], reverse=True)
        return [Media(config=self._config, **media_dict) for media_dict in media_dicts]

    def filter(self, captioned: None | bool = None, **by) -> list[Media]:
        """This is a thin wrapper around the tinydb's fragment method.

        Args:
            by: A dictionary of key-value pairs to filter by.
        """
        self._logger.info(f"Filtering media by: {by}")
        # Construct a query object to retrieve the media object by the specified attribute.
        filtered_media = self.search(Query().fragment(by))
        # Now if captioned is specified, filter by captioned or uncaptioned media.
        if captioned is not None:
            filtered_media = [media for media in filtered_media if media.has_captions() == captioned]

        return filtered_media

    def captioned(self) -> list[Media]:
        """Get media objects that have captions."""
        self._logger.info("Getting media with captions")
        # Construct a query object to retrieve the media object by the specified attribute.
        return self.search(Query().caption.exists())

    def search_by_title(self, query: str) -> list[Media]:
        """Search for media by title using a substring. Case insensitive.

        Args:
            query: The search query.
        """
        self._logger.info(f"Searching for media by title: {query}")
        # Construct a query object to search for the media by title.
        return self.search(Query().title.matches(f".*{query}.*", flags=re.IGNORECASE))

    # -------------------------- Render Methods -----------------------------
    def show(
        self, media: None | Media | list[Media] = None, caption_info: bool = False, media_info: bool = False
    ) -> None:
        """Prints the media objects in a pretty format.

        Args:
            media_objs: The media objects to print.
            caption_info: Whether to print the caption information.
            media_info: Whether to print the media information.
        """
        if media is None:
            media = self.all()

        if not isinstance(media, list):
            media = [media]

        for media_obj in media:
            print("=====")  # noqa: T201
            print(f"- ID: {media_obj.id} ({'video' if media_obj.is_video else 'audio'})")  # noqa: T201
            print(f"- Title: {media_obj.title}")  # noqa: T201
            uploaded_date = datetime.strptime(media_obj.upload_date, "%Y%m%d").date().strftime("%Y-%m-%d")
            print(f"- Uploader: {media_obj.uploader_name} [{uploaded_date}]")  # noqa: T201
            print(f"- Source: {media_obj.src}")  # noqa: T201
            print(f"- Location: {media_obj._loc.resolve()}")  # noqa: T201
            if media_info:
                print(f"- Duration: {media_obj.duration}")  # noqa: T201
                print(f"- Filesize: {media_obj.filesize}")  # noqa: T201
                print(f"- Categories: {media_obj.categories}")  # noqa: T201
                print(f"- Tags: {media_obj.tags}")  # noqa: T201
                print(f"- Thumbnail: {media_obj.thumbnail}")  # noqa: T201
                print(f"- Description: {media_obj.description}")  # noqa: T201
            if caption_info:
                for caption in media_obj.captions.all():
                    print(f"- Caption file: {caption._loc}")  # noqa: T201
                    print(f"- Caption by: {caption.by}")  # noqa: T201
                    print(f"- Caption lang: {caption.lang}")  # noqa: T201

import tempfile
from datetime import datetime
from pathlib import Path

from loguru import logger
from tinydb import Query, TinyDB

from frogbase.config import FrogBaseConfig
from frogbase.media import Media


# ----------------------------- Data Models --------------------------------
def test_media_instance_creation():
    """Test the Media dataclass."""

    with tempfile.TemporaryDirectory() as tmpdir:
        libdir = Path(tmpdir) / "test"
        Path(libdir).mkdir(parents=True, exist_ok=True)
        db = TinyDB(libdir / "db.json")

        config = FrogBaseConfig(
            datadir=tmpdir,
            libdir=libdir,
            db=db,
            logger=logger,
            download_archive=libdir / "downloaded.txt",
        )

        created_ts = datetime.now().isoformat()

        # Create a media object
        media = Media(
            id="test",
            loc=str(libdir / "test.mp4"),
            ext="mp3",
            is_video=True,
            infoloc=str(libdir / "info.json"),
            title="test",
            src="test",
            src_name="test",
            src_domain="test",
            uploader_id="test",
            uploader_name="test",
            uploader_url="test",
            upload_date="test",
            thumbnail="test",
            description="test",
            duration=1.0,
            filesize=1,
            tags=["test"],
            created=created_ts,
            rawinfoloc="test",
            config=config,
        )

        # Check if the media object is created correctly.
        assert media.id == "test"
        assert media.loc == str(libdir / "test.mp4")
        assert isinstance(media.loc, str)
        assert isinstance(media._loc, Path)
        assert media.ext == "mp3"
        assert media.is_video is True
        assert media.infoloc == str(libdir / "info.json")
        assert isinstance(media.infoloc, str)
        assert isinstance(media._infoloc, Path)
        assert media.title == "test"
        assert media.src == "test"
        assert media.src_name == "test"
        assert media.src_domain == "test"
        assert media.uploader_id == "test"
        assert media.uploader_name == "test"
        assert media.uploader_url == "test"
        assert media.upload_date == "test"
        assert media.thumbnail == "test"
        assert media.description == "test"
        assert media.duration == 1.0
        assert media.filesize == 1
        assert media.tags == ["test"]
        assert media.created == created_ts
        assert media.rawinfoloc == "test"
        # Check private attributes
        assert media._config == config
        assert media._logger == config.logger
        assert media._table == config.db.table("Media")

        # Test saving the media object to db and file.
        media._save(to_file=True)
        # Check if the media object is saved correctly.
        assert media._table.get(Query().id == media.id) == media.model_dump()
        assert media._infoloc.read_text() == media.model_dump_json()

        # Test deleting the media object from db and file.
        media.delete(bkup_files=True)
        # Check if the media object is deleted correctly.
        assert media._table.get(Query().id == media.id) is None
        assert not media._infoloc.exists()

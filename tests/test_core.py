# Function to test FrogBase library creation.
from pathlib import Path

import pytest
from tinydb import Query, TinyDB

from frogbase import FrogBase

# Add a marker for slow tests
slow = pytest.mark.skipif(
    "not config.getoption('--run-slow')",
    reason="Only run when --run-slow is given",
)


def test_frogbase_creation_defaults():
    """Test FrogBase default creation."""
    # Check defaults
    fb = FrogBase(persist=False, dev=True)
    assert fb._datadir.exists()
    assert fb._datadir.name == "frogverse"
    assert fb._library == "main"
    assert fb._libdir.exists()
    assert fb._libdir.name == "main"
    # Check tinydb creation
    assert isinstance(fb._dbpath, Path)
    assert fb._dbpath.name == "tinydb-dev.json"
    assert fb._dbpath.exists()
    assert isinstance(fb._db, TinyDB)
    # Since we're not persisting the tinydb instance, there should
    # only be one entry in the tinydb instance which is the version
    assert fb._db.get(Query().type == "meta")["__version__"] == fb._version


def test_frogbase_creation_with_custom_names():
    """Test FrogBase library creation with custom datadir."""
    # Check library creation with custom datadir
    fb = FrogBase(datadir="./mydata", library="errthang", persist=False, dev=True)
    assert fb._datadir.exists()
    assert fb._datadir.name == "mydata"
    assert fb._library == "errthang"
    assert fb._libdir.exists()
    assert fb._libdir.name == "errthang"
    # Check tinydb creation
    assert isinstance(fb._dbpath, Path)
    assert fb._dbpath.name == "tinydb-dev.json"
    assert fb._dbpath.exists()
    assert isinstance(fb._db, TinyDB)
    # Since we're not persisting the tinydb instance, there should
    # only be one entry in the tinydb instance which is the version
    assert fb._db.get(Query().type == "meta")["__version__"] == fb._version


def test_frogbase_library_update():
    """Test FrogBase library update."""
    fb = FrogBase(datadir="./test", persist=False, dev=True)
    # Check library update, creation, and removal
    fb.library = "test"
    assert fb._library == "test"
    assert fb._libdir.exists()
    assert fb._libdir.name == "test"

    # Check tinydb creation
    assert isinstance(fb._dbpath, Path)
    assert fb._dbpath.name == "tinydb-dev.json"
    assert fb._dbpath.exists()
    assert isinstance(fb._db, TinyDB)
    # Since we're not persisting the tinydb instance, there should
    # only be one entry in the tinydb instance which is the version
    assert fb._db.get(Query().type == "meta")["__version__"] == fb._version

    # Check library removal and if it reverts to main
    to_remove = fb._libdir.resolve()
    fb.remove_library("test")
    # Check if library test was removed
    assert not to_remove.exists()
    # Check if library reverted to main
    assert fb._library == "main"
    assert fb._libdir.exists()
    assert fb._libdir.name == "main"
    # Check tinydb creation
    assert isinstance(fb._dbpath, Path)
    assert fb._dbpath.name == "tinydb-dev.json"
    assert fb._dbpath.exists()
    assert isinstance(fb._db, TinyDB)


def test_frogbase_config_init():
    """Test FrogBase config manager."""
    fb = FrogBase(datadir="./test", persist=False, dev=True)

    # Check config manager creation
    assert fb.config.datadir is fb._datadir
    assert isinstance(fb.config.datadir, Path)
    assert fb.config.datadir.exists()
    assert fb.config.datadir.name == "test"
    assert fb.config.libdir.exists()
    assert fb.config.libdir.name == "main"
    assert fb.config.db is fb._db
    assert isinstance(fb.config.db, TinyDB)
    assert fb.config.logger is fb._logger
    assert fb.config.dev is True
    # Verbose will always be True if dev is True
    assert fb.config.verbose is True
    assert fb.config.download_archive == fb._libdir / "downloaded_media.txt"


@slow
@pytest.mark.simulate
def test_frogbase_add_media():
    fb = FrogBase(datadir="./tests/data", persist=False, dev=True)

    # # This is the bbc video about the desert rain frog
    source = "https://www.youtube.com/watch?v=HBxn56l9WcU"
    fb.add(source, audio_only=True)

    # Check if media was added
    assert fb.media.count() == 1
    # Check get method and existence of media
    media = fb.media.get(source)
    assert media is not None

    # Check media attributes
    assert media._loc.exists()
    assert (fb.config.libdir / media.loc).exists()
    assert (fb.config.libdir / media.infoloc).exists()
    assert media.id == "HBxn56l9WcU"
    assert media.ext == "mp3"
    assert media.is_video is False
    assert media.title == "A tiny angry squeaking Frog 🐸 | Super Cute Animals - BBC"
    assert media.src == "https://www.youtube.com/watch?v=HBxn56l9WcU"
    assert media.src_name == "youtube"
    assert media.src_domain == "youtube.com"
    assert media.uploader_id == "@BBC"
    assert media.uploader_name == "BBC"
    assert media.uploader_url == "https://www.youtube.com/@BBC"
    assert media.upload_date == "20150210"
    # Thumbnail exists
    assert media.thumbnail
    # Description exists
    assert media.description
    # Duration is 45.528 but might change
    assert media.duration >= 45
    assert media.duration <= 46
    # Simply check that filesize is greater than default 0
    assert media.filesize > 0

    # Check filter operation
    assert len(fb.media.filter(is_video=False)) == 1
    assert len(fb.media.filter(is_video=True)) == 0
    assert len(fb.media.filter(uploader_name="BBC")) == 1
    assert len(fb.media.filter(uploader_id="@hayabhay")) == 0
    # Check filters with multiple values
    assert len(fb.media.filter(uploader_name="BBC", is_video=False)) == 1
    assert len(fb.media.filter(uploader_name="BBC", is_video=True)) == 0
    # Check captioned filter
    assert len(fb.media.filter(captioned=True)) == 1
    assert len(fb.media.filter(captioned=False)) == 0
    # Check captioned filter with multiple values
    assert len(fb.media.filter(captioned=True, is_video=False)) == 1
    assert len(fb.media.filter(captioned=True, is_video=True)) == 0

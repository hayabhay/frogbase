import tempfile
from pathlib import Path

from loguru import logger
from loguru._logger import Logger
from tinydb import TinyDB

from frogbase.config import FrogBaseConfig


def test_config_creation():
    """Test that the config class can be created."""

    with tempfile.TemporaryDirectory() as tmpdir:
        libdir = Path(tmpdir)
        db = TinyDB(libdir / "test.json")

        config = FrogBaseConfig(
            datadir=tmpdir,
            libdir=libdir,
            db=db,
            logger=logger,
            download_archive=libdir / "test.txt",
        )

        assert isinstance(config, FrogBaseConfig)
        assert isinstance(config.libdir, Path)
        assert isinstance(config.db, TinyDB)
        assert isinstance(config.logger, Logger)
        assert isinstance(config.verbose, bool)
        assert isinstance(config.dev, bool)
        assert isinstance(config.download_archive, Path)

        assert config.libdir == libdir
        assert config.db == db
        assert config.logger == logger
        assert config.download_archive == libdir / "test.txt"
        assert config.verbose is False
        assert config.dev is False

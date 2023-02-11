"""Database config, models & operations
This is lumped together in a single file to keep things simple.
"""
import uuid
from datetime import datetime
from typing import List, Optional

from config import DATA_DIR, DEBUG
from sqlalchemy import ForeignKey, MetaData, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# This is a slightly augmented version of SQL model that adds some common fields
# that are used across all models
# Also, to keep things simple, only sqlite native types are used
class Base(DeclarativeBase):
    # Identifiers are all uuids
    id: Mapped[str] = mapped_column(default=lambda: str(uuid.uuid4()), primary_key=True)

    # All timestamps are timezone aware isoformatted strings (local timezone by default)
    created: Mapped[str] = mapped_column(default=lambda: datetime.now().astimezone().isoformat(), nullable=False)
    updated: Mapped[str] = mapped_column(default=lambda: datetime.now().astimezone().isoformat(), nullable=False)


# Models & Schemas
# ----------------------
# This is the core model that stitches a piece of Media with audio to derivative content
# like transcripts & derived data from them.
class Media(Base):
    __tablename__ = "media"

    # Source type is a string and is, as of now, either
    source_type: Mapped[str]
    source_name: Mapped[str]
    source_link: Mapped[Optional[str]]

    # Full path of where the audio is locally stored
    filepath: Mapped[str]

    # Additional metadata
    duration: Mapped[Optional[float]]

    # Flag to indicate if the audio has been transcribed
    transcript: Mapped["Transcript"] = relationship(back_populates="media", uselist=False, cascade="all, delete-orphan")
    segments: Mapped[List["Segment"]] = relationship(
        back_populates="media", order_by="Segment.number", cascade="all, delete-orphan"
    )


class Transcript(Base):
    """A transcript is the full text of an audio file's transcription"""

    __tablename__ = "transcript"

    # The media object that this transcript is for
    media_id: Mapped[str] = mapped_column(ForeignKey("media.id", ondelete="CASCADE"), nullable=False)
    media: Mapped["Media"] = relationship(back_populates="transcript")

    # The transcript
    text: Mapped[str]
    language: Mapped[str]
    generated_by: Mapped[str]


class Segment(Base):
    """A segment is a transcription of a specific audio segment within the file"""

    __tablename__ = "segment"

    # The media object that this transcript is for
    media_id: Mapped[str] = mapped_column(ForeignKey("media.id", ondelete="CASCADE"), nullable=False)
    media: Mapped["Media"] = relationship(back_populates="segments")

    # Segment text
    number: Mapped[int]
    text: Mapped[str]
    start: Mapped[float]
    end: Mapped[float]

    # OpenAI provided metadata
    generated_by: Mapped[str]
    temperature: Mapped[float]
    avg_logprob: Mapped[float]
    compression_ratio: Mapped[float]
    no_speech_prob: Mapped[float]


# Database config
# ----------------------
DATABASE_URL = f"sqlite:///{DATA_DIR}/db.sqlite3"
# DATABASE_URL = "sqlite+pysqlite:///:memory:"

# Create database engine
ENGINE = create_engine(DATABASE_URL, echo=True) if DEBUG else create_engine(DATABASE_URL)

# Create all tables
Base.metadata.create_all(ENGINE)

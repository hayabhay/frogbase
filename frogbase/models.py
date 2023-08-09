import hashlib
import json
import pickle
from pathlib import Path
from typing import Any, Literal

import hnswlib
import numpy as np
import whisper
from pydantic import BaseModel, ConfigDict, Field
from sentence_transformers import SentenceTransformer, util
from tinydb import Query

from frogbase.captions import Captions
from frogbase.config import FrogBaseConfig
from frogbase.media import Media


class WhisperSettings(BaseModel):
    """Pydantic model to store settings for the whisper model.
    This is a direct mapping of the CLI arguments & defaults for the whisper model.
    Reference: https://github.com/openai/whisper/blob/main/whisper/transcribe.py
    """

    model_config = ConfigDict(validate_assignment=True, arbitrary_types_allowed=True)

    family: Literal["whisper"] = Field(default="whisper", description="Always maps to 'whisper'")
    model: Literal["tiny", "tiny.en", "base", "base.en", "small", "small.en", "medium", "medium.en", "large"] = Field(
        default="base", description="Model variant"
    )

    # Whisper parameters
    task: Literal["translate", "transcribe"] = Field(default="transcribe")
    language: str = Field(default="en", description="Language code for the input text")
    verbose: bool | None = Field(default=None, description="Print verbose output")

    temperature: float | tuple[float, ...] = Field(
        default=(0.0, 0.2, 0.4, 0.6, 0.8, 1.0), description="Temperature for sampling"
    )
    best_of: int = Field(default=5, description="Number of samples to generate")
    beam_size: int = Field(default=5, description="Beam size for beam search")
    patience: float | None = Field(default=None, description="Patience for beam search")
    length_penalty: float | None = Field(default=None, description="Length penalty for beam search")

    initial_prompt: str | None = Field(default=None, description="Initial prompt for the model")
    condition_on_previous_text: bool = Field(default=True, description="Condition on previous text")
    fp16: bool = Field(default=True, description="Use fp16 for inference")

    compression_ratio_threshold: float = Field(default=2.4, description="Compression ratio threshold")
    logprob_threshold: float = Field(default=-1.0, description="Log probability threshold")
    no_speech_threshold: float = Field(default=0.6, description="No speech threshold")
    word_timestamps: bool = Field(default=False, description="Generate word timestamps")
    prepend_punctuations: str = Field(default="""\"'“¿([{-""", description="Punctuations to prepend")
    append_punctuations: str = Field(default="""\"'.。,，!！?？:：”)]}、""", description="Punctuations to append")

    def get_params_dict(self) -> dict:
        """Custom exclusion logic for the model parameters"""
        return self.model_dump(exclude={"family", "model"})

    def get_param_idstr(self) -> str:
        """Returns param values as a string. Useful for generating unique IDs for model runs"""
        params = self.model_dump(exclude={"verbose"})
        # TODO: Check if model_dump_json implicitly sorts the keys
        return json.dumps(params, sort_keys=True)


class SBertSettings(BaseModel):
    """Pydantic model to store settings for the sentence-transformers model.
    This is a direct mapping of CLI arguments & defaults for the sentence-transformers package.
    """

    model_config = ConfigDict(validate_assignment=True, arbitrary_types_allowed=True)

    family: Literal["sbert"] = Field(default="sbert", description="Always maps to 'sbert'")
    model: Literal[
        "msmarco-MiniLM-L-6-v3",
        "msmarco-MiniLM-L-12-v3",
        "msmarco-distilbert-base-v3",
        "msmarco-distilbert-base-v4",
        "msmarco-roberta-base-v3",
    ] = Field(default="msmarco-MiniLM-L-6-v3", description="Asymmetric sentence transformer model")

    # Sentence-transformers parameters
    # TODO: Add more knobs


class HNSWSettings(BaseModel):
    """Pydantic model to store settings for the hnswlib model.
    This is a direct mapping of CLI arguments & defaults for the hnswlib package.
    References: https://github.com/nmslib/hnswlib/blob/master/README.md
    """

    model_config = ConfigDict(validate_assignment=True, arbitrary_types_allowed=True)

    family: Literal["hnsw"] = Field(default="hnsw", description="Always maps to 'hnsw'")

    # TODO: This isn't particularly elegant. Find a better way to do this
    embedding_source: Literal[
        "msmarco-MiniLM-L-6-v3",
        "msmarco-MiniLM-L-12-v3",
        "msmarco-distilbert-base-v3",
        "msmarco-distilbert-base-v4",
        "msmarco-roberta-base-v3",
    ] = Field(default="msmarco-MiniLM-L-6-v3", description="The model that generated the embeddings for the index")

    # HNSW parameters
    M: int = Field(
        default=32, description=" the number of bi-directional links created for every new element during construction"
    )
    ef_construction: int = Field(default=400, description="controls index search speed / index recall tradeoff")
    ef_search: int = Field(default=50, description="controls index search speed / index recall tradeoff")

    # NOTE: This is dynamically increased as needed
    max_elements: int = Field(default=100000, description="Number of elements in the index")


class ModelManager:
    """
    Manager class to handle configurations and operations on all machine learning
    models used by FrogBase. Typically this is grouped along function like
    speech-to-text, text-to-vectors, image-to-text etc.
    """

    def __init__(self, config: FrogBaseConfig) -> None:
        """Initializes a MediaManager object. This is typically triggered by a FrogBase instance.

        Args:
            config: The config object for the FrogBase instance.
        """
        self._config = config
        self._libdir = config.libdir
        self._logger = config.logger
        self._table = config.db.table("model_settings")

        # Supported model families
        self._allowed_transcribers = ["whisper"]
        self._allowed_embedders = ["sbert"]
        self._allowed_indexers = ["hnsw"]
        # Dict to store model weights keyed by model family & model name
        self._models = {}

        # Check if the db table exists and if not, attempt to load if from a backup file if available
        if not self._table.all():
            self._logger.info("No model settings found in the database. Reverting to defaults.")

        # Initialize model configurations. If settings are missing in the db, use defaults.
        whisper_settings = self._table.get(Query().family == "whisper")
        self.whisper = WhisperSettings(**whisper_settings) if whisper_settings else WhisperSettings()

        sbert_settings = self._table.get(Query().family == "sbert")
        self.sbert = SBertSettings(**sbert_settings) if sbert_settings else SBertSettings()

        hnsw_settings = self._table.get(Query().family == "hnsw")
        self.hnsw = HNSWSettings(**hnsw_settings) if hnsw_settings else HNSWSettings()

        # Model defaults
        model_defaults = self._table.get(Query()["__defaults__"] == "__defaults__")
        if not model_defaults:
            model_defaults = {}
        # Set default model families for the instance
        self._default_transcriber = model_defaults.get("transcriber", "whisper")
        self._default_embedder = model_defaults.get("embedder", "sbert")
        self._default_indexer = model_defaults.get("indexer", "hnsw")

        # Trigger a save if any of the settings are missing
        # NOTE: This is a bulk overwrite but that should be okay for now.
        self.save_settings()

    def __repr__(self) -> str:
        """Returns a string representation of the ModelManager object."""
        return (
            "<ModelManager:\n"
            f" <Transcriber: {getattr(self, self._default_transcriber).__repr__()}>\n"
            f" <Embedder: {getattr(self, self._default_embedder).__repr__()}>\n"
            f" <Indexer: {getattr(self, self._default_indexer).__repr__()}>\n"
            ">"
        )

    def __str__(self) -> str:
        """Returns a string representation of the ModelManager object."""
        return self.__repr__()

    def save_settings(self) -> None:
        """Saves the model settings to the database."""
        # Save model defaults
        model_defaults = {
            "__defaults__": "__defaults__",
            "transcriber": self._default_transcriber,
            "embedder": self._default_embedder,
            "indexer": self._default_indexer,
        }
        self._table.upsert(model_defaults, Query()["__defaults__"] == "__defaults__")
        self._table.upsert(self.whisper.model_dump(), Query().family == "whisper")
        self._table.upsert(self.sbert.model_dump(), Query().family == "sbert")
        self._table.upsert(self.hnsw.model_dump(), Query().family == "hnsw")

    # ========================== Transcription ==========================
    def _run_transcriber(
        self, media_path: str, captions_path: str, transcriber: str, model_name: str, **model_params: dict[str, Any]
    ) -> None:
        """Runs a transcription engine on a single piece of media.

        Args:
            media_path: Absolute path to the media file.
            captions_path: Absolute path to the captions file.
            transcriber: Name of the transcription engine.
            model_name: Name of the model to use.
            model_params: Additional parameters to pass to the model.
        """

        if transcriber == "whisper":
            # First check if the model is available in the cache
            model_id = f"{transcriber}:{model_name}"
            if model_id not in self._models:
                self._models[model_id] = whisper.load_model(model_name)

            # Run the model and write the captions to file
            transcript = self._models[model_id].transcribe(media_path, **model_params)
            # Write the transcript to a .vtt file.
            for fmt in ["vtt", "srt", "json"]:
                writer = whisper.utils.get_writer(fmt, Path(captions_path).parent)
                writer(transcript, Path(captions_path).stem)

    def transcribe(
        self,
        media: None | Media | list[Media] = None,
        transcriber: str | None = None,
        model: str | None = None,
        keep_model_in_memory: bool = False,
        **params: dict[str, Any],
    ) -> list[Captions]:
        """Transcribe one or more media with a specified transcription engine and parameters.

        Args:
            media: The media object(s) to transcribe. If not specified, transcribe all the media in the library.
            transcriber: The transcription engine to use. Ex: "whisper", "deepspeech", etc.
            **params: The parameters to use for transcription.
        """
        # If media is not a list, convert it to a list.
        if not isinstance(media, list):
            media = [media]

        if transcriber and transcriber not in self._allowed_transcribers:
            self._logger.error(f"Transcriber {transcriber} not found. Using default transcriber.")
            transcriber = None

        # Set transcriber to default if not specified or invalid
        transcriber = transcriber if transcriber else self._default_transcriber

        # Next get the model name & params from settings
        model_settings = getattr(self, transcriber)

        # Overwrite the model name if specified
        # Note, this should also catch invalid model names
        if model:
            model_settings.model = model

        model_name = model_settings.model
        model_params = model_settings.get_params_dict()
        # Get the model config id
        model_params_idstr = model_settings.get_param_idstr()

        # If any additional params are specified, overwrite the model params
        # only for this run.
        for key in params:
            if key in model_params:
                model_params[key] = params[key]

        added_captions = []
        # Transcribe the media object(s).
        for media_obj in media:
            # Print a log message
            self._logger.info(f"Transcribing {media_obj.loc} with {transcriber}:{model_name}")
            # Get the media directory
            media_dir = (self._libdir / media_obj.loc).parent

            # Create a captions id based on the media id and param config to prevent re-runs
            by = f"{transcriber}:{model_name}"
            kind = "captions"
            lang = model_params["language"]
            id_str = f"{media_obj.id}{model_params_idstr}"
            captions_id = hashlib.sha256(id_str.encode()).hexdigest()[:16]
            captions_stem = f"captions::{by}::{lang}::{captions_id}"
            captions_fmt = "vtt"
            captions_fname = f"{captions_stem}.{captions_fmt}"
            captions_loc = media_dir / captions_fname

            # Check if captions already exist for this media object.
            captions_obj = media_obj.captions.get(captions_id)

            if captions_obj:
                self._logger.info(f"Captions <id: {captions_id}> have already been generated. Skipping.")
            else:
                self._logger.info(f"Generating captions <id: {captions_id}>.")

                # Run transcriber
                self._run_transcriber(
                    media_path=str((self._libdir / media_obj.loc).resolve()),
                    captions_path=str(captions_loc.resolve()),
                    transcriber=transcriber,
                    model_name=model_name,
                    **model_params,
                )

                # Create a captions object and add it to the media object.
                captions_obj = Captions(
                    id=captions_id,
                    media_id=media_obj.id,
                    loc=str(captions_loc.relative_to(self._libdir)),
                    infoloc=str((media_dir / ".bkup" / f"{captions_id}.captions.fb.json").relative_to(self._libdir)),
                    fmt=captions_fmt,
                    kind=kind,
                    lang=lang,
                    by=by,
                    settings=model_settings.model_dump(),
                    config=self._config,
                )

                captions_obj._save()

                added_captions.append(captions_obj)

        # Free up memory by deleting the transcriber engine.
        if not keep_model_in_memory and f"{transcriber}:{model_name}" in self._models:
            del self._models[f"{transcriber}:{model_name}"]

        return added_captions

    # ========================== Vectorization ==========================
    def embed(
        self,
        media: None | Media | list[Media] = None,
        embedder: str | None = None,
        model: str | None = None,
        keep_model_in_memory: bool = False,
        overwrite: bool = False,
        **params: dict[str, Any],
    ) -> list[Media]:
        """Embed one or more media with a specified vectorization engine and parameters."""

        # If media is not a list, convert it to a list.
        if not isinstance(media, list):
            media = [media]

        if embedder and embedder not in self._allowed_embedders:
            self._logger.error(f"Embedder {embedder} not found. Using default embedder.")
            embedder = None

        # Set embedder to default if not specified or invalid
        embedder = embedder if embedder else self._default_embedder

        # Next get the model name & params from settings
        model_settings = getattr(self, embedder)

        # Overwrite the model name if specified
        # Note, this should also catch invalid model names
        if model:
            model_settings.model = model

        model_name = model_settings.model

        # Load the model
        if model_settings.model not in self._models:
            self._models[f"{embedder}:{model_name}"] = SentenceTransformer(model_name)
        model = self._models[f"{embedder}:{model_name}"]

        # Load vector cache if it exists
        embeddings_cache = self._libdir / f"{model_name}:embeddings.pkl"

        embeddings = {}
        if embeddings_cache.exists():
            with open(embeddings_cache, "rb") as f:
                embeddings = pickle.load(f)

        # For each media object, embed all the caption segments
        # and save the embeddings to the vector cache.
        # Each segment looks forward to 30 seconds ahead to get the context
        # and then embeds the segment.
        # TODO: This is right now inefficient since vectorization is done
        # per media object. This will be slow if media is small.
        # Optimize this later

        # Maintain a list of media objects that have been embedded
        embedded_media = []

        for media_obj in media:
            # NOTE: For now, simply embed the last captions object.
            # Get the latest captions object
            # TODO: Add support to specify which captions to embed
            captions_obj = media_obj.captions.latest()

            if not captions_obj:
                self._logger.error(f"No captions found for media <id: {media_obj.id}>. Skipping.")
                continue

            # Get an embedding id as a hash of media id & captions id
            # TODO: Additional captions for the same media will create more embeddings that need to be consolidated
            # at retrieval time.
            # embed_id = hashlib.sha256(f"{media_obj.id}{captions_obj.id}".encode()).hexdigest()[:16]
            # NOTE: Because of the above, we will use only the media id and model name for now.
            # An additional flag to overwrite embeddings is added as a stop-gap measure.
            embed_id = hashlib.sha256(f"{media_obj.id}{model_name}".encode()).hexdigest()[:16]

            # If the embedding already exists, skip it.
            if embed_id in embeddings and not overwrite:
                self._logger.info(f"Embedding <id: {embed_id}> already exists. Skipping.")
                continue
            # Load captions
            # TODO: Experiment with adding windows over caption segments instead of a single segment
            captions = list(captions_obj.load())

            # Embed caption segments
            features = model.encode(
                [segment["text"] for segment in captions], show_progress_bar=True, convert_to_numpy=True
            )
            embeddings[embed_id] = {
                "media_id": media_obj.id,
                "captions_id": captions_obj.id,
                "model": model_name,
                "embeddings": features,
                "start_timestamps": [segment["start"] for segment in captions],
                "segment_ids": [segment["id"] for segment in captions],
            }

            # Add the media object to the list of embedded media
            embedded_media.append(media_obj)

        # Save the embeddings to the vector cache
        with open(embeddings_cache, "wb") as f:
            pickle.dump(embeddings, f)

        # Free up memory by deleting the vectorizing engine.
        if not keep_model_in_memory and f"{embedder}:{model_name}" in self._models:
            del self._models[f"{embedder}:{model_name}"]

        return embedded_media

    # TODO: Separate indexing bit out of models to manage it separately
    # ========================== Indexing ==========================
    def index(
        self,
        # media: None | Media | list[Media] = None,
        indexer: str | None = None,
        embedding_source: str | None = None,
        **params: dict[str, Any],
    ) -> dict[str, Any]:
        """Index one or more media with a specified indexing engine and parameters."""
        # NOTE: This is a placeholder for demo & testing purposes.
        # TODO: Add functionality to manage both indices & embeddings within them
        # This is especially important if and when new embeddings are generated from
        # different transcribers

        # If media is not a list, convert it to a list.
        # if not isinstance(media, list):
        #     media = [media]

        if indexer and indexer not in self._allowed_indexers:
            self._logger.error(f"Indexer {indexer} not found. Using default indexer.")
            indexer = None

        # Set indexer to default if not specified or invalid
        indexer = indexer if indexer else self._default_indexer

        # Next get the model name & params from settings
        model_settings = getattr(self, indexer)

        # Overwrite the model name if specified
        # Note, this should also catch invalid model names
        if embedding_source:
            model_settings.embedding_source = embedding_source

        embedding_source = model_settings.embedding_source

        # Load embeddings
        embeddings_cache = self._libdir / f"{embedding_source}:embeddings.pkl"
        if not embeddings_cache.exists():
            self._logger.error(f"Embeddings not found for {embedding_source}. Run embed() first.")
            return

        with open(embeddings_cache, "rb") as f:
            embeddings = pickle.load(f)

        # Get the dimensionality of the embeddings & number of elements
        embedding_dims = None
        total_elements = 0
        for meta in embeddings.values():
            total_elements += len(meta["embeddings"])
            embedding_dims = meta["embeddings"].shape[1]

        # Next, create an index id as a hash of model name and params
        index_id = hashlib.sha256(f"{model_settings.M}:{model_settings.ef_construction}".encode()).hexdigest()[:16]

        # Next, check if an index already exists. If so, load it.
        index_path = self._libdir / f"{embedding_source}:{index_id}.index"
        index_metapath = self._libdir / f"{embedding_source}:{index_id}.json"

        if index_path.exists():
            # Intiate an hnswlib index object
            index = hnswlib.Index(space="cosine", dim=embedding_dims)
            index.load_index(str(index_path))
            if index.max_elements < total_elements:
                self._logger.info(
                    f"Index max elements ({index.max_elements}) is less than total elements ({total_elements})."
                )
                self._logger.info("Rebuilding index.")
                # TODO: Scaling up index size by 10 is arbitrary. Not sure what the implications are
                index = hnswlib.Index(space="cosine", dim=embedding_dims)
                index.load_index(str(index_path), max_elements=total_elements * 10)
            # Load the index meta
            with open(index_metapath) as f:
                index_meta = json.load(f)
                # Convert all keys to int
                index_meta = {int(k): v for k, v in index_meta.items()}
        else:
            # Create a new index

            # Intiate an hnswlib index object
            index = hnswlib.Index(space="cosine", dim=embedding_dims)
            # Set the max elements to the total number of elements
            max_elements = (
                model_settings.max_elements if model_settings.max_elements > total_elements else total_elements * 10
            )
            # Initiate the index
            index.init_index(
                max_elements=max_elements, ef_construction=model_settings.ef_construction, M=model_settings.M
            )
            index_meta = {}

        # Add the embeddings to the index
        # Labels are media ids and start times
        # TODO: Refactor.
        labels = []
        data = []
        indexed = set(index_meta.values())
        for meta in embeddings.values():
            label_prefix = f"{meta['media_id']}::{meta['captions_id']}"
            skipped = False
            for segment_id, start_timestamp in zip(meta["segment_ids"], meta["start_timestamps"]):
                label = f"{label_prefix}::{segment_id}::{start_timestamp}"
                # If the first element is indexed, assume all elements are indexed
                if label in indexed:
                    skipped = True
                    break
                labels.append(label)
            if not skipped:
                data.append(meta["embeddings"])

        # Update label maps
        ids = []
        label_map = {}
        latest_index_value = index.element_count
        for i, label in enumerate(labels):
            ids.append(latest_index_value + i)
            label_map[latest_index_value + i] = label
        index_meta.update(label_map)

        # Update the index if there are new items
        if len(ids) > 0:
            index.add_items(np.concatenate(data, axis=0), ids)

            # Save the index & meta
            index.save_index(str(index_path))
            with open(index_metapath, "w") as f:
                json.dump(index_meta, f)

        # NOTE: Currently the most recent index is simply saved to the settings for use in search
        # This is a hack mainly for the Streamlit app. As a package, this is bad practice.
        # This will work since sbert is the only embedding source currently supported but will
        # break if this expands.
        # TODO: Add a way to specify which index to use for search
        index.set_ef(model_settings.ef_search)
        search_index = {
            "index": index,
            "meta": index_meta,
            "encoder": SentenceTransformer(embedding_source),
        }

        return search_index

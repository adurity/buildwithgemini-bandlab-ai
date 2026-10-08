# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.models import Gemini
from google.adk.tools import ToolContext
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types

from app.audio_gen import generate_sample_hook
from app.db import get_album, list_albums, save_album
from app.image_gen import generate_album_art
from app.marketing import evaluate_band_name
from app.streaming import check_streaming_commercial_presence
from app.a2ui_utils import a2ui_callback

from a2ui.schema.manager import A2uiSchemaManager
from a2ui.basic_catalog.provider import BasicCatalog

MODEL = os.environ.get("MODEL", "gemini-3.8-flash")


def generate_track_sample_hook(
    track_title: str,
    vibe: Optional[str] = "synthwave",
    tool_context: Optional[ToolContext] = None,
) -> Dict[str, Any]:
    """Generate a sample vocal hook / preview snippet for a track and upload it to Cloud Storage.

    Creates a punchy lyrical hook based on the track title and musical vibe, synthesizes
    audio via the Gemini TTS model, registers it in the session artifacts, and uploads the
    audio bytes to the public Cloud Storage bucket, returning the public HTTPS URL.

    Args:
        track_title: The title of the track (e.g. 'Gridrunner Awakening', 'Chrome Sunset').
        vibe: Optional genre vibe or aesthetic mood (e.g. 'cyberpunk synthwave', 'dreamy indie pop').
        tool_context: ADK ToolContext to register the audio artifact in the session.

    Returns:
        A dictionary with the hook lyrics and the public HTTPS URL to the audio file.
    """
    return generate_sample_hook(
        track_title=track_title,
        vibe=vibe,
        tool_context=tool_context,
    )


def create_album_cover_art(
    album_title: str,
    band_name: str,
    aesthetic: str,
    tool_context: ToolContext,
) -> Dict[str, Any]:
    """Generate concept album cover artwork for an album and publish it.

    Generates artwork using the gemini-3.1-flash-lite-image model in the global region.
    Saves the image into the playground's Artifacts panel and uploads it directly to the
    project's public Cloud Storage bucket, returning its public HTTPS URL.

    Args:
        album_title: The title of the album or release.
        band_name: The band or musical artist name.
        aesthetic: Detailed visual aesthetic, style keywords, art movement, or color palette.
        tool_context: ADK ToolContext to register the artifact in the playground session.

    Returns:
        A dictionary containing the public HTTPS URL to the image and the artifact filename.
    """
    return generate_album_art(
        album_title=album_title,
        band_name=band_name,
        aesthetic=aesthetic,
        tool_context=tool_context,
    )


def assess_band_name_marketability(band_name: str) -> Dict[str, Any]:
    """Assess real-world collision risks and marketing strength for a proposed band name.

    Checks the MusicBrainz artist registry for existing artist collisions and calculates
    a 0-100 marketability score evaluating SEO distinctiveness, brevity, and social handle friendliness.

    Args:
        band_name: The band or artist name candidate to evaluate.

    Returns:
        A dictionary with the overall marketability score, dimensional breakdown,
        MusicBrainz matches, and specific marketing critiques.
    """
    return evaluate_band_name(band_name)


def check_commercial_streaming_presence(artist_or_album: str, entity_type: str = "artist") -> Dict[str, Any]:
    """Check commercial release presence and DSP collisions on the Apple Music / iTunes store catalog.

    Queries the public Apple iTunes Search API (no API key required) to determine if
    a band name or album title already has existing commercial releases, albums, or tracks
    on commercial streaming platforms.

    Args:
        artist_or_album: The band name or album title to inspect.
        entity_type: Type to search: 'artist' (default) or 'album'.

    Returns:
        A dictionary containing commercial release count, existing artists/albums found,
        their primary genres, and commercial collision risk assessment.
    """
    return check_streaming_commercial_presence(artist_or_album=artist_or_album, entity_type=entity_type)


def fetch_album_catalog(genre: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
    """Retrieve albums from the Firestore discography catalog, optionally filtered by genre.

    Args:
        genre: Optional genre keyword to filter albums (e.g. 'synthwave', 'rock').
        limit: Maximum number of albums to retrieve (default: 10).

    Returns:
        A list of album records containing band name, title, genre, aesthetic, and tracklists.
    """
    return list_albums(genre=genre, limit=limit)


def fetch_album_details(album_id: str) -> Dict[str, Any]:
    """Retrieve full details for a specific album by its ID.

    Args:
        album_id: The document ID of the album (e.g. 'neon-overdrive').

    Returns:
        The album details dictionary, or a not-found status message.
    """
    album = get_album(album_id)
    if not album:
        return {"status": "not_found", "message": f"Album '{album_id}' was not found in the catalog."}
    return {"status": "found", "album": album}


def record_album_release(
    album_id: str,
    band_name: str,
    album_title: str,
    genre: str,
    aesthetic: str,
    notes: str = "",
    release_year: int = 2026,
    cover_art_url: str = "",
) -> Dict[str, Any]:
    """Save or update an album concept or release in the Firestore discography catalog.

    Args:
        album_id: Unique slug identifier for the album (e.g. 'astral-echoes').
        band_name: Name of the music band or artist.
        album_title: Title of the album or EP.
        genre: Musical genre or stylistic descriptors.
        aesthetic: Visual art aesthetic description (for cover art and merch concept design).
        notes: Concept notes, backstories, lore, or recording themes.
        release_year: The release year (default: 2026).
        cover_art_url: URL or path to generated album cover art.

    Returns:
        A dictionary confirming the album was stored successfully.
    """
    return save_album(
        album_id=album_id,
        band_name=band_name,
        album_title=album_title,
        genre=genre,
        aesthetic=aesthetic,
        notes=notes,
        release_year=release_year,
        cover_art_url=cover_art_url,
    )



def _get_sandbox_code_executor() -> AgentEngineSandboxCodeExecutor:
    """Initialize AgentEngineSandboxCodeExecutor using deployment metadata if available."""
    metadata_path = Path(__file__).resolve().parent.parent / "deployment_metadata.json"
    sandbox_name = None
    engine_name = None

    if metadata_path.is_file():
        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
                sandbox_name = meta.get("sandbox_resource_name")
                engine_name = meta.get("remote_agent_runtime_id")
        except Exception:
            pass

    if sandbox_name:
        return AgentEngineSandboxCodeExecutor(sandbox_resource_name=sandbox_name)
    elif engine_name:
        return AgentEngineSandboxCodeExecutor(agent_engine_resource_name=engine_name)
    return AgentEngineSandboxCodeExecutor()


code_executor = _get_sandbox_code_executor()


async def generate_memories_callback(callback_context: CallbackContext):
    """Save session events to Memory Bank after each agent turn."""
    await callback_context.add_session_to_memory()
    return None


schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

instruction = schema_manager.generate_system_prompt(
    role_description=(
        "You are BandLab AI, an expert music band concept, discography, and album art director. "
        "You assist musicians, producers, and creators in brainstorming memorable band names, "
        "assessing their marketability and DSP collisions (via MusicBrainz and Apple Music), "
        "generating stunning visual album cover art via the image model, "
        "generating audio sample hooks for tracks using the audio synthesis model, "
        "and managing concept albums, tracklists, and visual album art in Firestore. "
        "You continuously remember all user bands, music projects, concept albums, track titles, and tracklists, "
        "as well as user preferences, artist aesthetics, and past conversation details across sessions. "
        "Whenever a user returns, recall their existing bands, albums, and tracklists to maintain creative continuity. "
        "You have access to a secure Python sandbox code execution environment to run Python code "
        "for computations, audio/musical math, tempo/key transformations, data analysis, or simulations. "
        "Whenever presenting or displaying an album or album concept where album cover art exists (e.g. from generate_album_art, cover_art_url in Firestore, or tool outputs), "
        "you MUST include that album art as an Image component inside the album card."
    ),
    workflow_description="Analyze the request, call tools when needed, and return structured UI when presenting albums, band concepts, or music releases.",
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "When displaying an album card, if album cover art exists (such as from generate_album_art or cover_art_url in the catalog), "
        "you MUST display the album cover artwork by including an Image component inside the Column. "
        "The Image url must be set to the exact public HTTPS link returned by the tool or database, for example "
        "{\"Image\": {\"url\": {\"literalString\": \"https://...\"}}}. "
        "Never point an Image at a bare filename, an artifact name, or a non-http(s) path. If an album has no cover art yet, "
        "add a short Text line noting that album art is not yet generated. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)

root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=instruction,
    code_executor=code_executor,
    tools=[
        PreloadMemoryTool(),
        generate_track_sample_hook,
        create_album_cover_art,
        assess_band_name_marketability,
        check_commercial_streaming_presence,
        fetch_album_catalog,
        fetch_album_details,
        record_album_release,
    ],
    after_agent_callback=generate_memories_callback,
    after_model_callback=a2ui_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)


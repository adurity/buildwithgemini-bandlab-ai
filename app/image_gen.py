"""Image generation module for BandLab AI album cover and visual art."""

import re
import time
from typing import Any, Dict, Optional
from google import genai
from google.cloud import storage
from google.genai import types
from google.adk.tools import ToolContext

PROJECT_ID = "qwiklabs-gcp-04-a67514e0abc9"
BUCKET_NAME = "bandlab-album-art-qwiklabs-gcp-04-a67514e0abc9"
MODEL_NAME = "gemini-3.1-flash-lite-image"
LOCATION = "global"

_genai_client: Optional[genai.Client] = None
_storage_client: Optional[storage.Client] = None


def get_genai_client() -> genai.Client:
    global _genai_client
    if _genai_client is None:
        _genai_client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
    return _genai_client


def get_storage_client() -> storage.Client:
    global _storage_client
    if _storage_client is None:
        _storage_client = storage.Client(project=PROJECT_ID)
    return _storage_client


def generate_album_art(
    album_title: str,
    band_name: str,
    aesthetic: str,
    tool_context: ToolContext,
) -> Dict[str, Any]:
    """Generate concept album cover art, store it as an artifact, and upload to public Cloud Storage.

    Uses the gemini-3.1-flash-lite-image model in the global region to produce high quality
    square album art. The resulting image bytes are saved into the playground Artifacts panel
    via tool_context.save_artifact, and uploaded to the public GCS bucket.

    Args:
        album_title: Title of the album or release.
        band_name: Name of the music band or artist.
        aesthetic: Visual art description, aesthetic style, color palette, or mood.
        tool_context: ADK ToolContext to record session artifacts.

    Returns:
        A dict with the public https image URL, artifact filename, and status.
    """
    clean_title = album_title.strip()
    clean_band = band_name.strip()
    prompt = (
        f"A striking square music album cover art for the album '{clean_title}' by '{clean_band}'. "
        f"Visual style and aesthetic: {aesthetic}. "
        "Professional album artwork layout, high detail, artistic composition, no watermarks."
    )

    client = get_genai_client()
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE", "TEXT"],
        ),
    )

    image_bytes = None
    mime_type = "image/jpeg"

    if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
        for part in response.candidates[0].content.parts:
            if part.inline_data and part.inline_data.data:
                image_bytes = part.inline_data.data
                if part.inline_data.mime_type:
                    mime_type = part.inline_data.mime_type
                break

    if not image_bytes:
        return {
            "status": "error",
            "message": "No image was returned by the gemini-3.1-flash-lite-image model.",
        }

    # Generate filename / object key
    ext = "png" if "png" in mime_type else "jpg"
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", f"{clean_band}_{clean_title}").strip("_").lower()
    timestamp = int(time.time())
    filename = f"{slug}_{timestamp}.{ext}"

    # 1. Save artifact to ToolContext (shows up in Playground Artifacts panel)
    artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
    try:
        import inspect, asyncio
        res = tool_context.save_artifact(filename=filename, artifact=artifact_part)
        if inspect.iscoroutine(res):
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(res)
            except RuntimeError:
                asyncio.run(res)
    except Exception:
        pass

    # 2. Upload bytes to public Cloud Storage bucket
    storage_client = get_storage_client()
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(filename)
    blob.upload_from_string(image_bytes, content_type=mime_type)

    public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"

    return {
        "status": "success",
        "album_title": clean_title,
        "band_name": clean_band,
        "artifact_filename": filename,
        "public_image_url": public_url,
    }

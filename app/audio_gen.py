"""Studio-grade music hook generation module using Google's Lyria 3 model."""

import base64
import os
import re
import time
from typing import Any, Dict, Optional
import google.auth
import google.auth.transport.requests
import requests
from google.cloud import storage
from google.genai import types
from google.adk.tools import ToolContext

# Project and Storage bucket hardcoded as string
PROJECT_ID = "qwiklabs-gcp-04-a67514e0abc9"
BUCKET_NAME = "bandlab-album-art-qwiklabs-gcp-04-a67514e0abc9"
LYRIA_MODEL = "lyria-3-clip-preview"  # 30-second studio-grade 44.1kHz stereo music clip with vocals & instruments

_storage_client: Optional[storage.Client] = None
_credentials: Optional[google.auth.credentials.Credentials] = None


def get_storage_client() -> storage.Client:
    global _storage_client
    if _storage_client is None:
        _storage_client = storage.Client(project=PROJECT_ID)
    return _storage_client


def get_auth_token() -> str:
    """Get valid Google OAuth access token for Vertex AI interactions endpoint."""
    global _credentials
    if _credentials is None:
        _credentials, _ = google.auth.default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
    auth_req = google.auth.transport.requests.Request()
    if not _credentials.valid:
        _credentials.refresh(auth_req)
    return _credentials.token


def generate_sample_hook(
    track_title: str,
    vibe: Optional[str] = "cyberpunk synthwave",
    tool_context: Optional[ToolContext] = None,
) -> Dict[str, Any]:
    """Generate a high-fidelity 44.1kHz stereo music hook using Google's Lyria model.

    Synthesizes a full 30-second studio-produced music preview clip with complete
    instrumentation (drums, bassline, rhythm, synths/guitars) and vocal melody/lyrics,
    saves the track to the session artifacts panel, and uploads the MP3 bytes directly
    to the public Cloud Storage bucket without writing to a local file.

    Args:
        track_title: Title of the track to generate a sample hook for.
        vibe: Musical style, atmosphere, or genre vibe (e.g. '80s synthwave', 'indie alternative rock').
        tool_context: Optional ADK ToolContext to record the audio artifact in the session.

    Returns:
        A dictionary with the generated song structure, lyrics, and the public HTTPS URL.
    """
    clean_title = track_title.strip()
    clean_vibe = (vibe or "cyberpunk synthwave").strip()

    music_prompt = (
        f"A 30-second high-energy, studio-produced {clean_vibe} music hook for a track titled '{clean_title}'. "
        "High fidelity 44.1kHz stereo audio with full instrumental production including driving bassline, "
        "crisp percussion, melodic lead synths or guitars, and a powerful, memorable vocal chorus."
    )

    url = f"https://aiplatform.googleapis.com/v1beta1/projects/{PROJECT_ID}/locations/global/interactions"
    token = get_auth_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=utf-8",
    }
    payload = {
        "model": LYRIA_MODEL,
        "input": [
            {
                "type": "text",
                "text": music_prompt,
            }
        ],
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=90)
    if resp.status_code != 200:
        return {
            "status": "error",
            "message": f"Lyria generation failed: {resp.status_code} - {resp.text}",
        }

    data = resp.json()
    outputs = data.get("outputs", [])

    audio_bytes = None
    mime_type = "audio/mpeg"
    lyrics_text = ""
    caption_text = ""

    for out in outputs:
        out_type = out.get("type")
        if out_type == "audio" and out.get("data"):
            audio_bytes = base64.b64decode(out["data"])
            if out.get("mime_type"):
                mime_type = out["mime_type"]
        elif out_type == "text" and out.get("text"):
            text_val = out["text"]
            if text_val.startswith("Caption:"):
                caption_text = text_val
            else:
                lyrics_text = text_val

    if not audio_bytes:
        return {
            "status": "error",
            "message": "No audio returned by the Lyria model.",
        }

    # Generate filename and key
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", clean_title).strip("_").lower()
    timestamp = int(time.time())
    filename = f"lyria_hook_{slug}_{timestamp}.mp3"

    # Save to session artifacts if ToolContext is available
    if tool_context and hasattr(tool_context, "save_artifact"):
        try:
            import inspect, asyncio
            artifact_part = types.Part.from_bytes(data=audio_bytes, mime_type=mime_type)
            res = tool_context.save_artifact(filename=filename, artifact=artifact_part)
            if inspect.iscoroutine(res):
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(res)
                except RuntimeError:
                    asyncio.run(res)
        except Exception:
            pass

    # Upload audio bytes directly to public GCS bucket (no local file writing)
    storage_client = get_storage_client()
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(filename)
    blob.upload_from_string(audio_bytes, content_type=mime_type)

    public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"

    return {
        "status": "success",
        "model": LYRIA_MODEL,
        "track_title": clean_title,
        "vibe": clean_vibe,
        "lyrics_structure": lyrics_text,
        "caption": caption_text,
        "duration": "30 seconds (high-fidelity 44.1kHz stereo audio)",
        "artifact_filename": filename,
        "public_audio_url": public_url,
    }

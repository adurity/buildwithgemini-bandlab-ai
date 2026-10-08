"""Firestore database client and helper operations for BandLab AI."""

import logging
from typing import Any, Dict, List, Optional
from google.cloud import firestore

# IMPORTANT: Hardcode project ID as string.
# On Agent Platform, google.auth.default() or GOOGLE_CLOUD_PROJECT can return
# the project number instead of project ID, which breaks Firestore after deployment.
PROJECT_ID = "qwiklabs-gcp-04-a67514e0abc9"
COLLECTION_NAME = "albums"

logger = logging.getLogger(__name__)
_db_client: Optional[firestore.Client] = None


def get_db() -> firestore.Client:
    """Returns a singleton Firestore client instance initialized with the hardcoded project ID."""
    global _db_client
    if _db_client is None:
        _db_client = firestore.Client(project=PROJECT_ID)
    return _db_client


def list_albums(genre: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
    """List albums from the discography catalog, optionally filtered by genre.

    Args:
        genre: Optional genre keyword to filter albums (case-insensitive substring match).
        limit: Maximum number of albums to retrieve (default: 10).

    Returns:
        A list of album records containing band name, title, genre, aesthetic, tracklist, etc.
    """
    db = get_db()
    docs = db.collection(COLLECTION_NAME).limit(limit).stream()
    results = []

    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        if genre:
            doc_genre = data.get("genre", "").lower()
            if genre.lower() not in doc_genre:
                continue
        results.append(data)

    return results


def get_album(album_id: str) -> Optional[Dict[str, Any]]:
    """Get details for a specific album by its ID.

    Args:
        album_id: The document ID of the album.

    Returns:
        The album data dictionary if found, or None.
    """
    db = get_db()
    doc = db.collection(COLLECTION_NAME).document(album_id).get()
    if not doc.exists:
        return None
    data = doc.to_dict()
    data["id"] = doc.id
    return data


def save_album(
    album_id: str,
    band_name: str,
    album_title: str,
    genre: str,
    aesthetic: str,
    tracklist: Optional[List[Dict[str, Any]]] = None,
    notes: str = "",
    release_year: int = 2026,
    cover_art_url: str = "",
) -> Dict[str, Any]:
    """Create or update an album record in the discography catalog.

    Args:
        album_id: Unique identifier / slug for the album (e.g. 'neon-overdrive').
        band_name: Name of the music band or artist project.
        album_title: Title of the album or EP.
        genre: Musical genre or subgenres (e.g. 'Synthwave', 'Indie Rock').
        aesthetic: Visual and artistic aesthetic description for album art and merch.
        tracklist: List of tracks, each being a dict with 'track_number', 'title', and 'duration'.
        notes: Concept notes, backstories, or recording lore.
        release_year: Year of release (default: 2026).
        cover_art_url: URL or storage path to the generated album cover art.

    Returns:
        A dict confirming the saved album information.
    """
    db = get_db()
    payload = {
        "band_name": band_name,
        "album_title": album_title,
        "genre": genre,
        "aesthetic": aesthetic,
        "tracklist": tracklist or [],
        "notes": notes,
        "release_year": release_year,
        "cover_art_url": cover_art_url,
    }
    db.collection(COLLECTION_NAME).document(album_id).set(payload, merge=True)
    payload["id"] = album_id
    return {"status": "success", "album": payload}

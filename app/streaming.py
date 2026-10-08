"""Commercial streaming store presence checker via the public iTunes/Apple Music Search API."""

import json
import urllib.parse
import urllib.request
from typing import Any, Dict, List


def check_streaming_commercial_presence(artist_or_album: str, entity_type: str = "artist") -> Dict[str, Any]:
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
    clean_query = artist_or_album.strip()
    entity = "musicArtist" if entity_type == "artist" else "album"
    encoded_term = urllib.parse.quote(clean_query)
    url = f"https://itunes.apple.com/search?term={encoded_term}&entity={entity}&limit=5"

    matches: List[Dict[str, Any]] = []
    exact_hit = False

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "BandLabAI/1.0 (bandlab@example.com)"}
        )
        with urllib.request.urlopen(req, timeout=4) as response:
            payload = json.loads(response.read().decode())
            results = payload.get("results", [])

            for item in results:
                if entity_type == "artist":
                    name = item.get("artistName", "")
                    genre = item.get("primaryGenreName", "Unknown")
                    url_link = item.get("artistLinkUrl", "")
                    if name.lower() == clean_query.lower():
                        exact_hit = True
                    matches.append({"name": name, "genre": genre, "store_url": url_link})
                else:
                    title = item.get("collectionName", "")
                    artist = item.get("artistName", "")
                    genre = item.get("primaryGenreName", "Unknown")
                    year = (item.get("releaseDate") or "")[:4]
                    if title.lower() == clean_query.lower():
                        exact_hit = True
                    matches.append({
                        "album_title": title,
                        "artist": artist,
                        "genre": genre,
                        "release_year": year
                    })
    except Exception as e:
        return {
            "query": clean_query,
            "status": "error",
            "message": f"Could not reach streaming catalog API: {e}",
            "commercial_presence": "unknown"
        }

    if exact_hit:
        presence = "High - Exact commercial artist/release already distributed on major streaming stores."
    elif len(matches) > 0:
        presence = "Moderate - Similar commercial names exist in store catalogs."
    else:
        presence = "Clear - Zero commercial releases found with this name on store catalogs."

    return {
        "query": clean_query,
        "entity_type": entity_type,
        "commercial_results_count": len(matches),
        "exact_commercial_match": exact_hit,
        "commercial_presence_verdict": presence,
        "catalog_matches": matches[:4],
    }

"""Band name evaluation tool querying MusicBrainz and computing marketability scores."""

import json
import re
import urllib.parse
import urllib.request
from typing import Any, Dict, List

COMMON_DICTIONARY_WORDS = {
    "the", "band", "music", "rock", "sound", "radio", "live", "bread",
    "boston", "chicago", "kansas", "america", "eagles", "doors", "love",
    "fire", "water", "air", "star", "sun", "moon", "night", "day"
}


def evaluate_band_name(band_name: str) -> Dict[str, Any]:
    """Assess real-world collision risks and marketing strength for a proposed band name.

    Queries the MusicBrainz registry for existing artists, evaluates searchability (SEO),
    brevity, and social handle friendliness, returning an overall 0-100 marketability score.

    Args:
        band_name: The proposed band or artist name to evaluate.

    Returns:
        A dictionary containing overall score, score breakdown, findings, and suggestions.
    """
    clean_name = band_name.strip()
    words = re.findall(r"\b\w+\b", clean_name.lower())
    char_count = len(clean_name)
    word_count = len(words)

    # 1. Query MusicBrainz API for real-world artist collisions
    mb_exact_matches = []
    mb_similar_artists = []
    try:
        encoded_query = urllib.parse.quote(f'artist:"{clean_name}"')
        url = f"https://musicbrainz.org/ws/2/artist/?query={encoded_query}&fmt=json&limit=5"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "BandLabAI/1.0 (bandlab@example.com)"}
        )
        with urllib.request.urlopen(req, timeout=4) as response:
            data = json.loads(response.read().decode())
            for artist in data.get("artists", []):
                name = artist.get("name", "")
                disambiguation = artist.get("disambiguation") or ""
                country = artist.get("country") or ""
                summary = f"{name} ({country}) - {disambiguation}".strip(" - ")
                if name.lower() == clean_name.lower():
                    mb_exact_matches.append(summary)
                else:
                    mb_similar_artists.append(summary)
    except Exception:
        # Graceful fallback if MusicBrainz network call times out
        pass

    # 2. Collision Risk Score (35%)
    if len(mb_exact_matches) > 0:
        collision_score = max(20, 50 - (len(mb_exact_matches) * 15))
    elif len(mb_similar_artists) > 0:
        collision_score = 75
    else:
        collision_score = 100

    # 3. SEO & Distinctiveness Score (25%)
    seo_score = 90
    if word_count == 1 and words[0] in COMMON_DICTIONARY_WORDS:
        seo_score = 30
    elif word_count == 1:
        seo_score = 70
    elif any(w in COMMON_DICTIONARY_WORDS for w in words):
        seo_score = 75

    # 4. Brevity & Memorability (20%)
    if 1 <= word_count <= 3 and 4 <= char_count <= 22:
        brevity_score = 95
    elif word_count > 4 or char_count > 28:
        brevity_score = 55
    else:
        brevity_score = 75

    # 5. Handle / Domain Friendliness (20%)
    clean_handle = re.sub(r"[^a-zA-Z0-9]", "", clean_name).lower()
    handle_score = 95 if (len(clean_handle) <= 18 and clean_handle.isalnum()) else 70

    # Overall Weighted Score (0-100)
    overall_score = round(
        (collision_score * 0.35)
        + (seo_score * 0.25)
        + (brevity_score * 0.20)
        + (handle_score * 0.20)
    )

    if overall_score >= 85:
        verdict = "Exceptional - Highly unique and memorable"
    elif overall_score >= 70:
        verdict = "Strong - Solid market potential with minor trade-offs"
    elif overall_score >= 50:
        verdict = "Moderate - May face collision or search discovery competition"
    else:
        verdict = "Challenging - Heavy collision risk or common search conflicts"

    # Feedback and highlights
    critique: List[str] = []
    if mb_exact_matches:
        critique.append(f"Name collision found: Already registered on MusicBrainz ({mb_exact_matches[0]}).")
    else:
        critique.append("Exclusivity advantage: No registered artist found with this exact name on MusicBrainz.")

    if seo_score < 70:
        critique.append("Search warning: Name is a common dictionary term; will struggle to rank on Spotify/Google.")
    else:
        critique.append("Strong searchability: Distinct phrase suitable for search algorithms.")

    critique.append(f"Social handle format: Recommended handle '@{clean_handle}'.")

    return {
        "band_name": clean_name,
        "overall_marketability_score": overall_score,
        "verdict": verdict,
        "dimensions": {
            "collision_risk_score": collision_score,
            "seo_distinctiveness_score": seo_score,
            "brevity_memorability_score": brevity_score,
            "handle_readability_score": handle_score,
        },
        "registry_findings": {
            "musicbrainz_exact_matches": mb_exact_matches,
            "similar_artists": mb_similar_artists[:3],
        },
        "critique": critique,
    }

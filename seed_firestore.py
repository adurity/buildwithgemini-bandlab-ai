"""Seed script to populate Firestore with sample albums and discography items."""

from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-04-a67514e0abc9"
COLLECTION_NAME = "albums"

SAMPLE_ALBUMS = [
    {
        "id": "neon-overdrive",
        "band_name": "CyberPulse Syndicate",
        "album_title": "Neon Overdrive",
        "genre": "Synthwave / Cyberpunk",
        "aesthetic": "High-contrast magenta and cyan wireframes, retro gridscapes, 80s analog CRT glow",
        "release_year": 2026,
        "tracklist": [
            {"track_number": 1, "title": "Gridrunner Awakening", "duration": "3:45"},
            {"track_number": 2, "title": "Chrome Sunset", "duration": "4:12"},
            {"track_number": 3, "title": "Sublevel 9 Highway", "duration": "5:01"},
            {"track_number": 4, "title": "Memory Leak Serenade", "duration": "3:28"},
        ],
        "cover_art_url": "",
        "notes": "Debut concept album chronicling an AI escaping into a nocturnal megacity."
    },
    {
        "id": "velvet-decay",
        "band_name": "Ghost Orchid Trio",
        "album_title": "Velvet & Decay",
        "genre": "Dream Pop / Post-Punk",
        "aesthetic": "Faded polaroids, wilted botanicals, dusty lavender and desaturated charcoal textures",
        "release_year": 2025,
        "tracklist": [
            {"track_number": 1, "title": "Petals in the Ash", "duration": "4:30"},
            {"track_number": 2, "title": "Midnight Greenhouse", "duration": "3:55"},
            {"track_number": 3, "title": "Echo Chamber Lullaby", "duration": "4:18"},
        ],
        "cover_art_url": "",
        "notes": "Atmospheric, reverb-drenched guitars recorded in an abandoned conservatory."
    },
    {
        "id": "solar-static",
        "band_name": "Astro-Kinetics",
        "album_title": "Solar Static",
        "genre": "Space Rock / Psychedelic",
        "aesthetic": "Golden hour nebula swirls, vintage NASA flight manuals, grainy cosmic flares",
        "release_year": 2026,
        "tracklist": [
            {"track_number": 1, "title": "Orbital Decay", "duration": "6:14"},
            {"track_number": 2, "title": "Solar Wind Whispers", "duration": "5:02"},
            {"track_number": 3, "title": "Event Horizon Blues", "duration": "7:40"},
        ],
        "cover_art_url": "",
        "notes": "Heavy fuzz bass paired with cosmic synth arpeggios."
    }
]

def seed():
    print(f"Connecting to Firestore using project ID: '{PROJECT_ID}'...")
    db = firestore.Client(project=PROJECT_ID)
    collection_ref = db.collection(COLLECTION_NAME)

    for item in SAMPLE_ALBUMS:
        doc_id = item["id"]
        data = {k: v for k, v in item.items() if k != "id"}
        collection_ref.document(doc_id).set(data)
        print(f"Seeded album '{item['album_title']}' by '{item['band_name']}' (ID: {doc_id})")

    print("\nFirestore seeding completed successfully!")

if __name__ == "__main__":
    seed()

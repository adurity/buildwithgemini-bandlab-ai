# BandLab AI 🎵🎨

An autonomous AI agent and creative director for musicians, indie bands, and producers. Built with Google Agent Development Kit (ADK), Gemini 3.8, Gemini 3.1 Flash Lite Image, and Google Lyria 3.

## ✨ Features

- **Band Name Marketability & Registry Collision Checking**:
  - Validates names against the **MusicBrainz** open music registry.
  - Scores 0–100 across SEO distinctiveness, brevity, and social handle friendliness.
- **Commercial Streaming & DSP Verification**:
  - Queries Apple Music / iTunes Search API in real-time to check commercial collisions.
- **Concept Album Cover Art Generation**:
  - Uses `gemini-3.1-flash-lite-image` to generate 1:1 high-resolution concept album cover art.
  - Automatically registers artwork in session artifacts and uploads directly to Google Cloud Storage.
- **Studio-Grade 44.1 kHz Music Hook Generation**:
  - Powered by Google's dedicated music foundation model **Lyria 3** (`lyria-3-clip-preview`).
  - Synthesizes 30-second studio-produced stereo music hooks with drums, basslines, synths, and vocal melodies.
- **Firestore Discography Backend**:
  - Persistent storage for concept albums, tracklists, visual aesthetics, and release notes in Google Cloud Firestore.

## 🛠️ Tech Stack & Google Cloud Tools

- **Agent Framework**: Google ADK (Agent Development Kit)
- **Reasoning Model**: `gemini-3.8-flash`
- **Visual Art Model**: `gemini-3.1-flash-lite-image`
- **Music Generation**: `lyria-3-clip-preview` (Lyria 3 on Vertex AI)
- **Database**: Google Cloud Firestore (Native mode)
- **Object Storage**: Google Cloud Storage (Public asset hosting)
- **External Public APIs**: MusicBrainz API, Apple iTunes Search API

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- `uv` package manager
- Google Cloud SDK (`gcloud`) with access to Vertex AI, Firestore, and GCS

### Installation

```bash
uv sync
```

### Running Locally with ADK Web Playground

```bash
uv run adk web --port 8080 .
```

Navigate to `http://localhost:8080/dev-ui/` in your browser.

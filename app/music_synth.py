"""In-memory procedural music synthesizer and vocal-music audio mixer.

Generates genre-tailored musical backing tracks (chords, basslines, percussion)
and mixes them with vocal hooks in memory using 16-bit stereo PCM mastering.
"""

import io
import math
import struct
import wave
from typing import List


def generate_backing_music(duration_sec: float, sample_rate: int = 24000, vibe: str = "synthwave") -> List[float]:
    """Generates an in-memory musical backing track (chords, bassline, percussion).

    Args:
        duration_sec: Total duration in seconds.
        sample_rate: Audio sampling rate (e.g. 24000 Hz).
        vibe: Musical vibe or genre descriptor to adapt tempo and harmonics.

    Returns:
        A list of floating point audio samples (-1.0 to 1.0).
    """
    total_samples = int(duration_sec * sample_rate)
    samples = [0.0] * total_samples

    # Adjust BPM and progression based on vibe
    vibe_lower = vibe.lower()
    if "rock" in vibe_lower or "punk" in vibe_lower:
        bpm = 135
    elif "chill" in vibe_lower or "dream" in vibe_lower or "lofi" in vibe_lower:
        bpm = 95
    else:
        bpm = 120  # Classic synthwave / electronic pop

    beat_samples = int((60.0 / bpm) * sample_rate)
    eighth_samples = max(1, beat_samples // 2)

    # Progression: Am - F - C - G
    chords = [
        {"root": 55.0, "pad": [220.0, 261.63, 329.63]},   # Am (A3, C4, E4)
        {"root": 43.65, "pad": [174.61, 220.0, 261.63]},  # F (F3, A3, C4)
        {"root": 65.41, "pad": [261.63, 329.63, 392.0]},  # C (C4, E4, G4)
        {"root": 49.0, "pad": [196.0, 246.94, 293.66]},   # G (G3, B3, D4)
    ]
    chord_duration_samples = beat_samples * 4

    for i in range(total_samples):
        t = i / sample_rate
        chord_idx = (i // chord_duration_samples) % len(chords)
        chord = chords[chord_idx]

        # 1. Warm Synth / Ambient Pad with chorus detune
        pad_val = 0.0
        for freq in chord["pad"]:
            pad_val += 0.30 * math.sin(2 * math.pi * freq * t)
            pad_val += 0.15 * math.sin(2 * math.pi * (freq * 1.005) * t)

        # 2. Driving Bassline (rhythmic 8th-note pulse)
        note_in_measure = (i % eighth_samples) / eighth_samples
        bass_env = math.exp(-4.5 * note_in_measure)
        bass_freq = chord["root"]
        bass_val = 0.5 * (
            math.sin(2 * math.pi * bass_freq * t)
            + 0.35 * math.sin(2 * math.pi * bass_freq * 2 * t)
        ) * bass_env

        # 3. Dynamic Drum Rhythm (Kick, Snare/Clap, Crisp Hi-Hat)
        beat_num = (i // beat_samples) % 4
        pos_in_beat = (i % beat_samples) / beat_samples
        drum_val = 0.0

        # Kick on downbeats (0 and 2)
        if beat_num in (0, 2) and pos_in_beat < 0.22:
            kick_env = math.exp(-14.0 * pos_in_beat)
            kick_pitch = 120.0 * math.exp(-24.0 * pos_in_beat) + 48.0
            drum_val += 0.65 * math.sin(2 * math.pi * kick_pitch * (pos_in_beat * (60.0 / bpm))) * kick_env

        # Snare / Clap on backbeats (1 and 3)
        if beat_num in (1, 3) and pos_in_beat < 0.25:
            snare_env = math.exp(-11.0 * pos_in_beat)
            noise = ((math.sin(t * 12345.67) * 43758.5453) % 1.0) * 2.0 - 1.0
            snare_body = math.sin(2 * math.pi * 185.0 * (pos_in_beat * (60.0 / bpm)))
            drum_val += (0.28 * noise + 0.22 * snare_body) * snare_env

        # Hi-hat on every 8th note
        pos_in_eighth = (i % eighth_samples) / eighth_samples
        if pos_in_eighth < 0.08:
            hat_env = math.exp(-32.0 * pos_in_eighth)
            hat_noise = ((math.sin(t * 98765.43) * 23421.123) % 1.0) * 2.0 - 1.0
            drum_val += 0.16 * hat_noise * hat_env

        # Total musical mix sample
        samples[i] = (0.25 * pad_val) + (0.35 * bass_val) + (0.40 * drum_val)

    return samples


def mix_vocals_with_music(vocal_wav_bytes: bytes, vibe: str = "synthwave") -> bytes:
    """Takes vocal WAV bytes, generates synced music, mixes and returns mastered 16-bit stereo WAV.

    Args:
        vocal_wav_bytes: Raw bytes of synthesized vocal hook (RIFF WAV format).
        vibe: Style or genre vibe descriptor.

    Returns:
        Mastered stereo 16-bit WAV audio bytes.
    """
    with io.BytesIO(vocal_wav_bytes) as in_io:
        with wave.open(in_io, "rb") as wf:
            n_channels = wf.getnchannels()
            framerate = wf.getframerate()
            n_frames = wf.getnframes()
            raw_frames = wf.readframes(n_frames)

    fmt = f"<{n_frames * n_channels}h"
    raw_integers = struct.unpack(fmt, raw_frames)

    # Convert to mono float samples (-1.0 to 1.0)
    if n_channels == 1:
        vocal_floats = [val / 32768.0 for val in raw_integers]
    else:
        vocal_floats = [(raw_integers[i * 2] + raw_integers[i * 2 + 1]) / (2.0 * 32768.0) for i in range(n_frames)]

    duration_sec = n_frames / framerate
    music_duration = duration_sec + 0.7  # Small musical tail
    music_samples = generate_backing_music(music_duration, sample_rate=framerate, vibe=vibe)

    total_out_samples = len(music_samples)
    mixed_left: List[int] = []
    mixed_right: List[int] = []

    for i in range(total_out_samples):
        vocal = vocal_floats[i] if i < len(vocal_floats) else 0.0
        music = music_samples[i]

        # Automatic vocal sidechain ducking of background music
        vocal_duck = max(0.45, 1.0 - abs(vocal) * 0.75)
        music_ducked = music * vocal_duck

        # Master mix: Clear lead vocal with wide stereo backing tracks
        l_sample = (vocal * 0.85) + (music_ducked * 0.65)
        r_sample = (vocal * 0.85) + (music_ducked * 0.70)

        # Soft limiter
        l_clamped = max(-0.95, min(0.95, l_sample))
        r_clamped = max(-0.95, min(0.95, r_sample))

        mixed_left.append(int(l_clamped * 32767.0))
        mixed_right.append(int(r_clamped * 32767.0))

    out_io = io.BytesIO()
    with wave.open(out_io, "wb") as out_wf:
        out_wf.setnchannels(2)  # Stereo
        out_wf.setsampwidth(2)  # 16-bit
        out_wf.setframerate(framerate)

        interleaved: List[int] = []
        for l, r in zip(mixed_left, mixed_right):
            interleaved.append(l)
            interleaved.append(r)

        out_wf.writeframes(struct.pack(f"<{len(interleaved)}h", *interleaved))

    return out_io.getvalue()

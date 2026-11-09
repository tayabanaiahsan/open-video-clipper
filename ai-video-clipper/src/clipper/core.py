"""FFmpeg/ffprobe helpers and local scene-based highlight selection."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=True, text=True, capture_output=True)


def duration_seconds(path: Path) -> float:
    result = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)])
    return float(json.loads(result.stdout)["format"]["duration"])


def detect_scenes(path: Path, threshold: float = 0.35) -> list[float]:
    """Find timestamps of visual scene changes; fallback gracefully for static videos."""
    command = ["ffmpeg", "-hide_banner", "-i", str(path), "-vf", f"select='gt(scene,{threshold})',showinfo", "-an", "-f", "null", "-"]
    process = subprocess.run(command, capture_output=True, text=True, check=False)
    if process.returncode != 0:
        raise RuntimeError(f"FFmpeg scene detection failed: {process.stderr[-1000:]}")
    return [float(match) for match in re.findall(r"pts_time:([0-9.]+)", process.stderr)]


def choose_clips(duration: float, scenes: list[float], clip_length: float, count: int) -> list[tuple[float, float]]:
    """Prefer windows containing many cuts, spaced apart; deterministic, not AI virality prediction."""
    if duration <= 0 or clip_length <= 0 or count <= 0:
        raise ValueError("Duration, clip length, and count must be positive")
    length = min(duration, clip_length)
    max_start = max(0.0, duration - length)
    starts = {0.0, max_start}
    starts.update(min(max(0.0, t - length / 2), max_start) for t in scenes)
    # Also include regular windows for footage with few/no scene changes.
    step = max(length / 2, 1.0)
    starts.update(min(i * step, max_start) for i in range(int(max_start / step) + 1))
    candidates = sorted(starts, key=lambda s: (-sum(s <= t < s + length for t in scenes), s))
    selected: list[float] = []
    for start in candidates:
        if all(abs(start - prior) >= length * 0.8 for prior in selected):
            selected.append(start)
        if len(selected) == count:
            break
    return [(round(s, 3), round(length, 3)) for s in sorted(selected)]


def render_clip(source: Path, destination: Path, start: float, length: float, subtitles: Path | None = None) -> None:
    # Crop center to 9:16, then scale/pad to 1080x1920. Audio is preserved when present.
    filters = ["crop=w='min(iw,ih*9/16)':h='min(ih,iw*16/9)'", "scale=1080:1920:force_original_aspect_ratio=decrease", "pad=1080:1920:(ow-iw)/2:(oh-ih)/2", "setsar=1"]
    if subtitles is not None:
        # FFmpeg subtitles filter requires escaping special path characters.
        escaped = str(subtitles.resolve()).replace("\\", "/").replace(":", "\\:").replace("'", "\\'").replace("[", "\\[").replace("]", "\\]")
        filters.append(f"subtitles='{escaped}'")
    command = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-ss", str(start), "-i", str(source), "-t", str(length), "-vf", ",".join(filters), "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(destination)]
    run(command)

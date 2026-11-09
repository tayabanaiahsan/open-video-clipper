# Open Video Clipper 🎬

A **free, local-first, open-source** command-line tool to turn long videos into vertical shorts. It detects visual scene changes, picks non-overlapping highlight windows, crops to 9:16, and optionally generates subtitles using a local Whisper model.

> **Honest scope:** v0.1 selects clips by **scene-change density**, not semantic quality, engagement, or virality. No cloud account is required. Processing 1080×1920 clips can take time.

## Requirements

- Python 3.10+
- [FFmpeg](https://ffmpeg.org/download.html) (including `ffprobe`) installed and available on PATH
- Windows, macOS, or Linux

## Quick start

```bash
python -m venv .venv
# Windows PowerShell: .venv\\Scripts\\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -e .
open-video-clipper input.mp4 --count 3 --length 30 --output output
```

The tool creates `output/short_01.mp4`, etc., plus `output/manifest.json` with source timestamps.

## Optional automatic subtitles

```bash
python -m pip install -e ".[transcribe]"
open-video-clipper input.mp4 --count 3 --length 30 --subtitles --model small
```

The first run downloads the chosen Whisper model. GPU acceleration depends on your local CTranslate2/CUDA setup; CPU processing is supported. Subtitle burn-in requires an FFmpeg build with `libass` enabled. On Windows, subtitle paths with unusual special characters may need a simpler output folder path.

## Options

| Option | Default | Description |
|---|---|---|
| `--count` | 3 | Maximum number of clips |
| `--length` | 30 | Target clip duration (seconds) |
| `--threshold` | 0.35 | Scene-change detection threshold (0–1) |
| `--output` | output | Output directory |
| `--subtitles` | off | Local transcription and burned-in captions |
| `--model` | small | Faster-whisper model |

## How it works

1. `ffprobe` reads video duration.
2. FFmpeg `select` detects scene changes.
3. The selector ranks windows by scene-change count and avoids overlapping clips.
4. FFmpeg center-crops to 9:16 and renders H.264/AAC MP4 shorts.
5. Optional faster-whisper creates SRT captions and FFmpeg burns them into the video.

## Contributing

Issues, bug reports, tests, and pull requests are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md). Please only process videos you own or are licensed to edit.

## Roadmap

- [ ] Face/speaker-aware smart cropping
- [ ] Speech-based highlight ranking
- [ ] GUI for reviewing and trimming candidates
- [ ] Batch mode with resume and caching
- [ ] Hardware-accelerated encoding presets

## License

MIT — see [LICENSE](LICENSE).

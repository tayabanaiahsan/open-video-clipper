"""Command line entrypoint."""
import argparse
import json
import shutil
from pathlib import Path

from .core import choose_clips, detect_scenes, duration_seconds, render_clip


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate vertical shorts from a long video, locally.")
    parser.add_argument("video", type=Path, help="Input video file")
    parser.add_argument("--output", type=Path, default=Path("output"))
    parser.add_argument("--count", type=int, default=3)
    parser.add_argument("--length", type=float, default=30, help="Target seconds per clip")
    parser.add_argument("--threshold", type=float, default=0.35, help="Scene detection sensitivity (0-1)")
    parser.add_argument("--subtitles", action="store_true", help="Transcribe each clip with faster-whisper and burn captions")
    parser.add_argument("--model", default="small", help="Whisper model name (default: small)")
    args = parser.parse_args()
    if not args.video.is_file():
        parser.error("Input video not found")
    if not (0 < args.threshold < 1) or args.count < 1 or args.length <= 0:
        parser.error("Require 0 < threshold < 1, count >= 1 and length > 0")
    for program in ("ffmpeg", "ffprobe"):
        if not shutil.which(program):
            parser.error(f"{program} not found in PATH. Install FFmpeg first.")
    args.output.mkdir(parents=True, exist_ok=True)
    duration = duration_seconds(args.video)
    windows = choose_clips(duration, detect_scenes(args.video, args.threshold), args.length, args.count)
    model = None
    if args.subtitles:
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            parser.error("Install transcription extra: pip install -e '.[transcribe]'")
        model = WhisperModel(args.model, device="auto", compute_type="auto")
    manifest = []
    for index, (start, length) in enumerate(windows, 1):
        target = args.output / f"short_{index:02d}.mp4"
        if model is None:
            render_clip(args.video, target, start, length)
        else:
            raw = args.output / f"short_{index:02d}_raw.mp4"
            render_clip(args.video, raw, start, length)
            segments, _ = model.transcribe(str(raw), vad_filter=True)
            srt = args.output / f"short_{index:02d}.srt"
            def timestamp(t: float) -> str:
                ms = round(t * 1000)
                h, ms = divmod(ms, 3600000)
                m, ms = divmod(ms, 60000)
                s, ms = divmod(ms, 1000)
                return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
            with srt.open("w", encoding="utf-8") as file:
                for j, seg in enumerate(segments, 1):
                    file.write(f"{j}\n{timestamp(seg.start)} --> {timestamp(seg.end)}\n{seg.text.strip()}\n\n")
            if srt.stat().st_size:
                render_clip(raw, target, 0, length, srt)
                raw.unlink()
            else:
                raw.replace(target)
        manifest.append({"file": str(target), "start_seconds": start, "duration_seconds": length})
        print(f"Created {target}")
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print("Done. Selection uses scene density, not a guaranteed viral-score model.")

if __name__ == "__main__":
    main()

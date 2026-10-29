"""Prepara a música autoral offline, sem DSP ou dependências no loop do jogo."""
from array import array
import argparse
import hashlib
import json
from pathlib import Path
import sys
import subprocess
import wave


def prepare(source: Path, output: Path):
    with wave.open(str(source), "rb") as reader:
        channels, width, rate, frames, compression, _ = reader.getparams()
        if width != 2 or compression != "NONE" or channels not in (1, 2):
            raise ValueError("A preparação aceita WAV PCM16 mono/estéreo.")
        samples = array("h", reader.readframes(frames))
    if sys.byteorder != "little":
        samples.byteswap()
    crossfade = min(round(.75 * rate), frames // 8)
    # Sobreposição tail/head: a emenda preserva continuidade de amostras.
    base = samples[crossfade * channels:(frames - crossfade) * channels]
    for frame in range(crossfade):
        alpha = frame / max(1, crossfade - 1)
        for channel in range(channels):
            tail = samples[(frames - crossfade + frame) * channels + channel]
            head = samples[frame * channels + channel]
            base.append(round(tail * (1 - alpha) + head * alpha))
    length = len(base) // channels
    speed = 1
    output_samples = array("h")
    position = 0.0
    while position < length:
        phase = position % length
        index = int(phase)
        fraction = phase - index
        following = (index + 1) % length
        for channel in range(channels):
            first = base[index * channels + channel]
            second = base[following * channels + channel]
            output_samples.append(round(first + (second - first) * fraction))
        position += speed
    duration = len(output_samples) / channels / rate
    if sys.byteorder != "little":
        output_samples.byteswap()
    output.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(output), "wb") as writer:
        writer.setparams((channels, 2, rate, 0, "NONE", "not compressed"))
        writer.writeframes(output_samples.tobytes())
    metadata = {"source": source.name, "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "duration_seconds": round(duration, 3), "sample_rate": rate, "channels": channels,
                "playback_speed": speed,
                "seam_crossfade_seconds": crossfade / rate,
                "method": "Linear PCM resampling at constant 0.8x speed and pitch; seamless loop."}
    output.with_suffix(".json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(json.dumps(metadata))


def encode_ogg(wav_path: Path):
    """Conversor de desenvolvimento opcional; nunca importado pelo jogo."""
    import imageio_ffmpeg

    destination = wav_path.with_suffix(".ogg")
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-hide_banner", "-loglevel", "error",
                    "-y", "-i", str(wav_path), "-c:a", "libvorbis", "-q:a", "4", str(destination)], check=True)
    print(f"OGG: {destination} ({destination.stat().st_size} bytes)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] / "assets/audio/theme.wav")
    parser.add_argument("--ogg", action="store_true", help="Também codifica OGG via imageio-ffmpeg de desenvolvimento")
    args = parser.parse_args()
    prepare(args.source, args.output)
    if args.ogg:
        encode_ogg(args.output)

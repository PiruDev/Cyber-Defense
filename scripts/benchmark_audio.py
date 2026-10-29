"""Compara buffers no SDL local; não mede latência audível nem executa WASM."""
import argparse
import json
import os
from pathlib import Path
import statistics
import sys
from time import perf_counter
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def benchmark(frames):
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    import pygame
    from game.audio import AudioBus
    from game.effects import EffectEvent
    from game.enemies import Enemy
    from game.interface import render_world, create_fonts
    from game.music import MusicPlayer
    from game.settings import EffectSettings
    from game.world import GameWorld

    results = []
    for profile in ("desktop", "web_policy_in_cpython"):
        for buffer in (512, 1024, 2048):
            pygame.mixer.pre_init(44100, -16, 2, buffer)
            pygame.init()
            screen = pygame.display.set_mode((1100, 770))
            fonts = create_fonts(pygame)
            settings = EffectSettings()
            # Só escolhe a política do AudioBus; SDL e Python continuam nativos.
            with patch.object(sys, "platform", "emscripten" if profile.startswith("web") else sys.platform):
                audio = AudioBus(settings)
            world = GameWorld()
            world.phase, world.practice_remaining = "practice", 99999
            world.player.progression.hp = world.player.progression.hp_maximo = 99999
            world.enemies = [Enemy(world.player.x + (i % 5 - 2) * 55,
                                    world.player.y + (i // 5 * 2 - 1) * 70,
                                    hp=1000, max_hp=1000, speed=0) for i in range(10)]
            clock = pygame.time.Clock()
            music = MusicPlayer(settings)
            times, intervals = [], []
            events = [EffectEvent(kind, 0, 0) for kind in ("hit", "hit", "death", "death", "pickup", "score")]
            with patch.object(pygame.mixer.music, "set_volume", wraps=pygame.mixer.music.set_volume) as volume:
                music.start()
                for index in range(frames + 20):
                    interval = clock.tick(60)
                    start = perf_counter()
                    if index % 3 == 0:
                        for _ in range(10):
                            world.effects.emit("hit", world.player.x + 40, world.player.y, damage=1)
                    step = world.effects.update(1 / 60)
                    if step > 0:
                        world.update(step)
                    audio.play_events(events)
                    music.updatevolume()
                    render_world(screen, world, fonts)
                    pygame.display.flip()
                    if index >= 20:
                        times.append((perf_counter() - start) * 1000)
                        intervals.append(interval)
                record = {"profile": profile, "requested_buffer": buffer,
                          "mixer": pygame.mixer.get_init(), "voices": len(audio._channels),
                          "frames": frames, "cpu_median_ms": round(statistics.median(times), 3),
                          "cpu_p95_ms": round(sorted(times)[int(.95 * len(times))], 3),
                          "frame_p95_ms": sorted(intervals)[int(.95 * len(intervals))],
                          "frames_over_20ms": sum(value > 20 for value in intervals),
                          "music_volume_calls": volume.call_count,
                          "nominal_buffer_ms_not_measured_latency": round(buffer / 44100 * 1000, 3),
                          "music_busy_at_end": bool(pygame.mixer.music.get_busy())}
                results.append(record)
            music.close()
            audio.close()
            pygame.quit()
    return {"environment": "CPython + SDL dummy; no audible capture, no browser/WASM",
            "results": results}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frames", type=int, default=120)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.frames < 20:
        parser.error("--frames deve ser pelo menos 20")
    data = benchmark(args.frames)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(json.dumps(data))

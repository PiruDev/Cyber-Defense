"""Reproducible local sprite production; never modifies the approved source.

Run from the AgentOS root with .venv/Scripts/python.exe.
Only Pygame is used; all new art is derived from the existing SENTINEL pilot
or drawn here as original digital tiles. No image service or third-party art.
"""

from pathlib import Path
import hashlib
import json

import pygame


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "assets/sprites/player/sentinel_idle.png"
FRAME_SIZE = 48


def highlight(frame, phase):
    """One-pixel glints, using only the pilot's existing opaque palette."""
    if phase == 0:
        return
    for y in range(4, 29):
        for x in range(18, 29):
            pixel = frame.get_at((x, y))
            if pixel.a and tuple(pixel[:3]) == (73, 233, 245):
                if (x + y + phase * 2) % 7 == 0:
                    frame.set_at((x, y), (172, 247, 255, 255))


def player_sheets():
    source = pygame.image.load(str(SOURCE))
    assert source.get_size() == (48, 48)
    original_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    outputs = []
    for action, count, duration in (("idle", 4, 150), ("move", 6, 100)):
        sheet = pygame.Surface((48 * count, 48), pygame.SRCALPHA, 32)
        for index in range(count):
            frame = pygame.Surface((48, 48), pygame.SRCALPHA, 32)
            if action == "idle":
                frame.blit(source, (0, 0))
            else:
                # The upper body remains centered on the same 24px pivot.
                # Left/right leg strips travel one pixel in opposite phases.
                bob = (0, -1, -1, 0, -1, -1)[index]
                left_step = (0, -1, 0, 0, 1, 0)[index]
                right_step = -left_step
                frame.blit(source, (0, bob), pygame.Rect(0, 0, 48, 28))
                frame.blit(source, (0, 28 + left_step), pygame.Rect(0, 28, 24, 20))
                frame.blit(source, (24, 28 + right_step), pygame.Rect(24, 28, 24, 20))
            highlight(frame, index % 4)
            sheet.blit(frame, (index * 48, 0))
        target = ROOT / f"assets/sprites/player/sentinel_{action}_sheet.png"
        pygame.image.save(sheet, str(target))
        outputs.append(dict(file=target.relative_to(ROOT).as_posix(),
                            frame_size=[48, 48], frames=count, pivot=[24, 24],
                            facing="south", directions=["south"],
                            durations_ms=[duration] * count, loop=True))
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == original_hash
    return outputs


def floor_tiles():
    outputs = []
    for variant in ("grid", "circuit", "panel"):
        tile = pygame.Surface((40, 40), pygame.SRCALPHA, 32)
        tile.fill((8, 17, 33, 255))
        pygame.draw.line(tile, (16, 36, 58), (0, 0), (39, 0))
        pygame.draw.line(tile, (16, 36, 58), (0, 0), (0, 39))
        pygame.draw.rect(tile, (12, 25, 43), (4, 4, 32, 32), 1)
        if variant == "circuit":
            pygame.draw.lines(tile, (21, 60, 76), False,
                              [(0, 14), (9, 14), (15, 20), (29, 20), (29, 39)], 1)
            pygame.draw.lines(tile, (15, 43, 62), False,
                              [(0, 20), (7, 20), (13, 26), (23, 26), (23, 39)], 1)
            pygame.draw.rect(tile, (31, 77, 88), (12, 17, 3, 3))
            pygame.draw.rect(tile, (31, 77, 88), (27, 19, 4, 3), 1)
        elif variant == "panel":
            pygame.draw.rect(tile, (10, 21, 38), (7, 8, 26, 23))
            pygame.draw.rect(tile, (18, 39, 57), (7, 8, 26, 23), 1)
            for x, y in ((10, 11), (29, 11), (10, 27), (29, 27)):
                pygame.draw.rect(tile, (27, 51, 65), (x, y, 2, 2))
            pygame.draw.lines(tile, (16, 43, 61), False,
                              [(14, 13), (21, 13), (25, 17), (25, 24)], 1)
            pygame.draw.line(tile, (26, 67, 77), (14, 24), (20, 24))
        target = ROOT / f"assets/sprites/environment/digital_{variant}_tile.png"
        pygame.image.save(tile, str(target))
        outputs.append(dict(file=target.relative_to(ROOT).as_posix(), size=[40, 40],
                            frames=1, world_anchored=True))
    return outputs


def preview():
    canvas = pygame.Surface((720, 360))
    canvas.fill((5, 9, 22))
    for row, (action, count) in enumerate((("idle", 4), ("move", 6))):
        sheet = pygame.image.load(str(ROOT / f"assets/sprites/player/sentinel_{action}_sheet.png"))
        for index in range(count):
            cell = sheet.subsurface((index * 48, 0, 48, 48))
            canvas.blit(pygame.transform.scale(cell, (96, 96)), (12 + index * 116, 12 + row * 112))
    for index, name in enumerate(("grid", "circuit", "panel")):
        tile = pygame.image.load(str(ROOT / f"assets/sprites/environment/digital_{name}_tile.png"))
        canvas.blit(pygame.transform.scale(tile, (80, 80)), (20 + index * 96, 260))
    pygame.image.save(canvas, str(Path(__file__).resolve().parent / "player_floor_preview.png"))


def main():
    players = player_sheets()
    tiles = floor_tiles()
    preview()
    manifest = dict(source="assets/sprites/player/sentinel_idle.png",
                    source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                    players=players, tiles=tiles)
    destination = Path(__file__).resolve().parent / "asset_manifest.json"
    destination.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest))


if __name__ == "__main__":
    main()

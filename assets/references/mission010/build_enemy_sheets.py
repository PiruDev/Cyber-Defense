"""Prepara os sprites originais da MISSÃO 010; somente Pygame, sem janela/rede.

Fontes image_gen são preservadas. O espadachim é redesenhado na grade top-down
para corrigir a perspectiva da fonte. Destinos existentes exigem --overwrite.
"""

from argparse import ArgumentParser
import json
from math import atan2, cos, hypot, pi, sin
from pathlib import Path

import pygame


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DEST = ROOT / "assets/sprites/enemies"
INK = (7, 16, 31)
WHITE = (226, 247, 255)
PALETTES = {
    "basic": [INK, (30, 19, 40), (61, 27, 53), (101, 28, 59), (159, 49, 85), (202, 49, 91), (243, 86, 145), (255, 120, 132), (255, 182, 153), (255, 219, 178), WHITE, (76, 65, 88)],
    "swordsman": [INK, (28, 26, 43), (48, 39, 60), (80, 37, 61), (123, 43, 70), (174, 51, 76), (229, 61, 83), (255, 91, 100), (255, 159, 145), WHITE, (125, 59, 140), (194, 79, 180)],
    "archer": [INK, (35, 22, 43), (63, 25, 54), (105, 28, 66), (157, 43, 88), (204, 59, 111), (240, 92, 133), (158, 92, 47), (211, 142, 64), (243, 202, 117), (255, 230, 166), WHITE],
    "worm": [INK, (37, 29, 25), (64, 48, 25), (95, 67, 27), (131, 92, 33), (167, 122, 43), (205, 155, 59), (243, 202, 117), (255, 224, 144), (255, 244, 205), WHITE, (75, 65, 52)],
    "rootkit": [INK, (29, 19, 46), (52, 35, 79), (76, 43, 110), (112, 69, 166), (155, 85, 202), (196, 78, 209), (236, 103, 221), (255, 153, 240), WHITE, (162, 116, 63), (243, 202, 117)],
}


def canvas(size):
    return pygame.Surface((size, size), pygame.SRCALPHA, 32)


def quantized(source, size, fit, palette):
    bounds = source.get_bounding_rect(min_alpha=128)
    ratio = min(fit[0] / bounds.width, fit[1] / bounds.height)
    width, height = max(1, round(bounds.width * ratio)), max(1, round(bounds.height * ratio))
    reduced = pygame.transform.scale(source.subsurface(bounds), (width, height))
    result = canvas(size)
    ox, oy = (size - width) // 2, (size - height) // 2
    color_cache = {}
    for y in range(height):
        for x in range(width):
            color = reduced.get_at((x, y))
            if color.a < 128:
                continue
            rgb = tuple(color[:3])
            if rgb not in color_cache:
                color_cache[rgb] = min(palette, key=lambda p: 2 * (rgb[0] - p[0]) ** 2 + 3 * (rgb[1] - p[1]) ** 2 + (rgb[2] - p[2]) ** 2)
            result.set_at((ox + x, oy + y), (*color_cache[rgb], 255))
    return result


def polygon(surface, points, color, outline=True):
    pygame.draw.polygon(surface, color, points)
    if outline:
        pygame.draw.polygon(surface, INK, points, 1)


def swordsman(state, index, count):
    """Pose ortográfica original: cabeça à direita, ombros acima/abaixo."""
    result = canvas(64)
    p = PALETTES["swordsman"]
    phase = index / max(1, count - 1)
    foot = round(sin(index * 2 * pi / max(1, count)) * 2) if state == "move" else 0
    # Treads e ombreiras, separados por cabos/encaixes visíveis.
    for side in (-1, 1):
        y = 32 + side * 13
        x = 23 + (foot if side == 1 else -foot)
        polygon(result, [(x - 7, y - 5), (x + 7, y - 5), (x + 9, y), (x + 7, y + 5), (x - 7, y + 5)], p[2])
        pygame.draw.line(result, p[4], (x - 4, y - 3), (x + 5, y - 3), 2)
        for tread in (-3, 0, 3):
            pygame.draw.line(result, p[1], (x + tread, y), (x + tread, y + 3), 1)
        polygon(result, [(25, y - 6), (38, y - 6), (42, y), (38, y + 6), (25, y + 6), (22, y)], p[3])
        pygame.draw.line(result, p[6], (27, y - 4), (35, y - 4), 1)
    polygon(result, [(18, 23), (27, 19), (37, 23), (40, 32), (37, 41), (27, 45), (18, 41), (15, 32)], p[2])
    polygon(result, [(21, 24), (30, 22), (35, 27), (35, 37), (30, 42), (21, 40)], p[4])
    pygame.draw.line(result, p[5], (21, 25), (29, 24), 1)
    pygame.draw.line(result, p[10], (19, 28), (19, 37), 1)
    pygame.draw.line(result, p[11], (20, 28), (20, 33), 1)
    # Capacete visto pela coroa; visor de frente no extremo leste.
    polygon(result, [(31, 25), (39, 25), (46, 30), (46, 34), (39, 39), (31, 39), (28, 32)], p[2])
    pygame.draw.line(result, p[5], (33, 26), (39, 27), 1)
    pygame.draw.line(result, p[7], (43, 30), (43, 34), 2)
    pygame.draw.line(result, WHITE, (44, 31), (44, 32), 1)
    pygame.draw.rect(result, p[6 + (index % 2)], (27, 29, 4, 6))
    # Lâmina e punho acompanham a pose; a hitbox permanece no jogo.
    angle = -.25
    if state == "windup":
        angle = -.85 - phase * .45
    elif state == "attack":
        angle = -.65 + phase * 1.25
    origin = (40, 41)
    tip = (round(origin[0] + cos(angle) * 20), round(origin[1] + sin(angle) * 20))
    pygame.draw.line(result, INK, origin, tip, 5)
    pygame.draw.line(result, p[6], origin, tip, 3)
    pygame.draw.line(result, p[8] if state != "windup" else p[7], origin, tip, 1)
    pygame.draw.rect(result, p[10], (37, 39, 6, 5))
    pygame.draw.line(result, p[8], (39, 38), (42, 43), 1)
    if state == "attack":
        for radius in (22, 24):
            pts = [(round(32 + cos(a) * radius), round(32 + sin(a) * radius)) for a in (-.8 + phase * .5, -.4 + phase * .5, phase * .5)]
            pygame.draw.lines(result, p[6], False, pts, 1)
    return result


def warp(base, state, index, count, kind):
    size = base.get_width()
    result = canvas(size)
    center = size // 2
    p = PALETTES["worm" if kind.startswith("worm_") else kind]
    phase = index / max(1, count - 1)
    death = state in ("death", "rupture")
    for y in range(size):
        for x in range(size):
            color = base.get_at((x, y))
            if not color.a:
                continue
            nx, ny = x, y
            if death:
                group = (x // 3 * 11 + y // 3 * 7) % 11
                if group < round(phase * 9):
                    continue
                angle = atan2(y - center, x - center)
                radius = phase * min(8, size * .09)
                nx += round(cos(angle) * radius)
                ny += round(sin(angle) * radius)
                if (x + y + index) % 7 == 0:
                    color = pygame.Color(*p[-2], 255)
            elif state == "move":
                wave = sin(index * 2 * pi / count)
                if kind.startswith("worm_"):
                    ny += round(sin(x * .18 + index * 2 * pi / count) * 1.3)
                elif kind == "rootkit":
                    if abs(y - center) > 20:
                        nx += round(wave * (1 if y > center else -1))
                else:
                    if abs(y - center) > 9:
                        nx += round(wave * (1 if y > center else -1))
                    ny += (0, 1, 1, 0, -1, -1)[index % 6]
            elif state == "idle":
                # Pulsar só luzes já existentes: não pintar hachura sobre placas.
                if (hypot(x - center, y - center) < size * .22
                        and max(color[:3]) >= 190 and min(color[:3]) >= 55
                        and index in (1, 2)):
                    color = pygame.Color(*p[7 + (index == 2)], 255)
                if index == 3 and y < center - size * .2:
                    ny += 1
            elif state == "hurt":
                if index == 0 and (x + y) % 3:
                    color = pygame.Color(*WHITE, 255)
                elif index == 1:
                    nx -= 1
            elif state == "windup":
                if x > center + size * .08:
                    nx -= index
                if (hypot(x - center, y - center) < size * (.12 + .02 * index)
                        and max(color[:3]) >= 190 and min(color[:3]) >= 55):
                    color = pygame.Color(*p[8 + index % 2], 255)
            elif state == "attack":
                if x > center:
                    nx += (1, 0, -1, 0)[index % 4]
                if abs(y - center) <= 2 and x > center:
                    color = pygame.Color(*WHITE if index == 0 else p[7], 255)
            elif state == "new_head":
                if x > center:
                    nx += index - 1
                if hypot(x - center, y - center) < 11 and max(color[:3]) >= 190:
                    color = pygame.Color(*(p[8] if index == 0 else p[7]), 255)
            if 1 <= nx < size - 1 and 1 <= ny < size - 1:
                result.set_at((nx, ny), color)
    # Acende trilhas e arma; detalhes avançam por pixels inteiros.
    if state == "windup" and kind in ("archer", "rootkit"):
        cx = min(size - 4, center + round(size * .3))
        pygame.draw.circle(result, p[8], (cx, center), 2 + index, 1)
    if state == "attack" and kind in ("archer", "rootkit"):
        start = center + round(size * .23)
        end = min(size - 3, start + 4 + 3 * (count - index))
        pygame.draw.line(result, p[9], (start, center), (end, center), 2 if kind == "rootkit" else 1)
        pygame.draw.line(result, p[7], (end - 2, center - 2), (end, center), 1)
    return result


def load_bases():
    result = {}
    for kind, size, fit in (("basic", 48, (36, 36)), ("archer", 48, (38, 34)), ("rootkit", 96, (76, 76))):
        result[kind] = quantized(pygame.image.load(str(HERE / f"{kind}_source.png")), size, fit, PALETTES[kind])
    worm = pygame.image.load(str(HERE / "worm_source.png"))
    rects = sorted(pygame.mask.from_surface(worm, 128).get_bounding_rects(), key=lambda rect: rect.width * rect.height, reverse=True)[:3]
    rects.sort(key=lambda rect: rect.x)
    if len(rects) != 3:
        raise ValueError("A fonte da minhoca precisa conter três peças isoladas.")
    for kind, bounds, fit in zip(("worm_head", "worm_body", "worm_tail"), rects, ((48, 44), (44, 44), (48, 40))):
        base = quantized(worm.subsurface(bounds), 64, fit, PALETTES["worm"])
        # Cauda afunila para trás; frente lógica leste aponta para o elo anterior.
        result[kind] = pygame.transform.flip(base, True, False) if kind == "worm_tail" else base
    result["swordsman"] = swordsman("idle", 0, 4)
    return result


def clips(kind):
    if kind.startswith("worm_"):
        result = {"idle": (4, 600, True), "move": (4, 400, True), "hurt": (2, 100, False), "rupture": (4, 300, False)}
        if kind == "worm_head":
            result.update(new_head=(3, 150, False), death=(6, 450, False))
        return result
    result = {"idle": (4, 600, True), "move": (6, 600, True), "hurt": (2, 100, False), "death": (6 if kind == "rootkit" else 5, 450 if kind == "rootkit" else 300, False)}
    if kind != "basic":
        result.update(windup=(3, {"swordsman":350,"archer":450,"rootkit":650}[kind], False), attack=(4 if kind == "rootkit" else 3, 200 if kind == "rootkit" else 140, False))
    return result


def durations(count, total):
    base, remainder = divmod(total, count)
    return [base + (1 if i < remainder else 0) for i in range(count)]


def build(overwrite=False):
    bases = load_bases()
    manifest = {"version": 1, "types": {}}
    output_frames = {}
    for kind, base in bases.items():
        size = base.get_width()
        folder = "virus_basic" if kind == "basic" else "segmented_worm" if kind.startswith("worm_") else "rootkit_boss" if kind == "rootkit" else kind
        prefix = kind.removeprefix("worm_") + "_" if kind.startswith("worm_") else ""
        spec = {"frame_size": [size, size], "pivot": [size // 2, size // 2], "facing": "east", "palette": ["#%02X%02X%02X" % c for c in PALETTES["worm" if kind.startswith("worm_") else kind]], "states": {}}
        for state, (count, total, loop) in clips(kind).items():
            path = DEST / folder / f"{prefix}{state}.png"
            if path.exists() and not overwrite:
                raise FileExistsError(f"Destino existente preservado: {path}")
            frames = []
            for i in range(count):
                original = swordsman(state, i, count) if kind == "swordsman" and state in ("idle", "move", "windup", "attack") else base
                if kind == "worm_head" and state == "new_head":
                    if i == 0:
                        original = bases["worm_body"]
                    elif i == 1:
                        original = bases["worm_body"].copy()
                        original.fill((0, 0, 0, 0), (32, 0, 32, 64))
                        original.blit(base, (32, 0), (32, 0, 32, 64))
                frame = warp(original, state, i, count, kind)
                if not frame.get_bounding_rect():
                    raise ValueError((kind, state, i, "vazio"))
                frames.append(frame)
            sheet = pygame.Surface((size * count, size), pygame.SRCALPHA, 32)
            for i, frame in enumerate(frames):
                sheet.blit(frame, (i * size, 0))
            path.parent.mkdir(parents=True, exist_ok=True)
            pygame.image.save(sheet, str(path))
            spec["states"][state] = {"file": path.relative_to(DEST).as_posix(), "frames": count, "durations_ms": durations(count, total), "loop": loop}
            output_frames[kind, state] = frames
        manifest["types"][kind] = spec
    target = DEST / "manifest.json"
    if target.exists() and not overwrite:
        raise FileExistsError(target)
    target.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    atlas(output_frames)
    print(f"Produzidos {len(output_frames)} PNGs / {sum(len(f) for f in output_frames.values())} frames / 7 tipos")


def atlas(frames):
    pygame.font.init()
    font = pygame.font.Font(None, 23)
    small = pygame.font.Font(None, 18)
    kinds = ["basic", "swordsman", "archer", "worm_head", "worm_body", "worm_tail", "rootkit"]
    board = pygame.Surface((1120, 100 + len(kinds) * 150))
    board.fill((5, 9, 22))
    board.blit(font.render("CYBER DEFENSE / ENEMY SPRITES / MISSAO 010", True, (226, 247, 255)), (28, 20))
    board.blit(small.render("Native 1x | enlarged nearest 2x | idle / move / windup / attack / hurt / death or rupture", True, (121, 159, 185)), (28, 50))
    for row, kind in enumerate(kinds):
        y = 88 + row * 150
        board.blit(font.render(kind.upper(), True, (243, 202, 117)), (24, y + 8))
        keys = [(kind, state) for state in ("idle", "move", "windup", "attack", "hurt", "rupture", "new_head", "death") if (kind, state) in frames]
        idle = frames[keys[0]][0]
        board.blit(idle, idle.get_rect(center=(95, y + 85)))
        for col, key in enumerate(keys):
            x = 225 + col * 145
            sample = frames[key][min(1, len(frames[key]) - 1)]
            if kind == "rootkit":
                shown = sample
            else:
                shown = pygame.transform.scale(sample, (sample.get_width() * 2, sample.get_height() * 2))
            board.blit(shown, shown.get_rect(center=(x, y + 74)))
            board.blit(small.render(key[1], True, (226, 247, 255)), (x - 32, y + 130))
    pygame.image.save(board, str(HERE / "enemy_atlas.png"))


if __name__ == "__main__":
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--overwrite", action="store_true")
    build(parser.parse_args().overwrite)

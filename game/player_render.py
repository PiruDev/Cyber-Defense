"""SENTINEL-01: sprite original, animação e rotações nearest-neighbor em cache."""

from functools import lru_cache
from math import atan2, pi
from pathlib import Path

from .visual_config import PLAYER_SCALE

ROOT = Path(__file__).resolve().parents[1]
FRAME_SIZE = 48
PIVOT = (24, 24)


@lru_cache(maxsize=2)
def _frames(moving):
    import pygame

    name = "sentinel_move_sheet.png" if moving else "sentinel_idle_sheet.png"
    path = ROOT / "assets/sprites/player" / name
    if not path.is_file():
        path = ROOT / "assets/sprites/player/sentinel_idle.png"
    # Erros de um arquivo presente não são mascarados por um retângulo.
    sheet = pygame.image.load(str(path))
    if sheet.get_height() != FRAME_SIZE or sheet.get_width() % FRAME_SIZE:
        raise ValueError(f"Sprite SENTINEL-01 incompatível: {path}")
    return tuple(sheet.subsurface((index * FRAME_SIZE, 0, FRAME_SIZE, FRAME_SIZE)).copy()
                 for index in range(sheet.get_width() // FRAME_SIZE))


@lru_cache(maxsize=256)
def _pose(moving, index, direction, flash, scale):
    import pygame

    image = _frames(moving)[index]
    if flash:
        image = image.copy()
        image.fill((80, 80, 80, 0), special_flags=pygame.BLEND_RGB_ADD)
    size = round(FRAME_SIZE * scale)
    image = pygame.transform.scale(image, (size, size))
    # O desenho original olha para sul; a rotação é discreta em oito direções.
    image = pygame.transform.rotate(image, 90 - direction * 45)
    return image, (image.get_width() / 2, image.get_height() / 2)


def player_frame(player, elapsed, *, moving=False, flash=False, scale=PLAYER_SCALE):
    direction = round(atan2(player.facing_y, player.facing_x) / (pi / 4)) % 8
    frames = _frames(bool(moving))
    index = int(elapsed / (.10 if moving else .15)) % len(frames)
    return _pose(bool(moving), index, direction, bool(flash), scale)


def render_player(surface, world):
    import pygame

    player = world.player
    image, pivot = player_frame(player, world.elapsed, moving=world.player_moving,
                               flash=world.damage_cooldown > 0 and int(world.elapsed * 14) % 2)
    x, y = round(player.x), round(player.y)
    pygame.draw.ellipse(surface, (5, 12, 23), (x - 20, y + 14, 40, 13))
    if player.overclock_timer > 0:
        pygame.draw.circle(surface, (133, 65, 169), (x, y), 29, 1)
    surface.blit(image, (round(x - pivot[0]), round(y - pivot[1])))

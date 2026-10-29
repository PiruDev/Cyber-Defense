"""Piso digital estático em tiles; composição única por tamanho de arena."""

from functools import lru_cache
from pathlib import Path

from .visual_config import FLOOR_TILE_SIZE


@lru_cache(maxsize=1)
def _tiles():
    import pygame

    root = Path(__file__).resolve().parents[1] / "assets/sprites/environment"
    return tuple(pygame.image.load(str(root / name)) for name in (
        "digital_grid_tile.png", "digital_circuit_tile.png", "digital_panel_tile.png"))


@lru_cache(maxsize=2)
def floor_surface(arena):
    import pygame

    left, top, width, height = map(int, arena)
    floor = pygame.Surface((left + width, top + height))
    floor.fill((8, 17, 33))
    tiles = _tiles()
    for row, y in enumerate(range(top, top + height, FLOOR_TILE_SIZE)):
        for col, x in enumerate(range(left, left + width, FLOOR_TILE_SIZE)):
            code = (col * 73856093 ^ row * 19349663) % 19
            floor.blit(tiles[1 if code == 0 else 2 if code in (4, 11) else 0], (x, y))
    center = (left + width // 2, top + height // 2)
    for radius in (64, 76):
        pygame.draw.circle(floor, (23, 64, 81), center, radius, 1)
    pygame.draw.line(floor, (31, 48, 53), (center[0] - 90, center[1]), (center[0] + 90, center[1]))
    pygame.draw.line(floor, (31, 48, 53), (center[0], center[1] - 90), (center[0], center[1] + 90))
    pygame.draw.rect(floor, (26, 79, 99), arena, 3)
    return floor

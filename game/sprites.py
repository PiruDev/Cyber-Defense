"""Pequenos sprites procedurais: nenhuma janela ou imagem criada ao importar."""

import math
from functools import lru_cache

from .combat import ATTACK_ANGLE, ATTACK_DURATION


def sword_angle(facing_x, facing_y, attack_timer):
    """Ângulo em radianos de um arco suave, usando a direção fixada no golpe."""
    progress = max(0.0, min(1.0, 1.0 - attack_timer / ATTACK_DURATION))
    eased = progress * progress * (3.0 - 2.0 * progress)
    return math.atan2(facing_y, facing_x) + math.radians(ATTACK_ANGLE * (eased - 0.5))


@lru_cache(maxsize=8)
def potion_sprite(size=48):
    """Pacote de reparo digital, compartilhado por drops e inventário."""
    import pygame

    sprite = pygame.Surface((48, 48), pygame.SRCALPHA)
    points = [(14, 5), (35, 5), (42, 12), (42, 36), (35, 43), (12, 43), (6, 37), (6, 13)]
    pygame.draw.polygon(sprite, (13, 49, 66), points)
    pygame.draw.polygon(sprite, (93, 239, 225), points, 2)
    pygame.draw.rect(sprite, (27, 87, 104), (12, 13, 25, 23), border_radius=4)
    pygame.draw.rect(sprite, (227, 251, 255), (21, 16, 7, 17), border_radius=1)
    pygame.draw.rect(sprite, (227, 251, 255), (16, 21, 17, 7), border_radius=1)
    pygame.draw.line(sprite, (235, 131, 236), (11, 37), (22, 37), 2)
    if size != 48:
        return pygame.transform.smoothscale(sprite, (size, size))
    return sprite


@lru_cache(maxsize=8)
def overclock_sprite(size=48):
    import pygame
    sprite = pygame.Surface((48, 48), pygame.SRCALPHA)
    pygame.draw.polygon(sprite, (58, 28, 87), [(24, 3), (45, 24), (24, 45), (3, 24)])
    pygame.draw.polygon(sprite, (233, 117, 248), [(24, 3), (45, 24), (24, 45), (3, 24)], 2)
    pygame.draw.polygon(sprite, (245, 221, 128), [(27, 8), (13, 26), (23, 26), (20, 40), (36, 20), (26, 20)])
    return sprite if size == 48 else pygame.transform.smoothscale(sprite, (size, size))


@lru_cache(maxsize=1)
def sword_sprite():
    """Espada voltada para a direita; a ponta fica a 70 px do jogador."""
    import pygame

    sprite = pygame.Surface((72, 24), pygame.SRCALPHA)
    pygame.draw.polygon(sprite, (16, 33, 40), ((20, 7), (60, 7), (71, 12), (60, 17), (20, 17)))
    pygame.draw.polygon(sprite, (214, 235, 235), ((22, 8), (60, 8), (70, 12), (60, 16), (22, 16)))
    pygame.draw.polygon(sprite, (146, 181, 189), ((22, 12), (70, 12), (60, 16), (22, 16)))
    pygame.draw.line(sprite, (255, 255, 246), (24, 9), (60, 9), 1)
    pygame.draw.rect(sprite, (36, 72, 105), (6, 9, 14, 6), border_radius=2)
    for x in (9, 13, 17):
        pygame.draw.line(sprite, (173, 133, 71), (x, 9), (x, 14))
    pygame.draw.rect(sprite, (243, 202, 117), (19, 3, 4, 18), border_radius=2)
    pygame.draw.circle(sprite, (243, 202, 117), (5, 12), 4)
    return sprite

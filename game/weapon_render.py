"""Animações procedurais das armas, centralizadas por tipo de equipamento."""

import math
from functools import lru_cache

from .sprites import sword_angle, sword_sprite
from .slash_render import render_slash


@lru_cache(maxsize=4)
def weapon_sprite(weapon_id):
    import pygame

    if weapon_id in ("sword", "katana"):
        image = sword_sprite().copy()
        if weapon_id == "katana":
            pygame.draw.line(image, (117, 241, 255), (23, 8), (64, 8), 2)
        return image
    if weapon_id == "bow":
        image = pygame.Surface((54, 54), pygame.SRCALPHA)
        points = [(19 + math.cos(math.radians(a)) * 28, 27 + math.sin(math.radians(a)) * 25)
                  for a in range(-75, 76, 5)]
        pygame.draw.lines(image, (72, 231, 244), False, points, 4)
        pygame.draw.line(image, (210, 244, 255), points[0], points[-1], 1)
        pygame.draw.rect(image, (231, 134, 249), (43, 21, 5, 12), border_radius=2)
        return image
    image = pygame.Surface((112, 22), pygame.SRCALPHA)
    pygame.draw.line(image, (44, 98, 124), (2, 11), (94, 11), 6)
    pygame.draw.line(image, (87, 234, 242), (2, 10), (95, 10), 2)
    pygame.draw.polygon(image, (226, 247, 255), [(111, 11), (91, 2), (96, 11), (91, 20)])
    pygame.draw.line(image, (240, 112, 235), (87, 4), (87, 18), 3)
    return image


def _slash(surface, world, image_factory, angle_function):
    import pygame

    player = world.player
    config = world.weapons.config
    x, y = player.x, player.y
    reach = config.reach * (1 + .15 * player.upgrades.get("range", 0))
    reverse = False
    if config.id == "sword":
        angle = angle_function(world.attack_facing_x, world.attack_facing_y, world.attack_timer)
        image = image_factory()
    else:
        elapsed = config.animation_duration - world.attack_timer
        reverse = elapsed >= .10
        phase = min(1, elapsed / .10) if not reverse else min(1, (elapsed - .10) / .14)
        phase = phase * phase * (3 - 2 * phase)
        sweep = -50 + 100 * phase if not reverse else 50 - 100 * phase
        angle = math.atan2(world.attack_facing_y, world.attack_facing_x) + math.radians(sweep)
        image = weapon_sprite("katana")
    elapsed = config.animation_duration - world.attack_timer
    duration = .10 if config.id == "katana" and not reverse else .14
    progress = (elapsed - (.10 if reverse else 0)) / duration
    render_slash(surface, (x, y), math.atan2(world.attack_facing_y, world.attack_facing_x),
                 max(0, min(1, progress)), reach, reverse=reverse,
                 reduced=world.effects.settings.particle_scale < 1)
    scale = reach / 70
    image = pygame.transform.scale(image, (max(1, round(image.get_width() * scale)),
                                          max(1, round(image.get_height() * scale))))
    image = pygame.transform.rotate(image, -math.degrees(angle))
    center = (x + math.cos(angle) * 36 * scale, y + math.sin(angle) * 36 * scale)
    surface.blit(image, image.get_rect(center=center))


def _bow(surface, world, *_):
    import pygame

    angle = math.atan2(world.attack_facing_y, world.attack_facing_x)
    image = pygame.transform.rotate(weapon_sprite("bow"), -math.degrees(angle))
    surface.blit(image, image.get_rect(center=(world.player.x + math.cos(angle) * 24,
                                               world.player.y + math.sin(angle) * 24)))


def _spear(surface, world, *_):
    import pygame

    config = world.weapons.config
    elapsed = config.animation_duration - world.attack_timer
    extension = min(1, elapsed / .08) if elapsed < .08 else max(0, 1 - (elapsed - .08) / .14)
    reach = config.reach * (1 + .15 * world.player.upgrades.get("range", 0))
    length = 30 + (reach - 30) * extension
    image = pygame.transform.scale(weapon_sprite("spear"), (max(1, round(length)), 22))
    angle = math.atan2(world.attack_facing_y, world.attack_facing_x)
    image = pygame.transform.rotate(image, -math.degrees(angle))
    surface.blit(image, image.get_rect(center=(world.player.x + math.cos(angle) * length / 2,
                                               world.player.y + math.sin(angle) * length / 2)))


_RENDERERS = {"sword": _slash, "katana": _slash, "bow": _bow, "spear": _spear}


def render_weapon(surface, world, *, image_factory=sword_sprite, angle_function=sword_angle):
    if world.attack_timer > 0:
        _RENDERERS[world.weapon_id](surface, world, image_factory, angle_function)

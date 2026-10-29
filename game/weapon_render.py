"""Animações procedurais das armas, centralizadas por tipo de equipamento."""

import math
from functools import lru_cache
from pathlib import Path

from .sprites import sword_angle, sword_sprite
from .slash_render import render_slash
from .balance import SPEAR_RETURN_DURATION, SPEAR_SPIN_DURATION, SPEAR_SPIN_REACH


@lru_cache(maxsize=6)
def weapon_sprite(weapon_id):
    import pygame

    if weapon_id in ("longbow", "returning_spear"):
        return pygame.image.load(str(Path(__file__).resolve().parents[1]
                                     / "assets/sprites/weapons" / (weapon_id + ".png")))
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
    image = pygame.transform.rotate(weapon_sprite(world.weapon_id), -math.degrees(angle))
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


_RENDERERS = {"sword": _slash, "katana": _slash, "bow": _bow, "longbow": _bow, "spear": _spear}


def _rest(surface, world):
    import pygame

    player = world.player
    angle = math.atan2(player.facing_y, player.facing_x)
    image = weapon_sprite(world.weapon_id)
    image = pygame.transform.scale(image, (round(image.get_width() * .65), round(image.get_height() * .65)))
    image = pygame.transform.rotate(image, -math.degrees(angle - .55))
    center = (player.x - math.sin(angle) * 24 + math.cos(angle) * 7,
              player.y + math.cos(angle) * 24 + math.sin(angle) * 7)
    surface.blit(image, image.get_rect(center=center))


def render_thrown_spear(surface, world):
    import pygame

    weapons = world.weapons
    spear = weapons.returning_spear
    if spear is not None:
        x, y = spear.x, spear.y
        angle = math.atan2(spear.projectile.vy, spear.projectile.vx)
        if spear.landed:
            pygame.draw.circle(surface, (62, 48, 91), (round(x), round(y)), 24, 1)
            pygame.draw.circle(surface, (116, 185, 202), (round(x), round(y)), 29, 1)
    elif weapons.return_timer > 0 and weapons.return_origin is not None:
        progress = 1 - weapons.return_timer / SPEAR_RETURN_DURATION
        origin = weapons.return_origin
        x = origin[0] + (world.player.x - origin[0]) * progress
        y = origin[1] + (world.player.y - origin[1]) * progress
        angle = math.atan2(world.player.y - origin[1], world.player.x - origin[0])
    else:
        return
    image = pygame.transform.scale(weapon_sprite("returning_spear"), (76, 15))
    image = pygame.transform.rotate(image, -math.degrees(angle))
    surface.blit(image, image.get_rect(center=(x, y)))


def _spin(surface, world):
    import pygame

    progress = 1 - world.weapons.spin_timer / SPEAR_SPIN_DURATION
    angle = progress * math.tau
    reach = SPEAR_SPIN_REACH * world.player.attack_range / 70
    render_slash(surface, (world.player.x, world.player.y), angle, .5, reach, half_angle=90,
                 reduced=world.effects.settings.particle_scale < 1)
    image = pygame.transform.rotate(weapon_sprite("returning_spear"), -math.degrees(angle))
    center = (world.player.x + math.cos(angle) * 44, world.player.y + math.sin(angle) * 44)
    surface.blit(image, image.get_rect(center=center))


def render_weapon(surface, world, *, image_factory=sword_sprite, angle_function=sword_angle):
    if world.weapons.spin_timer > 0:
        _spin(surface, world)
        return
    if world.weapons.returning_spear is not None or world.weapons.return_timer > 0:
        return
    if world.attack_timer > 0:
        renderer = _RENDERERS.get(world.weapon_id)
        if renderer is not None:
            renderer(surface, world, image_factory, angle_function)
    else:
        _rest(surface, world)

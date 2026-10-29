"""Desenho dos inimigos e projéteis; toda a IA permanece nos módulos de lógica."""

import math

from .sprites import sword_sprite
from .combat import ATTACK_DURATION
from .enemy_animation import choose_state, state_progress
from .enemy_assets import get_library
from .visual_config import enemy_scale, feedback_radius
from .slash_render import render_slash, render_windup


def _rootkit_telegraph(surface, enemy):
    import pygame

    x, y = int(enemy.x), int(enemy.y)
    magenta, cyan = (236, 103, 221), (73, 233, 245)
    angle = math.atan2(enemy.facing_y, enemy.facing_x)
    if enemy.telegraph_timer > 0 or enemy.attack_timer > 0:
        color = (224, 104, 174) if enemy.telegraph_timer > 0 else (255, 174, 221)
        if enemy.pattern == "cone":
            points = [(x, y)] + [(x + math.cos(angle + math.radians(a)) * enemy.attack_range,
                                   y + math.sin(angle + math.radians(a)) * enemy.attack_range)
                                  for a in range(round(-enemy.attack_angle / 2), round(enemy.attack_angle / 2) + 1, 5)] + [(x, y)]
            pygame.draw.lines(surface, color, False, points, 2)
        else:
            pygame.draw.circle(surface, (90, 44, 102), (x, y), 80, 2)
            for index in range(enemy.projectile_count):
                direction = index * 2 * math.pi / enemy.projectile_count
                pygame.draw.line(surface, color,
                                 (x + math.cos(direction) * 45, y + math.sin(direction) * 45),
                                 (x + math.cos(direction) * 150, y + math.sin(direction) * 150), 2)
    if enemy.entrance_timer > 0:
        pygame.draw.circle(surface, cyan, (x, y), round(45 + enemy.entrance_timer * 65), 2)


def _render_rootkit(surface, enemy):
    import pygame

    _rootkit_telegraph(surface, enemy)
    x, y = int(enemy.x), int(enemy.y)
    magenta, cyan = (236, 103, 221), (73, 233, 245)
    points = [(x + math.cos(math.pi / 4 * index + math.pi / 8) * 40,
               y + math.sin(math.pi / 4 * index + math.pi / 8) * 40) for index in range(8)]
    pygame.draw.polygon(surface, (47, 23, 70), points)
    pygame.draw.polygon(surface, magenta, points, 3)
    pygame.draw.rect(surface, (21, 42, 64), (x - 25, y - 25, 50, 50), border_radius=6)
    pygame.draw.rect(surface, (238, 249, 255) if enemy.hit_flash_timer > 0 else (163, 76, 197),
                     (x - 17, y - 17, 34, 34), border_radius=3)
    for offset in (-10, 0, 10):
        pygame.draw.line(surface, cyan, (x - 24, y + offset), (x - 32, y + offset), 2)
        pygame.draw.line(surface, cyan, (x + 24, y + offset), (x + 32, y + offset), 2)
    pygame.draw.rect(surface, (6, 14, 29), (x - 10, y - 8, 20, 7), border_radius=2)
    pygame.draw.line(surface, cyan, (x - 9, y + 8), (x + 7, y + 8), 2)


def _render_enemy_fallback(surface, enemy, *, effects=None):
    import pygame

    x, y, radius = int(enemy.x), int(enemy.y), int(enemy.radius)
    kind = getattr(enemy, "kind", "basic")
    if kind == "rootkit":
        _render_rootkit(surface, enemy)
        return
    angle = math.atan2(getattr(enemy, "facing_y", 1), getattr(enemy, "facing_x", 0))
    flash = enemy.hit_flash_timer > 0
    color = (231, 237, 235) if flash else (244, 113, 113)
    if kind == "worm":
        segments = enemy.segments
        for first, second in zip(segments, segments[1:]):
            pygame.draw.line(surface, (80, 74, 40), (first.x, first.y), (second.x, second.y), 17)
        for index in range(len(segments)):
            segment = segments[index]
            pos = (int(segment.x), int(segment.y))
            pygame.draw.circle(surface, (87, 65, 42), pos, int(segment.radius) + 3)
            pygame.draw.circle(surface, (243, 202, 117) if index == 0 else (166, 141, 82), pos, int(segment.radius))
            pygame.draw.circle(surface, (109, 84, 49), pos, max(3, int(segment.radius) - 7), 2)
            if index == 0:
                if flash:
                    pygame.draw.circle(surface, (231, 237, 235), pos, int(segment.radius) - 3)
                pygame.draw.circle(surface, (12, 19, 28), (pos[0] - 7, pos[1] - 5), 4)
                pygame.draw.circle(surface, (12, 19, 28), (pos[0] + 7, pos[1] - 5), 4)
                highlight = effects.head_highlights.get(id(enemy), 0) if effects else 0
                if highlight > 0:
                    pulse = round(6 * (1 - min(1, highlight / 0.15)))
                    pygame.draw.circle(surface, (255, 249, 205), pos, int(segment.radius) + 4 + pulse, 2)
    else:
        if getattr(enemy, "telegraph_timer", 0) > 0:
            if kind == "swordsman":
                render_windup(surface, (x, y), angle)
                pygame.draw.circle(surface, (243, 202, 117), (x, y - radius - 19), 3)
            elif kind == "archer":
                for distance in range(26, 146, 13):
                    pygame.draw.circle(surface, (244, 191, 99),
                                       (int(x + math.cos(angle) * distance), int(y + math.sin(angle) * distance)), 2)
        pygame.draw.ellipse(surface, (9, 19, 24), (x - radius, y + 8, radius * 2, 13))
        if kind == "target":
            pygame.draw.rect(surface, (15, 55, 75), (x - radius, y - radius, radius * 2, radius * 2), border_radius=5)
            pygame.draw.rect(surface, color if flash else (104, 214, 221), (x - radius, y - radius, radius * 2, radius * 2), 2, border_radius=5)
            pygame.draw.circle(surface, (104, 214, 221), (x, y), 8, 2)
        elif kind == "archer":
            if not flash:
                color = (130, 172, 224)
            pygame.draw.polygon(surface, (53, 75, 111), [(x, y - 22), (x + 20, y - 6), (x + 15, y + 18), (x - 15, y + 18), (x - 20, y - 6)])
            pygame.draw.circle(surface, color, (x, y), radius - 3)
            bow = [(x + math.cos(angle + math.radians(a)) * 25, y + math.sin(angle + math.radians(a)) * 25)
                   for a in range(-60, 61, 10)]
            pygame.draw.lines(surface, (243, 202, 117), False, bow, 3)
            pygame.draw.line(surface, (181, 195, 199), bow[0], bow[-1], 1)
        elif kind == "swordsman":
            pygame.draw.rect(surface, (102, 56, 75), (x - radius, y - radius, radius * 2, radius * 2), border_radius=6)
            pygame.draw.rect(surface, color, (x - radius + 4, y - radius + 3, radius * 2 - 8, radius * 2 - 6), border_radius=4)
            pygame.draw.line(surface, (37, 34, 44), (x - 9, y - 4), (x + 9, y - 4), 5)
            if getattr(enemy, "attack_timer", 0) > 0:
                swing = angle + math.radians(45 - 90 * min(1, enemy.attack_timer / ATTACK_DURATION))
                image = pygame.transform.rotate(pygame.transform.scale(sword_sprite(), (61, 20)), -math.degrees(swing))
                surface.blit(image, image.get_rect(center=(x + math.cos(swing) * 31, y + math.sin(swing) * 31)))
                render_slash(surface, (x, y), angle, 1 - enemy.attack_timer / ATTACK_DURATION,
                             60, theme="enemy", half_angle=45)
        else:
            for side in (-1, 1):
                pygame.draw.line(surface, (153, 68, 83), (x + side * 10, y - 4), (x + side * 23, y - 12), 3)
                pygame.draw.line(surface, (153, 68, 83), (x + side * 11, y + 7), (x + side * 23, y + 14), 3)
            pygame.draw.circle(surface, (116, 53, 72), (x, y), radius)
            pygame.draw.circle(surface, color, (x, y - 3), max(2, radius - 4))
        if kind != "target":
            pygame.draw.circle(surface, (12, 19, 28), (x - 5, y - 4), 3)
            pygame.draw.circle(surface, (12, 19, 28), (x + 5, y - 4), 3)
        if enemy.hp_bar_timer > 0:
            pygame.draw.rect(surface, (10, 19, 27), (x - 18, y - radius - 9, 36, 4), border_radius=2)
            hp_width = max(0, min(36, round(36 * enemy.hp / enemy.max_hp)))
            if hp_width:
                pygame.draw.rect(surface, color, (x - 18, y - radius - 9, hp_width, 4), border_radius=2)
    if enemy.stun_timer > 0:
        for offset in (-9, 0, 9):
            pygame.draw.circle(surface, (243, 202, 117), (x + offset, y - radius - 17 - (3 if offset == 0 else 0)), 2)


def _blit(surface, frame, x, y):
    image, pivot = frame
    surface.blit(image, (round(x - pivot[0]), round(y - pivot[1])))


def _telegraph(surface, enemy, angle):
    import pygame

    if enemy.kind == "rootkit":
        _rootkit_telegraph(surface, enemy)
        return
    if getattr(enemy, "telegraph_timer", 0) <= 0:
        return
    x, y = round(enemy.x), round(enemy.y)
    if enemy.kind == "swordsman":
        render_windup(surface, (x, y), angle)
        pygame.draw.circle(surface, (243, 202, 117), (x, y - round(feedback_radius(enemy)) - 12), 3)
    elif enemy.kind == "archer":
        for distance in range(26, 146, 13):
            pygame.draw.circle(surface, (244, 191, 99),
                               (round(x + math.cos(angle) * distance),
                                round(y + math.sin(angle) * distance)), 2)


def _feedback(surface, enemy):
    import pygame

    x, y, radius = round(enemy.x), round(enemy.y), round(feedback_radius(enemy))
    if enemy.kind not in ("worm", "rootkit") and enemy.hp_bar_timer > 0:
        pygame.draw.rect(surface, (10, 19, 27), (x - 18, y - radius - 9, 36, 4), border_radius=2)
        filled = round(36 * max(0, min(1, enemy.hp / enemy.max_hp))) if enemy.max_hp > 0 else 0
        if filled:
            color = (231, 237, 235) if enemy.hit_flash_timer > 0 else (244, 113, 113)
            pygame.draw.rect(surface, color, (x - 18, y - radius - 9, filled, 4), border_radius=2)
    if enemy.stun_timer > 0:
        for offset in (-9, 0, 9):
            pygame.draw.circle(surface, (243, 202, 117),
                               (x + offset, y - radius - 17 - (3 if offset == 0 else 0)), 2)


def _render_worm(surface, enemy, effects, animation_time, moving, motion_direction):
    import pygame

    library = get_library()
    segments, frames = enemy.segments, []
    if not segments:
        return True
    state = choose_state(enemy, moving)
    head_highlight = effects.head_highlights.get(id(enemy), 0) if effects else 0
    for index, segment in enumerate(segments):
        kind = "worm_head" if index == 0 else "worm_tail" if index == len(segments) - 1 else "worm_body"
        segment_state = "new_head" if index == 0 and head_highlight > 0 else state
        if index:
            direction = segments[index - 1].x - segment.x, segments[index - 1].y - segment.y
        elif motion_direction is not None and math.hypot(*motion_direction) > 1e-12:
            direction = motion_direction
        elif len(segments) > 1:
            direction = segment.x - segments[1].x, segment.y - segments[1].y
        else:
            direction = (1, 0)
        angle = math.atan2(direction[1], direction[0])
        duration = library.duration(kind, segment_state)
        if segment_state == "new_head":
            phase = duration * max(0, min(1, 1 - head_highlight / .15))
        else:
            phase = state_progress(enemy, segment_state, animation_time, duration)
        frame = library.frame(kind, segment_state, phase, angle, flash=enemy.hit_flash_timer > 0,
                              scale=enemy_scale(kind))
        if frame is None:
            return False
        frames.append((frame, segment.x, segment.y))
    for first, second in zip(segments, segments[1:]):
        pygame.draw.line(surface, (80, 74, 40), (first.x, first.y), (second.x, second.y), 17)
    if head_highlight > 0:
        pulse = round(6 * (1 - min(1, head_highlight / .15)))
        pygame.draw.circle(surface, (255, 249, 205),
                           (round(enemy.x), round(enemy.y)), round(enemy.radius) + 4 + pulse, 2)
    # Ordem de trilha: a cabeça e seu halo ficam sob a cauda nos cruzamentos.
    for frame, x, y in frames:
        _blit(surface, frame, x, y)
    _feedback(surface, enemy)
    return True


def render_enemy(surface, enemy, *, effects=None, animation_time=0, moving=None, motion_direction=None):
    """Render puro: o relógio e os sinais de movimento vêm do mundo."""
    import pygame

    kind = getattr(enemy, "kind", "basic")
    if kind == "worm":
        if not _render_worm(surface, enemy, effects, animation_time, moving, motion_direction):
            _render_enemy_fallback(surface, enemy, effects=effects)
        return
    if kind not in ("basic", "swordsman", "archer", "rootkit"):
        _render_enemy_fallback(surface, enemy, effects=effects)
        return
    if kind in ("swordsman", "archer", "rootkit"):
        direction = enemy.facing_x, enemy.facing_y
    else:
        direction = motion_direction if motion_direction is not None else (0, 1)
    angle = math.atan2(direction[1], direction[0])
    library = get_library()
    state = choose_state(enemy, moving)
    phase = state_progress(enemy, state, animation_time, library.duration(kind, state))
    frame = library.frame(kind, state, phase, angle, flash=enemy.hit_flash_timer > 0,
                          scale=enemy_scale(kind))
    if frame is None:
        _render_enemy_fallback(surface, enemy, effects=effects)
        return
    _telegraph(surface, enemy, angle)
    x, y, radius = round(enemy.x), round(enemy.y), round(enemy.radius)
    pygame.draw.ellipse(surface, (9, 19, 24), (x - radius, y + 8, radius * 2, 13))
    _blit(surface, frame, enemy.x, enemy.y)
    if kind == "swordsman" and enemy.attack_timer > 0:
        render_slash(surface, (enemy.x, enemy.y), angle, 1 - enemy.attack_timer / ATTACK_DURATION,
                     60, theme="enemy", half_angle=45,
                     reduced=effects is not None and effects.settings.particle_scale < 1)
    _feedback(surface, enemy)


def render_enemy_ghosts(surface, effects):
    """Corpos visuais após remoção lógica; não possuem colisão ou recompensa."""
    import pygame

    library = get_library()
    for ghost in effects.enemy_ghosts:
        if ghost.remaining <= 0:
            continue
        angle = math.atan2(ghost.direction[1], ghost.direction[0])
        duration = library.duration(ghost.kind, ghost.state)
        progress = max(0, min(1, 1 - ghost.remaining / ghost.total_life)) if ghost.total_life > 0 else 1
        frame = library.frame(ghost.kind, ghost.state, duration * progress, angle,
                              scale=enemy_scale(ghost.kind))
        if frame is not None:
            _blit(surface, frame, ghost.x, ghost.y)
        else:
            # Mesmo sem PNG, a morte continua legível como dispersão simples.
            radius = max(1, round((32 if ghost.kind == "rootkit" else 17) * (1 - progress)))
            pygame.draw.circle(surface, (144, 69, 125), (round(ghost.x), round(ghost.y)), radius, 1)


def render_projectile(surface, projectile):
    import pygame

    angle = math.atan2(projectile.vy, projectile.vx)
    x, y = projectile.x, projectile.y
    pygame.draw.circle(surface, (53, 68, 64), (round(x), round(y)), 7)
    tail = (x - math.cos(angle) * 14, y - math.sin(angle) * 14)
    color = (73, 233, 245) if getattr(projectile, "team", "enemy") == "player" else (243, 202, 117)
    if getattr(projectile, "kind", "arrow") == "piercing_arrow":
        color = (172, 114, 219)
        pygame.draw.line(surface, (42, 67, 92),
                         (x - math.cos(angle) * 27, y - math.sin(angle) * 27), (x, y), 5)
        pygame.draw.circle(surface, (73, 233, 245), (round(x), round(y)), 5, 1)
    pygame.draw.line(surface, color, tail, (x, y), 3)
    pygame.draw.polygon(surface, (231, 237, 235), [(x + math.cos(angle) * 5, y + math.sin(angle) * 5),
        (x + math.cos(angle + 2.4) * 6, y + math.sin(angle + 2.4) * 6),
        (x + math.cos(angle - 2.4) * 6, y + math.sin(angle - 2.4) * 6)])

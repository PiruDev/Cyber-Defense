"""Corte cibernético procedural: apenas apresentação, sem lógica de impactos."""

from math import cos, sin, radians

PLAYER_COLORS = ((16, 51, 68), (24, 111, 140), (73, 233, 245), (210, 251, 255))
ENEMY_COLORS = ((59, 20, 49), (130, 38, 83), (255, 91, 135), (255, 210, 230))


def render_slash(surface, center, direction, progress, reach, *, theme="player", reverse=False,
                 half_angle=50, reduced=False):
    """8 poses de surgimento/varredura/dissipação dentro do arco mecânico."""
    import pygame

    if not 0 <= progress < 1:
        return
    colors = ENEMY_COLORS if theme == "enemy" else PLAYER_COLORS
    pose = min(7, int(progress * 8))
    leading = -half_angle + half_angle * 2 * min(1, (pose + 1) / 6)
    trailing = max(-half_angle, leading - (35 + pose * 8))
    dissipate = max(.15, min(1, (1 - progress) / .3))
    sign = -1 if reverse else 1
    for fraction, thickness, color in ((.96, 7, colors[0]), (.98, 4, colors[1]), (1, 2, colors[2])):
        if reduced and thickness == 7:
            continue
        points = [(center[0] + cos(direction + radians(angle * sign)) * reach * fraction,
                   center[1] + sin(direction + radians(angle * sign)) * reach * fraction)
                  for angle in range(round(trailing), round(leading) + 1, 2)]
        if len(points) > 1:
            pygame.draw.lines(surface, color, False, points, max(1, round(thickness * dissipate)))
    # Pequeno núcleo na ponta; a dissipação não ilumina a tela inteira.
    angle = direction + radians(leading * sign)
    if progress < .8:
        pygame.draw.circle(surface, colors[3], (round(center[0] + cos(angle) * reach),
                                                round(center[1] + sin(angle) * reach)), 2)


def render_windup(surface, center, direction, reach=60, *, half_angle=45):
    import pygame

    points = [(center[0] + cos(direction + radians(a)) * reach,
               center[1] + sin(direction + radians(a)) * reach)
              for a in range(-half_angle, half_angle + 1, 3)]
    pygame.draw.lines(surface, (151, 61, 100), False, points, 2)

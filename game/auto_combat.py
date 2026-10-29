"""Aquisição de alvo sem Pygame; a direção final é capturada por ciclo."""

from math import hypot


def nearest_target(player, enemies, reach):
    nearest, minimum = None, float("inf")
    for enemy in enemies:
        if enemy.hp <= 0:
            continue
        for part in getattr(enemy, "segments", (enemy,)):
            distance = hypot(part.x - player.x, part.y - player.y)
            if distance <= reach + part.radius and distance < minimum:
                nearest, minimum = (enemy, part), distance
    return nearest

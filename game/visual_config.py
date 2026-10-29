"""Escala visual e câmera: estes valores não redefinem colisões ou combate."""

WORLD_ARENA = (0, 0, 2400, 1600)
ARENA_VIEWPORT = (32, 154, 1036, 530)
CAMERA_FOLLOW_RATE = 10.0
FLOOR_TILE_SIZE = 40
PLAYER_SCALE = 1.25
ENEMY_SCALES = {
    "basic": 1.5, "archer": 1.5, "swordsman": 1.25,
    "worm_head": 1.0, "worm_body": 1.0, "worm_tail": 1.0,
    "rootkit": 1.15,
}


def enemy_scale(kind):
    return ENEMY_SCALES.get(kind, 1.0)


def feedback_radius(enemy):
    """Altura legível das barras, baseada no corpo opaco e não no canvas."""
    body_radius = {"basic": 18, "archer": 20, "swordsman": 24, "rootkit": 39}
    return max(enemy.radius, body_radius.get(enemy.kind, enemy.radius) * enemy_scale(enemy.kind))

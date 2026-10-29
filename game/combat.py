"""Cálculos puros de alcance, dano e contato."""

from math import cos, hypot, radians


ATTACK_RANGE = 70
ATTACK_ANGLE = 100
ATTACK_COOLDOWN = 0.35
ATTACK_DURATION = 0.14
DAMAGE_COOLDOWN = 0.8
KNOCKBACK_DISTANCE = 20
KNOCKBACK_DURATION = 0.10
STUN_DURATION = 0.20
HIT_FLASH_DURATION = 0.10
SHAKE_DURATION = 0.10
SHAKE_AMPLITUDE = 3


def apply_enemy_hit(player, enemy, damage=None, direction=None) -> bool:
    """Aplica um acerto real e inicia o recuo; não avança seus novos timers."""
    damage = getattr(player, "damage", player.progression.dano) if damage is None else damage
    if enemy.hp <= 0 or damage <= 0:
        return False
    if enemy.take_damage(damage) <= 0:
        return False
    enemy.hit_flash_timer = HIT_FLASH_DURATION
    enemy.hp_bar_timer = 0.35
    if not getattr(enemy, "interruptible", True):
        return True
    dx, dy = enemy.x - player.x, enemy.y - player.y
    if direction is not None:
        dx, dy = direction
    length = hypot(dx, dy)
    if not length:
        dx, dy = player.facing_x, player.facing_y
        length = hypot(dx, dy)
    if not length:
        dx, dy, length = 0, 1, 1
    speed = KNOCKBACK_DISTANCE / KNOCKBACK_DURATION
    enemy.knockback_vx = dx / length * speed
    enemy.knockback_vy = dy / length * speed
    enemy.knockback_timer = KNOCKBACK_DURATION
    enemy.stun_timer = STUN_DURATION
    if hasattr(enemy, "telegraph_timer"):
        # Um golpe interrompido precisa ser anunciado novamente após recuperar.
        enemy.telegraph_timer = 0.0
        enemy.attack_timer = 0.0
        enemy.state = "recover"
        enemy.attack_cooldown = max(enemy.attack_cooldown, 0.3)
    return True


def in_attack_range(player, enemy) -> bool:
    return in_cone(player.x, player.y, player.facing_x, player.facing_y,
                   enemy.x, enemy.y, enemy.radius,
                   getattr(player, "attack_range", ATTACK_RANGE), ATTACK_ANGLE)


def in_cone(x, y, facing_x, facing_y, target_x, target_y, target_radius, reach, angle) -> bool:
    dx, dy = target_x - x, target_y - y
    distance = hypot(dx, dy)
    if distance > reach + target_radius:
        return False
    if distance == 0:
        return True
    facing_length = hypot(facing_x, facing_y)
    if not facing_length:
        return False
    dot = (dx * facing_x + dy * facing_y) / (distance * facing_length)
    return dot >= cos(radians(angle / 2)) - 1e-12


def touching(first, second) -> bool:
    return hypot(first.x - second.x, first.y - second.y) <= first.radius + second.radius


def in_thrust(x, y, facing_x, facing_y, target, reach, width) -> bool:
    length = hypot(facing_x, facing_y)
    if not length:
        return False
    dx, dy = target.x - x, target.y - y
    forward = (dx * facing_x + dy * facing_y) / length
    side = abs(dx * facing_y - dy * facing_x) / length
    nearest_forward = max(0, min(reach, forward))
    nearest_side = max(0, side - width / 2)
    return (forward - nearest_forward) ** 2 + nearest_side ** 2 <= target.radius ** 2


def apply_damage(progression, amount) -> int:
    """Aplica dano e retorna a perda efetiva de HP."""
    previous = progression.hp
    progression.hp = max(0, progression.hp - max(0, amount))
    return previous - progression.hp

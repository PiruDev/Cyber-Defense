"""Espadachim com direção fixa e antecipação legível antes do golpe."""

from dataclasses import dataclass
from math import hypot

from .enemies import Enemy


@dataclass
class Swordsman(Enemy):
    kind: str = "swordsman"
    facing_x: float = 0
    facing_y: float = 1
    state: str = "chase"
    telegraph_timer: float = 0.0
    attack_timer: float = 0.0
    attack_cooldown: float = 0.0

    def advance_ai(self, dt, player, arena) -> bool:
        if self.hp <= 0 or self.stun_timer > 0 or self.knockback_timer > 0:
            return False
        self.attack_timer = max(0, self.attack_timer - dt)
        self.attack_cooldown = max(0, self.attack_cooldown - dt)
        if self.state == "windup":
            self.telegraph_timer = max(0, self.telegraph_timer - dt)
            if self.telegraph_timer <= 1e-12:
                self.telegraph_timer = 0
                self.state = "recover"
                self.attack_timer = 0.14
                self.attack_cooldown = 1.1
                return True
            return False
        if self.attack_cooldown > 0:
            self.state = "recover"
            return False
        self.state = "chase"
        dx, dy = player.x - self.x, player.y - self.y
        distance = hypot(dx, dy)
        if distance:
            self.facing_x, self.facing_y = dx / distance, dy / distance
        if distance <= 60 + player.radius:
            self.state = "windup"
            self.telegraph_timer = 0.35
        else:
            self.move_towards(player, dt)
        return False

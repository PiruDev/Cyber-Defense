"""Arqueiro que mantém distância e antecipa disparos direcionais."""

from dataclasses import dataclass
from math import hypot

from .enemies import Enemy
from .projectiles import Projectile


@dataclass
class Archer(Enemy):
    speed: float = 65
    damage: float = 8
    kind: str = "archer"
    facing_x: float = 0
    facing_y: float = 1
    state: str = "chase"
    telegraph_timer: float = 0.0
    attack_timer: float = 0.0
    attack_cooldown: float = 0.0

    def advance_ai(self, dt, player, arena):
        if self.hp <= 0 or self.stun_timer > 0 or self.knockback_timer > 0:
            return None
        self.attack_timer = max(0, self.attack_timer - dt)
        self.attack_cooldown = max(0, self.attack_cooldown - dt)
        if self.state == "windup":
            self.telegraph_timer = max(0, self.telegraph_timer - dt)
            if self.telegraph_timer <= 1e-12:
                self.telegraph_timer = 0
                self.state = "recover"
                self.attack_timer = 0.14
                self.attack_cooldown = 2.2
                return Projectile(self.x, self.y, self.facing_x * 180,
                                  self.facing_y * 180, damage=self.damage)
            return None
        dx, dy = player.x - self.x, player.y - self.y
        distance = hypot(dx, dy)
        if distance:
            self.facing_x, self.facing_y = dx / distance, dy / distance
        if distance < 180:
            self.x -= self.facing_x * self.speed * dt
            self.y -= self.facing_y * self.speed * dt
        elif distance > 260:
            self.move_towards(player, dt)
        left, top, width, height = arena
        self.x = max(left + self.radius, min(left + width - self.radius, self.x))
        self.y = max(top + self.radius, min(top + height - self.radius, self.y))
        self.state = "recover" if self.attack_cooldown > 0 else "chase"
        if self.attack_cooldown <= 0:
            self.state = "windup"
            self.telegraph_timer = 0.45
        return None

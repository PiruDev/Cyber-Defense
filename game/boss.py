"""Rootkit: núcleo protegido com dois padrões antecipados e alternados."""

from dataclasses import dataclass
from math import cos, hypot, pi, sin

from .enemies import Enemy
from .projectiles import Projectile


@dataclass(frozen=True)
class BossAction:
    pattern: str
    x: float
    y: float
    facing_x: float
    facing_y: float
    projectiles: tuple = ()


@dataclass
class Rootkit(Enemy):
    hp: float = 48
    max_hp: float = 48
    radius: float = 32
    speed: float = 50
    damage: float = 18
    kind: str = "rootkit"
    interruptible: bool = False
    facing_x: float = 0
    facing_y: float = 1
    state: str = "chase"
    pattern: str = "cone"
    telegraph_timer: float = 0.0
    attack_timer: float = 0.0
    attack_cooldown: float = 0.0
    attack_range: float = 150
    attack_angle: float = 110
    telegraph_duration: float = .65
    recovery_duration: float = 2.5
    projectile_speed: float = 180
    projectile_count: int = 6
    entrance_timer: float = 0.65
    _pattern_index: int = 0

    def advance_ai(self, dt, player, arena):
        if self.hp <= 0:
            return None
        self.entrance_timer = max(0, self.entrance_timer - dt)
        self.attack_timer = max(0, self.attack_timer - dt)
        self.attack_cooldown = max(0, self.attack_cooldown - dt)
        if self.state == "windup":
            self.telegraph_timer = max(0, self.telegraph_timer - dt)
            if self.telegraph_timer > 1e-12:
                return None
            self.telegraph_timer = 0.0
            self.state = "recover"
            self.attack_timer = 0.20
            self.attack_cooldown = self.recovery_duration
            self._pattern_index += 1
            projectiles = ()
            if self.pattern == "burst":
                projectiles = tuple(Projectile(self.x, self.y,
                                               cos(index * 2 * pi / self.projectile_count) * self.projectile_speed,
                                               sin(index * 2 * pi / self.projectile_count) * self.projectile_speed,
                                               damage=self.damage)
                                    for index in range(self.projectile_count))
            return BossAction(self.pattern, self.x, self.y, self.facing_x,
                              self.facing_y, projectiles)
        if self.attack_cooldown > 0:
            self.state = "recover"
            return None
        self.state = "chase"
        dx, dy = player.x - self.x, player.y - self.y
        distance = hypot(dx, dy)
        if distance:
            self.facing_x, self.facing_y = dx / distance, dy / distance
        self.pattern = "cone" if self._pattern_index % 2 == 0 else "burst"
        threshold = self.attack_range + player.radius if self.pattern == "cone" else 450
        if distance > threshold:
            self.move_towards(player, dt)
        else:
            self.state = "windup"
            self.telegraph_timer = self.telegraph_duration
        return None

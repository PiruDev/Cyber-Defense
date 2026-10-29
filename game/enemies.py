"""Estado e perseguição dos inimigos."""

from dataclasses import dataclass
from math import hypot


@dataclass
class Enemy:
    x: float
    y: float
    hp: int = 3
    max_hp: int = 3
    speed: float = 85
    damage: int = 10
    radius: float = 17
    kind: str = "basic"
    stun_timer: float = 0.0
    knockback_timer: float = 0.0
    knockback_vx: float = 0.0
    knockback_vy: float = 0.0
    hit_flash_timer: float = 0.0
    hp_bar_timer: float = 0.0

    def receive_damage(self, amount) -> float:
        previous = self.hp
        self.hp = max(0, self.hp - max(0, amount))
        return previous - self.hp

    def take_damage(self, amount) -> float:
        return self.receive_damage(amount)

    def advance_feedback(self, dt, arena) -> float:
        """Avança recuo e timers; retorna o tempo restante livre para perseguir."""
        blocked_time = max(self.stun_timer, self.knockback_timer)
        recoil_dt = min(dt, self.knockback_timer)
        self.x += self.knockback_vx * recoil_dt
        self.y += self.knockback_vy * recoil_dt
        if recoil_dt:
            left, top, width, height = arena
            self.x = max(left + self.radius, min(left + width - self.radius, self.x))
            self.y = max(top + self.radius, min(top + height - self.radius, self.y))
        for name in ("stun_timer", "knockback_timer", "hit_flash_timer", "hp_bar_timer"):
            value = max(0.0, getattr(self, name) - dt)
            setattr(self, name, 0.0 if value < 1e-12 else value)
        if not self.knockback_timer:
            self.knockback_vx = self.knockback_vy = 0.0
        return max(0.0, dt - blocked_time)

    def move_towards(self, player, dt) -> None:
        dx, dy = player.x - self.x, player.y - self.y
        distance = hypot(dx, dy)
        if distance and self.hp > 0 and self.stun_timer <= 0 and self.knockback_timer <= 0:
            step = min(self.speed * dt, distance)
            self.x += dx / distance * step
            self.y += dy / distance * step


@dataclass
class Drop:
    x: float
    y: float
    radius: float = 10
    kind: str = "repair"

"""Estado e movimentação do jogador sem dependências gráficas."""

from dataclasses import dataclass, field
from math import hypot

from .inventory import Inventory
from .progression import Progressao


@dataclass
class Player:
    x: float = 550
    y: float = 419
    radius: float = 16
    speed: float = 220
    facing_x: float = 0
    facing_y: float = 1
    progression: Progressao = field(default_factory=Progressao)
    inventory: Inventory = field(default_factory=Inventory)
    upgrades: dict = field(default_factory=dict)
    overclock_timer: float = 0.0
    overclock_multiplier: float = 1.25

    @property
    def damage(self):
        return self.progression.dano * 1.2 ** self.upgrades.get("damage", 0)

    @property
    def attack_range(self):
        return 70 * (1 + 0.15 * self.upgrades.get("range", 0))

    @property
    def attack_interval(self):
        return 0.35 * 0.9 ** self.upgrades.get("cooldown", 0)

    @property
    def move_speed(self):
        boost = self.overclock_multiplier if self.overclock_timer > 0 else 1.0
        return self.speed * (1 + 0.12 * self.upgrades.get("speed", 0)) * boost

    @property
    def damage_multiplier(self):
        return 0.9 ** self.upgrades.get("reduction", 0)

    @property
    def regen_heal(self):
        return self.upgrades.get("regen", 0)

    @property
    def kill_heal(self):
        return 2 * self.upgrades.get("kill_heal", 0)

    def move(self, dx, dy, dt, arena) -> None:
        length = hypot(dx, dy)
        if length:
            dx, dy = dx / length, dy / length
            self.facing_x, self.facing_y = dx, dy
            base_speed = self.speed * (1 + 0.12 * self.upgrades.get("speed", 0))
            boosted_time = min(dt, max(0.0, self.overclock_timer))
            distance = base_speed * (dt + (self.overclock_multiplier - 1) * boosted_time)
            self.x += dx * distance
            self.y += dy * distance
        left, top, width, height = arena
        self.x = max(left + self.radius, min(left + width - self.radius, self.x))
        self.y = max(top + self.radius, min(top + height - self.radius, self.y))

"""Flechas e colisão varrida, sem dependências gráficas."""

from dataclasses import dataclass, field
from math import hypot, sqrt


@dataclass
class Projectile:
    x: float
    y: float
    vx: float
    vy: float
    damage: float = 8
    radius: float = 5
    ttl: float = 4
    team: str = "enemy"
    range_remaining: float | None = None
    previous_x: float = field(init=False)
    previous_y: float = field(init=False)

    def __post_init__(self):
        self.previous_x, self.previous_y = self.x, self.y

    def advance(self, dt) -> None:
        self.previous_x, self.previous_y = self.x, self.y
        travel_time = min(max(0, dt), max(0, self.ttl))
        speed = hypot(self.vx, self.vy)
        if self.range_remaining is not None and speed:
            travel_time = min(travel_time, max(0, self.range_remaining) / speed)
        self.x += self.vx * travel_time
        self.y += self.vy * travel_time
        if self.range_remaining is not None:
            self.range_remaining = max(0.0, self.range_remaining - speed * travel_time)
        self.ttl = max(0, self.ttl - dt)

    def hits(self, target) -> bool:
        return self.hit_fraction(target) is not None

    def hit_fraction(self, target):
        dx, dy = self.x - self.previous_x, self.y - self.previous_y
        length_squared = dx * dx + dy * dy
        offset_x, offset_y = self.previous_x - target.x, self.previous_y - target.y
        radius = self.radius + target.radius
        c = offset_x * offset_x + offset_y * offset_y - radius * radius
        if c <= 0:
            return 0.0
        if not length_squared:
            return None
        b = 2 * (offset_x * dx + offset_y * dy)
        discriminant = b * b - 4 * length_squared * c
        if discriminant < 0:
            return None
        fraction = (-b - sqrt(discriminant)) / (2 * length_squared)
        return fraction if 0 <= fraction <= 1 else None

    def outside(self, arena) -> bool:
        left, top, width, height = arena
        return (self.x + self.radius < left or self.x - self.radius > left + width
                or self.y + self.radius < top or self.y - self.radius > top + height)

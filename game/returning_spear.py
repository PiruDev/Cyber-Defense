"""Estado da lança no mundo; relógio alimentado somente pela simulação ativa."""

from dataclasses import dataclass

from .balance import SPEAR_RECALL_SECONDS
from .projectiles import Projectile


@dataclass
class ReturningSpear:
    projectile: Projectile
    elapsed: float = 0.0
    landed: bool = False

    @property
    def x(self):
        return self.projectile.x

    @property
    def y(self):
        return self.projectile.y

    @property
    def expired(self):
        return self.elapsed >= SPEAR_RECALL_SECONDS - 1e-12

    def advance(self, dt, arena):
        active_dt = min(dt, max(0, SPEAR_RECALL_SECONDS - self.elapsed))
        self.elapsed += active_dt
        if not self.landed:
            self.projectile.advance(active_dt)
            left, top, width, height = arena
            radius = self.projectile.radius
            x = max(left + radius, min(left + width - radius, self.x))
            y = max(top + radius, min(top + height - radius, self.y))
            if (x, y) != (self.x, self.y) or self.projectile.range_remaining <= 0:
                self.land_at(x, y)

    def land_at(self, x, y):
        self.projectile.x, self.projectile.y = x, y
        self.landed = True

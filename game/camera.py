"""Câmera em coordenadas de mundo, sem Pygame ou estado de janela."""

from math import exp, isfinite

from .visual_config import ARENA_VIEWPORT, CAMERA_FOLLOW_RATE


class Camera:
    def __init__(self, world_bounds, viewport=ARENA_VIEWPORT, follow_rate=CAMERA_FOLLOW_RATE):
        self.world_bounds = tuple(world_bounds)
        self.viewport = tuple(viewport)
        self.follow_rate = follow_rate
        self.x, self.y = world_bounds[:2]

    def _clamp(self, x, y):
        left, top, width, height = self.world_bounds
        return (max(left, min(left + max(0, width - self.viewport[2]), x)),
                max(top, min(top + max(0, height - self.viewport[3]), y)))

    def update(self, x, y, dt, *, snap=False):
        if not all(isfinite(value) for value in (x, y, dt)) or dt < 0:
            raise ValueError("Posição e tempo da câmera devem ser finitos; tempo não negativo.")
        target_x, target_y = self._clamp(x - self.viewport[2] / 2, y - self.viewport[3] / 2)
        alpha = 1.0 if snap else 1 - exp(-self.follow_rate * dt)
        self.x, self.y = self._clamp(self.x + (target_x - self.x) * alpha,
                                    self.y + (target_y - self.y) * alpha)

    def origin(self, shake=(0, 0)):
        # Uma única origem inteira serve ao blit e às duas transformações.
        x, y = self._clamp(self.x - shake[0], self.y - shake[1])
        return round(x), round(y)

    def project(self, x, y, shake=(0, 0)):
        ox, oy = self.origin(shake)
        return x - ox + self.viewport[0], y - oy + self.viewport[1]

    def unproject(self, x, y, shake=(0, 0)):
        ox, oy = self.origin(shake)
        return x + ox - self.viewport[0], y + oy - self.viewport[1]

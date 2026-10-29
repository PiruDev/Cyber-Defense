"""Separação suave de círculos e grupos rígidos, sem RNG ou regras de combate."""

from math import ceil, cos, hypot, isfinite, pi, sin

from .feel_config import (
    SEPARATION_MAX_STEP, SEPARATION_PASSES, SEPARATION_SLOP, SEPARATION_STRENGTH,
    SEPARATION_REFERENCE_FPS, SEPARATION_MAX_DT, SEPARATION_SUBSTEP, SEPARATION_MAX_SUBSTEPS,
)


class SeparationSystem:
    """Identidades seguem o registro, nunca endereços usados como direção."""

    def __init__(self):
        self._registered = {}
        self._next_order = 0

    def register(self, enemy) -> int:
        identity = id(enemy)
        if identity not in self._registered:
            self._registered[identity] = (enemy, self._next_order)
            self._next_order += 1
        return self._registered[identity][1]

    @staticmethod
    def _parts(enemy):
        segments = getattr(enemy, "segments", None)
        return tuple(segments) if segments else (enemy,)

    @classmethod
    def _limits(cls, enemy, arena):
        path_limits = getattr(enemy, "translation_limits", None)
        if path_limits is not None:
            return path_limits(arena)
        left, top, width, height = arena
        parts = cls._parts(enemy)
        return (max(left + part.radius - part.x for part in parts),
                min(left + width - part.radius - part.x for part in parts),
                max(top + part.radius - part.y for part in parts),
                min(top + height - part.radius - part.y for part in parts))

    @classmethod
    def translate(cls, enemy, dx, dy, arena) -> tuple:
        """Limita a translação do grupo inteiro sem comprimir seus segmentos."""
        minimum_x, maximum_x, minimum_y, maximum_y = cls._limits(enemy, arena)
        dx = max(minimum_x, min(maximum_x, dx))
        dy = max(minimum_y, min(maximum_y, dy))
        translate_rigid = getattr(enemy, "translate_rigid", None)
        if translate_rigid is not None:
            translate_rigid(dx, dy)
            return dx, dy
        parts = cls._parts(enemy)
        for part in parts:
            part.x += dx
            part.y += dy
        if parts[0] is not enemy:
            enemy.x, enemy.y = parts[0].x, parts[0].y
        return dx, dy

    def direction_from(self, enemy, x, y) -> tuple:
        dx, dy = enemy.x - x, enemy.y - y
        distance = hypot(dx, dy)
        if distance > 1e-12:
            return dx / distance, dy / distance
        angle = (self.register(enemy) * 137.507764 + 23) * pi / 180
        return cos(angle), sin(angle)

    @classmethod
    def _capacity(cls, enemy, nx, ny, arena) -> float:
        minimum_x, maximum_x, minimum_y, maximum_y = cls._limits(enemy, arena)
        capacity = float("inf")
        if nx > 1e-12:
            capacity = min(capacity, maximum_x / nx)
        elif nx < -1e-12:
            capacity = min(capacity, minimum_x / nx)
        if ny > 1e-12:
            capacity = min(capacity, maximum_y / ny)
        elif ny < -1e-12:
            capacity = min(capacity, minimum_y / ny)
        return max(0.0, capacity)

    def _contact(self, first, second):
        deepest = None
        for part_a in self._parts(first):
            for part_b in self._parts(second):
                dx, dy = part_b.x - part_a.x, part_b.y - part_a.y
                distance = hypot(dx, dy)
                penetration = part_a.radius + part_b.radius - distance - SEPARATION_SLOP
                if penetration <= 0 or (deepest is not None and penetration <= deepest[0]):
                    continue
                if distance > 1e-12:
                    nx, ny = dx / distance, dy / distance
                else:
                    a, b = self.register(first), self.register(second)
                    angle = ((a * 73856093 ^ b * 19349663) % 360) * pi / 180
                    nx, ny = cos(angle), sin(angle)
                deepest = penetration, nx, ny
        return deepest

    def update(self, enemies, arena, dt) -> None:
        if not isfinite(dt) or dt < 0:
            raise ValueError("O tempo da separação deve ser finito e não negativo.")
        alive = [enemy for enemy in enemies if enemy.hp > 0
                 and getattr(enemy, "kind", "") not in ("training", "target")]
        for enemy in alive:
            self.register(enemy)
        alive.sort(key=self.register)
        if dt <= 0:
            return
        for enemy in alive:
            self.translate(enemy, 0, 0, arena)
        if len(alive) < 2:
            return
        # Uma pausa do processo não produz deslocamento ou trabalho sem limite.
        duration = min(dt, SEPARATION_MAX_DT)
        steps = min(SEPARATION_MAX_SUBSTEPS, max(1, ceil(duration / SEPARATION_SUBSTEP - 1e-12)))
        step = duration / steps
        inverse_masses = [1 / max(1, sum(part.radius ** 2 for part in self._parts(enemy)))
                          for enemy in alive]
        fraction = 1 - (1 - SEPARATION_STRENGTH) ** (step * SEPARATION_REFERENCE_FPS / SEPARATION_PASSES)
        for _ in range(steps):
            budget = [SEPARATION_MAX_STEP * step * SEPARATION_REFERENCE_FPS for _ in alive]
            for _ in range(SEPARATION_PASSES):
                shifts = [[0.0, 0.0] for _ in alive]
                for i, first in enumerate(alive):
                    for j in range(i + 1, len(alive)):
                        second = alive[j]
                        contact = self._contact(first, second)
                        if contact is None:
                            continue
                        penetration, nx, ny = contact
                        cap_a = min(budget[i], self._capacity(first, -nx, -ny, arena))
                        cap_b = min(budget[j], self._capacity(second, nx, ny, arena))
                        if cap_a + cap_b < 1e-12:
                            # Coincidência num canto: encontre um eixo que permita sair.
                            alternatives = [(1, 0), (0, 1), (-1, 0), (0, -1)]
                            nx, ny = max(alternatives, key=lambda n:
                                self._capacity(first, -n[0], -n[1], arena)
                                + self._capacity(second, n[0], n[1], arena))
                            cap_a = min(budget[i], self._capacity(first, -nx, -ny, arena))
                            cap_b = min(budget[j], self._capacity(second, nx, ny, arena))
                        correction = penetration * fraction
                        weight = inverse_masses[i] / (inverse_masses[i] + inverse_masses[j])
                        move_a = min(cap_a, correction * weight)
                        move_b = min(cap_b, correction - move_a)
                        move_a += min(cap_a - move_a, max(0, correction - move_a - move_b))
                        shifts[i][0] -= nx * move_a
                        shifts[i][1] -= ny * move_a
                        shifts[j][0] += nx * move_b
                        shifts[j][1] += ny * move_b
                for index, enemy in enumerate(alive):
                    dx, dy = shifts[index]
                    distance = hypot(dx, dy)
                    if distance <= 1e-12:
                        continue
                    scale = min(1.0, budget[index] / distance)
                    dx, dy = self.translate(enemy, dx * scale, dy * scale, arena)
                    budget[index] = max(0, budget[index] - hypot(dx, dy))

"""Hordas finitas e preparação entre elas, sem dependência gráfica."""

from math import isfinite

from .modes import GameMode


_COMPOSITIONS = (
    (6, 0, 0),
    (6, 2, 0),
    (7, 3, 0),
    (8, 4, 0),
    (9, 5, 1),
)


class WaveManager:
    def __init__(self, max_waves: int = 5, mode=None):
        self.mode = GameMode(mode) if mode is not None else None
        if self.mode is not None:
            max_waves = 6 if self.mode == GameMode.DEFENSE else 5
        if isinstance(max_waves, bool) or not isinstance(max_waves, int) or not 1 <= max_waves <= 6:
            raise ValueError("A campanha deve ter entre uma e seis hordas.")
        self.max_waves = max_waves
        self.number = 1
        self.spawned = 0
        self.defeated = 0
        self.preparation_timer = 0.0
        self.complete = False
        self.victory = False
        self.specs = self._make_specs()

    def _make_specs(self) -> list[str]:
        if self.number == 6:
            return ["rootkit"]
        swords, archers, worms = _COMPOSITIONS[self.number - 1]
        # Intercala arqueiros para não deixar todos os ataques à distância no fim.
        specs = []
        while swords or archers:
            if swords:
                specs.append("swordsman")
                swords -= 1
            if archers:
                specs.append("archer")
                archers -= 1
        return specs + ["worm"] * worms

    @property
    def total(self) -> int:
        return len(self.specs)

    @property
    def remaining(self) -> int:
        return max(0, self.total - self.defeated)

    @property
    def can_spawn(self) -> bool:
        return (not self.complete and not self.victory
                and self.preparation_timer <= 0 and self.spawned < self.total)

    @property
    def stat_scale(self) -> float:
        return 1 + 0.15 * (self.number - 1)

    @property
    def damage_scale(self) -> float:
        return 1 + 0.10 * (self.number - 1)

    def next_kind(self) -> str | None:
        """Reserva um spawn; chamar apenas quando o mundo puder materializá-lo."""
        if not self.can_spawn:
            return None
        kind = self.specs[self.spawned]
        self.spawned += 1
        return kind

    def register_defeat(self) -> None:
        """O mundo chama uma vez por morte confirmada da horda atual."""
        if self.defeated < self.spawned:
            self.defeated += 1

    def update(self, dt: float, alive_count: int) -> None:
        """Recebe somente tempo ativo; o mundo controla pausa e limite de vivos."""
        if not isfinite(dt) or dt < 0:
            raise ValueError("O tempo deve ser finito e não negativo.")
        if alive_count < 0:
            raise ValueError("A quantidade de inimigos vivos não pode ser negativa.")
        if self.victory:
            return
        if self.complete:
            self.preparation_timer = max(0.0, self.preparation_timer - dt)
            if self.preparation_timer == 0:
                self.number += 1
                self.spawned = 0
                self.defeated = 0
                self.complete = False
                self.specs = self._make_specs()
            return
        if self.spawned == self.total and self.defeated == self.total and alive_count == 0:
            self.complete = True
            if self.number == self.max_waves:
                self.victory = True
            else:
                self.preparation_timer = 3.0

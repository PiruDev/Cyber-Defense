"""Armas compartilham pulsos únicos e um relógio de ataque independente do render."""

from dataclasses import dataclass
from math import isfinite

from .balance import WEAPON_CONFIGS
from .enemies import Enemy


WEAPON_CHOICES = ("katana", "bow", "spear")


@dataclass(frozen=True)
class AttackPulse:
    serial: tuple
    weapon_id: str
    damage: float
    facing_x: float
    facing_y: float
    reach: float
    width: float
    angle: float


@dataclass
class TrainingTarget(Enemy):
    hp: float = 6
    max_hp: float = 6
    speed: float = 0
    damage: float = 0
    kind: str = "target"


class WeaponSystem:
    def __init__(self, weapon_id="sword"):
        if weapon_id not in WEAPON_CONFIGS:
            raise ValueError("Arma desconhecida.")
        self.weapon_id = weapon_id
        self.cooldown = 0.0
        self.animation_timer = 0.0
        self.elapsed = 0.0
        self.pending = []
        self._serial = 0

    @property
    def config(self):
        return WEAPON_CONFIGS[self.weapon_id]

    def cancel_pending(self) -> None:
        self.pending.clear()
        self.animation_timer = 0.0
        self.elapsed = 0.0

    def switch(self, weapon_id) -> bool:
        if weapon_id not in WEAPON_CONFIGS:
            return False
        self.cancel_pending()
        self.weapon_id = weapon_id
        return True

    def start(self, player) -> tuple:
        if self.cooldown > 1e-12:
            return ()
        self._serial += 1
        self.cooldown = self.config.cooldown * player.attack_interval / 0.35
        self.animation_timer = self.config.animation_duration
        self.elapsed = 0.0
        pulses = []
        for index, impact_time in enumerate(self.config.impact_times):
            pulse = AttackPulse((self._serial, index), self.weapon_id,
                                player.damage * self.config.damage_multiplier,
                                player.facing_x, player.facing_y,
                                self.config.reach * player.attack_range / 70,
                                self.config.width, self.config.angle)
            if impact_time <= 0:
                pulses.append(pulse)
            else:
                self.pending.append((impact_time, pulse))
        return tuple(pulses)

    def update(self, dt) -> tuple:
        if not isfinite(dt) or dt < 0:
            raise ValueError("O tempo da arma deve ser finito e não negativo.")
        self.cooldown = max(0.0, self.cooldown - dt)
        self.animation_timer = max(0.0, self.animation_timer - dt)
        self.elapsed += dt
        ready, pending = [], []
        for remaining, pulse in self.pending:
            remaining -= dt
            if remaining <= 1e-12:
                ready.append(pulse)
            else:
                pending.append((remaining, pulse))
        self.pending = pending
        return tuple(ready)

"""Valores centrais da campanha, armas e treinamento."""

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class WeaponConfig:
    id: str
    name: str
    damage_multiplier: float
    cooldown: float
    reach: float
    width: float
    angle: float
    impact_times: tuple[float, ...]
    animation_duration: float
    projectile_speed: float = 0


WEAPON_CONFIGS = {
    "sword": WeaponConfig("sword", "Espada", 1, .35, 70, 0, 100, (0,), .14),
    "katana": WeaponConfig("katana", "Katana", .6, .40, 70, 0, 100, (0, .10), .24),
    "bow": WeaponConfig("bow", "Arco", 1.4, .50, 500, 0, 0, (0,), .18, 400),
    "spear": WeaponConfig("spear", "Lança", 1.2, .42, 105, 14, 0, (.08,), .22),
    "longbow": WeaponConfig("longbow", "Arco Longo", 1.4, .50, 500, 0, 0, (0,), .18, 400),
    "returning_spear": WeaponConfig("returning_spear", "Lança de Retorno", 1.2, .42, 240, 14, 0, (0,), .22, 400),
}

SPEAR_RECALL_SECONDS = 3.0
SPEAR_SPIN_DURATION = .30
SPEAR_RETURN_DURATION = .18
SPEAR_SPIN_REACH = 105
SPEAR_PICKUP_RADIUS = 18
LONGBOW_MAX_HITS = 3


@dataclass(frozen=True)
class BalanceConfig:
    drop_chance: float = .20
    repair_share: float = .50
    overclock_multiplier: float = 1.25
    overclock_duration: float = 5
    rootkit_hp: float = 48
    rootkit_speed: float = 50
    rootkit_damage: float = 18
    rootkit_telegraph: float = .65
    rootkit_recovery: float = 2.5
    rootkit_attack_range: float = 150
    rootkit_attack_angle: float = 110
    rootkit_projectile_speed: float = 180
    rootkit_projectile_count: int = 6
    defense_practice_seconds: float = 15
    lab_practice_seconds: float = 45
    training_target_hp: float = 6
    training_targets: int = 3
    max_player_projectiles: int = 40
    weapon_card_chance: float = .08
    evolved_weapon_weight: float = .25

    def __post_init__(self):
        for name in ("drop_chance", "repair_share", "weapon_card_chance", "evolved_weapon_weight"):
            value = getattr(self, name)
            if not isfinite(value) or not 0 <= value <= 1:
                raise ValueError(f"{name} deve estar entre zero e um.")
        for name in ("overclock_multiplier", "overclock_duration", "rootkit_hp",
                     "rootkit_speed", "rootkit_damage", "rootkit_telegraph", "rootkit_recovery",
                     "rootkit_attack_range", "rootkit_attack_angle", "rootkit_projectile_speed", "defense_practice_seconds",
                     "lab_practice_seconds", "training_target_hp"):
            value = getattr(self, name)
            if not isfinite(value) or value <= 0:
                raise ValueError(f"{name} deve ser finito e positivo.")
        for name in ("training_targets", "max_player_projectiles", "rootkit_projectile_count"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ValueError(f"{name} deve ser inteiro positivo.")
        if self.training_targets > 9 or self.max_player_projectiles > 80 or self.rootkit_projectile_count > 24:
            raise ValueError("A configuração excede os limites seguros de entidades.")

"""Sorteio e coleta de reparo/overclock, independentes do Pygame."""

from dataclasses import dataclass

from .items import collect_potion


@dataclass(frozen=True)
class DropResult:
    score: int = 0
    healed: float = 0
    potions: int = 0
    overclock: bool = False


def roll_drop(rng, config) -> str | None:
    if rng.random() >= config.drop_chance:
        return None
    return "repair" if rng.random() < config.repair_share else "overclock"


def collect_drop(player, kind: str, config) -> DropResult:
    if player.progression.hp <= 0:
        return DropResult()
    if kind == "repair":
        previous_hp = player.progression.hp
        previous_potions = player.inventory.potions
        score = collect_potion(player)
        return DropResult(score=score,
                          healed=player.progression.hp - previous_hp,
                          potions=player.inventory.potions - previous_potions)
    if kind == "overclock":
        player.overclock_timer = config.overclock_duration
        return DropResult(overclock=True)
    return DropResult()

"""Inventário de poções, independente de Pygame."""

from dataclasses import dataclass


@dataclass
class Inventory:
    potions: int = 2
    max_potions: int = 5

    def add_potion(self) -> bool:
        if self.potions >= self.max_potions:
            return False
        self.potions += 1
        return True

    def use_potion(self, progression) -> bool:
        if self.potions <= 0 or progression.hp <= 0 or progression.hp >= progression.hp_maximo:
            return False
        progression.hp = min(progression.hp_maximo, progression.hp + 35)
        self.potions -= 1
        return True

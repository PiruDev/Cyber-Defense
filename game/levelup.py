"""Estado de apresentação da evolução, avançado somente pelo relógio da UI."""

from enum import Enum
from math import isfinite

from .feel_config import CARD_ENTRY_DURATION, CARD_STAGGER, LEVEL_UP_INTRO_DURATION, clamp01


class LevelUpPhase(str, Enum):
    GAMEPLAY = "GAMEPLAY"
    LEVEL_UP_INTRO = "LEVEL_UP_INTRO"
    LEVEL_UP_CARDS = "LEVEL_UP_CARDS"


class LevelUpState:
    def __init__(self):
        self.end()

    @property
    def active(self) -> bool:
        return self.state != LevelUpPhase.GAMEPLAY

    @property
    def cards_elapsed(self) -> float:
        return max(0.0, self.elapsed - LEVEL_UP_INTRO_DURATION) if self.active else 0.0

    @property
    def selection_ready(self) -> bool:
        return (self.state == LevelUpPhase.LEVEL_UP_CARDS
                and self.cards_elapsed + 1e-12 >= CARD_ENTRY_DURATION + 2 * CARD_STAGGER)

    def card_progress(self, index) -> float:
        if (self.state != LevelUpPhase.LEVEL_UP_CARDS or isinstance(index, bool)
                or not isinstance(index, int) or not 0 <= index < 3):
            return 0.0
        return clamp01((self.cards_elapsed - index * CARD_STAGGER) / CARD_ENTRY_DURATION)

    def start(self) -> None:
        self.state = LevelUpPhase.LEVEL_UP_INTRO
        self.elapsed = 0.0

    def end(self) -> None:
        self.state = LevelUpPhase.GAMEPLAY
        self.elapsed = 0.0

    def advance(self, dt) -> bool:
        if not isfinite(dt) or dt < 0:
            raise ValueError("O tempo da apresentação deve ser finito e não negativo.")
        if not self.active:
            return False
        self.elapsed += dt
        if (self.state == LevelUpPhase.LEVEL_UP_INTRO
                and self.elapsed + 1e-12 >= LEVEL_UP_INTRO_DURATION):
            self.state = LevelUpPhase.LEVEL_UP_CARDS
            return True
        return False

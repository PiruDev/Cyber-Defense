"""Identidades dos dois modos finitos de CyberDefense."""

from enum import Enum


class GameMode(str, Enum):
    DEFENSE = "defense"
    LABORATORY = "laboratory"

"""Configuração dos efeitos visuais e sonoros, sem inicializar dispositivos."""

from dataclasses import dataclass
from math import isfinite


def _scale(value, default):
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError):
        return default
    return max(0.0, min(1.0, result)) if isfinite(result) else default


def _capacity(value, default, maximum):
    try:
        return max(0, min(maximum, int(value)))
    except (TypeError, ValueError, OverflowError):
        return default


@dataclass
class EffectSettings:
    shake_scale: float = 1.0
    particle_scale: float = 1.0
    max_particles: int = 160
    max_texts: int = 32
    audio_enabled: bool = True
    volume: float = 0.18
    music_enabled: bool = True
    music_volume: float = 0.15

    def __post_init__(self):
        self.shake_scale = _scale(self.shake_scale, 1.0)
        self.particle_scale = _scale(self.particle_scale, 1.0)
        self.max_particles = _capacity(self.max_particles, 160, 320)
        self.max_texts = _capacity(self.max_texts, 32, 64)
        self.audio_enabled = bool(self.audio_enabled)
        self.volume = _scale(self.volume, 0.18)
        self.music_enabled = bool(self.music_enabled)
        self.music_volume = _scale(self.music_volume, 0.15)

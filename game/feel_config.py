"""Parâmetros de apresentação e separação; funções puras, sem Pygame."""


LEVEL_UP_INTRO_DURATION = 0.5
CARD_ENTRY_DURATION = 0.20
CARD_STAGGER = 0.04
LEVEL_UP_PUSH_DISTANCE = 64
LEVEL_UP_PUSH_DURATION = 0.4
WAVE_DURATION = 0.65
WAVE_RADIUS = 150
LEVEL_UP_TEXT_DROP_DURATION = 0.22
LEVEL_UP_TEXT_FADE_START = 0.32
LEVEL_UP_TEXT_IMPACT_DURATION = 0.08
LEVEL_UP_TEXT_IMPACT_SCALE = 0.035
LEVEL_UP_TEXT_START_Y = -65
LEVEL_UP_TEXT_TARGET_Y = 207
LEVEL_UP_PARTICLE_Y = 170
CARD_ENTRY_OFFSET = 28

SEPARATION_PASSES = 6
SEPARATION_SLOP = 0.5
SEPARATION_STRENGTH = 0.8
SEPARATION_MAX_STEP = 4
SEPARATION_REFERENCE_FPS = 60
SEPARATION_MAX_DT = 0.1
SEPARATION_SUBSTEP = 1 / 120
SEPARATION_MAX_SUBSTEPS = 12


def clamp01(value: float) -> float:
    """Limita um progresso ao intervalo fechado de zero a um."""
    return max(0.0, min(1.0, value))


def ease_out_cubic(value: float) -> float:
    """Desacelera a entrada até o destino sem ultrapassá-lo."""
    progress = clamp01(value)
    return 1 - (1 - progress) ** 3


def smoothstep(value: float) -> float:
    """Interpola suavemente, com velocidade zero nas duas extremidades."""
    progress = clamp01(value)
    return progress * progress * (3 - 2 * progress)

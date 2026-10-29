"""Feedback visual puro: relógio próprio, limites e RNG separado da partida."""

from dataclasses import dataclass, field
from math import cos, isfinite, pi, sin
from random import Random

from .combat import SHAKE_AMPLITUDE, SHAKE_DURATION
from .settings import EffectSettings
from .feel_config import CARD_ENTRY_DURATION, CARD_STAGGER


def shake_offset(timer, duration=SHAKE_DURATION, amplitude=SHAKE_AMPLITUDE) -> tuple[int, int]:
    if timer <= 0:
        return 0, 0
    remaining = min(1.0, timer / duration) if duration > 0 else 0
    phase = (duration - min(timer, duration)) * 110
    amplitude *= remaining
    return round(cos(phase) * amplitude), round(sin(phase * 1.37) * amplitude)


@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    remaining: float
    total_life: float
    size: float
    color: tuple
    kind: str = "arena"
    origin_x: float | None = None
    origin_y: float | None = None
    ui_anchor_y: float = 110

    def __post_init__(self):
        if self.origin_x is None:
            self.origin_x = self.x
        if self.origin_y is None:
            self.origin_y = self.y


@dataclass
class FloatingText:
    text: str
    x: float
    y: float
    remaining: float = 0.65
    total_life: float = 0.65
    color: tuple = (255, 244, 204)
    size: int = 22


@dataclass(frozen=True)
class EffectEvent:
    kind: str
    x: float
    y: float
    payload: dict = field(default_factory=dict)


@dataclass
class EnemyGhost:
    """Snapshot visual sem entidade, colisão ou recompensa associada."""

    kind: str
    x: float
    y: float
    direction: tuple
    remaining: float
    total_life: float
    state: str = "death"


class EffectSystem:
    """Apresentação observa eventos; nunca altera entidades ou recompensas."""

    def __init__(self, settings=None, rng=None):
        self.settings = settings if settings is not None else EffectSettings()
        self.rng = rng if rng is not None else Random(0)
        self.reset()

    def reset(self) -> None:
        self.particles = []
        self.texts = []
        self.events = []
        self.hitstop_timer = 0.0
        self.shake_timer = 0.0
        self.shake_duration = SHAKE_DURATION
        self.shake_amplitude = SHAKE_AMPLITUDE
        self.card_transition_timer = 0.0
        self.confirmation_timer = 0.0
        self.finale_timer = 0.0
        self.selected_card_index = -1
        self.confirmation_text = ""
        self.head_highlights = {}
        self.enemy_ghosts = []

    @property
    def shake_offset(self) -> tuple[int, int]:
        scale = self.settings.shake_scale
        return shake_offset(self.shake_timer, self.shake_duration,
                            self.shake_amplitude * scale)

    def consume_events(self) -> tuple:
        events = tuple(self.events)
        self.events.clear()
        return events

    def _burst(self, x, y, count, life, color, *, kind="arena", speed=95, ui_anchor_y=110):
        count = max(0, round(count * self.settings.particle_scale))
        capacity = max(0, self.settings.max_particles)
        count = min(count, capacity)
        overflow = max(0, len(self.particles) + count - capacity)
        if overflow:
            del self.particles[:overflow]
        for _ in range(count):
            angle = self.rng.uniform(0, 2 * pi)
            velocity = self.rng.uniform(speed * 0.45, speed)
            particle = Particle(x, y, cos(angle) * velocity, sin(angle) * velocity,
                                life, life, self.rng.uniform(2, 4), color, kind,
                                ui_anchor_y=ui_anchor_y)
            self.particles.append(particle)

    def _text(self, text, x, y, color, *, strong=False):
        capacity = max(0, self.settings.max_texts)
        if not capacity:
            self.texts.clear()
            return
        overflow = max(0, len(self.texts) + 1 - capacity)
        if overflow:
            del self.texts[:overflow]
        self.texts.append(FloatingText(text, x, y - 20, color=color,
                                       size=28 if strong else 22))

    def _impact(self, strong):
        duration = 0.16 if strong else 0.10
        amplitude = 6 if strong else 3
        self.hitstop_timer = max(self.hitstop_timer, 0.07 if strong else 0.04)
        if self.shake_timer <= 0:
            self.shake_duration = duration
            self.shake_amplitude = amplitude
        else:
            self.shake_duration = max(self.shake_duration, duration)
            self.shake_amplitude = max(self.shake_amplitude, amplitude)
        self.shake_timer = max(self.shake_timer, duration)

    def _enemy_ghost(self, x, y, payload, state, life):
        kind = payload.get("enemy_kind", "")
        if kind == "worm":
            kind = "worm_head"
        if kind not in ("basic", "swordsman", "archer", "rootkit",
                        "worm_head", "worm_body", "worm_tail"):
            return
        direction = (payload.get("facing_x", 1), payload.get("facing_y", 0))
        self.enemy_ghosts.append(EnemyGhost(kind, x, y, direction, life, life, state))
        # A morte lógica já ocorreu: limitar os registros afeta somente o desenho.
        if len(self.enemy_ghosts) > 32:
            del self.enemy_ghosts[:-32]

    def emit(self, kind, x, y, **payload) -> None:
        """Registra uma confirmação lógica e cria apenas feedback limitado."""
        self.events.append(EffectEvent(kind, x, y, dict(payload)))
        if len(self.events) > 128:
            del self.events[:-128]
        strong = bool(payload.get("strong", False))
        if kind == "hit":
            damage = payload.get("damage", 0)
            if damage <= 0:
                return
            self._impact(strong)
            color = (255, 205, 115) if strong else (255, 244, 220)
            self._burst(x, y, 12 if strong else 8, 0.22, color)
            self._text(format(damage, ".3g"), x, y, color, strong=strong)
        elif kind == "death":
            self._enemy_ghost(x, y, payload, "death", 0.45 if strong else 0.30)
            if strong:
                self.finale_timer = max(self.finale_timer, 0.45)
            self._burst(x, y, 20 if strong else 12, 0.45 if strong else 0.30,
                        (237, 111, 225) if strong else (208, 85, 166), speed=125)
        elif kind in ("wormrupture", "rupture"):
            if not payload.get("final", False):
                self._enemy_ghost(x, y, dict(payload, enemy_kind="worm_head"), "rupture", 0.30)
            self._burst(x, y, 16, 0.30, (255, 191, 98), speed=140)
        elif kind == "newhead":
            enemy_id = payload.get("enemy_id")
            if enemy_id is not None:
                self.head_highlights[enemy_id] = 0.15
        elif kind == "levelup":
            from .feel_config import LEVEL_UP_PARTICLE_Y
            self._burst(x, y, 18, 0.40, (135, 255, 211), kind="ui", speed=130,
                        ui_anchor_y=LEVEL_UP_PARTICLE_Y)
        elif kind == "cards_show":
            self.card_transition_timer = CARD_ENTRY_DURATION + 2 * CARD_STAGGER
        elif kind == "card_select":
            self.confirmation_timer = 0.20
            self.confirmation_text = payload.get("name", payload.get("card_id", "Melhoria adquirida"))
            self._burst(x, y, 12, 0.30, (255, 225, 147), kind="ui", speed=110)
        elif kind == "pickup":
            color = (219, 131, 250) if payload.get("overclock") else (115, 240, 229)
            self._burst(x, y, 8, 0.25, color, speed=65)
            if payload.get("overclock"):
                self._text("OVERCLOCK +25%", x, y, color)
        elif kind == "score":
            self._text(f"+{payload.get('amount', 10):g} pontos", x, y, (255, 218, 127))
        elif kind == "archerfire":
            self._burst(x, y, 4, 0.06, (255, 220, 153), speed=80)
        elif kind == "boss_spawn":
            self._burst(x, y, 24, 0.6, (222, 112, 247), speed=125)
            self._text("ROOTKIT", x, y - 28, (244, 159, 245), strong=True)

    def update(self, dt, paused=False) -> float:
        if not isfinite(dt) or dt < 0:
            raise ValueError("O tempo dos efeitos deve ser finito e não negativo.")
        previous_hitstop = self.hitstop_timer
        self.hitstop_timer = max(0.0, self.hitstop_timer - dt)
        self.card_transition_timer = max(0.0, self.card_transition_timer - dt)
        self.confirmation_timer = max(0.0, self.confirmation_timer - dt)
        self.finale_timer = max(0.0, self.finale_timer - dt)
        if not paused:
            for ghost in self.enemy_ghosts:
                ghost.remaining = max(0.0, ghost.remaining - dt)
            self.enemy_ghosts = [ghost for ghost in self.enemy_ghosts if ghost.remaining > 1e-12]
            self.shake_timer = max(0.0, self.shake_timer - dt)
            self.head_highlights = {key: remaining - dt for key, remaining in self.head_highlights.items()
                                    if remaining - dt > 1e-12}
        active_particles = []
        for particle in self.particles:
            if not paused or particle.kind == "ui":
                step = min(dt, particle.remaining)
                particle.x += particle.vx * step
                particle.y += particle.vy * step
                particle.remaining = max(0.0, particle.remaining - dt)
            if particle.remaining > 1e-12:
                active_particles.append(particle)
        particle_cap = max(0, self.settings.max_particles)
        self.particles = active_particles[-particle_cap:] if particle_cap else []
        if not paused:
            for text in self.texts:
                text.y -= 32 * min(dt, text.remaining)
                text.remaining = max(0.0, text.remaining - dt)
            self.texts = [text for text in self.texts if text.remaining > 1e-12]
        text_cap = max(0, self.settings.max_texts)
        self.texts = self.texts[-text_cap:] if text_cap else []
        return 0.0 if paused else max(0.0, dt - previous_hitstop)

"""Sons gerados em memória. Importar este módulo não inicializa o Pygame."""

from array import array
from math import pi, sin


_TONES = {
    "hit": (180, 85, 0.055),
    "death": (155, 45, 0.14),
    "pickup": (580, 920, 0.09),
    "cards_show": (720, 1240, 0.13),
    "boss_entry": (440, 1100, 0.20),
    "select": (700, 980, 0.065),
    "score": (850, 1250, 0.08),
    "archer_fire": (450, 150, 0.045),
}

_ALIASES = {
    "card_select": "select",
    "archerfire": "archer_fire",
    "archer_shot": "archer_fire",
    "enemy_death": "death",
    "worm_break": "death",
    "wormrupture": "death",
    "worm_death": "death",
    "player_hit": "hit",
    "boss_spawn": "boss_entry",
}


class AudioBus:
    """Toca até quatro eventos por quadro e oito vozes simultâneas.

    O chamador entrega eventos já consumidos; este objeto não guarda nem repete
    eventos. Dispositivo indisponível desativa apenas o áudio.
    """

    def __init__(self, settings):
        self.settings = settings
        self.enabled = False
        self._pygame = None
        self._sounds = {}
        self._channels = []
        if not settings.audio_enabled:
            return
        try:
            import pygame

            self._pygame = pygame
            if pygame.mixer.get_init() is None:
                pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            frequency, size, channels = pygame.mixer.get_init()
            if size not in (-8, 8, -16, 16, -32, 32) or channels < 1:
                return
            if pygame.mixer.get_num_channels() < 8:
                pygame.mixer.set_num_channels(8)
            self._channels = [pygame.mixer.Channel(index) for index in range(8)]
            for kind, tone in _TONES.items():
                self._sounds[kind] = pygame.mixer.Sound(
                    buffer=self._samples(*tone, frequency, size, channels))
            self.enabled = True
        except Exception:
            # O áudio é opcional: nem falha de driver nem formato impede jogar.
            self.enabled = False
            self._sounds.clear()

    @staticmethod
    def _samples(start, end, duration, frequency, size, channels):
        bits = abs(size)
        signed = size < 0
        code = {8: "b" if signed else "B",
                16: "h" if signed else "H",
                32: "i" if signed else "I"}[bits]
        samples = array(code)
        amplitude = (2 ** (bits - 1) - 1) * 0.4
        offset = 0 if signed else 2 ** (bits - 1)
        length = max(2, round(duration * frequency))
        phase = 0.0
        for index in range(length):
            progress = index / (length - 1)
            pitch = start + (end - start) * progress
            envelope = min(1.0, index / max(1, frequency * 0.004)) * (1 - progress) ** 2
            value = round(offset + sin(phase) * amplitude * envelope)
            samples.extend([value] * channels)
            phase += 2 * pi * pitch / frequency
        return samples.tobytes()

    def play_events(self, events) -> None:
        if not self.enabled or not self.settings.audio_enabled:
            return
        played = 0
        try:
            volume = max(0.0, min(1.0, float(self.settings.volume)))
            for event in events:
                kind = getattr(event, "kind", None)
                if kind is None and isinstance(event, dict):
                    kind = event.get("kind")
                sound = self._sounds.get(_ALIASES.get(kind, kind))
                if sound is None:
                    continue
                channel = next((voice for voice in self._channels
                                if not voice.get_busy()), None)
                if channel is None:
                    break
                channel.set_volume(volume)
                channel.play(sound)
                played += 1
                if played >= 4:
                    break
        except Exception:
            self.enabled = False

    def close(self) -> None:
        """Interrompe nossas vozes sem encerrar o Pygame ou outros subsistemas."""
        self.enabled = False
        for channel in self._channels:
            try:
                channel.stop()
            except Exception:
                pass
        self._channels.clear()
        self._sounds.clear()

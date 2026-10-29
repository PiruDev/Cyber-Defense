"""Reprodução opcional de música autoral fornecida em assets/audio."""

from pathlib import Path


class MusicPlayer:
    def __init__(self, settings):
        self.settings = settings
        self.status = "Música opcional não iniciada."
        self.enabled = False
        self._started = False
        self._playing = False
        self._pygame = None

    def start(self) -> bool:
        """Inicia uma única reprodução em loop; ausência de arquivo é normal."""
        if self._started:
            return self.enabled
        self._started = True
        if not getattr(self.settings, "music_enabled", True):
            self.status = "Música desativada."
            return False
        directory = Path(__file__).resolve().parents[1] / "assets" / "audio"
        track = next((directory / name for name in ("theme.ogg", "theme.mp3")
                      if (directory / name).is_file()), None)
        if track is None:
            self.status = "Música autoral opcional ausente."
            return False
        try:
            import pygame

            self._pygame = pygame
            if pygame.mixer.get_init() is None:
                pygame.mixer.init()
            pygame.mixer.music.load(str(track))
            self.updatevolume()
            pygame.mixer.music.play(loops=-1)
            self._playing = True
            self.enabled = True
            self.status = f"Música: {track.name}"
            return True
        except Exception:
            self.enabled = False
            self.status = "Música indisponível neste dispositivo."
            return False

    def updatevolume(self) -> None:
        if self._pygame is None:
            return
        try:
            volume = float(getattr(self.settings, "music_volume", .15))
            volume = max(0.0, min(1.0, volume))
            if not getattr(self.settings, "music_enabled", True):
                volume = 0.0
            self._pygame.mixer.music.set_volume(volume)
        except Exception:
            self.enabled = False

    def update_volume(self) -> None:
        """Alias legível para chamadores que usam snake_case."""
        self.updatevolume()

    def close(self) -> None:
        if self._pygame is not None and self._playing:
            try:
                self._pygame.mixer.music.stop()
            except Exception:
                pass
        self._playing = False
        self.enabled = False

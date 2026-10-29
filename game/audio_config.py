"""Configuração do mixer antes de pygame.init; buffers comparáveis por URL/env."""
import os

BUFFER_SIZES = (512, 1024, 2048)
DEFAULT_BUFFER = 2048  # Preserva o padrão; não afirma ser o melhor para todo browser.


def buffer_from_query(query):
    for item in str(query).lstrip("?").split("&"):
        key, _, value = item.partition("=")
        if key == "audio_buffer" and value in ("512", "1024", "2048"):
            return int(value)
    return DEFAULT_BUFFER


def requested_buffer(browser=False):
    value = os.environ.get("CYBER_AUDIO_BUFFER", "")
    if value in ("512", "1024", "2048"):
        return int(value)
    if browser:
        try:
            from platform import window
            return buffer_from_query(window.location.search)
        except (ImportError, AttributeError):
            pass
    return DEFAULT_BUFFER


def preconfigure(pygame, browser=False):
    buffer = requested_buffer(browser)
    try:
        pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=buffer)
    except Exception:
        # Backend sem áudio continua pelo mesmo fallback opcional do jogo.
        pass
    return buffer

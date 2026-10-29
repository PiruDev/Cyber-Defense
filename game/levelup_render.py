"""Onda e título da atualização; relógio de UI, sem modificar a simulação."""

from functools import lru_cache
from math import sin, pi

from .feel_config import (
    LEVEL_UP_INTRO_DURATION, LEVEL_UP_TEXT_DROP_DURATION,
    LEVEL_UP_TEXT_FADE_START, WAVE_DURATION, WAVE_RADIUS,
    LEVEL_UP_TEXT_IMPACT_DURATION, LEVEL_UP_TEXT_IMPACT_SCALE,
    LEVEL_UP_TEXT_START_Y, LEVEL_UP_TEXT_TARGET_Y,
    clamp01, ease_out_cubic, smoothstep,
)


@lru_cache(maxsize=2)
def _layer(size):
    import pygame
    return pygame.Surface(size, pygame.SRCALPHA)


@lru_cache(maxsize=1)
def _title():
    import pygame
    font = pygame.font.Font(None, 86)
    return font.render("LEVEL UP!", True, (226, 255, 251))


def render_levelup_wave(surface, world):
    import pygame

    sequence = world.level_up
    if not sequence.active or sequence.elapsed >= WAVE_DURATION:
        return
    progress = clamp01(sequence.elapsed / WAVE_DURATION)
    radius = max(1, round(20 + (WAVE_RADIUS - 20) * ease_out_cubic(progress)))
    center = (round(world.player.x), round(world.player.y))
    layer = _layer(surface.get_size())
    clip = surface.get_clip()
    old_clip = layer.get_clip()
    layer.set_clip(clip)
    layer.fill((0, 0, 0, 0), clip)
    alpha = round(190 * (1 - progress))
    pygame.draw.circle(layer, (73, 233, 245, alpha // 5), center, radius + 5, 7)
    pygame.draw.circle(layer, (105, 255, 225, alpha), center, radius, 2)
    pygame.draw.circle(layer, (73, 233, 245, alpha // 2), center, max(1, radius - 12), 1)
    surface.blit(layer, clip.topleft, clip)
    layer.set_clip(old_clip)


def render_levelup_intro(surface, world, fonts):
    import pygame

    elapsed = world.level_up.elapsed
    drop = ease_out_cubic(elapsed / LEVEL_UP_TEXT_DROP_DURATION)
    fade = 1 - smoothstep((elapsed - LEVEL_UP_TEXT_FADE_START) /
                         (LEVEL_UP_INTRO_DURATION - LEVEL_UP_TEXT_FADE_START))
    layer = _layer(surface.get_size())
    layer.fill((0, 0, 0, 24))
    y = round(LEVEL_UP_TEXT_START_Y + (LEVEL_UP_TEXT_TARGET_Y - LEVEL_UP_TEXT_START_Y) * drop)
    image = _title()
    impact = max(0, 1 - abs(elapsed - LEVEL_UP_TEXT_DROP_DURATION) / LEVEL_UP_TEXT_IMPACT_DURATION)
    # O impacto fica no título; não move câmera nem produz flash de tela.
    scale = 1 + LEVEL_UP_TEXT_IMPACT_SCALE * sin(pi / 2 * impact)
    title = pygame.transform.smoothscale(image, (round(image.get_width() * scale), round(image.get_height() * scale)))
    title.set_alpha(round(255 * fade))
    rect = title.get_rect(center=(surface.get_width() // 2, y))
    glow = pygame.transform.smoothscale(image, (rect.width + 8, rect.height + 4))
    glow.set_alpha(round(26 * fade))
    layer.blit(glow, glow.get_rect(center=rect.center))
    layer.blit(title, rect)
    caption = fonts["small"].render("SENTINEL-01  //  PROTOCOLO DE ATUALIZAÇÃO", True, (73, 233, 245))
    caption.set_alpha(round(220 * fade * drop))
    layer.blit(caption, caption.get_rect(center=(surface.get_width() // 2, y + 48)))
    surface.blit(layer, (0, 0))

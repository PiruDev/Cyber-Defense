"""Renderização de FX, com superfícies e fontes reutilizadas."""

from functools import lru_cache


@lru_cache(maxsize=2)
def _layer(size):
    import pygame
    return pygame.Surface(size, pygame.SRCALPHA)


@lru_cache(maxsize=8)
def _font(size):
    import pygame
    return pygame.font.Font(None, size)


@lru_cache(maxsize=128)
def _label(value, color, size):
    return _font(size).render(value, True, color)


def render_effects(surface, effects, *, ui=False):
    import pygame

    layer = _layer(surface.get_size())
    clip = surface.get_clip()
    old_clip = layer.get_clip()
    layer.set_clip(clip)
    layer.fill((0, 0, 0, 0), clip)
    if effects.settings.particle_scale > 0:
        for particle in effects.particles:
            if (particle.kind == "ui") != ui:
                continue
            ratio = max(0, min(1, particle.remaining / particle.total_life))
            alpha = round(255 * ratio)
            if ui:
                # Confete na faixa superior, nunca sobre as descrições das cartas.
                position = (round(surface.get_width() / 2 + particle.x - particle.origin_x),
                            round(particle.ui_anchor_y + particle.y - particle.origin_y))
            else:
                position = (round(particle.x), round(particle.y))
            radius = max(1, round(particle.size * (0.5 + ratio * 0.5)))
            if ui:
                pygame.draw.rect(layer, (*particle.color[:3], alpha),
                                 (position[0] - radius, position[1] - radius, radius * 2, radius * 2), 1)
            else:
                pygame.draw.circle(layer, (*particle.color[:3], alpha), position, radius)
            if radius >= 3:
                pygame.draw.circle(layer, (255, 251, 225, alpha), position, 1)
    if not ui:
        for number in effects.texts:
            ratio = max(0, min(1, number.remaining / number.total_life))
            image = _label(number.text, tuple(number.color), number.size)
            image.set_alpha(round(255 * min(1, ratio * 1.7)))
            layer.blit(image, image.get_rect(center=(round(number.x), round(number.y))))
    surface.blit(layer, clip.topleft, clip)
    layer.set_clip(old_clip)


def render_confirmation(surface, effects):
    import pygame

    if effects.confirmation_timer <= 0 or not effects.confirmation_text:
        return
    ratio = min(1, effects.confirmation_timer / 0.20)
    image = _label(effects.confirmation_text, (105, 231, 186), 24)
    width = min(1000, image.get_width() + 44)
    layer = _layer(surface.get_size())
    layer.fill((0, 0, 0, 0))
    rect = pygame.Rect((surface.get_width() - width) // 2, 674, width, 32)
    pygame.draw.rect(layer, (22, 45, 48, round(245 * ratio)), rect, border_radius=9)
    pygame.draw.rect(layer, (105, 231, 186, round(180 * ratio)), rect, 1, border_radius=9)
    image.set_alpha(round(255 * ratio))
    layer.blit(image, image.get_rect(center=rect.center))
    surface.blit(layer, (0, 0))

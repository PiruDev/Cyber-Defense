"""Layout e renderização das escolhas; sem dependência de janela ao importar."""

import math
from functools import lru_cache

from .feel_config import CARD_ENTRY_OFFSET, ease_out_cubic


@lru_cache(maxsize=2)
def _shade(size):
    import pygame
    return pygame.Surface(size, pygame.SRCALPHA)


@lru_cache(maxsize=2)
def _content(size):
    import pygame
    return pygame.Surface(size, pygame.SRCALPHA)


@lru_cache(maxsize=3)
def _card_layer(index):
    import pygame
    return pygame.Surface((316, 336), pygame.SRCALPHA)


def card_rects():
    """A mesma geometria é usada para desenho e seleção com o mouse."""
    return [(70 + index * 330, 255, 300, 320) for index in range(3)]


def _wrapped(surface, font, value, x, y, color, width=252):
    line = ""
    for word in value.split():
        candidate = (line + " " + word).strip()
        if font.size(candidate)[0] > width and line:
            surface.blit(font.render(line, True, color), (x, y))
            y += 25
            line = word
        else:
            line = candidate
    if line:
        surface.blit(font.render(line, True, color), (x, y))


def _icon(pygame, surface, kind, center, color):
    x, y = center
    if kind in ("damage", "range", "cooldown"):
        pygame.draw.line(surface, color, (x - 15, y + 17), (x + 17, y - 17), 6)
        pygame.draw.line(surface, color, (x - 18, y + 4), (x - 3, y + 18), 4)
        if kind == "range":
            pygame.draw.circle(surface, color, center, 29, 1)
        elif kind == "cooldown":
            pygame.draw.arc(surface, color, (x - 28, y - 28, 56, 56), 0, math.pi * 1.4, 2)
    elif kind in ("max_hp", "regen", "kill_heal"):
        pygame.draw.rect(surface, color, (x - 5, y - 20, 10, 40), border_radius=2)
        pygame.draw.rect(surface, color, (x - 20, y - 5, 40, 10), border_radius=2)
        if kind != "max_hp":
            pygame.draw.circle(surface, color, center, 28, 1)
    elif kind == "speed":
        pygame.draw.lines(surface, color, False, [(x - 22, y - 16), (x, y), (x - 22, y + 16)], 5)
        pygame.draw.lines(surface, color, False, [(x, y - 16), (x + 22, y), (x, y + 16)], 5)
    else:
        pygame.draw.polygon(surface, color, [(x - 20, y - 20), (x + 20, y - 20), (x + 16, y + 9), (x, y + 25), (x - 16, y + 9)], 3)


def render_cards(surface, world, fonts):
    import pygame

    ink, muted, mint, gold = (226, 247, 255), (121, 159, 185), (73, 233, 245), (243, 202, 117)
    entry = ease_out_cubic(world.level_up.card_progress(0))
    shade = _shade(surface.get_size())
    shade.fill((4, 10, 18, round(170 + 60 * entry)))
    surface.blit(shade, (0, 0))
    target = surface
    surface = _content(target.get_size())
    surface.fill((0, 0, 0, 0))
    surface.set_alpha(255)
    surface.blit(fonts["small"].render("ATUALIZAÇÃO DISPONÍVEL  /  SIMULAÇÃO PAUSADA", True, mint), (70, 153))
    surface.blit(fonts["large"].render("Instale sua próxima melhoria", True, ink), (70, 185))
    mouse = pygame.mouse.get_pos()
    focus = world.effects.selected_card_index
    hovered = next((i for i, rect in enumerate(card_rects()) if pygame.Rect(rect).collidepoint(mouse)), -1)
    active_index = focus if focus >= 0 else hovered if hovered >= 0 else 0
    for index, (card, rect) in enumerate(zip(world.card_choices, card_rects())):
        progress = ease_out_cubic(world.level_up.card_progress(index))
        if progress <= 0:
            continue
        panel = _card_layer(index)
        panel.fill((0, 0, 0, 0))
        x, y, width, height = 8, 8, rect[2], rect[3]
        active = index == active_index
        color = gold if active else mint
        body = (x, y, width, height)
        if active:
            pulse = 0.85 + 0.15 * math.sin(world.level_up.cards_elapsed * 4)
            for pad, alpha in ((7, 18), (4, 30)):
                pygame.draw.rect(panel, (*color, round(alpha * pulse)),
                                 (x - pad, y - pad, width + pad * 2, height + pad * 2), border_radius=15 + pad)
        pygame.draw.rect(panel, (27, 43, 54) if active else (22, 33, 46), body, border_radius=15)
        pygame.draw.rect(panel, color if active else (62, 86, 95), body, 2, border_radius=15)
        pygame.draw.circle(panel, (34, 57, 63), (x + 54, y + 57), 36)
        _icon(pygame, panel, card.id, (x + 54, y + 57), color)
        panel.blit(fonts["body"].render(f"[ {index + 1} ]", True, color), (x + 228, y + 39))
        panel.blit(fonts["body"].render(card.name, True, ink), (x + 23, y + 113))
        _wrapped(panel, fonts["small"], card.description, x + 23, y + 160, muted)
        stacks = world.player.upgrades.get(card.id, 0)
        panel.blit(fonts["small"].render(f"Melhoria {stacks + 1} / {card.max_stacks}", True, color), (x + 23, y + 250))
        pygame.draw.line(panel, (50, 74, 84), (x + 23, y + 282), (x + 277, y + 282))
        if progress < 1:
            pygame.draw.line(panel, color, (x + 23, y + 282), (x + 23 + 254 * progress, y + 282), 2)
        panel.set_alpha(round(255 * progress))
        surface.blit(panel, (rect[0] - 8, rect[1] - 8 + round(CARD_ENTRY_OFFSET * (1 - progress))))
    hint = ("Clique ou use 1/2/3  ·  Setas e Enter também selecionam"
            if world.level_up.selection_ready else "Sincronizando atualizações… aguarde a entrada das cartas")
    surface.blit(fonts["body"].render(hint, True, ink if world.level_up.selection_ready else muted), (70, 619))
    surface.blit(fonts["small"].render(f"Escolhas pendentes: {world.pending_levelups}  /  Efeito permanente nesta partida", True, muted), (70, 657))
    surface.set_alpha(round(160 + 95 * entry))
    target.blit(surface, (0, 0))

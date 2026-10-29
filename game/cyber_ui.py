"""Menu, lore e equipamento do protótipo Cyber Defense."""

from functools import lru_cache

from .balance import WEAPON_CONFIGS
from .weapon_render import weapon_sprite


CYAN = (73, 233, 245)
MAGENTA = (237, 111, 225)
INK = (226, 247, 255)
MUTED = (121, 159, 185)


def menu_rects():
    return [(70, 375, 465, 168), (565, 375, 465, 168)]


def weapon_rects():
    return [(70 + index * 330, 255, 300, 320) for index in range(3)]


def _text(surface, font, value, pos, color=INK):
    surface.blit(font.render(value, True, color), pos)


@lru_cache(maxsize=2)
def _shade(size):
    import pygame
    image = pygame.Surface(size, pygame.SRCALPHA)
    image.fill((3, 7, 19, 239))
    return image


def render_menu(surface, fonts, selected=0, music_status="", clock=0):
    import pygame

    surface.fill((5, 9, 22))
    for x in range(0, 1100, 40):
        pygame.draw.line(surface, (12, 28, 45), (x, 0), (x, 770))
    for y in range(0, 770, 40):
        pygame.draw.line(surface, (12, 28, 45), (0, y), (1100, y))
    for index in range(10):
        x = (index * 137 + 31) % 1100
        y = (index * 91 + int(clock * 12)) % 770
        pygame.draw.line(surface, (53, 31, 72), (x, y), (x + 34, y), 2)
    _text(surface, fonts["small"], "AGENTOS  /  PROTOCOLO DE CONTENÇÃO", (70, 55), CYAN)
    _text(surface, fonts["large"], "CYBER DEFENSE", (70, 95), INK)
    _text(surface, fonts["body"], "SENTINEL-01  //  ANTIVÍRUS ATIVO", (70, 170), MAGENTA)
    _text(surface, fonts["body"], "Vírus, malwares e processos corrompidos invadiram o sistema.", (70, 226), MUTED)
    _text(surface, fonts["body"], "Defenda o núcleo do sistema operacional. Recupere dados e instale atualizações.", (70, 259), MUTED)
    _text(surface, fonts["small"], "SELECIONE UM PROTOCOLO", (70, 333), CYAN)
    descriptions = (("[1]  MODO DEFESA", "6 hordas · ROOTKIT · arma desbloqueada", "Conclua um teste breve e encerre a operação."),
                    ("[2]  MODO LABORATÓRIO", "5 hordas · sem ROOTKIT · seis armas", "Alterne equipamentos em um treino de 45 s."))
    for index, (rect, labels) in enumerate(zip(menu_rects(), descriptions)):
        active = index == selected
        x, y, width, height = rect
        pygame.draw.rect(surface, (19, 37, 56) if active else (12, 23, 41), rect, border_radius=13)
        pygame.draw.rect(surface, CYAN if active else (49, 64, 90), rect, 2, border_radius=13)
        _text(surface, fonts["title"], labels[0], (x + 23, y + 23), CYAN if active else INK)
        _text(surface, fonts["small"], labels[1], (x + 23, y + 84), INK)
        _text(surface, fonts["small"], labels[2], (x + 23, y + 120), MUTED)
    _text(surface, fonts["body"], "1 / 2, clique ou use setas e Enter para iniciar", (70, 590))
    _text(surface, fonts["small"], "WASD/SETAS mover  ·  ATAQUE AUTOMÁTICO  ·  H reparar  ·  I inventário  ·  F2/F3 efeitos", (70, 637), MUTED)
    _text(surface, fonts["small"], music_status, (70, 702), MUTED)
    _text(surface, fonts["small"], "Áudio autoral: Firewall_8bit · velocidade fixa 0,8×     |     ESC sair", (70, 733), MUTED)


def render_weapon_choice(surface, world, fonts):
    import pygame

    surface.blit(_shade(surface.get_size()), (0, 0))
    _text(surface, fonts["small"], "ROOTKIT NEUTRALIZADO" if world.mode.value == "defense" else "LABORATÓRIO DESBLOQUEADO", (70, 154), CYAN)
    _text(surface, fonts["large"], "Selecione seu equipamento", (70, 186))
    ids = ("katana", "bow", "spear")
    descriptions = ("Dois cortes consecutivos por ativação.", "Flechas direcionais de longo alcance.", "Estocada estreita com avanço e retorno.")
    mouse = pygame.mouse.get_pos()
    focus = world.effects.selected_card_index
    hovered = next((i for i, rect in enumerate(weapon_rects()) if pygame.Rect(rect).collidepoint(mouse)), 0)
    active_index = focus if focus >= 0 else hovered
    for index, (weapon_id, rect) in enumerate(zip(ids, weapon_rects())):
        x, y, width, height = rect
        active = index == active_index
        pygame.draw.rect(surface, (18, 34, 53), rect, border_radius=14)
        pygame.draw.rect(surface, CYAN if active else (49, 64, 90), rect, 2, border_radius=14)
        sprite = weapon_sprite(weapon_id)
        sprite = pygame.transform.rotozoom(sprite, 20 if weapon_id != "bow" else 0, 1.5)
        surface.blit(sprite, sprite.get_rect(center=(x + 150, y + 76)))
        _text(surface, fonts["title"], f"[{index + 1}] {WEAPON_CONFIGS[weapon_id].name}", (x + 22, y + 137), CYAN if active else INK)
        from .card_ui import _wrapped
        _wrapped(surface, fonts["small"], descriptions[index], x + 22, y + 195, MUTED)
        _text(surface, fonts["small"], f"Intervalo-base {WEAPON_CONFIGS[weapon_id].cooldown:g} s", (x + 22, y + 270), MUTED)
    rule = "Escolha uma arma para o teste final de 15 segundos." if world.mode.value == "defense" else "Treino: 1 Katana · 2 Arco · 3 Lança · 4 Arco Longo · 5 Retorno · 6 Espada. Até 45 s."
    _text(surface, fonts["body"], "Clique ou pressione 1, 2 ou 3", (70, 620))
    _text(surface, fonts["small"], rule, (70, 663), MUTED)

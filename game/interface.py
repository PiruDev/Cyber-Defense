"""Renderização da arena. Importar este módulo não inicializa o Pygame."""

from functools import lru_cache

from .sprites import potion_sprite, sword_angle, sword_sprite
from .enemy_render import render_enemy, render_enemy_ghosts, render_projectile
from .card_ui import render_cards
from .effect_render import render_effects
from .weapon_render import render_weapon
from .cyber_ui import render_weapon_choice
from .levelup_render import render_levelup_intro, render_levelup_wave
from .player_render import render_player
from .floor import floor_surface


BG = (5, 9, 22)
PANEL = (14, 25, 43)
INK = (226, 247, 255)
MUTED = (121, 159, 185)
MINT = (73, 233, 245)
CORAL = (243, 86, 145)
GOLD = (243, 202, 117)


def create_fonts(pygame):
    return {name: pygame.font.Font(None, size) for name, size in
            (("small", 22), ("body", 27), ("title", 40), ("large", 62))}


def text(surface, font, value, position, color=INK):
    surface.blit(font.render(value, True, color), position)


def bar(pygame, surface, rect, value, maximum, color):
    pygame.draw.rect(surface, (10, 19, 27), rect, border_radius=4)
    filled = max(0, min(1, value / maximum)) if maximum else 0
    if filled:
        pygame.draw.rect(surface, color, (rect[0], rect[1], max(1, int(rect[2] * filled)), rect[3]), border_radius=4)


@lru_cache(maxsize=2)
def _arena_layer(size):
    import pygame

    return pygame.Surface(size)


def render_world(surface, world, fonts):
    import pygame

    surface.fill(BG)
    text(surface, fonts["title"], "CYBER DEFENSE", (32, 20), MINT)
    text(surface, fonts["small"], "SENTINEL-01", (303, 30), MUTED)
    mode_name = "DEFESA" if world.mode.value == "defense" else "LAB"
    text(surface, fonts["small"], f"{mode_name} {world.waves.number}/{world.waves.max_waves}", (600, 27), MINT)
    remaining = f"ALVOS {len(world.enemies)}" if world.phase == "practice" else f"RESTAM {world.waves.remaining}"
    text(surface, fonts["small"], remaining, (737, 27), MUTED)
    text(surface, fonts["small"], f"PONTOS {world.score}", (869, 27), GOLD)
    text(surface, fonts["small"], f"ABATES {world.kills}", (1000, 27), MUTED)

    p = world.player.progression
    for rect in ((32, 65, 420, 61), (466, 65, 420, 61), (900, 65, 168, 61)):
        pygame.draw.rect(surface, PANEL, rect, border_radius=9)
    text(surface, fonts["small"], "INTEGRIDADE", (46, 74), MUTED)
    text(surface, fonts["small"], f"{round(p.hp, 1):g} / {p.hp_maximo:g}", (328, 74), INK)
    bar(pygame, surface, (46, 103, 392, 9), p.hp, p.hp_maximo, CORAL)
    text(surface, fonts["small"], "DADOS RECUPERADOS", (480, 74), MUTED)
    text(surface, fonts["small"], f"{p.xp} / {p.xp_necessario}", (777, 74), MINT)
    bar(pygame, surface, (480, 103, 392, 9), p.xp, p.xp_necessario, MINT)
    text(surface, fonts["small"], "REPARO  [H]", (917, 74), MUTED)
    text(surface, fonts["body"], f"{world.player.inventory.potions:02d}  /  05", (917, 98), GOLD)
    if world.player.overclock_timer > 0:
        text(surface, fonts["small"], f"OC {world.player.overclock_timer:.1f}s", (976, 132), (218, 133, 250))

    # Mundo e colisões usam a mesma coordenada. Só a cópia visível é projetada.
    # O clip limita o trabalho de desenho; o piso é composto uma única vez.
    floor = floor_surface(world.arena)
    scene = _arena_layer(floor.get_size())
    ox, oy = world.camera.origin(world.shake_offset)
    viewport = pygame.Rect(world.camera.viewport)
    source = pygame.Rect(ox, oy, min(viewport.width, world.arena[2]), min(viewport.height, world.arena[3]))
    previous_scene_clip = scene.get_clip()
    scene.set_clip(source)
    scene.blit(floor, source.topleft, source)
    _draw_arena(scene, world)
    scene.set_clip(previous_scene_clip)
    previous_clip = surface.get_clip()
    surface.set_clip(previous_clip.clip(viewport))
    surface.blit(scene, viewport.topleft, source)
    surface.set_clip(previous_clip)
    pygame.draw.rect(surface, (26, 79, 99), viewport.inflate(4, 4), 2, border_radius=5)

    text(surface, fonts["small"], "WASD/SETAS mover   ESPAÇO atacar   H reparar   I inventário   F2/F3 efeitos   M menu   ESC sair", (32, 707), MUTED)
    boss = next((enemy for enemy in world.enemies if getattr(enemy, "kind", "basic") in ("rootkit", "worm")), None)
    if boss:
        text(surface, fonts["small"], "ROOTKIT // BOSS" if boss.kind == "rootkit" else "MALWARE // SEMIBOSS", (32, 735), CORAL if boss.kind == "rootkit" else GOLD)
        bar(pygame, surface, (235, 739, 530, 12), boss.hp, boss.max_hp, GOLD)
        detail = "Resiste a interrupções" if boss.kind == "rootkit" else f"{len(boss.segments)} segmentos"
        text(surface, fonts["small"], f"{boss.hp:g}/{boss.max_hp:g}  |  {detail}", (788, 735), GOLD)
    elif world.phase == "practice":
        rule = "1 Katana · 2 Arco · 3 Lança" if world.mode.value == "laboratory" else "Equipamento selecionado"
        text(surface, fonts["small"], f"TREINO {world.practice_remaining:.1f}s  /  {world.weapons.config.name}  /  {rule}", (32, 735), MINT)
    elif world.waves.preparation_timer > 0:
        text(surface, fonts["body"], f"Prepare-se! Horda {world.waves.number + 1} em {world.waves.preparation_timer:.1f} s", (32, 735), GOLD)
    else:
        boost = f"  ·  OVERCLOCK {world.player.overclock_timer:.1f}s" if world.player.overclock_timer > 0 else ""
        text(surface, fonts["small"], f"{world.weapons.config.name}  /  Atualizações por nível · Reparos e overclock nos drops{boost}", (32, 735), MINT if boost else MUTED)


def _draw_arena(surface, world):
    import pygame

    previous_clip = surface.get_clip()
    surface.set_clip(previous_clip.clip(pygame.Rect(world.arena)))
    for drop in world.drops:
        dx, dy = int(drop.x), int(drop.y)
        pygame.draw.circle(surface, (26, 59, 72), (dx, dy), 17)
        if getattr(drop, "kind", "repair") == "overclock":
            from .sprites import overclock_sprite
            surface.blit(overclock_sprite(28), (dx - 14, dy - 14))
        else:
            surface.blit(potion_sprite(28), (dx - 14, dy - 14))

    render_enemy_ghosts(surface, world.effects)
    for enemy in world.enemies:
        motion = world.enemy_motion.get(id(enemy))
        render_enemy(surface, enemy, effects=world.effects, animation_time=world.elapsed,
                     moving=motion[0] if motion else False,
                     motion_direction=motion[1:] if motion else None)
    for projectile in world.projectiles:
        render_projectile(surface, projectile)

    render_player(surface, world)
    render_weapon(surface, world, image_factory=sword_sprite, angle_function=sword_angle)
    render_levelup_wave(surface, world)
    render_effects(surface, world.effects)
    surface.set_clip(previous_clip)


def render_overlay(surface, world, fonts):
    import pygame

    if world.level_up.state == "LEVEL_UP_INTRO":
        render_levelup_intro(surface, world, fonts)
        return
    if world.choosing_card:
        render_cards(surface, world, fonts)
        return
    if world.choosing_weapon:
        if world.effects.finale_timer <= 0:
            render_weapon_choice(surface, world, fonts)
        return
    if world.victory and world.effects.finale_timer > 0:
        return
    if not world.inventory_open and not world.game_over and not world.victory:
        return
    shade = _overlay_shade(surface.get_size())
    surface.blit(shade, (0, 0))
    pygame.draw.rect(surface, PANEL, (300, 211, 500, 354), border_radius=15)
    pygame.draw.rect(surface, (61, 88, 95), (300, 211, 500, 354), 1, border_radius=15)
    if world.game_over or world.victory:
        text(surface, fonts["small"], "PROTOCOLO CONCLUÍDO" if world.victory else "SENTINEL-01 DESCONECTADO", (340, 245), GOLD if world.victory else CORAL)
        text(surface, fonts["large"], "Vitória!" if world.victory else "Game Over", (340, 283), INK)
        text(surface, fonts["body"], f"{world.kills} abates  /  {world.score} pontos", (340, 352), MUTED)
        text(surface, fonts["body"], "R   Iniciar uma nova jornada", (340, 428), MINT)
        text(surface, fonts["small"], "M   Menu     /     ESC   Sair", (340, 482), MUTED)
    else:
        text(surface, fonts["small"], "PARTIDA PAUSADA", (340, 245), MINT)
        text(surface, fonts["title"], "Pacotes do sistema", (340, 281), INK)
        potions = world.player.inventory.potions
        pygame.draw.rect(surface, (29, 44, 57), (330, 337, 440, 117), border_radius=12)
        pygame.draw.rect(surface, (61, 83, 91), (330, 337, 440, 117), 1, border_radius=12)
        pygame.draw.line(surface, GOLD if potions else MUTED, (332, 355), (332, 435), 3)
        pygame.draw.rect(surface, (41, 56, 62), (345, 360, 70, 70), border_radius=10)
        surface.blit(potion_sprite(64), (348, 363))
        pygame.draw.rect(surface, (86, 90, 71), (345, 360, 70, 70), 1, border_radius=10)
        text(surface, fonts["body"], "Pacote de reparo", (433, 350), GOLD if potions else MUTED)
        text(surface, fonts["body"], f"Quantidade  {potions} / {world.player.inventory.max_potions}", (433, 384), INK)
        text(surface, fonts["small"], "Recupera 35 HP, até o máximo.", (433, 420), MUTED)
        text(surface, fonts["body"], "H   Aplicar reparo" if potions else "Sem pacotes", (340, 476), MINT if potions else MUTED)
        text(surface, fonts["small"], f"I   Continuar   /   {sum(world.player.upgrades.values())} melhorias", (340, 518), MUTED)
        text(surface, fonts["small"], f"Shake {world.effects.settings.shake_scale:.0%}  /  Partículas {world.effects.settings.particle_scale:.0%}", (340, 543), MUTED)


@lru_cache(maxsize=2)
def _overlay_shade(size):
    import pygame
    shade = pygame.Surface(size, pygame.SRCALPHA)
    shade.fill((4, 10, 18, 205))
    return shade

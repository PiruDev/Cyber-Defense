"""Ponto de entrada do RPG de arena AgentOS, sem efeitos ao importar."""

import asyncio
import sys

if __package__:
    from .progression import Progressao
    from .world import GameWorld
    from .interface import create_fonts, render_world, render_overlay
    from .card_ui import card_rects
    from .audio import AudioBus
    from .effect_render import render_effects, render_confirmation
    from .cyber_ui import render_menu, menu_rects, weapon_rects
    from .music import MusicPlayer
    from .modes import GameMode
else:
    # Permite também executar diretamente: python game/main.py.
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from game.progression import Progressao
    from game.world import GameWorld
    from game.interface import create_fonts, render_world, render_overlay
    from game.card_ui import card_rects
    from game.audio import AudioBus
    from game.effect_render import render_effects, render_confirmation
    from game.cyber_ui import render_menu, menu_rects, weapon_rects
    from game.music import MusicPlayer
    from game.modes import GameMode


def desenhar_hud(tela, fonte, progressao: Progressao, *, compacto=False, damage=None) -> None:
    """Desenha os atributos atuais sem alterar as regras de progressão."""
    linhas = (
        f"Nível: {progressao.nivel}",
        f"{'Dados' if compacto else 'XP'}: {progressao.xp}/{progressao.xp_necessario}",
        f"HP: {round(progressao.hp, 1):g}/{progressao.hp_maximo:g}",
        f"Dano: {progressao.dano if damage is None else round(damage, 2):g}",
    )
    for indice, texto in enumerate(linhas):
        imagem = fonte.render(texto, True, (240, 240, 245))
        posicao = (40 + indice * 260, 132) if compacto else (16, 16 + indice * 28)
        tela.blit(imagem, posicao)


async def main_async(*, max_frames=None, capture_path=None, start_mode=None) -> None:
    """max_frames limita smoke tests; capture_path salva o último quadro."""
    if max_frames is not None and (not isinstance(max_frames, int) or max_frames < 1):
        raise ValueError("max_frames deve ser um inteiro positivo")
    import pygame

    browser = sys.platform == "emscripten"
    audio = None
    music = None
    try:
        pygame.init()
        tela = pygame.display.set_mode((1100, 770))
        pygame.display.set_caption("AgentOS | CYBER DEFENSE — SENTINEL-01")
        relogio = pygame.time.Clock()
        fontes = create_fonts(pygame)
        mundo = GameWorld()
        menu_active = start_mode is None
        if start_mode is not None and mundo.mode != GameMode(start_mode):
            mundo.restart(mode=start_mode)
        menu_index = 0
        presentation_clock = 0.0
        audio = AudioBus(mundo.effects.settings)
        music = MusicPlayer(mundo.effects.settings)
        if not browser:
            music.start()
        executando = True
        quadros = 0

        while executando:
            # No navegador o agendador WASM fornece o ritmo: tick(60) bloquearia.
            ui_dt = relogio.tick(0 if browser else 60) / 1000.0
            # Interface usa tempo real; animações e regras têm um passo limitado.
            dt = min(ui_dt, 0.05)
            presentation_clock += ui_dt
            choosing_at_start = mundo.choosing_card or mundo.choosing_weapon
            # Entradas anteriores ao último quadro da entrada não ficam em fila.
            card_input_ready = mundo.choosing_card and mundo.level_up.selection_ready
            # A partida encerrada congela regras, mas deixa a dispersão terminar.
            weapon_ready = mundo.choosing_weapon and mundo.effects.finale_timer <= 0
            paused = menu_active or mundo.inventory_open or mundo.choosing_card or weapon_ready
            simulation_dt = mundo.effects.update(dt, paused=paused)
            if not menu_active:
                mundo.advance_presentation(ui_dt)
            selected = False
            for evento in pygame.event.get():
                if browser and evento.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                    music.start()
                if evento.type == pygame.QUIT:
                    executando = False
                elif evento.type == pygame.KEYDOWN:
                    if evento.key == pygame.K_ESCAPE:
                        executando = False
                    elif evento.key == pygame.K_F2:
                        value = mundo.effects.settings.shake_scale
                        mundo.effects.settings.shake_scale = 0.5 if value > 0.5 else 0.0 if value > 0 else 1.0
                    elif evento.key == pygame.K_F3:
                        value = mundo.effects.settings.particle_scale
                        mundo.effects.settings.particle_scale = 0.5 if value > 0.5 else 0.0 if value > 0 else 1.0
                    elif evento.key == pygame.K_m:
                        menu_active = True
                        selected = True
                    elif menu_active:
                        if evento.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN):
                            menu_index = 1 - menu_index
                        elif evento.key in (pygame.K_1, pygame.K_2, pygame.K_RETURN, pygame.K_KP_ENTER):
                            if evento.key in (pygame.K_1, pygame.K_2):
                                menu_index = 0 if evento.key == pygame.K_1 else 1
                            mundo.restart(mode=GameMode.DEFENSE if menu_index == 0 else GameMode.LABORATORY)
                            menu_active = False
                            selected = True
                    elif (mundo.choosing_card or (mundo.choosing_weapon and mundo.effects.finale_timer <= 0)) and not selected:
                        if mundo.choosing_card and (not card_input_ready or getattr(evento, "repeat", False)):
                            continue
                        indexes = {pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2,
                                   pygame.K_KP1: 0, pygame.K_KP2: 1, pygame.K_KP3: 2}
                        if evento.key in indexes:
                            choose = mundo.choose_card if mundo.choosing_card else mundo.choose_weapon
                            selected = choose(indexes[evento.key])
                        elif evento.key in (pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d):
                            direction = 1 if evento.key in (pygame.K_RIGHT, pygame.K_d) else -1
                            current = mundo.effects.selected_card_index
                            mundo.effects.selected_card_index = ((0 if current < 0 else current) + direction) % 3
                        elif evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                            index = mundo.effects.selected_card_index
                            if index < 0:
                                position = pygame.mouse.get_pos()
                                rects = card_rects() if mundo.choosing_card else weapon_rects()
                                index = next((i for i, rect in enumerate(rects)
                                              if pygame.Rect(rect).collidepoint(position)), 0)
                            choose = mundo.choose_card if mundo.choosing_card else mundo.choose_weapon
                            selected = choose(index)
                    elif (mundo.phase == "practice" and mundo.mode == GameMode.LABORATORY
                          and evento.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6)):
                        selected = mundo.switch_weapon(evento.key - pygame.K_1)
                    elif evento.key == pygame.K_i:
                        mundo.toggle_inventory()
                    elif evento.key == pygame.K_h:
                        mundo.use_potion()
                    elif evento.key == pygame.K_r and (mundo.game_over or mundo.victory):
                        mundo.restart()
                elif (evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1
                      and not selected and (menu_active or mundo.choosing_card
                                            or (mundo.choosing_weapon and mundo.effects.finale_timer <= 0))):
                    if not menu_active and mundo.choosing_card and not card_input_ready:
                        continue
                    rects = menu_rects() if menu_active else card_rects() if mundo.choosing_card else weapon_rects()
                    for index, rect in enumerate(rects):
                        if pygame.Rect(rect).collidepoint(evento.pos):
                            if menu_active:
                                menu_index = index
                                mundo.restart(mode=GameMode.DEFENSE if index == 0 else GameMode.LABORATORY)
                                menu_active = False
                                selected = True
                            else:
                                choose = mundo.choose_card if mundo.choosing_card else mundo.choose_weapon
                                selected = choose(index)
                            break
                elif evento.type == pygame.MOUSEMOTION:
                    if menu_active:
                        menu_index = next((i for i, rect in enumerate(menu_rects())
                                           if pygame.Rect(rect).collidepoint(evento.pos)), menu_index)
                    elif (mundo.choosing_card and card_input_ready) or mundo.choosing_weapon:
                        mundo.effects.selected_card_index = -1

            teclas = pygame.key.get_pressed()
            dx = int(teclas[pygame.K_d] or teclas[pygame.K_RIGHT]) - int(teclas[pygame.K_a] or teclas[pygame.K_LEFT])
            dy = int(teclas[pygame.K_s] or teclas[pygame.K_DOWN]) - int(teclas[pygame.K_w] or teclas[pygame.K_UP])
            # O tempo deste quadro pertence à escolha, mesmo após a confirmação.
            if (not choosing_at_start and not selected and simulation_dt > 0
                    and not menu_active and not mundo.game_over and not mundo.victory):
                mundo.update(simulation_dt, dx, dy)
            audio.play_events(mundo.effects.consume_events())
            music.updatevolume()
            if menu_active:
                render_menu(tela, fontes, menu_index, music.status, presentation_clock)
            else:
                render_world(tela, mundo, fontes)
                desenhar_hud(tela, fontes["small"], mundo.player.progression, compacto=True,
                             damage=mundo.player.damage * mundo.weapons.config.damage_multiplier)
                render_overlay(tela, mundo, fontes)
                render_effects(tela, mundo.effects, ui=True)
                render_confirmation(tela, mundo.effects)
            pygame.display.flip()
            quadros += 1
            if max_frames is not None and quadros >= max_frames:
                executando = False
            await asyncio.sleep(0)
        if capture_path is not None:
            pygame.image.save(tela, str(capture_path))
    finally:
        if music is not None:
            music.close()
        if audio is not None:
            audio.close()
        pygame.quit()


def main(*, max_frames=None, capture_path=None, start_mode=None) -> None:
    """Entrada desktop síncrona preservada; o navegador aguarda main_async."""
    asyncio.run(main_async(max_frames=max_frames, capture_path=capture_path, start_mode=start_mode))


if __name__ == "__main__":
    main()

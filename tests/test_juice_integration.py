import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import unittest


@unittest.skipUnless(importlib.util.find_spec("pygame"), "Pygame não instalado")
class JuiceIntegrationTests(unittest.TestCase):
    def executar(self, script):
        ambiente = os.environ.copy()
        ambiente.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy", PYGAME_HIDE_SUPPORT_PROMPT="1")
        resultado = subprocess.run(
            [sys.executable, "-c", script], cwd=Path(__file__).resolve().parents[1],
            env=ambiente, capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(resultado.returncode, 0, resultado.stdout + resultado.stderr)

    def test_audio_sem_device_falhas_sound_play_e_limite_quatro_vozes(self):
        self.executar('''
from unittest.mock import Mock, patch
import pygame
from game.audio import AudioBus
from game.effects import EffectEvent
from game.settings import EffectSettings

settings = EffectSettings()
pygame.mixer.quit()
with patch.object(pygame.mixer, "init", side_effect=pygame.error("sem dispositivo")):
    bus = AudioBus(settings)
    assert not bus.enabled
    bus.play_events([EffectEvent("hit", 0, 0)])
    bus.close()
pygame.mixer.init()
with patch.object(pygame.mixer, "Sound", side_effect=pygame.error("som indisponível")):
    bus = AudioBus(settings)
    assert not bus.enabled
    bus.close()
bus = AudioBus(settings)
assert bus.enabled
voices = [Mock() for _ in range(8)]
for voice in voices:
    voice.get_busy.return_value = False
bus._channels = voices
events = [EffectEvent("hit", 0, 0) for _ in range(100)]
bus.play_events(events)
assert sum(voice.play.call_count for voice in voices) == 4
bus.play_events([])
assert sum(voice.play.call_count for voice in voices) == 4
voices[0].play.side_effect = pygame.error("canal perdido")
bus.play_events(events)
assert not bus.enabled
for voice in voices:
    voice.stop.side_effect = pygame.error("já fechado")
bus.close()
bus.close()
with patch.object(pygame.mixer, "init", side_effect=AssertionError("não abrir áudio desativado")):
    muted = AudioBus(EffectSettings(audio_enabled=False))
    assert not muted.enabled
    muted.close()
pygame.quit()
''')

    def test_main_hitstop_residual_um_tick_fx_por_frame_e_toggles(self):
        self.executar('''
from pathlib import Path
import random
from unittest.mock import Mock, patch
import pygame
from game import main as app
from game.world import GameWorld
from game.enemies import Enemy

world = GameWorld(rng=random.Random(17))
world.enemies = [Enemy(world.player.x + 45, world.player.y, speed=0)]
world.player.facing_x, world.player.facing_y = 1, 0
world.effects.consume_events()
start_x = world.player.x
frame = 0
def events():
    global frame
    frame += 1
    if frame > 1:
        return [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F2),
                pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F3)]
    return []
class Keys:
    def __getitem__(self, key):
        return key == pygame.K_d or (key == pygame.K_SPACE and frame == 1)
clock = Mock()
clock.tick.return_value = 16
audio = Mock()
reports = Path("reports")
reports.mkdir(exist_ok=True)
with patch.object(app, "GameWorld", return_value=world), \\
     patch.object(app, "AudioBus", return_value=audio), \\
     patch.object(pygame.time, "Clock", return_value=clock), \\
     patch.object(pygame.event, "get", side_effect=events), \\
     patch.object(pygame.key, "get_pressed", return_value=Keys()), \\
     patch.object(world.effects, "update", wraps=world.effects.update) as fx_tick, \\
     patch.object(world.effects, "consume_events", wraps=world.effects.consume_events) as consume, \\
     patch.object(world, "update", wraps=world.update) as simulation:
    app.main(max_frames=4, capture_path=reports / "mission006-main.png", start_mode="defense")
    assert fx_tick.call_count == 4
    assert consume.call_count == audio.play_events.call_count == 4
    assert simulation.call_count == 2
    assert abs(simulation.call_args_list[1].args[0] - 0.008) < 1e-9
    delivered = [event for call in audio.play_events.call_args_list for event in call.args[0]]
    assert sum(event.kind == "hit" for event in delivered) == 1
assert abs(world.elapsed - 0.024) < 1e-9
assert abs(world.player.x - start_x - 220 * 0.024) < 1e-9
assert world.enemies[0].hp == 2
assert world.effects.settings.shake_scale == world.effects.settings.particle_scale == 1
audio.close.assert_called_once()
assert not pygame.get_init()
''')

    def test_render_fx_alpha_cartas_foco_pausa_e_capturas(self):
        self.executar('''
from pathlib import Path
import pickle
import random
from unittest.mock import patch
import pygame
from game import main as app
from game import interface as ui
from game.effect_render import render_effects, render_confirmation
from game.enemy_render import render_enemy
from game.card_ui import card_rects
from game.effects import EffectSystem
from game.enemies import Enemy, Drop
from game.worm import Worm
from game.world import GameWorld

pygame.init()
try:
    screen = pygame.display.set_mode((1100, 770))
    fonts = ui.create_fonts(pygame)
    reports = Path("reports")
    reports.mkdir(exist_ok=True)
    def world():
        state = GameWorld(rng=random.Random(11))
        state.enemies.clear()
        state.player.facing_x, state.player.facing_y = 1, 0
        state.effects.consume_events()
        return state
    def draw(state, name):
        before = pickle.dumps(state)
        ui.render_world(screen, state, fonts)
        app.desenhar_hud(screen, fonts["small"], state.player.progression,
                         compacto=True, damage=state.player.damage)
        ui.render_overlay(screen, state, fonts)
        render_effects(screen, state.effects, ui=True)
        render_confirmation(screen, state.effects)
        assert pickle.dumps(state) == before
        pygame.image.save(screen, reports / ("mission006-" + name + ".png"))

    state = world()
    state.enemies = [Enemy(state.player.x + 45, state.player.y, speed=0)]
    state.update(0, attack=True)
    draw(state, "hit")
    state = world()
    state.enemies = [Enemy(state.player.x + 45, state.player.y, hp=0.2, speed=0)]
    state.update(0, attack=True)
    state.effects.update(0.08)
    draw(state, "death")
    state = world()
    state.player.progression.dano = 100
    worm = Worm(state.player.x + 45, state.player.y, speed=0)
    for index, segment in enumerate(worm.segments):
        segment.x = worm.x + index * 32
        segment.y = worm.y
    state.enemies = [worm]
    state.update(0, attack=True)
    assert len(worm.segments) == 5
    draw(state, "worm-rupture")
    state = world()
    state.player.inventory.potions = 5
    state.drops = [Drop(state.player.x, state.player.y)]
    state.update(0)
    draw(state, "score")
    assert state.effects.texts[0].text == "+10 pontos"
    state = world()
    state.grant_xp(250)
    state.advance_presentation(0.8)
    state.effects.update(0.1, paused=True)
    state.effects.selected_card_index = 1
    with patch.object(pygame.mouse, "get_pos", return_value=pygame.Rect(card_rects()[0]).center):
        draw(state, "cards")
        # O foco de teclado prevalece sobre hover em outra carta.
        assert screen.get_at((550, 255))[:3] == (243, 202, 117)
    ui_layer = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    render_effects(ui_layer, state.effects, ui=True)
    assert 0 < ui_layer.get_bounding_rect().bottom < 255, "Partículas cobriram os cards"
    state.choose_card(1)
    assert state.pending_levelups == 1
    draw(state, "confirmation")
    state.advance_presentation(0.8)
    state.choose_card(0)
    state.toggle_inventory()
    draw(state, "inventory")

    # O mesmo texto em dois tempos não pode reutilizar alpha incorreto do cache.
    fx = EffectSystem()
    fx.emit("hit", 100, 100, damage=2)
    fx.particles.clear()
    layer = pygame.Surface((200, 200), pygame.SRCALPHA)
    render_effects(layer, fx)
    early_alpha = sum(layer.get_at((x, y)).a for x in range(70, 130) for y in range(60, 100))
    fx.update(0.60)
    layer.fill((0, 0, 0, 0))
    render_effects(layer, fx)
    late_alpha = sum(layer.get_at((x, y)).a for x in range(70, 130) for y in range(35, 100))
    assert 0 < late_alpha < early_alpha
    fx.update(0.06)
    assert fx.texts == []
    # Inimigos intactos não exibem HP; dano torna a barra temporariamente visível.
    enemy = Enemy(50, 60)
    layer = pygame.Surface((100, 100))
    layer.fill((0, 0, 0))
    render_enemy(layer, enemy)
    # MISSÃO011: sprite básico 1,5x; barra deslocada acima do corpo ampliado.
    assert layer.get_at((50, 26))[:3] == (0, 0, 0)
    enemy.hp_bar_timer = 0.35
    render_enemy(layer, enemy)
    assert layer.get_at((50, 26))[:3] != (0, 0, 0)
    enemy.advance_feedback(0.36, (0, 0, 100, 100))
    layer.fill((0, 0, 0))
    render_enemy(layer, enemy)
    assert layer.get_at((50, 26))[:3] == (0, 0, 0)
finally:
    pygame.quit()
''')

    def test_main_foco_setas_enter_e_hover_preservam_fila_e_pausa(self):
        self.executar('''
from unittest.mock import Mock, patch
import pygame
from game import main as app
from game.card_ui import card_rects
from game.world import GameWorld

world = GameWorld()
world.enemies.clear()
world.grant_xp(250)
frame = 0
def events():
    global frame
    frame += 1
    if frame == 50:
        return [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT)]
    if frame == 51 or frame == 102:
        return [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)]
    if frame == 101:
        return [pygame.event.Event(pygame.MOUSEMOTION, pos=pygame.Rect(card_rects()[2]).center)]
    return []
class Keys:
    def __getitem__(self, key):
        return key in (pygame.K_SPACE, pygame.K_d)
clock = Mock()
clock.tick.return_value = 16
with patch.object(app, "GameWorld", return_value=world), \\
     patch.object(app, "AudioBus", return_value=Mock()), \\
     patch.object(pygame.time, "Clock", return_value=clock), \\
     patch.object(pygame.event, "get", side_effect=events), \\
     patch.object(pygame.mouse, "get_pos", return_value=pygame.Rect(card_rects()[2]).center), \\
     patch.object(pygame.key, "get_pressed", return_value=Keys()), \\
     patch.object(world, "choose_card", wraps=world.choose_card) as choose, \\
     patch.object(world, "update", wraps=world.update) as simulation:
    app.main(max_frames=102, start_mode="defense")
    assert [call.args[0] for call in choose.call_args_list] == [1, 2]
    assert simulation.call_count == 0
assert world.pending_levelups == 0
assert sum(world.player.upgrades.values()) == 2
assert world.elapsed == world.attack_timer == 0
assert not pygame.get_init()
''')

    def test_main_ultimo_verme_anima_morte_antes_escolha_arma_sem_xp_extra(self):
        self.executar('''
from pathlib import Path
from unittest.mock import Mock, patch
import pygame
from game import main as app
from game.world import GameWorld
from game.worm import Worm, Segment
from game import interface as ui

world = GameWorld(mode="laboratory")
world.drops.clear()
world.effects.consume_events()
world.player.facing_x, world.player.facing_y = 1, 0
world.player.progression.dano = 100
world.waves.number = 5
world.waves.specs = world.waves._make_specs()
world.waves.spawned = world.waves.total
world.waves.defeated = world.waves.total - 1
world.kills = 50
x, y = world.player.x + 45, world.player.y
world.enemies = [Worm(x, y, segments=[Segment(x, y)])]
frame = 0
def events():
    global frame
    frame += 1
    return []
class Keys:
    def __getitem__(self, key):
        return frame == 1 and key == pygame.K_SPACE
clock = Mock()
clock.tick.return_value = 50
real_overlay = app.render_overlay
reports = Path("reports")
reports.mkdir(exist_ok=True)
def overlay(screen, state, fonts):
    real_overlay(screen, state, fonts)
    assert state.choosing_weapon and not state.victory
    assert state.kills == 51 and state.player.progression.xp == 25
    assert abs(state.elapsed - 0.05) < 1e-9
    if frame == 1:
        assert state.effects.finale_timer == 0.45
        assert state.effects.particles
        assert screen.get_at((310, 230))[:3] != (22, 33, 46)
        pygame.image.save(screen, reports / "mission006-finale-start.png")
    if frame == 3:
        assert state.effects.finale_timer > 0
        assert state.effects.particles
        assert screen.get_at((310, 230))[:3] != (22, 33, 46)
        pygame.image.save(screen, reports / "mission006-finale-middle.png")
    if frame == 11:
        assert state.effects.finale_timer == 0
        assert state.effects.particles == []
        assert weapon_overlay.call_count >= 1
with patch.object(app, "GameWorld", return_value=world), \\
     patch.object(app, "AudioBus", return_value=Mock()), \\
     patch.object(pygame.time, "Clock", return_value=clock), \\
     patch.object(pygame.event, "get", side_effect=events), \\
     patch.object(pygame.key, "get_pressed", return_value=Keys()), \\
     patch.object(app, "render_overlay", side_effect=overlay), \\
     patch.object(ui, "render_weapon_choice", wraps=ui.render_weapon_choice) as weapon_overlay, \\
     patch.object(world.effects, "update", wraps=world.effects.update) as fx:
    app.main(max_frames=11, capture_path=reports / "mission006-finale-weapon.png", start_mode="laboratory")
    assert fx.call_count == 11
    assert all(not call.kwargs["paused"] for call in fx.call_args_list[:9])
assert world.kills == 51 and world.player.progression.xp == 25
assert not pygame.get_init()
''')


if __name__ == "__main__":
    unittest.main()

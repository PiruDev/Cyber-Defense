import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import unittest


@unittest.skipUnless(importlib.util.find_spec("pygame"), "Pygame não instalado")
class Mission008IntegrationTests(unittest.TestCase):
    def executar(self, script):
        ambiente = os.environ.copy()
        ambiente.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy", PYGAME_HIDE_SUPPORT_PROMPT="1")
        resultado = subprocess.run([sys.executable, "-c", script],
            cwd=Path(__file__).resolve().parents[1], env=ambiente,
            capture_output=True, text=True, timeout=30)
        self.assertEqual(resultado.returncode, 0, resultado.stdout + resultado.stderr)

    def test_main_intro_entrada_input_prematuro_repeat_fila_e_som_unico(self):
        self.executar('''
from pathlib import Path
from unittest.mock import Mock, patch
import pygame
from game import main as app
from game.archer import Archer
from game.card_ui import card_rects
from game.projectiles import Projectile
from game.world import GameWorld

world = GameWorld()
enemy = Archer(world.player.x + 80, world.player.y, speed=0,
               state="windup", telegraph_timer=0.3)
world.enemies = [enemy]
world.projectiles = [Projectile(world.player.x, world.player.y, 180, 0)]
world.player.overclock_timer = 5
world.attack_cooldown = 0.3
world.grant_xp(250)
start_x = world.player.x
frame = 0
clock = Mock()
clock.tick.return_value = 50
audio = Mock()
reports = Path("reports")
reports.mkdir(exist_ok=True)
def events():
    global frame
    frame += 1
    if frame == 2:
        return [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_1),
                pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                    pos=pygame.Rect(card_rects()[2]).center)]
    if frame == 16:
        return [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)]
    if frame == 17:
        return [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_1, repeat=True)]
    if frame == 18:
        return [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                    pos=pygame.Rect(card_rects()[2]).center),
                pygame.event.Event(pygame.KEYDOWN, key=pygame.K_1)]
    if frame == 35:
        return [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_2)]
    return []
class Keys:
    def __getitem__(self, key):
        return key in (pygame.K_d, pygame.K_SPACE)
real_flip = pygame.display.flip
def snapshot():
    real_flip()
    screen = pygame.display.get_surface()
    if frame <= 35:
        assert world.elapsed == 0 and world.player.x == start_x
        assert world.player.progression.hp == world.player.progression.hp_maximo
        assert world.player.overclock_timer == 5
        assert world.attack_cooldown == 0.3
        assert enemy.telegraph_timer == 0.3
        assert world.projectiles[0].ttl == 4
    if frame in (2, 16, 17):
        assert world.pending_levelups == 2
    if frame in (5, 12, 16):
        name = {5: "levelup-intro", 12: "cards-entering", 16: "cards-ready"}[frame]
        pygame.image.save(screen, reports / ("mission008-" + name + ".png"))
    if frame == 18:
        assert world.pending_levelups == 1
        assert world.level_up.state.value == "LEVEL_UP_INTRO"
    if frame == 36:
        assert abs(world.elapsed - 0.05) < 1e-9
        assert world.player.x > start_x
        assert world.player.overclock_timer < 5
with patch.object(app, "GameWorld", return_value=world), \\
     patch.object(app, "AudioBus", return_value=audio), \\
     patch.object(app, "MusicPlayer", return_value=Mock(status="")), \\
     patch.object(pygame.time, "Clock", return_value=clock), \\
     patch.object(pygame.event, "get", side_effect=events), \\
     patch.object(pygame.key, "get_pressed", return_value=Keys()), \\
     patch.object(pygame.display, "flip", side_effect=snapshot), \\
     patch.object(world, "choose_card", wraps=world.choose_card) as choose:
    app.main(max_frames=36, start_mode="defense")
    assert [call.args[0] for call in choose.call_args_list] == [2, 1]
delivered = [event for call in audio.play_events.call_args_list for event in call.args[0]]
assert sum(event.kind == "cards_show" for event in delivered) == 2
assert sum(event.kind == "card_select" for event in delivered) == 2
assert world.pending_levelups == 0
assert not pygame.get_init()
''')

    def test_hitch_usa_tempo_real_intro_sem_simulacao_ou_selecao_oculta(self):
        self.executar('''
from unittest.mock import Mock, patch
import pygame
from game import main as app
from game.world import GameWorld

world = GameWorld()
world.enemies.clear()
world.grant_xp(100)
frame = 0
def events():
    global frame
    frame += 1
    if frame <= 2:
        return [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_1)]
    return []
class Keys:
    def __getitem__(self, key):
        return False
clock = Mock()
clock.tick.side_effect = [3000, 16, 16]
flip = pygame.display.flip
def check():
    flip()
    if frame == 1:
        assert world.level_up.selection_ready
        assert world.pending_levelups == 1 and world.elapsed == 0
    if frame == 2:
        assert world.pending_levelups == 0 and world.elapsed == 0
with patch.object(app, "GameWorld", return_value=world), \\
     patch.object(app, "AudioBus", return_value=Mock()), \\
     patch.object(app, "MusicPlayer", return_value=Mock(status="")), \\
     patch.object(pygame.time, "Clock", return_value=clock), \\
     patch.object(pygame.event, "get", side_effect=events), \\
     patch.object(pygame.key, "get_pressed", return_value=Keys()), \\
     patch.object(pygame.display, "flip", side_effect=check), \\
     patch.object(world, "choose_card", wraps=world.choose_card) as choose:
    app.main(max_frames=3, start_mode="defense")
    assert choose.call_count == 1
assert abs(world.elapsed - 0.016) < 1e-9
''')

    def test_menu_aberto_durante_intro_aceita_click_e_limpa_estado(self):
        self.executar('''
from unittest.mock import Mock, patch
import pygame
from game import main as app
from game.cyber_ui import menu_rects
from game.modes import GameMode
from game.world import GameWorld

world = GameWorld()
world.grant_xp(250)
frame = 0
def events():
    global frame
    frame += 1
    if frame == 1:
        return [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_m)]
    if frame == 2:
        return [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                pos=pygame.Rect(menu_rects()[1]).center)]
    return []
class Keys:
    def __getitem__(self, key):
        return False
clock = Mock()
clock.tick.return_value = 16
with patch.object(app, "GameWorld", return_value=world), \\
     patch.object(app, "AudioBus", return_value=Mock()), \\
     patch.object(app, "MusicPlayer", return_value=Mock(status="")), \\
     patch.object(pygame.time, "Clock", return_value=clock), \\
     patch.object(pygame.event, "get", side_effect=events), \\
     patch.object(pygame.key, "get_pressed", return_value=Keys()):
    app.main(max_frames=3, start_mode="defense")
assert world.mode == GameMode.LABORATORY
assert not world.level_up.active and not world.choosing_card
assert world.pending_levelups == 0
assert abs(world.elapsed - 0.016) < 1e-9
assert not pygame.get_init()
''')

    def test_audio_som_apenas_cards_show_e_render_separacao_imutavel(self):
        self.executar('''
from pathlib import Path
import pickle
from unittest.mock import Mock
import pygame
from game.audio import AudioBus
from game.effects import EffectEvent
from game.settings import EffectSettings
from game.world import GameWorld
from game.enemies import Enemy
from game.boss import Rootkit
from game import interface as ui
from game import main as app

pygame.init()
try:
    bus = AudioBus(EffectSettings())
    assert bus.enabled
    voice = Mock()
    voice.get_busy.return_value = False
    bus._channels = [voice]
    bus.play_events([EffectEvent("levelup", 0, 0)])
    assert voice.play.call_count == 0
    bus.play_events([EffectEvent("cards_show", 0, 0)])
    assert voice.play.call_count == 1
    bus.play_events([])
    assert voice.play.call_count == 1
    bus.close()
    screen = pygame.display.set_mode((1100, 770))
    fonts = ui.create_fonts(pygame)
    world = GameWorld()
    world.enemies = [Enemy(780, 400, speed=0) for _ in range(9)] + [Rootkit(780, 400, speed=0)]
    for _ in range(180):
        world.physics.update(world.enemies, world.arena, 1 / 60)
    before = pickle.dumps(world)
    ui.render_world(screen, world, fonts)
    app.desenhar_hud(screen, fonts["small"], world.player.progression,
                     compacto=True, damage=world.player.damage)
    ui.render_overlay(screen, world, fonts)
    assert pickle.dumps(world) == before
    reports = Path("reports")
    reports.mkdir(exist_ok=True)
    pygame.image.save(screen, reports / "mission008-separation.png")
finally:
    pygame.quit()
''')


if __name__ == "__main__":
    unittest.main()

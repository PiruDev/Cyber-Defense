import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import unittest


@unittest.skipUnless(importlib.util.find_spec("pygame"), "Pygame não instalado")
class Mission007IntegrationTests(unittest.TestCase):
    def executar(self, script):
        ambiente = os.environ.copy()
        ambiente.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy", PYGAME_HIDE_SUPPORT_PROMPT="1")
        resultado = subprocess.run([sys.executable, "-c", script],
            cwd=Path(__file__).resolve().parents[1], env=ambiente,
            capture_output=True, text=True, timeout=30)
        self.assertEqual(resultado.returncode, 0, resultado.stdout + resultado.stderr)

    def test_menu_padrao_teclado_mouse_retorno_e_musica_nao_reinicia(self):
        self.executar('''
from pathlib import Path
from unittest.mock import Mock, patch
import pygame
from game import main as app
from game.cyber_ui import menu_rects
from game.modes import GameMode
from game.world import GameWorld

world = GameWorld()
frame = 0
clock = Mock()
clock.tick.return_value = 16
music = Mock(status="Música opcional ausente.")
reports = Path("reports")
reports.mkdir(exist_ok=True)
def events():
    global frame
    frame += 1
    if frame == 2:
        return [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_2)]
    if frame == 4:
        return [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_m)]
    if frame == 5:
        return [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                pos=pygame.Rect(menu_rects()[0]).center)]
    if frame == 7:
        return [pygame.event.Event(pygame.QUIT)]
    return []
class Keys:
    def __getitem__(self, key):
        return False
flip = pygame.display.flip
def snapshot():
    flip()
    if frame == 1:
        assert world.elapsed == 0
        pygame.image.save(pygame.display.get_surface(), reports / "mission007-menu.png")
    if frame == 3:
        assert world.mode == GameMode.LABORATORY
        assert abs(world.elapsed - 0.016) < 1e-9
        pygame.image.save(pygame.display.get_surface(), reports / "mission007-laboratory.png")
    if frame == 6:
        assert world.mode == GameMode.DEFENSE
        assert world.waves.max_waves == 6
        assert abs(world.elapsed - 0.016) < 1e-9
        pygame.image.save(pygame.display.get_surface(), reports / "mission007-defense.png")
with patch.object(app, "GameWorld", return_value=world), \\
     patch.object(app, "AudioBus", return_value=Mock()), \\
     patch.object(app, "MusicPlayer", return_value=music), \\
     patch.object(pygame.time, "Clock", return_value=clock), \\
     patch.object(pygame.event, "get", side_effect=events), \\
     patch.object(pygame.key, "get_pressed", return_value=Keys()), \\
     patch.object(pygame.display, "flip", side_effect=snapshot), \\
     patch.object(world, "restart", wraps=world.restart) as restart:
    app.main(max_frames=8)
    assert restart.call_count == 2
music.start.assert_called_once()
music.close.assert_called_once()
assert frame == 7
assert not pygame.get_init()
''')

    def test_rootkit_morte_animada_escolha_unica_pratica_vitoria_restart(self):
        self.executar('''
from pathlib import Path
from unittest.mock import Mock, patch
import pygame
from game import main as app
from game.boss import Rootkit
from game.cyber_ui import weapon_rects
from game.world import GameWorld

world = GameWorld()
world.player.facing_x, world.player.facing_y = 1, 0
world.waves.number = 6
world.waves.specs = world.waves._make_specs()
world.waves.spawned = 1
world.enemies = [Rootkit(world.player.x + 45, world.player.y, hp=0.2, speed=0)]
world.player.progression.xp = 0
world.effects.consume_events()
frame = 0
clock = Mock()
clock.tick.return_value = 50
reports = Path("reports")
reports.mkdir(exist_ok=True)
def events():
    global frame
    frame += 1
    if frame == 2:
        return [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_1)]
    if frame == 12:
        return [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                pos=pygame.Rect(weapon_rects()[1]).center),
                pygame.event.Event(pygame.KEYDOWN, key=pygame.K_3)]
    if frame == 14:
        world.practice_remaining = 0.01
    if frame == 15:
        return [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_r)]
    return []
class Keys:
    def __getitem__(self, key):
        return frame == 1 and key == pygame.K_SPACE
flip = pygame.display.flip
first_particles = None
def snapshot():
    global first_particles
    flip()
    screen = pygame.display.get_surface()
    if frame == 1:
        assert world.choosing_weapon and not world.victory
        first_particles = [(p.x, p.y) for p in world.effects.particles]
        assert first_particles
        pygame.image.save(screen, reports / "mission007-rootkit-death.png")
    if frame == 2:
        assert world.choosing_weapon and world.weapon_id == "sword"
        assert [(p.x, p.y) for p in world.effects.particles] != first_particles
    if frame == 11:
        assert world.choosing_weapon and world.effects.finale_timer == 0
        pygame.image.save(screen, reports / "mission007-weapons.png")
    if frame == 13:
        assert world.phase == "practice" and world.weapon_id == "bow"
        assert world.kills == 1 and world.player.progression.xp == 25
        pygame.image.save(screen, reports / "mission007-bow-practice.png")
    if frame == 14:
        assert world.victory and world.phase == "victory"
        assert world.kills == 1 and world.player.progression.xp == 25
        pygame.image.save(screen, reports / "mission007-victory.png")
    if frame == 15:
        assert world.phase == "waves" and world.weapon_id == "sword"
        assert world.kills == 0 and world.player.progression.xp == 0
with patch.object(app, "GameWorld", return_value=world), \\
     patch.object(app, "AudioBus", return_value=Mock()), \\
     patch.object(app, "MusicPlayer", return_value=Mock(status="")), \\
     patch.object(pygame.time, "Clock", return_value=clock), \\
     patch.object(pygame.event, "get", side_effect=events), \\
     patch.object(pygame.key, "get_pressed", return_value=Keys()), \\
     patch.object(pygame.display, "flip", side_effect=snapshot), \\
     patch.object(world, "choose_weapon", wraps=world.choose_weapon) as choose:
    app.main(max_frames=15, start_mode="defense")
    assert choose.call_count == 1
    assert choose.call_args.args == (1,)
assert not pygame.get_init()
''')

    def test_lab_teclas_trocam_sem_reset_e_render_armas_rootkit(self):
        self.executar('''
from pathlib import Path
import pickle
from unittest.mock import Mock, patch
import pygame
from game import main as app
from game import interface as ui
from game.boss import Rootkit
from game.enemies import Drop
from game.world import GameWorld

world = GameWorld(mode="laboratory")
world.enemies.clear()
world.phase = "weapon_choice"
frame = 0
def events():
    global frame
    frame += 1
    if frame == 2:
        world.attack_cooldown = 0.2
    key = (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_1)[frame - 1]
    return [pygame.event.Event(pygame.KEYDOWN, key=key)]
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
     patch.object(pygame.key, "get_pressed", return_value=Keys()), \\
     patch.object(world, "switch_weapon", wraps=world.switch_weapon) as switch:
    app.main(max_frames=4, start_mode="laboratory")
    assert [call.args[0] for call in switch.call_args_list] == [1, 2, 0]
assert world.weapon_id == "katana" and world.attack_cooldown == 0.2
assert world.practice_remaining == 45 and world.elapsed == 0

pygame.init()
try:
    screen = pygame.display.set_mode((1100, 770))
    fonts = ui.create_fonts(pygame)
    reports = Path("reports")
    reports.mkdir(exist_ok=True)
    def draw(state, name):
        before = pickle.dumps(state)
        ui.render_world(screen, state, fonts)
        app.desenhar_hud(screen, fonts["small"], state.player.progression,
                         compacto=True, damage=state.player.damage)
        ui.render_overlay(screen, state, fonts)
        assert pickle.dumps(state) == before
        pygame.image.save(screen, reports / ("mission007-" + name + ".png"))
    for weapon in ("katana", "bow", "spear"):
        state = GameWorld(mode="laboratory")
        state.phase = "weapon_choice"
        state.choose_weapon(weapon)
        state.player.facing_x, state.player.facing_y = 1, 0
        state.enemies[0].x = state.player.x + 60
        state.enemies[0].y = state.player.y
        state.update(0, attack=True)
        state.update(0.1)
        state.effects.update(0.05)
        draw(state, weapon)
    state = GameWorld()
    state.waves.number = 6
    state.waves.specs = state.waves._make_specs()
    state.waves.spawned = 1
    boss = Rootkit(state.player.x + 130, state.player.y, speed=0,
                   state="windup", telegraph_timer=0.4, facing_x=-1, facing_y=0)
    state.enemies = [boss]
    state.drops = [Drop(350, 400, kind="repair"), Drop(420, 400, kind="overclock")]
    draw(state, "rootkit")
    boss.pattern = "burst"
    draw(state, "rootkit-burst")
finally:
    pygame.quit()
''')


if __name__ == "__main__":
    unittest.main()

import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import unittest


@unittest.skipUnless(importlib.util.find_spec("pygame"), "Pygame não instalado")
class ArenaIntegrationTests(unittest.TestCase):
    def test_eventos_reais_renderizacao_reinicio_e_capturas(self):
        script = '''
from pathlib import Path
import random
import tempfile
from unittest.mock import Mock, patch
import pygame
from game import main as app
from game.enemies import Enemy, Drop
from game.world import GameWorld

reports = Path("reports")
reports.mkdir(exist_ok=True)
world = GameWorld(rng=random.Random(123))
world.player.progression.hp = 55
world.player.progression.xp = 75
world.enemies = [Enemy(world.player.x + 50, world.player.y, speed=0)]
world.drops = [Drop(world.player.x - 90, world.player.y + 50)]
origin_x = world.player.x
frame = 0
real_overlay = app.render_overlay

def events():
    global frame
    frame += 1
    if frame in (2, 4):
        return [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_i)]
    if frame == 3:
        return [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_h)]
    if frame == 5:
        world.player.progression.hp = 0
    if frame == 6:
        return [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_r)]
    if frame == 7:
        return [pygame.event.Event(pygame.QUIT)]
    if frame > 7:
        raise AssertionError("Loop não encerrou após QUIT")
    return []

class Keys:
    def __getitem__(self, key):
        return frame == 1 and key in (pygame.K_d, pygame.K_SPACE)

def overlay(surface, state, fonts):
    real_overlay(surface, state, fonts)
    if frame == 1:
        assert state.player.x > origin_x
        assert state.enemies[0].hp == 2
        assert state.attack_timer > 0
        pygame.image.save(surface, reports / "mission003-gameplay.png")
    if frame == 2:
        assert state.inventory_open
        pygame.image.save(surface, reports / "mission003-inventory.png")
    if frame == 3:
        assert state.player.progression.hp == 90
        assert state.player.inventory.potions == 1
    if frame == 5:
        assert state.game_over
        pygame.image.save(surface, reports / "mission003-gameover.png")
    if frame == 6:
        assert not state.game_over
        assert state.player.progression.hp == 100
        assert state.player.progression.xp == 0
        assert state.player.inventory.potions == 2
        assert len(state.enemies) == 3

clock = Mock()
clock.tick.return_value = 16
with tempfile.TemporaryDirectory() as temporary:
    final_capture = Path(temporary) / "final.png"
    with patch.object(app, "GameWorld", return_value=world), \\
         patch.object(pygame.time, "Clock", return_value=clock), \\
         patch.object(pygame.event, "get", side_effect=events), \\
         patch.object(pygame.key, "get_pressed", return_value=Keys()), \\
         patch.object(app, "render_overlay", side_effect=overlay), \\
         patch.object(world, "toggle_inventory", wraps=world.toggle_inventory) as inventory, \\
         patch.object(world, "use_potion", wraps=world.use_potion) as potion, \\
         patch.object(world, "restart", wraps=world.restart) as restart:
        app.main(max_frames=9, capture_path=final_capture, start_mode="defense")
        assert inventory.call_count == 2
        assert potion.call_count == 1
        assert restart.call_count == 1
    assert final_capture.is_file()
    assert final_capture.stat().st_size > 1000
assert frame == 7
assert not pygame.get_init()
assert not pygame.display.get_init()
for name in ("gameplay", "inventory", "gameover"):
    path = reports / ("mission003-" + name + ".png")
    assert path.is_file() and path.stat().st_size > 1000
'''
        ambiente = os.environ.copy()
        ambiente.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy", PYGAME_HIDE_SUPPORT_PROMPT="1")
        resultado = subprocess.run(
            [sys.executable, "-c", script],
            cwd=Path(__file__).resolve().parents[1],
            env=ambiente,
            capture_output=True,
            text=True,
            timeout=20,
        )
        self.assertEqual(resultado.returncode, 0, resultado.stdout + resultado.stderr)


if __name__ == "__main__":
    unittest.main()

import importlib.util
import math
import os
from pathlib import Path
import subprocess
import sys
import unittest

from game.sprites import sword_angle


class SwordAngleTests(unittest.TestCase):
    def test_arco_tem_inicio_meio_fim_em_quatro_direcoes(self):
        for fx, fy in ((1, 0), (0, 1), (-1, 0), (0, -1)):
            with self.subTest(direcao=(fx, fy)):
                base = math.atan2(fy, fx)
                self.assertAlmostEqual(sword_angle(fx, fy, 0.14), base - math.radians(50))
                self.assertAlmostEqual(sword_angle(fx, fy, 0.07), base)
                self.assertAlmostEqual(sword_angle(fx, fy, 0), base + math.radians(50))
                valores = [sword_angle(fx, fy, 0.14 * (1 - passo / 10)) for passo in range(11)]
                self.assertEqual(valores, sorted(valores))


@unittest.skipUnless(importlib.util.find_spec("pygame"), "Pygame não instalado")
class GameFeelRenderingTests(unittest.TestCase):
    def test_sprites_animacao_card_camera_e_capturas(self):
        script = '''
from pathlib import Path
import pickle
import random
from unittest.mock import patch
import pygame
from game import interface as ui
from game.main import desenhar_hud
from game.enemies import Enemy, Drop
from game.sprites import potion_sprite, sword_sprite
from game.world import GameWorld

pygame.init()
try:
    screen = pygame.display.set_mode((1100, 770))
    fonts = ui.create_fonts(pygame)
    reports = Path("reports")
    reports.mkdir(exist_ok=True)
    for size in (28, 48, 64):
        sprite = potion_sprite(size)
        assert sprite.get_size() == (size, size)
        assert sprite.get_at((0, 0)).a == 0
        assert sprite.get_bounding_rect().width > 0
        assert potion_sprite(size) is sprite
    sword = sword_sprite()
    assert sword.get_size() == (72, 24)
    assert sword.get_at((0, 0)).a == 0
    assert sword.get_at((60, 12)).a > 0

    def world():
        state = GameWorld(rng=random.Random(17))
        state.enemies = [Enemy(state.player.x + 45, state.player.y, speed=0)]
        state.drops = [Drop(state.player.x - 90, state.player.y + 60)]
        state.player.facing_x, state.player.facing_y = 1, 0
        return state

    def draw(state, name):
        before = pickle.dumps(state)
        original_clip = screen.get_clip()
        ui.render_world(screen, state, fonts)
        desenhar_hud(screen, fonts["small"], state.player.progression, compacto=True)
        ui.render_overlay(screen, state, fonts)
        assert pickle.dumps(state) == before, "Renderização alterou o mundo"
        assert screen.get_clip() == original_clip
        if name:
            pygame.image.save(screen, reports / ("gamefeel-" + name + ".png"))
        return pygame.image.tostring(screen, "RGB")

    state = world()
    state.update(0, attack=True)
    frames = []
    with patch.object(ui, "sword_sprite", wraps=sword_sprite) as render_sword:
        frames.append(draw(state, "sword-start"))
        assert render_sword.call_count == 1
        state.update(0.07)
        frames.append(draw(state, "sword-middle"))
        state.update(0.069)
        frames.append(draw(state, "sword-end"))
        assert render_sword.call_count == 3
        state.update(0.002)
        draw(state, "sword-finished")
        assert render_sword.call_count == 3, "Espada permaneceu após terminar golpe"
    assert len(set(frames)) == 3

    miss = world()
    miss.enemies.clear()
    miss.update(0, attack=True)
    assert miss.shake_offset == (0, 0)
    with patch.object(ui, "sword_sprite", wraps=sword_sprite) as render_sword:
        draw(miss, "sword-miss")
        assert render_sword.call_count == 1

    for name, fx, fy in (("right", 1, 0), ("down", 0, 1), ("left", -1, 0), ("up", 0, -1)):
        state = world()
        state.enemies.clear()
        state.player.facing_x, state.player.facing_y = fx, fy
        state.update(0, attack=True)
        state.update(0.07)
        # Mudar a direção atual não deve girar a espada de um golpe em andamento.
        state.player.facing_x, state.player.facing_y = -fy, fx
        with patch.object(ui, "sword_angle", wraps=ui.sword_angle) as angle:
            draw(state, "sword-" + name)
            assert angle.call_count >= 1
            assert all(call.args[:2] == (fx, fy) for call in angle.call_args_list)

    state = world()
    state.update(0, attack=True)
    state.shake_timer = 0
    draw(state, None)
    header = pygame.image.tostring(screen.subsurface((0, 0, 1100, 150)), "RGB")
    footer = pygame.image.tostring(screen.subsurface((0, 700, 1100, 70)), "RGB")
    arena = pygame.image.tostring(screen.subsurface(pygame.Rect(state.camera.viewport)), "RGB")
    state.shake_timer = 0.1
    draw(state, "hit-shake")
    assert header == pygame.image.tostring(screen.subsurface((0, 0, 1100, 150)), "RGB")
    assert footer == pygame.image.tostring(screen.subsurface((0, 700, 1100, 70)), "RGB")
    assert arena != pygame.image.tostring(screen.subsurface(pygame.Rect(state.camera.viewport)), "RGB")

    state.toggle_inventory()
    # MISSÃO005: o limite autorizado mudou de nove para cinco poções.
    for count in (0, 2, 5):
        state.player.inventory.potions = count
        with patch.object(ui, "text", wraps=ui.text) as text, \\
             patch.object(ui, "potion_sprite", wraps=potion_sprite) as potion:
            draw(state, "inventory-" + str(count))
            labels = [call.args[2] for call in text.call_args_list]
            assert "Pacote de reparo" in labels
            assert "Quantidade  " + str(count) + " / 5" in labels
            assert "Recupera 35 HP, até o máximo." in labels
            assert ("Sem pacotes" if count == 0 else "H   Aplicar reparo") in labels
            assert any(call.args == (64,) for call in potion.call_args_list)
finally:
    pygame.quit()
assert not pygame.get_init()
'''
        ambiente = os.environ.copy()
        ambiente.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy", PYGAME_HIDE_SUPPORT_PROMPT="1")
        resultado = subprocess.run(
            [sys.executable, "-c", script],
            cwd=Path(__file__).resolve().parents[1],
            env=ambiente,
            capture_output=True,
            text=True,
            timeout=25,
        )
        self.assertEqual(resultado.returncode, 0, resultado.stdout + resultado.stderr)


if __name__ == "__main__":
    unittest.main()

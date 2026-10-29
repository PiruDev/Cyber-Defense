import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import unittest


@unittest.skipUnless(importlib.util.find_spec("pygame"), "Pygame não instalado")
class RogueliteIntegrationTests(unittest.TestCase):
    def test_main_escolha_mouse123_sem_tempo_acumulado_e_capturas(self):
        script = '''
from pathlib import Path
import pickle
import random
from unittest.mock import Mock, patch
import pygame
from game import main as app
from game import interface as ui
from game.card_ui import card_rects
from game.swordsman import Swordsman
from game.archer import Archer
from game.worm import Worm
from game.projectiles import Projectile
from game.world import GameWorld
from game.weapons import TrainingTarget
from game.balance import BalanceConfig

reports = Path("reports")
reports.mkdir(exist_ok=True)
world = GameWorld(rng=random.Random(13), config=BalanceConfig(weapon_card_chance=0))
world.enemies.clear()
world.grant_xp(700)
assert world.pending_levelups == 4
frame = 0
overlay = app.render_overlay
initial_x = world.player.x

def events():
    global frame
    frame += 1
    if frame == 1:
        return [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_i),
                pygame.event.Event(pygame.KEYDOWN, key=pygame.K_h)]
    if frame == 2:
        return [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_1)]
    if frame == 17:
        return [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_1),
                pygame.event.Event(pygame.KEYDOWN, key=pygame.K_1)]
    if frame == 34:
        return [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                pos=pygame.Rect(card_rects()[1]).center)]
    if frame in (51, 68):
        return [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_2 if frame == 51 else pygame.K_3)]
    if frame == 69:
        # Ao retomar, o ataque depende de um alvo válido, sem tecla Espaço.
        world.enemies=[TrainingTarget(world.player.x+40,world.player.y,hp=100,max_hp=100)]
    if frame > 69:
        raise AssertionError("Loop excedeu max_frames")
    return []

class Keys:
    def __getitem__(self, key):
        return key == pygame.K_d

def checked_overlay(surface, state, fonts):
    before = pickle.dumps({k: v for k, v in vars(state).items() if not callable(v)})
    overlay(surface, state, fonts)
    assert pickle.dumps({k: v for k, v in vars(state).items() if not callable(v)}) == before
    if frame == 16:
        pygame.image.save(surface, reports / "mission005-cards.png")
    if frame <= 68:
        assert state.elapsed == 0
        assert state.player.x == initial_x
        assert state.attack_timer == 0
        assert state.player.inventory.potions == 2
    if frame == 2:
        assert state.pending_levelups == 4, "Input prematuro selecionou carta invisível"
    if frame == 17:
        assert state.pending_levelups == 3, "Dois eventos escolheram duas cartas no mesmo quadro"

clock = Mock()
clock.tick.return_value = 50
with patch.object(app, "GameWorld", return_value=world), \\
     patch.object(pygame.time, "Clock", return_value=clock), \\
     patch.object(pygame.event, "get", side_effect=events), \\
     patch.object(pygame.key, "get_pressed", return_value=Keys()), \\
     patch.object(app, "render_overlay", side_effect=checked_overlay), \\
     patch.object(world, "choose_card", wraps=world.choose_card) as choose, \\
     patch.object(world, "update", wraps=world.update) as update:
    app.main(max_frames=69, capture_path=reports / "mission005-resumed.png", start_mode="defense")
    assert [c.args[0] for c in choose.call_args_list] == [0, 1, 1, 2]
    assert update.call_count == 1
assert world.pending_levelups == 0
assert sum(world.player.upgrades.values()) == 4
assert abs(world.elapsed - 0.05) < 1e-9
assert world.player.x > initial_x
assert world.attack_timer > 0
assert world.enemies[0].hp < 100
assert not pygame.get_init()

pygame.init()
try:
    screen = pygame.display.set_mode((1100, 770))
    fonts = ui.create_fonts(pygame)
    def draw(state, name):
        before = pickle.dumps(state)
        ui.render_world(screen, state, fonts)
        app.desenhar_hud(screen, fonts["small"], state.player.progression,
                         compacto=True, damage=state.player.damage)
        ui.render_overlay(screen, state, fonts)
        assert pickle.dumps(state) == before
        pygame.image.save(screen, reports / ("mission005-" + name + ".png"))

    scene = GameWorld(rng=random.Random(7))
    scene.player.x, scene.player.y = 450, 470
    scene.player.progression.hp = 78
    scene.score = 30
    sword = Swordsman(530, 450, state="windup", telegraph_timer=0.2, facing_x=-1, facing_y=0)
    archer = Archer(800, 280, state="windup", telegraph_timer=0.3, facing_x=-1, facing_y=0.2)
    scene.enemies = [sword, archer]
    scene.projectiles = [Projectile(690, 370, -160, 70)]
    draw(scene, "arena")
    worm = Worm(720, 430)
    scene.enemies.append(worm)
    for _ in range(4):
        while scene.waves.can_spawn:
            scene.waves.next_kind()
        while scene.waves.defeated < scene.waves.total:
            scene.waves.register_defeat()
        scene.waves.update(0, 0)
        scene.waves.update(3, 0)
    draw(scene, "worm")

    campaign = GameWorld(rng=random.Random(29), mode="laboratory")
    for _ in range(200):
        for enemy in campaign.enemies:
            enemy.hp = 0
        campaign.update(1)
        while campaign.choosing_card:
            campaign.advance_presentation(0.8)
            campaign.choose_card(0)
        if campaign.choosing_weapon:
            break
    assert campaign.choosing_weapon and campaign.kills == 51
    assert campaign.choose_weapon("katana")
    campaign.update(45)
    assert campaign.victory
    # MISSÃO006: a vitória lógica antecede a animação final e sua tela modal.
    campaign.effects.update(0.5)
    draw(campaign, "victory")
finally:
    pygame.quit()
'''
        ambiente = os.environ.copy()
        ambiente.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy", PYGAME_HIDE_SUPPORT_PROMPT="1")
        resultado = subprocess.run(
            [sys.executable, "-c", script],
            cwd=Path(__file__).resolve().parents[1],
            env=ambiente,
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(resultado.returncode, 0, resultado.stdout + resultado.stderr)


if __name__ == "__main__":
    unittest.main()

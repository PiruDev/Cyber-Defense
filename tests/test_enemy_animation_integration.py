"""Integração real de animação, Pygame e combate em subprocessos SDL dummy."""

import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(importlib.util.find_spec("pygame"), "Pygame não instalado")
class EnemyAnimationIntegrationTests(unittest.TestCase):
    def executar(self, script):
        environment = os.environ.copy()
        environment.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy", PYGAME_HIDE_SUPPORT_PROMPT="1")
        result = subprocess.run([sys.executable, "-c", script], cwd=ROOT,
                                env=environment, text=True, capture_output=True, timeout=35)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_importacao_sem_janela_ou_leitura_de_png(self):
        self.executar('''
from unittest.mock import patch
import pygame
assert not pygame.get_init()
with patch.object(pygame.image, "load", side_effect=AssertionError("IO durante import")):
    from game import enemy_assets, enemy_animation, enemy_render
assert not pygame.get_init() and not pygame.display.get_init()
''')

    def test_cache_rotacoes_nitidas_cwd_independente_e_fallback_real(self):
        self.executar('''
import json
import math
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import pygame
from game.enemy_assets import AssetLibrary
from game import enemy_render
from game.enemies import Enemy
from game.swordsman import Swordsman

root = Path.cwd()
(root / "reports").mkdir(exist_ok=True)
pygame.init()
try:
    pygame.display.set_mode((200, 200))
    with TemporaryDirectory(dir=root / "reports") as folder:
        temporary = Path(folder)
        sheet = pygame.Surface((96, 48), pygame.SRCALPHA)
        pygame.draw.rect(sheet, (240, 40, 80), (10, 14, 29, 19))
        pygame.draw.rect(sheet, (250, 190, 80), (28, 17, 13, 5))
        pygame.draw.rect(sheet, (100, 20, 90), (58, 10, 27, 27))
        pygame.image.save(sheet, temporary / "good.png")
        (temporary / "bad.png").write_bytes(b"not a PNG")
        states = {
            "idle": {"file": "good.png", "frames": 2, "durations_ms": [50, 50], "loop": True},
            "move": {"file": "missing.png", "frames": 2, "durations_ms": [50, 50], "loop": True},
            "hurt": {"file": "bad.png", "frames": 2, "durations_ms": [50, 50], "loop": False},
        }
        manifest = temporary / "manifest.json"
        manifest.write_text(json.dumps({"version": 1, "types": {"basic": {
            "frame_size": [48, 48], "pivot": [24, 24], "facing": "east", "states": states}}}), encoding="utf-8")
        library = AssetLibrary(manifest)
        with patch.object(pygame.image, "load", wraps=pygame.image.load) as loader:
            first = library.frame("basic", "idle", 0, 0)
            assert first is not None
            assert first[0].get_size() == (48, 48) and tuple(first[1]) == (24, 24)
            for _ in range(20):
                assert library.frame("basic", "idle", 0, 0)[0] is first[0]
            assert loader.call_count == 1, "Leitura repetida do mesmo sheet"
            second = library.frame("basic", "idle", 51, 0)
            assert pygame.image.tostring(first[0], "RGBA") != pygame.image.tostring(second[0], "RGBA")
            assert library.frame("basic", "idle", 100, 0)[0] is first[0]
            for index in range(8):
                angle = index * math.pi / 4
                rotated = library.frame("basic", "idle", 0, angle)
                assert rotated is not None
                image, pivot = rotated
                assert 0 <= pivot[0] < image.get_width() and 0 <= pivot[1] < image.get_height()
                assert {image.get_at((x,y)).a for x in range(image.get_width())
                        for y in range(image.get_height())} == {0, 255}
                assert library.frame("basic", "idle", 0, angle)[0] is image
            assert loader.call_count == 1
            original_pixels = pygame.image.tostring(first[0], "RGBA")
            flashed = library.frame("basic", "idle", 0, 0, flash=True)
            assert flashed is not None
            assert flashed[0] is not first[0]
            assert pygame.image.tostring(first[0], "RGBA") == original_pixels
            background = pygame.Surface((100,100))
            background.fill((5,9,22))
            background.blit(flashed[0],(0,0))
            assert background.get_at((0,0))[:3] == (5,9,22), "Flash pintou fundo transparente"
            assert library.frame("basic", "idle", 0, 0, flash=True)[0] is flashed[0]
            assert library.frame("basic", "move", 0, 0) is None
            assert library.frame("basic", "move", 0, 0) is None
            assert library.frame("basic", "hurt", 0, 0) is None
            assert library.frame("basic", "hurt", 0, 0) is None
            assert library.frame("unknown", "idle", 0, 0) is None
            assert loader.call_count <= 3, "Falha de carga não ficou em cache"
        missing = AssetLibrary(temporary / "absent-manifest.json")
        assert missing.frame("basic", "idle", 0, 0) is None
        malformed = temporary / "malformed.json"
        malformed.write_text("[]",encoding="utf-8")
        assert AssetLibrary(malformed).frame("basic","idle",0,0) is None
        malformed.write_text(json.dumps({"version":1,"types":{"basic":{
            "frame_size":[48,48],"pivot":[24,24],"facing":"east","states":[]}}}),encoding="utf-8")
        assert AssetLibrary(malformed).frame("basic","idle",0,0) is None
        screen = pygame.Surface((240, 240), pygame.SRCALPHA)
        with patch.object(enemy_render, "get_library", return_value=missing):
            enemy_render.render_enemy(screen, Enemy(100, 100))
            enemy_render.render_enemy(screen, Swordsman(150, 100, state="windup", telegraph_timer=.2,
                                                        facing_x=1, facing_y=0))
        assert screen.get_bounding_rect().width > 0, "Fallback não desenhou inimigo"
        assert screen.get_at((210,100)).a > 0, "Fallback ocultou antecipação direcional"
        pygame.image.save(sheet, temporary / "bad.png")
        assert library.frame("basic", "hurt", 0, 0) is None, "Falha não ficou em cache"
        library.clear()
        assert library.frame("basic", "idle", 0, 0) is not None
        assert library.frame("basic", "hurt", 0, 0) is not None, "clear não descartou falha antiga"
        saved = os.getcwd()
        try:
            os.chdir(temporary)
            default = AssetLibrary()
            assert default.frame("rootkit", "idle", 0, 0) is not None
        finally:
            os.chdir(saved)
finally:
    pygame.quit()
assert not pygame.get_init()
''')

    def test_estados_e_progresso_observam_timers_sem_modificar_logica(self):
        self.executar('''
import pickle
from game.enemy_animation import choose_state, state_progress
from game.enemies import Enemy
from game.swordsman import Swordsman
from game.archer import Archer
from game.boss import Rootkit

basic = Enemy(100, 100)
assert choose_state(basic, False) == "idle"
assert choose_state(basic, True) == "move"
basic.stun_timer = .2
assert choose_state(basic, True) == "idle"
basic.hit_flash_timer = .1
assert choose_state(basic, True) == "hurt"
for enemy, windup, attack in ((Swordsman(100,100), .35, .14),
                               (Archer(100,100), .45, .14),
                               (Rootkit(100,100), .65, .20)):
    enemy.state = "windup"
    enemy.telegraph_timer = windup
    before = pickle.dumps(enemy)
    assert choose_state(enemy, False) == "windup"
    assert abs(state_progress(enemy, "windup", 20, 300)) < 1e-8
    assert pickle.dumps(enemy) == before
    enemy.telegraph_timer = windup / 2
    assert abs(state_progress(enemy, "windup", 20, 300) - 150) < 1e-8
    enemy.state = "recover"
    enemy.telegraph_timer = 0
    enemy.attack_timer = attack
    assert choose_state(enemy, False) == "attack"
    assert abs(state_progress(enemy, "attack", 20, 140)) < 1e-8
    enemy.attack_timer = attack / 2
    assert abs(state_progress(enemy, "attack", 20, 140) - 70) < 1e-8
rootkit = Rootkit(100,100,state="windup",telegraph_timer=.3,hit_flash_timer=.1)
assert choose_state(rootkit, True) == "windup", "Dano escondeu antecipação do boss"
rootkit.state = "recover"
rootkit.telegraph_timer = 0
rootkit.attack_timer = .1
assert choose_state(rootkit, True) == "attack", "Dano escondeu ataque protegido do boss"
''')

    def test_render_usa_tipos_reais_e_oito_direcoes_sem_mutar_mundo(self):
        self.executar('''
import math
import pickle
from pathlib import Path
from unittest.mock import patch
import pygame
from game import interface as ui
from game import main as app
from game import enemy_render
from game.enemy_assets import get_library
from game.enemies import Enemy
from game.swordsman import Swordsman
from game.archer import Archer
from game.worm import Worm
from game.boss import Rootkit
from game.world import GameWorld

pygame.init()
try:
    screen = pygame.display.set_mode((1100,770))
    fonts = ui.create_fonts(pygame)
    reports = Path("reports")
    reports.mkdir(exist_ok=True)
    world = GameWorld()
    worm = Worm(790,550,speed=0)
    worm._follow_segments(world.arena)
    world.enemies = [Enemy(130,310,speed=0), Swordsman(320,310,speed=0),
                     Archer(510,310,speed=0), worm, Rootkit(920,340,speed=0)]
    before = pickle.dumps(world)
    library = get_library()
    with patch.object(library, "frame", wraps=library.frame) as frames:
        ui.render_world(screen,world,fonts)
        app.desenhar_hud(screen,fonts["small"],world.player.progression,compacto=True)
        called = [call.args[0] for call in frames.call_args_list]
        assert {"basic","swordsman","archer","worm_head","worm_body","worm_tail","rootkit"}.issubset(called)
        head_calls = [call for call in frames.call_args_list if call.args[0]=="worm_head"]
        expected = math.atan2(worm.head.y-worm.segments[1].y, worm.head.x-worm.segments[1].x)
        assert len(head_calls)==1 and abs(head_calls[0].args[3]-expected)<1e-9, "Cabeça inicial diverge da tangente"
    assert pickle.dumps(world) == before
    pygame.image.save(screen,reports/"mission010-enemies.png")
    grid = pygame.Surface((1100,770))
    grid.fill((5,9,22))
    for row, cls in enumerate((Swordsman,Archer,Rootkit)):
        for column in range(8):
            angle = column * math.pi/4
            enemy = cls(85+column*132,170+row*210,state="windup",
                        telegraph_timer=.2,facing_x=math.cos(angle),facing_y=math.sin(angle))
            before = pickle.dumps(enemy)
            enemy_render.render_enemy(grid,enemy,animation_time=.2,moving=False)
            assert pickle.dumps(enemy) == before
    pygame.image.save(grid,reports/"mission010-directions.png")
    sheet = pygame.Surface((1100,770))
    sheet.fill((5,9,22))
    examples = (Enemy(80,180),Swordsman(80,350),Archer(80,520),Rootkit(80,690))
    for row, prototype in enumerate(examples):
        for column, state in enumerate(("idle","move","windup","attack","hurt")):
            enemy = type(prototype)(100+column*215,180+row*170)
            moving = state == "move"
            if state == "windup" and hasattr(enemy,"state"):
                enemy.state="windup"
                enemy.telegraph_timer=.2
            elif state == "attack" and hasattr(enemy,"attack_timer"):
                enemy.attack_timer=.08
            elif state == "hurt":
                enemy.hit_flash_timer=.07
            enemy_render.render_enemy(sheet,enemy,animation_time=.2,moving=moving)
    pygame.image.save(sheet,reports/"mission010-states.png")
finally:
    pygame.quit()
''')

    def test_movimento_visual_pausa_stun_e_ghost_sem_recompensa_extra(self):
        self.executar('''
import pickle
from game.enemies import Enemy
from game.world import GameWorld

world = GameWorld()
world.enemies = [Enemy(world.player.x+100,world.player.y)]
enemy = world.enemies[0]
world.update(.05)
assert world.enemy_motion[id(enemy)][0]
enemy.x = world.player.x+45
world.player.facing_x,world.player.facing_y=1,0
world.update(0,attack=True)
world.update(.05)
assert enemy.stun_timer > 0 and enemy.knockback_timer > 0
assert not world.enemy_motion[id(enemy)][0], "Recuo virou animação de caminhada"
world.toggle_inventory()
before = pickle.dumps(world)
world.update(20,move_x=1,attack=True)
assert pickle.dumps(world) == before
world.toggle_inventory()
enemy.hp=0
world.update(0)
assert enemy not in world.enemies
assert (world.kills,world.player.progression.xp)==(1,25)
assert len(world.effects.enemy_ghosts)==1
ghost=world.effects.enemy_ghosts[0]
assert ghost.kind=="basic" and ghost.state=="death"
life=ghost.remaining
world.effects.update(.2,paused=True)
assert ghost.remaining==life
world.update(0)
assert (world.kills,world.player.progression.xp)==(1,25)
world.effects.update(.31)
assert not world.effects.enemy_ghosts
world.restart()
assert not world.effects.enemy_ghosts
''')

    def test_min_hoca_promove_cabeca_renderiza_partes_e_final_tem_um_ghost(self):
        self.executar('''
from collections import Counter
import pickle
from pathlib import Path
from unittest.mock import patch
import pygame
from game import enemy_render
from game.enemy_assets import get_library
from game.world import GameWorld
from game.worm import Worm

world=GameWorld()
worm=Worm(world.player.x+80,world.player.y,speed=0)
worm._follow_segments(world.arena)
world.enemies=[worm]
next_head=worm.segments[1]
assert world._hit_enemy(worm,worm.x,worm.y,damage=1000)
assert worm.head is next_head and len(worm.segments)==5
assert (world.kills,world.player.progression.xp)==(0,0)
assert world.effects.head_highlights[id(worm)] > 0
pygame.init()
try:
    pygame.display.set_mode((1100,770))
    surface=pygame.Surface((1100,770))
    surface.fill((5,9,22))
    library=get_library()
    before=pickle.dumps(world)
    with patch.object(library,"frame",wraps=library.frame) as frames:
        enemy_render.render_enemy(surface,worm,effects=world.effects,animation_time=.1,moving=True)
        kinds=Counter(call.args[0] for call in frames.call_args_list)
        assert kinds["worm_head"]==1 and kinds["worm_tail"]==1 and kinds["worm_body"]==3
        assert any(call.args[0]=="worm_head" and call.args[1]=="new_head" for call in frames.call_args_list)
    assert pickle.dumps(world)==before
    enemy_render.render_enemy_ghosts(surface,world.effects)
    Path("reports").mkdir(exist_ok=True)
    pygame.image.save(surface,"reports/mission010-worm-rupture.png")
finally:
    pygame.quit()
for _ in range(5):
    assert world._hit_enemy(worm,worm.x,worm.y,damage=1000)
world._collect_defeated()
assert not worm.segments and not world.enemies
assert (world.kills,world.player.progression.xp)==(1,25)
assert Counter(g.state for g in world.effects.enemy_ghosts)=={"rupture":5,"death":1}
world._collect_defeated()
assert (world.kills,world.player.progression.xp)==(1,25)
''')

    def test_horda_seis_boss_antecipa_ataca_morre_e_main_fecha_com_sprites(self):
        self.executar('''
from pathlib import Path
from random import Random
from unittest.mock import patch
import pygame
from game import interface as ui
from game import main as app
from game.boss import Rootkit
from game.world import GameWorld
from game.enemy_assets import get_library

world=GameWorld(mode="defense",rng=Random(29))
boss=None
for _ in range(220):
    boss=next((enemy for enemy in world.enemies if isinstance(enemy,Rootkit)),None)
    if boss is not None:
        break
    for enemy in world.enemies:
        enemy.hp=0
    world.update(1)
    while world.choosing_card:
        world.advance_presentation(.8)
        assert world.choose_card(0)
assert boss is not None and world.waves.number==6 and world.kills==51
boss.x,boss.y=world.player.x+100,world.player.y
world.effects.enemy_ghosts.clear()
world.effects.particles.clear()
world.effects.texts.clear()
world.effects.consume_events()
world.update(0)
assert boss.state=="windup" and boss.telegraph_timer==boss.telegraph_duration
assert world._hit_enemy(boss,boss.x,boss.y,damage=1)
assert boss.state=="windup" and boss.stun_timer==boss.knockback_timer==0
before_hp=world.player.progression.hp
world.update(.65)
assert world.player.progression.hp < before_hp and boss.attack_timer > 0
pygame.init()
try:
    screen=pygame.display.set_mode((1100,770))
    fonts=ui.create_fonts(pygame)
    Path("reports").mkdir(exist_ok=True)
    ui.render_world(screen,world,fonts)
    app.desenhar_hud(screen,fonts["small"],world.player.progression,compacto=True)
    pygame.image.save(screen,"reports/mission010-rootkit-attack.png")
    assert world._hit_enemy(boss,boss.x,boss.y,damage=10000)
    world._collect_defeated()
    assert world.kills==52 and world.choosing_weapon and boss not in world.enemies
    assert sum(ghost.kind=="rootkit" for ghost in world.effects.enemy_ghosts)==1
    reward=(world.kills,world.player.progression.xp)
    world.effects.update(.15)
    ui.render_world(screen,world,fonts)
    ui.render_overlay(screen,world,fonts)
    pygame.image.save(screen,"reports/mission010-rootkit-death.png")
    world.effects.update(.31)
    assert not world.effects.enemy_ghosts
    assert reward==(world.kills,world.player.progression.xp)
finally:
    pygame.quit()
get_library().clear()
with patch.object(pygame.image,"load",wraps=pygame.image.load) as load:
    app.main(max_frames=90,capture_path=Path("reports/mission010-game-smoke.png"),start_mode="defense")
    assert any("enemies" in str(call.args[0]) for call in load.call_args_list)
assert not pygame.get_init()
''')

    def test_render_com_cache_aquecido_sem_io_por_quadro(self):
        self.executar('''
import json
from pathlib import Path
from time import perf_counter
from unittest.mock import patch
import pygame
from game.enemy_render import render_enemy
from game.enemies import Enemy
from game.swordsman import Swordsman
from game.archer import Archer
from game.boss import Rootkit

pygame.init()
try:
    surface=pygame.display.set_mode((1100,770))
    enemies=[cls(100+index*95,400) for index,cls in enumerate(
        (Enemy,Swordsman,Archer,Enemy,Swordsman,Archer,Enemy,Swordsman,Archer,Rootkit))]
    def render(frame):
        for index,enemy in enumerate(enemies):
            render_enemy(surface,enemy,animation_time=frame/60,moving=True,
                         motion_direction=(1,0))
    for frame in range(180):
        render(frame)
    with patch.object(pygame.image,"load",side_effect=AssertionError("IO no cache aquecido")):
        start=perf_counter()
        for frame in range(120):
            render(frame)
        elapsed=perf_counter()-start
    Path("reports").mkdir(exist_ok=True)
    Path("reports/mission010-render-metrics.json").write_text(json.dumps({
        "enemy_count":10,"frames":120,"mean_render_ms":elapsed*1000/120,
        "scope":"Somente renderização de inimigos em SDL dummy; não é FPS completo."},indent=2),encoding="utf-8")
finally:
    pygame.quit()
''')


if __name__ == "__main__":
    unittest.main()

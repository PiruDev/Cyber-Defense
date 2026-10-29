"""Verificação gráfica controlada; SDL dummy não equivale a um playtest humano."""

import os
from pathlib import Path
import subprocess
import sys
import unittest


class Mission011RenderTests(unittest.TestCase):
    def execute(self, script, timeout=35):
        environment = os.environ.copy()
        environment.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy",
                           PYGAME_HIDE_SUPPORT_PROMPT="1")
        result = subprocess.run([sys.executable, "-c", script],
                                cwd=Path(__file__).resolve().parents[1], env=environment,
                                capture_output=True, text=True, timeout=timeout)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_imports_nao_abrem_janela_ou_carregam_assets(self):
        self.execute('''
from unittest.mock import patch
import pygame
assert not pygame.get_init()
with patch.object(pygame.image,"load",side_effect=AssertionError("IO no import")):
    from game import camera, floor, player_render, slash_render, interface
assert not pygame.get_init() and not pygame.display.get_init()
''')

    def test_player_original_preservado_animacoes_escala_pivo_e_cache(self):
        self.execute('''
import hashlib
import math
from pathlib import Path
from unittest.mock import patch
import pygame
from game.player import Player
from game import player_render as renderer

original=Path("assets/sprites/player/sentinel_idle.png")
assert hashlib.sha256(original.read_bytes()).hexdigest()=="1b6ba716b67876fa32fedde73ab1a38352d08991a2e3acbe58473b13884dde35"
pygame.init()
try:
    pygame.display.set_mode((120,120))
    player=Player(x=100,y=100)
    for moving,count in ((False,4),(True,6)):
        frames=renderer._frames(moving)
        assert len(frames)==count
        assert all(frame.get_size()==(48,48) for frame in frames)
        assert len({pygame.image.tostring(frame,"RGBA") for frame in frames})>=2
        for frame in frames:
            assert frame.get_at((0,0)).a==0
            assert {frame.get_at((x,y)).a for x in range(48) for y in range(48)}=={0,255}
    player.facing_x,player.facing_y=0,1
    image,pivot=renderer.player_frame(player,0,moving=False)
    assert image.get_size()==(60,60) and pivot==(30,30)
    expected=pygame.transform.scale(renderer._frames(False)[0],(60,60))
    assert pygame.image.tostring(image,"RGBA")==pygame.image.tostring(expected,"RGBA")
    dimensions=(player.radius,player.speed,player.damage)
    for direction in range(8):
        angle=direction*math.pi/4
        player.facing_x,player.facing_y=math.cos(angle),math.sin(angle)
        frame,pivot=renderer.player_frame(player,.25,moving=True,flash=True)
        assert pivot==(frame.get_width()/2,frame.get_height()/2)
        assert {frame.get_at((x,y)).a for x in range(frame.get_width()) for y in range(frame.get_height())}=={0,255}
        assert renderer.player_frame(player,.25,moving=True,flash=True)[0] is frame
    assert (player.radius,player.speed,player.damage)==dimensions
    with patch.object(pygame.image,"load",side_effect=AssertionError("IO repetido")):
        renderer.player_frame(player,.25,moving=True,flash=True)
finally:
    pygame.quit()
''')

    def test_sprites_inimigos_ampliados_sem_mudar_colisoes(self):
        self.execute('''
import pygame
from game.enemy_assets import get_library
from game.visual_config import ENEMY_SCALES
from game.enemies import Enemy
from game.swordsman import Swordsman
from game.archer import Archer
from game.worm import Worm
from game.boss import Rootkit

pygame.init()
try:
    pygame.display.set_mode((120,120))
    library=get_library()
    for enemy in (Enemy(100,100),Swordsman(100,100),Archer(100,100),Rootkit(100,100)):
        before=(enemy.x,enemy.y,enemy.radius,enemy.hp,enemy.speed,enemy.damage)
        source,pivot=library.frame(enemy.kind,"idle",0,0)
        scale=ENEMY_SCALES[enemy.kind]
        image,new_pivot=library.frame(enemy.kind,"idle",0,0,scale=scale)
        assert image.get_size()==(round(source.get_width()*scale),round(source.get_height()*scale))
        assert new_pivot==(round(pivot[0]*scale),round(pivot[1]*scale))
        assert pygame.image.tostring(image,"RGBA")==pygame.image.tostring(pygame.transform.scale(source,image.get_size()),"RGBA")
        assert before==(enemy.x,enemy.y,enemy.radius,enemy.hp,enemy.speed,enemy.damage)
finally:
    pygame.quit()
''')

    def test_slash_curto_em_arco_direcional_sem_triangulo_ou_mutacao(self):
        self.execute('''
import math
import pygame
from game.slash_render import render_slash

pygame.init()
try:
    surface=pygame.Surface((400,400),pygame.SRCALPHA)
    frames=[]
    for progress in (0,.3,.6,.95):
        surface.fill((0,0,0,0))
        render_slash(surface,(200,200),0,progress,70)
        points=[(x,y) for x in range(400) for y in range(400) if surface.get_at((x,y)).a]
        assert points
        assert all(55<=math.hypot(x-200,y-200)<=75 for x,y in points), "Slash desenhou triângulo preenchido/fora do alcance"
        assert all(x>200 for x,y in points), "Slash não respeitou direção leste"
        frames.append(pygame.image.tostring(surface,"RGBA"))
    assert len(set(frames))==4
    surface.fill((0,0,0,0))
    render_slash(surface,(200,200),0,1,70)
    assert not surface.get_bounding_rect().width, "Slash não desapareceu"
    render_slash(surface,(200,200),math.pi,.4,60,theme="enemy",half_angle=45)
    points=[(x,y) for x in range(400) for y in range(400) if surface.get_at((x,y)).a]
    assert points and all(x<200 for x,y in points)
    assert any(surface.get_at(point).r>surface.get_at(point).b for point in points)
finally:
    pygame.quit()
''')

    def test_render_de_golpe_nao_repete_dano_e_respeita_timers(self):
        self.execute('''
import pickle
from unittest.mock import patch
import pygame
from game import interface as ui
from game.world import GameWorld
from game.enemies import Enemy
from game.swordsman import Swordsman
from game.enemy_render import render_enemy

pygame.init()
try:
    screen=pygame.display.set_mode((1100,770))
    fonts=ui.create_fonts(pygame)
    world=GameWorld()
    world.enemies.clear()
    world.player.facing_x,world.player.facing_y=1,0
    enemy=Enemy(world.player.x+45,world.player.y,hp=20,max_hp=20,speed=0)
    world.enemies=[enemy]
    world.update(0,attack=True)
    assert enemy.hp==19
    before=pickle.dumps(world)
    for _ in range(20):
        ui.render_world(screen,world,fonts)
    assert pickle.dumps(world)==before and enemy.hp==19
    world.enemies.clear()
    world.weapons.switch("katana")
    world.attack_cooldown=0
    enemy=Enemy(world.player.x+45,world.player.y,hp=20,max_hp=20,speed=0)
    world.enemies=[enemy]
    world.update(0,attack=True)
    first=enemy.hp
    for _ in range(20):
        ui.render_world(screen,world,fonts)
    assert enemy.hp==first
    world.update(.1)
    assert enemy.hp<first
    second=enemy.hp
    for _ in range(20):
        ui.render_world(screen,world,fonts)
    world.update(.1)
    assert enemy.hp==second, "Um frame visual gerou terceiro impacto"
    swordsman=Swordsman(300,300,speed=0)
    swordsman.attack_timer=.14
    before=pickle.dumps(swordsman)
    for _ in range(10):
        render_enemy(screen,swordsman)
    assert pickle.dumps(swordsman)==before
finally:
    pygame.quit()
''')

    def test_piso_estatico_mundo_camera_e_hud_fixos(self):
        self.execute('''
import pickle
import pygame
from game.floor import floor_surface
from game.world import GameWorld
from game import interface as ui

pygame.init()
try:
    screen=pygame.display.set_mode((1100,770))
    fonts=ui.create_fonts(pygame)
    world=GameWorld()
    world.enemies.clear()
    floor=floor_surface(world.arena)
    floor_bytes=pygame.image.tostring(floor,"RGB")
    point=(1100,700)
    expected=floor.get_at(point)[:3]
    before=pickle.dumps(world)
    ui.render_world(screen,world,fonts)
    assert pickle.dumps(world)==before
    screen_point=world.camera.project(*point)
    assert screen.get_at(tuple(map(round,screen_point)))[:3]==expected
    header=pygame.image.tostring(screen.subsurface((0,0,1100,150)),"RGB")
    footer=pygame.image.tostring(screen.subsurface((0,700,1100,70)),"RGB")
    world.camera.update(1360,900,0,snap=True)
    world.elapsed=10
    ui.render_world(screen,world,fonts)
    moved_point=world.camera.project(*point)
    assert screen_point!=moved_point
    assert screen.get_at(tuple(map(round,moved_point)))[:3]==expected
    assert floor_surface(world.arena) is floor
    assert pygame.image.tostring(floor,"RGB")==floor_bytes
    assert header==pygame.image.tostring(screen.subsurface((0,0,1100,150)),"RGB")
    assert footer==pygame.image.tostring(screen.subsurface((0,700,1100,70)),"RGB")
finally:
    pygame.quit()
''')

    def test_slash_temporal_observa_janela_das_armas_e_espadachim(self):
        self.execute('''
from unittest.mock import patch
import pygame
from game.world import GameWorld
from game import weapon_render, enemy_render
from game.swordsman import Swordsman

pygame.init()
try:
    pygame.display.set_mode((1100,770))
    layer=pygame.Surface((2400,1600),pygame.SRCALPHA)
    world=GameWorld()
    world.enemies.clear()
    world.player.facing_x,world.player.facing_y=1,0
    with patch.object(weapon_render,"render_slash",wraps=weapon_render.render_slash) as slash:
        weapon_render.render_weapon(layer,world)
        assert not slash.called
        world.update(0,attack=True)
        weapon_render.render_weapon(layer,world)
        assert abs(slash.call_args.args[3])<1e-9
        world.update(.07)
        weapon_render.render_weapon(layer,world)
        assert abs(slash.call_args.args[3]-.5)<1e-9
        world.update(.071)
        count=slash.call_count
        weapon_render.render_weapon(layer,world)
        assert slash.call_count==count
    enemy=Swordsman(400,400,state="windup",telegraph_timer=.35)
    with patch.object(enemy_render,"render_slash",wraps=enemy_render.render_slash) as slash:
        enemy_render.render_enemy(layer,enemy)
        assert not slash.called
        enemy.telegraph_timer=0
        enemy.state="recover"
        enemy.attack_timer=.14
        enemy_render.render_enemy(layer,enemy)
        assert slash.call_args.kwargs["theme"]=="enemy"
        assert abs(slash.call_args.args[3])<1e-9
        enemy.attack_timer=.07
        enemy_render.render_enemy(layer,enemy)
        assert abs(slash.call_args.args[3]-.5)<1e-9
        enemy.attack_timer=0
        count=slash.call_count
        enemy_render.render_enemy(layer,enemy)
        assert slash.call_count==count
finally:
    pygame.quit()
''')

    def test_entidades_ataque_drops_projeteis_fx_viajam_juntos_com_camera(self):
        self.execute('''
import pygame
from game.world import GameWorld
from game.enemies import Enemy,Drop
from game.projectiles import Projectile
from game.floor import floor_surface
from game import interface as ui

pygame.init()
try:
    screen=pygame.display.set_mode((1100,770))
    fonts=ui.create_fonts(pygame)
    world=GameWorld()
    world.player.x,world.player.y=1600,1000
    world.player.facing_x,world.player.facing_y=1,0
    world.enemies=[Enemy(1660,1060,speed=0)]
    world.drops=[Drop(1530,1070)]
    world.projectiles=[Projectile(1700,920,100,0)]
    world.effects.emit("hit",1460,900,damage=2)
    world.update(0,attack=True)
    world.effects.shake_timer=0
    world.camera.update(1600,1000,0,snap=True)
    points=((1600,1000),(1660,1060),(1530,1070),(1700,920),(1460,900),(1665,980))
    floor=floor_surface(world.arena)
    ui.render_world(screen,world,fonts)
    crops=[]
    for point in points:
        sx,sy=map(round,world.camera.project(*point))
        rect=pygame.Rect(sx-22,sy-22,44,44)
        crop=pygame.image.tostring(screen.subsurface(rect),"RGB")
        floor_rect=pygame.Rect(point[0]-22,point[1]-22,44,44)
        assert crop!=pygame.image.tostring(floor.subsurface(floor_rect),"RGB"), "Objeto/efeito não foi desenhado"
        crops.append(crop)
    world.camera.update(1664,1064,0,snap=True)
    ui.render_world(screen,world,fonts)
    for point,crop in zip(points,crops):
        sx,sy=map(round,world.camera.project(*point))
        assert crop==pygame.image.tostring(screen.subsurface((sx-22,sy-22,44,44)),"RGB"), "Camada não acompanhou a transformação comum"
finally:
    pygame.quit()
''')

    def test_cabeca_desenhada_atras_da_cauda_no_cruzamento(self):
        self.execute('''
import pickle
from unittest.mock import patch
import pygame
from game import enemy_render
from game.worm import Worm

class SolidLibrary:
    def duration(self,*args):
        return 100
    def frame(self,kind,*args,**kwargs):
        image=pygame.Surface((12,12),pygame.SRCALPHA)
        image.fill({"worm_head":(255,0,0),"worm_body":(0,255,0),"worm_tail":(0,0,255)}[kind])
        return image,(6,6)

pygame.init()
try:
    surface=pygame.Surface((400,400),pygame.SRCALPHA)
    worm=Worm(200,200)
    for index,segment in enumerate(worm.segments):
        segment.x,segment.y=200+index*20,240
    worm.head.x,worm.head.y=200,200
    worm.segments[-1].x,worm.segments[-1].y=200,200
    before=pickle.dumps(worm)
    with patch.object(enemy_render,"get_library",return_value=SolidLibrary()):
        enemy_render.render_enemy(surface,worm)
    assert surface.get_at((200,200))[:3]==(0,0,255), "Cabeça cobriu a cauda ao cruzar"
    assert pickle.dumps(worm)==before
finally:
    pygame.quit()
''')

    def test_smoke_real_dois_modos_saida_controlada_e_sprite_ativo(self):
        self.execute('''
from pathlib import Path
from unittest.mock import patch
import pygame
from game import main as app
from game import player_render

reports=Path("reports")
reports.mkdir(exist_ok=True)
for mode in ("defense","laboratory"):
    player_render._frames.cache_clear()
    player_render._pose.cache_clear()
    with patch.object(pygame.image,"load",wraps=pygame.image.load) as loader:
        path=reports/("mission011-smoke-"+mode+".png")
        app.main(max_frames=45,capture_path=path,start_mode=mode)
        assert path.is_file() and path.stat().st_size>1000
        assert any("sentinel" in str(call.args[0]) for call in loader.call_args_list)
    assert not pygame.get_init()
''')


if __name__ == "__main__":
    unittest.main()

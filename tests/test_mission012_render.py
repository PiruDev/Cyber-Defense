"""Assets, armas equipadas e UI; SDL dummy não é playtest humano."""

import os
from pathlib import Path
import subprocess
import sys
import unittest


class Mission012RenderTests(unittest.TestCase):
    def execute(self, script, timeout=40):
        environment = os.environ.copy()
        environment.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy",
                           PYGAME_HIDE_SUPPORT_PROMPT="1")
        result = subprocess.run([sys.executable, "-c", script],
                                cwd=Path(__file__).resolve().parents[1], env=environment,
                                capture_output=True, text=True, timeout=timeout)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_assets_originais_evoluidos_png_alfa_e_escala_nn(self):
        self.execute('''
from pathlib import Path
import pygame
from game.weapon_render import weapon_sprite

pygame.init()
try:
    pygame.display.set_mode((200,200))
    for kind,size in (("longbow",(54,54)),("returning_spear",(112,22))):
        source=pygame.image.load(str(Path("assets/sprites/weapons")/(kind+".png")))
        assert source.get_size()==size
        assert {source.get_at((x,y)).a for x in range(size[0]) for y in range(size[1])}=={0,255}
        assert source.get_at((0,0)).a==0
        image=weapon_sprite(kind)
        assert image.get_size()==size
        assert pygame.image.tostring(image,"RGBA")==pygame.image.tostring(source,"RGBA")
        assert weapon_sprite(kind) is image
finally:
    pygame.quit()
''')

    def test_todas_armas_visiveis_em_repouso_e_apos_cancelamento(self):
        self.execute('''
import pickle
from pathlib import Path
import pygame
from game.world import GameWorld
from game.weapon_render import render_weapon

pygame.init()
try:
    pygame.display.set_mode((1100,770))
    world=GameWorld()
    world.enemies.clear()
    world.player.x,world.player.y=180,180
    gallery=pygame.Surface((1080,420))
    gallery.fill((5,9,22))
    for i,kind in enumerate(("sword","katana","bow","spear","longbow","returning_spear")):
        world.equip_weapon(kind)
        assert world.attack_timer==0
        layer=pygame.Surface((360,360),pygame.SRCALPHA)
        before=pickle.dumps(world)
        render_weapon(layer,world)
        assert layer.get_bounding_rect().width>0, "Arma sumiu em repouso: "+kind
        assert pickle.dumps(world)==before
        world.weapons.start(world.player)
        world.weapons.cancel_pending()
        layer.fill((0,0,0,0))
        render_weapon(layer,world)
        assert layer.get_bounding_rect().width>0, "Arma sumiu apos interrupcao: "+kind
        icon=layer.subsurface((90,90,180,180))
        gallery.blit(icon,((i%3)*360+90,(i//3)*210))
        label=pygame.font.Font(None,24).render(kind,True,(226,247,255))
        gallery.blit(label,((i%3)*360+70,(i//3)*210+180))
    Path("reports").mkdir(exist_ok=True)
    pygame.image.save(gallery,"reports/mission012-equipped-weapons.png")
finally:
    pygame.quit()
''')

    def test_carta_de_arma_exibe_aviso_e_layout_distinto(self):
        self.execute('''
from pathlib import Path
from unittest.mock import patch
import pygame
from game.interface import create_fonts
from game.card_ui import render_cards
from game.world import GameWorld
from game.weapon_cards import WeaponCard,WEAPON_REPLACEMENT_WARNING

pygame.init()
try:
    screen=pygame.display.set_mode((1100,770))
    fonts=create_fonts(pygame)
    world=GameWorld()
    world.enemies.clear()
    world.grant_xp(100)
    world.advance_presentation(.8)
    world.card_choices[0]=WeaponCard("longbow")
    labels=[]
    class CapturingFont:
        def __init__(self,font): self.font=font
        def render(self,value,*args,**kwargs):
            labels.append(value)
            return self.font.render(value,*args,**kwargs)
        def __getattr__(self,name): return getattr(self.font,name)
    fonts={key:CapturingFont(font) for key,font in fonts.items()}
    render_cards(screen,world,fonts)
    assembled=" ".join(labels)
    assert "Arco Longo" in assembled
    assert "ATEN" in assembled and "VOC" in assembled and "PERDER" in assembled
    assert "ARMA ATUAL" in assembled
    assert "Melhoria 1 / 1" not in labels, "Carta de arma tratada como stack de atributo"
    Path("reports").mkdir(exist_ok=True)
    pygame.image.save(screen,"reports/mission012-weapon-card.png")
finally:
    pygame.quit()
''')

    def test_menu_e_hitstop_nao_disparam_arma(self):
        self.execute('''
from unittest.mock import patch
from game import main as app
from game.world import GameWorld
from game.weapons import TrainingTarget

for menu in (True,False):
    world=GameWorld()
    target=TrainingTarget(world.player.x+40,world.player.y,hp=100,max_hp=100)
    world.enemies=[target]
    if not menu: world.effects.hitstop_timer=1
    with patch.object(app,"GameWorld",return_value=world):
        app.main(max_frames=2,start_mode=None if menu else "defense")
    assert target.hp==100
    assert world.attack_timer==0
''')

    def test_smoke_real_dois_modos_sem_espaco(self):
        self.execute('''
from pathlib import Path
from game.main import main
import pygame
Path("reports").mkdir(exist_ok=True)
for mode in ("defense","laboratory"):
    path=Path("reports")/("mission012-smoke-"+mode+".png")
    main(max_frames=45,capture_path=path,start_mode=mode)
    assert path.is_file() and path.stat().st_size>1000
    assert not pygame.get_init()
''')

    def test_teclas456_do_main_alternam_armas_no_laboratorio(self):
        self.execute('''
from unittest.mock import Mock,patch
import pygame
from game import main as app
from game.world import GameWorld

world=GameWorld(mode="laboratory")
world.phase="weapon_choice"
assert world.choose_weapon("katana")
observed=[]
base_overlay=app.render_overlay
def overlay(surface,state,fonts):
    observed.append(state.weapon_id)
    base_overlay(surface,state,fonts)
clock=Mock()
clock.tick.return_value=16
def events():
    key=(pygame.K_4,pygame.K_5,pygame.K_6)[len(observed)]
    return [pygame.event.Event(pygame.KEYDOWN,key=key)]
with patch.object(app,"GameWorld",return_value=world), \\
     patch.object(app,"render_overlay",side_effect=overlay), \\
     patch.object(pygame.event,"get",side_effect=events), \\
     patch.object(pygame.time,"Clock",return_value=clock):
    app.main(max_frames=3,start_mode="laboratory")
assert observed==["longbow","returning_spear","sword"]
assert world.practice_remaining==45, "Troca de equipamento acumulou tempo de gameplay"
assert not pygame.get_init()
''')


if __name__ == "__main__":
    unittest.main()

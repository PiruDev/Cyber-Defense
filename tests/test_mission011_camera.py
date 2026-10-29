"""Regressões de câmera em coordenadas de mundo, sem inicializar Pygame."""

import math
import pickle
from random import Random
import unittest

from game.camera import Camera
from game.enemies import Drop, Enemy
from game.projectiles import Projectile
from game.world import GameWorld


class Mission011CameraTests(unittest.TestCase):
    def test_transformacao_mouse_mundo_tela_reversivel_com_shake(self):
        camera = Camera((0, 0, 2400, 1600))
        camera.update(1300.5, 920.25, 0, snap=True)
        for shake in ((0, 0), (3, -2), (-3, 2)):
            for point in ((0, 0), (1300.5, 920.25), (2399.5, 1599.5)):
                with self.subTest(shake=shake, point=point):
                    self.assertEqual(camera.unproject(*camera.project(*point, shake), shake), point)
            screen_point = camera.project(1300.5, 920.25, shake)
            # O blit usa origem inteira: no máximo meio pixel de quantização.
            self.assertLessEqual(abs(screen_point[0] - (550 + shake[0])), .5)

    def test_limites_nos_quatro_cantos_e_shake_sem_mostrar_exterior(self):
        camera = Camera((0, 0, 2400, 1600))
        for target in ((0, 0), (2400, 0), (0, 1600), (2400, 1600)):
            camera.update(*target, 0, snap=True)
            for shake in ((0, 0), (-100, -100), (100, 100)):
                ox, oy = camera.origin(shake)
                self.assertGreaterEqual(ox, 0)
                self.assertGreaterEqual(oy, 0)
                self.assertLessEqual(ox + camera.viewport[2], 2400)
                self.assertLessEqual(oy + camera.viewport[3], 1600)
        camera.update(2400, 1600, 0, snap=True)
        self.assertEqual(camera.origin(), (1364, 1070))

    def test_suavidade_monotonica_independente_de_fps(self):
        origins = []
        for fps in (30, 60, 120):
            camera = Camera((0, 0, 2400, 1600))
            previous = camera.x
            for _ in range(fps):
                camera.update(1400, 900, 1 / fps)
                self.assertGreaterEqual(camera.x, previous)
                self.assertLessEqual(camera.x, 1400 - 1036 / 2)
                previous = camera.x
            origins.append((camera.x, camera.y))
        for position in origins[1:]:
            self.assertAlmostEqual(position[0], origins[0][0], places=8)
            self.assertAlmostEqual(position[1], origins[0][1], places=8)
        self.assertLess(abs(origins[0][0] - (1400 - 1036 / 2)), .1)

    def test_arena_com_origem_propria_e_tempos_invalidos(self):
        camera = Camera((32, 154, 1036, 530))
        camera.update(550, 419, 0, snap=True)
        self.assertEqual(camera.origin(), (32, 154))
        self.assertEqual(camera.project(500, 400), (500, 400))
        for value in (-.1, float("inf"), float("nan")):
            with self.assertRaises(ValueError):
                camera.update(500, 400, value)

    def test_arena_grande_default_e_restart_encaixa_camera(self):
        for mode in ("defense", "laboratory"):
            world = GameWorld(rng=Random(11), mode=mode)
            self.assertEqual(world.arena, (0, 0, 2400, 1600))
            self.assertEqual(world.camera.viewport, (32, 154, 1036, 530))
            self.assertEqual(world.camera.project(world.player.x, world.player.y), (550, 419))
            world.enemies.clear()
            world.update(.05, move_x=1)
            self.assertGreater(world.camera.x, 682)
            self.assertLess(world.camera.x, world.player.x - 518)
            world.restart()
            self.assertEqual(world.camera.origin(), (682, 535))

    def test_camera_nao_muda_regras_de_ataque_flecha_ou_coleta(self):
        world = GameWorld(rng=Random(19))
        world.enemies.clear()
        world.player.x, world.player.y = 1860, 1100
        world.player.facing_x, world.player.facing_y = 1, 0
        world.camera.update(world.player.x, world.player.y, 0, snap=True)
        self.assertGreater(world.camera.x, 1000)
        self.assertGreater(world.camera.y, 500)
        enemy = Enemy(world.player.x + 45, world.player.y, hp=3, speed=0)
        world.enemies = [enemy]
        world.drops = [Drop(world.player.x, world.player.y)]
        potions = world.player.inventory.potions
        world.update(0, attack=True)
        self.assertEqual(enemy.hp, 2)
        self.assertEqual(world.player.inventory.potions, potions + 1)
        self.assertFalse(world.drops)
        world.projectiles = [Projectile(world.player.x - 100, world.player.y, 1000, 0)]
        world.update(.2)
        self.assertEqual(world.player.progression.hp, 92)
        self.assertFalse(world.projectiles)

    def test_camera_e_simulacao_congeladas_nas_cartas_e_inventario(self):
        world = GameWorld(rng=Random(4))
        world.grant_xp(250)
        before = pickle.dumps(world)
        world.update(50, move_x=1, attack=True)
        self.assertEqual(pickle.dumps(world), before)
        camera = (world.camera.x, world.camera.y)
        while world.choosing_card:
            world.advance_presentation(.8)
            self.assertEqual((world.camera.x, world.camera.y), camera)
            self.assertTrue(world.choose_card(0))
        world.toggle_inventory()
        before = pickle.dumps(world)
        world.update(20, move_y=-1)
        self.assertEqual(pickle.dumps(world), before)
        world.toggle_inventory()
        world.update(.016, move_x=1)
        self.assertLessEqual(math.hypot(world.player.x - 1200, world.player.y - 800), 4)


if __name__ == "__main__":
    unittest.main()

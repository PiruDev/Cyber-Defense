"""Trajetórias, cruzamentos e promoção sem repulsão interna da minhoca."""

import math
import unittest
from types import SimpleNamespace

from game.combat import apply_enemy_hit
from game.physics import SeparationSystem
from game.player import Player
from game.worm import Worm


class Mission011WormTests(unittest.TestCase):
    arena = (0, 0, 2400, 1600)

    def worm(self):
        worm = Worm(700, 500)
        worm.reset_trail(self.arena)
        return worm

    def trace(self, worm, destinations, step=1):
        for target_x, target_y in destinations:
            while math.hypot(target_x - worm.x, target_y - worm.y) > 1e-8:
                dx, dy = target_x - worm.x, target_y - worm.y
                distance = math.hypot(dx, dy)
                amount = min(step, distance)
                worm.x += dx / distance * amount
                worm.y += dy / distance * amount
                worm._follow_segments(self.arena)

    def assert_body(self, worm):
        self.assertEqual((worm.x, worm.y), (worm.head.x, worm.head.y))
        for index, segment in enumerate(worm.segments):
            expected = worm.sample_trail(index * worm.segment_spacing)
            self.assertAlmostEqual(segment.x, expected[0], places=7)
            self.assertAlmostEqual(segment.y, expected[1], places=7)
            self.assertGreaterEqual(segment.x, segment.radius - 1e-8)
            self.assertGreaterEqual(segment.y, segment.radius - 1e-8)
            self.assertLessEqual(segment.x, 2400 - segment.radius + 1e-8)
            self.assertLessEqual(segment.y, 1600 - segment.radius + 1e-8)
        for first, second in zip(worm.segments, worm.segments[1:]):
            self.assertLessEqual(math.hypot(first.x-second.x, first.y-second.y), 32 + 1e-7)

    def test_distancia_de_caminho_em_curvas_fechadas(self):
        worm = self.worm()
        self.trace(worm, ((740, 500), (740, 540), (700, 540), (700, 500)))
        self.assert_body(worm)
        # Perímetro 160: a cabeça retorna à cauda sem deslocar o corpo para fora.
        self.assertAlmostEqual(worm.head.x, worm.segments[-1].x, places=6)
        self.assertAlmostEqual(worm.head.y, worm.segments[-1].y, places=6)
        expected = ((700,500), (700,532), (724,540), (740,524), (732,500), (700,500))
        for segment, point in zip(worm.segments, expected):
            self.assertAlmostEqual(segment.x, point[0], delta=.05)
            self.assertAlmostEqual(segment.y, point[1], delta=.05)

    def test_cabeca_cruza_cauda_sem_colisao_interna_ou_impulso(self):
        worm = self.worm()
        self.trace(worm, ((740, 500), (740, 540), (700, 540), (700, 500)))
        before = [(segment.x, segment.y) for segment in worm.segments]
        trail = worm.trail_snapshot
        SeparationSystem().update([worm], self.arena, .1)
        self.assertEqual(before, [(segment.x, segment.y) for segment in worm.segments])
        self.assertEqual(trail, worm.trail_snapshot)
        self.trace(worm, ((720,500),))
        self.assert_body(worm)

    def test_promocao_preserva_sobreviventes_e_remove_so_uma_cabeca(self):
        worm = self.worm()
        self.trace(worm, ((740, 500), (740, 540), (700, 540)))
        for remaining in range(5, 0, -1):
            survivors = [(id(segment), segment.x, segment.y) for segment in worm.segments[1:]]
            self.assertEqual(worm.receive_damage(1000), 10)
            self.assertEqual(len(worm.segments), remaining)
            self.assertEqual([(id(segment),segment.x,segment.y) for segment in worm.segments], survivors)
            worm._follow_segments(self.arena)
            for segment, (_, x, y) in zip(worm.segments, survivors):
                self.assertAlmostEqual(segment.x, x, places=6)
                self.assertAlmostEqual(segment.y, y, places=6)
            self.assert_body(worm)
        self.assertEqual(worm.receive_damage(1000), 10)
        self.assertFalse(worm.segments)
        self.assertEqual(worm.hp, 0)
        self.assertEqual(worm.receive_damage(1000), 0)

    def test_translacao_externa_move_historico_e_nao_adiciona_distancia(self):
        worm = self.worm()
        self.trace(worm, ((740, 500), (740, 540), (700, 540)))
        before = worm.trail_snapshot
        positions = [(segment.x, segment.y) for segment in worm.segments]
        dx, dy = SeparationSystem.translate(worm, 13, -9, self.arena)
        self.assertEqual((dx,dy), (13,-9))
        for (old_s,old_x,old_y), (s,x,y) in zip(before, worm.trail_snapshot):
            self.assertEqual(s, old_s)
            self.assertAlmostEqual(x-old_x, dx)
            self.assertAlmostEqual(y-old_y, dy)
        worm._follow_segments(self.arena)
        for segment, (x,y) in zip(worm.segments, positions):
            self.assertAlmostEqual(segment.x-x, dx)
            self.assertAlmostEqual(segment.y-y, dy)

    def test_trajeto_independente_fps_e_memoria_limitada(self):
        samples = []
        for fps in (30, 120):
            worm = self.worm()
            for target in ((920,500), (920,720), (700,720), (700,500)):
                player = SimpleNamespace(x=target[0], y=target[1])
                for _ in range(4*fps):
                    worm.move_towards(player, 1/fps)
            self.assert_body(worm)
            samples.append([(segment.x,segment.y) for segment in worm.segments])
            self.assertLess(len(worm.trail_snapshot), 1200)
        for first, second in zip(*samples):
            self.assertAlmostEqual(first[0], second[0], delta=.05)
            self.assertAlmostEqual(first[1], second[1], delta=.05)

    def test_knockback_stun_e_limites_preservam_corpo(self):
        worm = Worm(2380, 1580)
        worm.reset_trail(self.arena)
        player = Player(x=worm.x-40, y=worm.y)
        self.assertTrue(apply_enemy_hit(player, worm))
        free = worm.advance_feedback(.05, self.arena)
        self.assertEqual(free, 0)
        self.assertGreater(worm.stun_timer, 0)
        self.assert_body(worm)
        for _ in range(20):
            free = worm.advance_feedback(.05, self.arena)
            worm.move_towards(SimpleNamespace(x=2390,y=1590), free)
            self.assert_body(worm)


if __name__ == "__main__":
    unittest.main()

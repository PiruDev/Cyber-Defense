"""Perfuração: colisões ordenadas e deduplicação por criatura."""

from random import Random
import unittest

from game.balance import WEAPON_CONFIGS
from game.world import GameWorld
from game.weapons import TrainingTarget
from game.worm import Worm


class LongbowTests(unittest.TestCase):
    def world(self):
        world = GameWorld(rng=Random(12))
        world.phase = "practice"
        world.practice_remaining = 999
        world.enemies.clear()
        world.weapons.switch("longbow")
        return world

    def test_perfura_tres_alvos_diferentes_em_ordem_e_para_no_terceiro(self):
        world = self.world()
        targets = [TrainingTarget(world.player.x + distance, world.player.y,
                                  hp=100, max_hp=100) for distance in (100, 180, 260, 340)]
        world.enemies = list(reversed(targets))
        world.update(0)
        self.assertEqual(len(world.projectiles), 1)
        world.auto_attack = False
        damage = world.player.damage * WEAPON_CONFIGS["longbow"].damage_multiplier
        world.update(1)
        for target in targets[:3]:
            self.assertAlmostEqual(target.hp, 100 - damage)
        self.assertEqual(targets[-1].hp, 100)
        self.assertFalse(world.projectiles)

    def test_mesma_flecha_nao_repete_hit_enquanto_sobreposta(self):
        world = self.world()
        target = TrainingTarget(world.player.x + 100, world.player.y, hp=100, max_hp=100,
                                radius=50)
        world.enemies = [target]
        world.update(0)
        arrow = world.projectiles[0]
        world.auto_attack = False
        world.update(.2)
        after = target.hp
        self.assertLess(after, 100)
        for _ in range(4):
            world.update(0)
        self.assertEqual(target.hp, after)
        self.assertIn(arrow, world.projectiles)

    def test_segmentos_da_minhoca_contam_como_uma_criatura(self):
        world = self.world()
        worm = Worm(world.player.x + 180, world.player.y, speed=0)
        worm.reset_trail(world.arena)
        world.enemies = [worm]
        world.update(0)
        self.assertEqual(len(world.projectiles), 1)
        world.auto_attack = False
        world.update(.5)
        expected = 60 - world.player.damage * WEAPON_CONFIGS["longbow"].damage_multiplier
        self.assertAlmostEqual(worm.hp, expected)
        for _ in range(5):
            world.update(.05)
        self.assertAlmostEqual(worm.hp, expected)
        self.assertEqual(len(worm.segments), 6)

    def test_flecha_sem_tres_acertos_desaparece_ao_exceder_alcance(self):
        world = self.world()
        target = TrainingTarget(world.player.x + 150, world.player.y, hp=100, max_hp=100)
        world.enemies = [target]
        world.update(0)
        arrow = world.projectiles[0]
        start_x = arrow.x
        reach = arrow.range_remaining
        world.auto_attack = False
        world.update(10)
        self.assertFalse(world.projectiles)
        self.assertAlmostEqual(arrow.x - start_x, reach)
        self.assertEqual(arrow.range_remaining, 0)


if __name__ == "__main__":
    unittest.main()

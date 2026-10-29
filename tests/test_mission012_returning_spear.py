"""Lança arremessada, recuperação e relógio de gameplay."""

from random import Random
import unittest

from game.balance import BalanceConfig, WEAPON_CONFIGS
from game.projectiles import Projectile
from game.world import GameWorld
from game.weapons import TrainingTarget


class ReturningSpearTests(unittest.TestCase):
    def world(self):
        world = GameWorld(rng=Random(12), config=BalanceConfig(weapon_card_chance=0))
        world.phase = "practice"
        world.practice_remaining = 999
        world.enemies = [TrainingTarget(world.player.x + 200, world.player.y,
                                        hp=100, max_hp=100)]
        world.weapons.switch("returning_spear")
        world.update(0)
        self.assertIsNotNone(world.weapons.returning_spear)
        return world

    def land(self, world):
        world.update(.7)
        spear = world.weapons.returning_spear
        self.assertIsNotNone(spear)
        self.assertTrue(spear.landed)
        return spear

    def test_arremesso_causa_dano_e_lanca_fica_no_mundo_sem_novos_ataques(self):
        world = self.world()
        target = world.enemies[0]
        spear = self.land(world)
        damage = world.player.damage * WEAPON_CONFIGS["returning_spear"].damage_multiplier
        self.assertAlmostEqual(target.hp, 100 - damage)
        position = spear.x, spear.y
        world.update(.8)
        self.assertIs(world.weapons.returning_spear, spear)
        self.assertEqual((spear.x, spear.y), position)
        self.assertAlmostEqual(target.hp, 100 - damage)
        self.assertEqual(world.weapons.start(world.player), ())

    def test_coleta_manual_ativa_um_giro360_com_hit_unico_por_alvo(self):
        world = self.world()
        spear = self.land(world)
        world.player.x, world.player.y = spear.x, spear.y
        x, y = spear.x, spear.y
        targets = [TrainingTarget(x+dx, y+dy, hp=100, max_hp=100)
                   for dx, dy in ((80,0),(-80,0),(0,80),(0,-80),(150,0))]
        world.enemies = targets
        world.update(0)
        self.assertIsNone(world.weapons.returning_spear)
        self.assertGreater(world.weapons.spin_timer, 0)
        damage = world.player.damage * WEAPON_CONFIGS["returning_spear"].damage_multiplier
        for target in targets[:4]:
            self.assertAlmostEqual(target.hp, 100 - damage)
        self.assertEqual(targets[-1].hp, 100)
        snapshot = [target.hp for target in targets]
        for _ in range(10):
            world.update(.02)
        self.assertEqual([target.hp for target in targets], snapshot)

    def test_retorno_automatico_apos3segundos_nao_ativa_giro(self):
        world = self.world()
        spear = self.land(world)
        target = world.enemies[0]
        hp = target.hp
        world.update(2.29)
        self.assertIs(world.weapons.returning_spear, spear)
        self.assertAlmostEqual(spear.elapsed, 2.99)
        world.update(.01)
        self.assertIsNone(world.weapons.returning_spear)
        self.assertEqual(world.weapons.spin_timer, 0)
        self.assertGreater(world.weapons.return_timer, 0)
        self.assertGreater(world.attack_cooldown, 0)
        self.assertEqual(target.hp, hp)
        world.update(.1)
        self.assertIsNone(world.weapons.returning_spear)
        self.assertEqual(world.weapons.spin_timer, 0)
        self.assertEqual(target.hp, hp)

    def test_contato_no_limite_de3segundos_prioriza_retorno_sem_giro(self):
        world = self.world()
        spear = self.land(world)
        world.update(2.29)
        world.player.x, world.player.y = spear.x, spear.y
        world.update(.01)
        self.assertIsNone(world.weapons.returning_spear)
        self.assertEqual(world.weapons.spin_timer, 0)

    def test_tempo_congela_no_inventario_e_nas_cartas(self):
        world = self.world()
        spear = self.land(world)
        elapsed = spear.elapsed
        position = spear.x, spear.y
        world.inventory_open = True
        world.update(30)
        self.assertEqual(spear.elapsed, elapsed)
        world.inventory_open = False
        world.phase = "waves"
        world.grant_xp(100)
        world.advance_presentation(10)
        world.update(30)
        self.assertEqual(spear.elapsed, elapsed)
        self.assertEqual((spear.x, spear.y), position)
        self.assertTrue(world.choose_card(0))
        world.update(.01)
        self.assertAlmostEqual(spear.elapsed, elapsed+.01)

    def test_recuperacao_manual_respeita_novo_cooldown(self):
        world = self.world()
        spear = self.land(world)
        world.player.x, world.player.y = spear.x, spear.y
        world.update(0)
        self.assertGreater(world.attack_cooldown, 0)
        world.update(.3)
        self.assertIsNone(world.weapons.returning_spear)
        self.assertEqual(world.weapons.start(world.player), ())
        world.update(.13)
        self.assertIsNotNone(world.weapons.returning_spear)

    def test_troca_remove_lanca_pulsos_giro_retorno_e_projeteis_do_jogador(self):
        world = self.world()
        self.land(world)
        world.player.upgrades["speed"] = 2
        world.player.progression.hp = 70
        world.projectiles.extend((Projectile(100,100,1,0,team="player"),
                                  Projectile(200,200,1,0,team="enemy")))
        world.weapons.spin_timer = .1
        world.weapons.return_timer = .1
        self.assertTrue(world.equip_weapon("bow"))
        self.assertEqual(world.weapon_id, "bow")
        self.assertIsNone(world.weapons.returning_spear)
        self.assertEqual(world.weapons.pending, [])
        self.assertEqual(world.attack_timer, 0)
        self.assertEqual(world.weapons.spin_timer, 0)
        self.assertEqual(world.weapons.return_timer, 0)
        self.assertEqual([projectile.team for projectile in world.projectiles], ["enemy"])
        self.assertEqual(world.player.upgrades, {"speed": 2})
        self.assertEqual(world.player.progression.hp, 70)


if __name__ == "__main__":
    unittest.main()

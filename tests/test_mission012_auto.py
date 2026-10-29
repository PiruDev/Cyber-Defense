"""Combate automático: contratos observáveis, sem janela Pygame."""

import pickle
from random import Random
import unittest

from game.world import GameWorld
from game.weapons import TrainingTarget, WeaponSystem
from game.balance import WEAPON_CONFIGS
from game.player import Player


class AutomaticCombatTests(unittest.TestCase):
    def world(self, weapon="sword"):
        world = GameWorld(rng=Random(1212))
        world.phase = "practice"
        world.practice_remaining = 999
        world.enemies.clear()
        world.weapons.switch(weapon)
        return world

    def target(self, world, dx, dy=0, *, hp=100):
        return TrainingTarget(world.player.x + dx, world.player.y + dy,
                              hp=hp, max_hp=max(1, hp))

    def test_automatico_padrao_mira_vivo_mais_proximo_sem_espaco(self):
        world = self.world()
        left = self.target(world, -45)
        right = self.target(world, 65)
        dead = self.target(world, 1, hp=0)
        world.enemies = [right, dead, left]
        world.update(0)
        self.assertEqual(left.hp, 99)
        self.assertEqual(right.hp, 100)
        self.assertAlmostEqual(world.attack_facing_x, -1)
        self.assertAlmostEqual(world.attack_facing_y, 0)
        self.assertGreater(world.attack_timer, 0)

    def test_nenhum_alvo_ao_alcance_mantem_repouso(self):
        for weapon in ("sword", "katana", "spear", "bow", "longbow", "returning_spear"):
            with self.subTest(weapon=weapon):
                world = self.world(weapon)
                world.enemies = [self.target(world, 1000)]
                world.update(.05)
                self.assertEqual(world.attack_timer, 0)
                self.assertEqual(world.attack_cooldown, 0)
                self.assertFalse(world.projectiles)
                self.assertEqual(world.enemies[0].hp, 100)

    def test_espada_respeita_cooldown_sem_dano_por_frame(self):
        world = self.world()
        target = self.target(world, 40)
        world.enemies = [target]
        world.update(0)
        self.assertEqual(target.hp, 99)
        for _ in range(6):
            world.update(.05)
        self.assertEqual(target.hp, 99)
        world.update(.05)
        self.assertEqual(target.hp, 98)

    def test_katana_dois_impactos_por_ciclo_e_direcao_capturada(self):
        world = self.world("katana")
        target = self.target(world, 40)
        world.enemies = [target]
        world.update(0)
        self.assertAlmostEqual(target.hp, 99.4)
        world.player.facing_x, world.player.facing_y = 0, -1
        world.update(.099)
        self.assertAlmostEqual(target.hp, 99.4)
        world.update(.001)
        self.assertAlmostEqual(target.hp, 98.8)
        world.update(.139)
        world.update(0)
        self.assertAlmostEqual(target.hp, 98.8)

    def test_lanca_aplica_somente_estocada_no_tempo_de_impacto(self):
        world = self.world("spear")
        target = self.target(world, 90)
        world.enemies = [target]
        world.update(0)
        self.assertEqual(target.hp, 100)
        world.update(.079)
        self.assertEqual(target.hp, 100)
        world.update(.001)
        self.assertAlmostEqual(target.hp, 98.8)
        for _ in range(4):
            world.update(.05)
        self.assertAlmostEqual(target.hp, 98.8)

    def test_arco_usa_direcao_do_alvo_no_instante_do_disparo(self):
        world = self.world("bow")
        near = self.target(world, 0, -220)
        farther = self.target(world, 300)
        world.enemies = [farther, near]
        world.update(0)
        self.assertEqual(len(world.projectiles), 1)
        arrow = world.projectiles[0]
        self.assertAlmostEqual(arrow.vx, 0)
        self.assertAlmostEqual(arrow.vy, -400)
        self.assertAlmostEqual(arrow.damage, 1.4)
        self.assertEqual(arrow.range_remaining, 500)
        world.player.facing_x, world.player.facing_y = 1, 0
        near.x += 150
        world.update(.05)
        self.assertEqual(len(world.projectiles), 1)
        self.assertAlmostEqual(arrow.vx, 0)
        self.assertAlmostEqual(arrow.vy, -400)

    def test_pauses_nao_criam_ataque_ou_avancam_timers(self):
        for state in ("inventory", "game_over", "victory", "weapon_choice", "cards"):
            with self.subTest(state=state):
                world = self.world()
                world.enemies = [self.target(world, 40)]
                if state == "inventory":
                    world.inventory_open = True
                elif state == "game_over":
                    world.game_over = True
                elif state == "victory":
                    world.victory = True
                elif state == "weapon_choice":
                    world.phase = "weapon_choice"
                else:
                    world.phase = "waves"
                    world.grant_xp(100)
                before = pickle.dumps(world)
                world.update(100, move_x=1)
                self.assertEqual(pickle.dumps(world), before)

    def test_alcance_especifico_e_direcao_nao_restringe_auto_alvo(self):
        world = self.world()
        world.player.facing_x, world.player.facing_y = 1, 0
        target = self.target(world, -250)
        world.enemies = [target]
        world.update(0)
        self.assertEqual(world.attack_timer, 0)
        world.weapons.switch("bow")
        world.update(0)
        self.assertEqual(len(world.projectiles), 1)
        self.assertAlmostEqual(world.projectiles[0].vx, -400)

    def test_stun_do_jogador_bloqueia_inicio_de_ataque(self):
        world = self.world()
        target = self.target(world, 40)
        world.enemies = [target]
        world.player.stun_timer = .2
        world.update(0)
        self.assertEqual(target.hp, 100)
        self.assertEqual(world.attack_timer, 0)
        world.player.stun_timer = 0
        world.update(0)
        self.assertEqual(target.hp, 99)

    def test_cooldown8_upgrades_preserva_cadencia_sem_gate_visual_extra(self):
        for weapon_id in ("katana", "spear"):
            with self.subTest(weapon=weapon_id):
                player = Player(upgrades={"cooldown": 8})
                weapon = WeaponSystem(weapon_id)
                config = WEAPON_CONFIGS[weapon_id]
                weapon.start(player)
                interval = config.cooldown * .9**8
                pulses = weapon.update(interval)
                self.assertEqual(len(pulses), 1)
                self.assertAlmostEqual(weapon.cooldown, 0)
                self.assertGreater(weapon.animation_timer, 0)
                # O próximo ciclo começa no intervalo mecânico mesmo que a pose
                # do ciclo anterior ainda não tenha desaparecido completamente.
                immediate = weapon.start(player)
                self.assertEqual(len(immediate), int(weapon_id == "katana"))
                self.assertEqual(len(weapon.pending), 1)
                self.assertAlmostEqual(weapon.cooldown, interval)
                self.assertAlmostEqual(weapon.animation_timer, config.animation_duration)


if __name__ == "__main__":
    unittest.main()

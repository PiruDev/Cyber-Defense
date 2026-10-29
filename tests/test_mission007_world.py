import pickle
import random
import unittest
from unittest.mock import patch

from game.balance import BalanceConfig
from game.boss import Rootkit
from game.cards import apply_card
from game.combat import apply_enemy_hit
from game.enemies import Drop, Enemy
from game.modes import GameMode
from game.projectiles import Projectile
from game.world import GameWorld


class Mission007WorldTests(unittest.TestCase):
    def mundo(self, mode="defense"):
        world = GameWorld(rng=random.Random(7), mode=mode)
        world.enemies.clear()
        world.drops.clear()
        world.player.x, world.player.y = 500, 400
        world.player.facing_x, world.player.facing_y = 1, 0
        return world

    def treino(self, mode="defense", weapon="katana"):
        world = self.mundo(mode)
        world.phase = "weapon_choice"
        self.assertTrue(world.choose_weapon(weapon))
        return world

    def test_defesa_seis_ondas_e_lab_cinco_terminam_em_escolha_nao_vitoria(self):
        for mode, kills, waves in (("defense", 52, 6), ("laboratory", 51, 5)):
            with self.subTest(mode=mode):
                world = GameWorld(mode=mode, rng=random.Random(7))
                boss_seen = False
                for _ in range(200):
                    for enemy in world.enemies:
                        if isinstance(enemy, Rootkit):
                            boss_seen = True
                            self.assertEqual(enemy.max_hp, 48)
                        enemy.hp = 0
                    world.update(1)
                    while world.choosing_card:
                        world.advance_presentation(0.8)
                        self.assertTrue(world.choose_card(0))
                    if world.choosing_weapon:
                        break
                self.assertEqual(boss_seen, mode == "defense")
                self.assertEqual((world.kills, world.waves.number), (kills, waves))
                self.assertTrue(world.choosing_weapon)
                self.assertFalse(world.victory)
                self.assertEqual((world.drops, world.projectiles), ([], []))
                antes = pickle.dumps(world)
                world.update(10, move_x=1, attack=True)
                world.toggle_inventory()
                self.assertFalse(world.use_potion())
                self.assertEqual(pickle.dumps(world), antes)

    def test_escolha_arma_unica_valida_e_defesa_nao_troca_na_pratica(self):
        world = self.mundo()
        self.assertFalse(world.choose_weapon("katana"))
        world.phase = "weapon_choice"
        for invalido in (-1, 3, True, "sword", "inexistente", 0.0):
            self.assertFalse(world.choose_weapon(invalido))
        self.assertTrue(world.choose_weapon(0))
        self.assertEqual((world.weapon_id, world.phase, world.practice_remaining), ("katana", "practice", 15))
        self.assertFalse(world.choose_weapon(1))
        self.assertFalse(world.switch_weapon("bow"))
        self.assertEqual(world.weapon_id, "katana")

    def test_defesa_pratica_tres_alvos_nao_concede_drops_xp_ou_abates(self):
        world = self.treino()
        antes = (world.kills, world.player.progression.xp, world.score)
        self.assertEqual(len(world.enemies), 3)
        for enemy in world.enemies:
            enemy.hp = 0
        world.update(0)
        self.assertTrue(world.victory)
        self.assertEqual(world.practice_kills, 3)
        self.assertEqual((world.kills, world.player.progression.xp, world.score), antes)
        self.assertEqual(world.drops, [])
        self.assertEqual(world.projectiles, [])

    def test_pratica_timer_finito_e_pausa_sem_creditar_tempo(self):
        for mode, duracao in (("defense", 15), ("laboratory", 45)):
            with self.subTest(mode=mode):
                world = self.treino(mode)
                inicio = world.elapsed
                world.toggle_inventory()
                world.update(100)
                self.assertEqual(world.practice_remaining, duracao)
                world.toggle_inventory()
                world.update(100)
                self.assertTrue(world.victory)
                self.assertEqual(world.practice_remaining, 0)
                self.assertAlmostEqual(world.elapsed - inicio, duracao)

    def test_lab_tres_alvos_por_arma_nao_repoe_ao_revisitar(self):
        world = self.treino("laboratory")
        for enemy in world.enemies:
            enemy.hp = 0
        world.update(0)
        self.assertFalse(world.victory)
        self.assertTrue(world.switch_weapon("bow"))
        self.assertEqual(len(world.enemies), 3)
        bow_ids = [id(enemy) for enemy in world.enemies]
        world.enemies[0].hp = 2
        world.attack_cooldown = 0.3
        world.projectiles.append(Projectile(500, 400, 400, 0, team="player"))
        self.assertTrue(world.switch_weapon("katana"))
        self.assertEqual(world.enemies, [])
        self.assertTrue(world.switch_weapon("bow"))
        self.assertEqual([id(enemy) for enemy in world.enemies], bow_ids)
        self.assertEqual(world.enemies[0].hp, 2)
        self.assertEqual(world.attack_cooldown, 0.3)
        self.assertEqual(world.projectiles, [])
        for enemy in world.enemies:
            enemy.hp = 0
        world.update(0)
        self.assertTrue(world.switch_weapon("spear"))
        for enemy in world.enemies:
            enemy.hp = 0
        world.update(0)
        self.assertEqual(world.practice_kills, 9)
        self.assertTrue(world.victory)
        self.assertFalse(world.switch_weapon("katana"))
        self.assertEqual((world.kills, world.player.progression.xp), (0, 0))

    def test_katana_world_duas_janelas_sem_dano_por_frame_repetido(self):
        world = self.mundo()
        world.weapons.switch("katana")
        target = Enemy(545, 400, hp=5, max_hp=5, speed=0)
        world.enemies = [target]
        world.update(0, attack=True)
        self.assertAlmostEqual(target.hp, 4.4)
        for _ in range(5):
            world.update(0, attack=True)
        self.assertAlmostEqual(target.hp, 4.4)
        world.update(0.1)
        self.assertAlmostEqual(target.hp, 3.8)
        for _ in range(5):
            world.update(0)
        self.assertAlmostEqual(target.hp, 3.8)
        self.assertEqual(sum(e.kind == "hit" for e in world.effects.consume_events()), 2)

    def test_pulso_melee_preserva_recuo_radial_fora_do_eixo(self):
        world = self.mundo()
        enemy = Enemy(540, 430, speed=0)
        world.enemies = [enemy]
        world.update(0, attack=True)
        self.assertAlmostEqual(enemy.knockback_vx, 160)
        self.assertAlmostEqual(enemy.knockback_vy, 120)

    def test_arco_colide_primeiro_alvo_varrido_sem_dano_ao_jogador(self):
        world = self.mundo()
        world.weapons.switch("bow")
        perto = Enemy(600, 400, speed=0)
        longe = Enemy(700, 400, speed=0)
        world.enemies = [longe, perto]
        world.update(0, attack=True)
        self.assertEqual(len(world.projectiles), 1)
        self.assertEqual(world.projectiles[0].team, "player")
        world.update(0.5)
        self.assertAlmostEqual(perto.hp, 1.6)
        self.assertEqual(longe.hp, 3)
        self.assertEqual(world.player.progression.hp, 100)
        self.assertEqual(world.projectiles, [])

    def test_lanca_fina_alcanca_frente_e_exclui_lateral_e_atras(self):
        world = self.mundo()
        world.weapons.switch("spear")
        frente = Enemy(600, 400, speed=0)
        lateral = Enemy(570, 440, speed=0)
        atras = Enemy(470, 400, speed=0)
        world.enemies = [frente, lateral, atras]
        world.update(0, attack=True)
        self.assertEqual(frente.hp, 3)
        world.update(0.08)
        self.assertAlmostEqual(frente.hp, 1.8)
        self.assertEqual((lateral.hp, atras.hp), (3, 3))

    def test_rootkit_resiste_interrupcao_mas_recebe_dano_real(self):
        world = self.mundo()
        boss = Rootkit(545, 400, state="windup", telegraph_timer=0.4)
        self.assertTrue(apply_enemy_hit(world.player, boss))
        self.assertEqual((boss.hp, boss.stun_timer, boss.knockback_timer), (47, 0, 0))
        self.assertEqual((boss.state, boss.telegraph_timer), ("windup", 0.4))
        self.assertEqual(boss.hit_flash_timer, 0.1)
        boss = Rootkit(545, 400, state="windup", telegraph_timer=0.4)
        world.enemies = [boss]
        world.update(0.05, attack=True)
        self.assertEqual(boss.hit_flash_timer, 0.1)
        self.assertAlmostEqual(boss.telegraph_timer, 0.35)
        self.assertEqual((boss.stun_timer, boss.knockback_timer), (0, 0))

    def test_rootkit_antecipa_cone_e_rajada_seis_sem_repetir_frame(self):
        world = self.mundo()
        boss = Rootkit(455, 400, speed=0)
        self.assertIsNone(boss.advance_ai(0, world.player, world.arena))
        self.assertEqual((boss.pattern, boss.telegraph_timer), ("cone", 0.65))
        self.assertIsNone(boss.advance_ai(0.64, world.player, world.arena))
        action = boss.advance_ai(0.01, world.player, world.arena)
        self.assertEqual(action.pattern, "cone")
        self.assertEqual(boss.attack_cooldown, 2.5)
        self.assertIsNone(boss.advance_ai(0, world.player, world.arena))
        self.assertIsNone(boss.advance_ai(2.5, world.player, world.arena))
        self.assertEqual(boss.pattern, "burst")
        action = boss.advance_ai(0.65, world.player, world.arena)
        self.assertEqual(action.pattern, "burst")
        self.assertEqual(len(action.projectiles), 6)
        self.assertTrue(all(p.team == "enemy" for p in action.projectiles))
        self.assertEqual(len({(round(p.vx, 4), round(p.vy, 4)) for p in action.projectiles}), 6)

    def test_bosses_nao_sorteiam_drop_comum(self):
        from game.worm import Worm
        for classe in (Rootkit, Worm):
            world = self.mundo()
            enemy = classe(800, 400)
            enemy.hp = 0
            world.enemies = [enemy]
            with patch("game.world.roll_drop", side_effect=AssertionError("Boss não é comum")):
                world.update(0)
            self.assertEqual(world.drops, [])
            self.assertEqual((world.kills, world.player.progression.xp), (1, 25))

    def test_overclock_pausa_cinco_segundos_refresh_e_restart(self):
        world = self.mundo()
        world.drops = [Drop(500, 400, kind="overclock")]
        world.update(0)
        self.assertEqual(world.player.overclock_timer, 5)
        world.toggle_inventory()
        world.update(10)
        self.assertEqual(world.player.overclock_timer, 5)
        world.toggle_inventory()
        world.update(0.1)
        self.assertAlmostEqual(world.player.overclock_timer, 4.9)
        world.grant_xp(100)
        world.update(10)
        self.assertAlmostEqual(world.player.overclock_timer, 4.9)
        world.advance_presentation(0.8)
        world.choose_card(0)
        world.drops = [Drop(world.player.x, world.player.y, kind="overclock")]
        world.update(0)
        self.assertEqual(world.player.overclock_timer, 5)
        world.update(5)
        self.assertEqual(world.player.overclock_timer, 0)
        world.restart(mode="laboratory")
        self.assertEqual(world.player.overclock_timer, 0)
        self.assertEqual((world.mode, world.waves.max_waves), (GameMode.LABORATORY, 5))


if __name__ == "__main__":
    unittest.main()

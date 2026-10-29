import pickle
import random
import unittest

from game.archer import Archer
from game.enemies import Enemy
from game.projectiles import Projectile
from game.world import GameWorld


class LevelUpPresentationTests(unittest.TestCase):
    def mundo(self):
        world = GameWorld(rng=random.Random(19))
        world.enemies.clear()
        world.drops.clear()
        return world

    def test_intro_meio_segundo_e_entrada_escalonada_ate_pronto(self):
        world = self.mundo()
        world.grant_xp(100)
        self.assertTrue(world.level_up.active)
        self.assertEqual(world.level_up.state.value, "LEVEL_UP_INTRO")
        self.assertEqual(len(world.card_choices), 3)
        self.assertFalse(world.choose_card(0))
        world.advance_presentation(0.499)
        self.assertFalse(world.level_up.selection_ready)
        self.assertEqual(world.level_up.state.value, "LEVEL_UP_INTRO")
        world.advance_presentation(0.001)
        self.assertEqual(world.level_up.state.value, "LEVEL_UP_CARDS")
        self.assertFalse(world.level_up.selection_ready)
        self.assertEqual([world.level_up.card_progress(i) for i in range(3)], [0, 0, 0])
        world.advance_presentation(0.2)
        self.assertAlmostEqual(world.level_up.card_progress(0), 1)
        self.assertLess(world.level_up.card_progress(1), 1)
        self.assertLess(world.level_up.card_progress(2), world.level_up.card_progress(1))
        self.assertFalse(world.choose_card(0))
        world.advance_presentation(0.08)
        self.assertTrue(world.level_up.selection_ready)
        for index in range(3):
            self.assertAlmostEqual(world.level_up.card_progress(index), 1)
        self.assertTrue(world.choose_card(0))
        self.assertFalse(world.level_up.active)

    def test_delta_grande_equivale_a_parcelado_sem_simulacao(self):
        inteiro, parcelado = self.mundo(), self.mundo()
        for world in (inteiro, parcelado):
            world.grant_xp(100)
        inteiro.advance_presentation(0.8)
        for _ in range(80):
            parcelado.advance_presentation(0.01)
        self.assertTrue(inteiro.level_up.selection_ready)
        self.assertTrue(parcelado.level_up.selection_ready)
        self.assertEqual([c.id for c in inteiro.card_choices], [c.id for c in parcelado.card_choices])
        self.assertEqual((inteiro.elapsed, parcelado.elapsed), (0, 0))

    def test_world_update_nao_avanca_intro_nem_timers_de_gameplay(self):
        world = self.mundo()
        enemy = Archer(world.player.x + 60, world.player.y, state="windup", telegraph_timer=0.3)
        world.enemies = [enemy]
        world.projectiles = [Projectile(world.player.x, world.player.y, 180, 0)]
        world.player.overclock_timer = 5
        world.attack_cooldown = 0.3
        world.damage_cooldown = 0.4
        world.grant_xp(100)
        before = pickle.dumps(world)
        world.update(10, move_x=1, attack=True)
        self.assertEqual(pickle.dumps(world), before)
        self.assertFalse(world._damage_player(50))
        self.assertEqual(world.player.progression.hp, 100)
        world.advance_presentation(0.8)
        self.assertEqual((enemy.telegraph_timer, world.projectiles[0].ttl,
                          world.player.overclock_timer, world.attack_cooldown,
                          world.damage_cooldown, world.elapsed), (0.3, 4, 5, 0.3, 0.4, 0))
        self.assertFalse(world._damage_player(50))

    def test_push_radial_64_sem_dano_ou_consumir_rng(self):
        world = self.mundo()
        x, y = world.player.x, world.player.y
        enemy = Enemy(x + 80, y, speed=0, stun_timer=0.1)
        world.enemies = [enemy]
        world.grant_xp(100)
        state_rng = world.rng.getstate()
        world.advance_presentation(0.4)
        self.assertAlmostEqual(enemy.x, x + 144)
        self.assertAlmostEqual(enemy.y, y)
        self.assertEqual((enemy.hp, enemy.stun_timer), (3, 0.1))
        world.advance_presentation(0.4)
        self.assertAlmostEqual(enemy.x, x + 144)
        self.assertEqual(world.rng.getstate(), state_rng)
        self.assertEqual(world.kills, 0)

    def test_fila_reinicia_intro_sem_consumir_duas_escolhas(self):
        world = self.mundo()
        world.grant_xp(300)
        world.advance_presentation(0.8)
        self.assertTrue(world.choose_card(0))
        self.assertEqual(world.pending_levelups, 1)
        self.assertEqual(world.level_up.state.value, "LEVEL_UP_INTRO")
        self.assertFalse(world.choose_card(1))
        world.advance_presentation(0.8)
        self.assertTrue(world.choose_card(1))
        self.assertFalse(world.choosing_card)
        self.assertEqual(sum(world.player.upgrades.values()), 2)
        kinds = [e.kind for e in world.effects.consume_events()]
        self.assertEqual(kinds.count("levelup"), 2)
        self.assertEqual(kinds.count("cards_show"), 2)
        self.assertEqual(kinds.count("card_select"), 2)
        world.advance_presentation(10)
        self.assertEqual(world.effects.consume_events(), ())

    def test_hitstop_decai_mas_intro_usa_tempo_real(self):
        world = self.mundo()
        world.effects.emit("hit", world.player.x, world.player.y, damage=1)
        world.grant_xp(100)
        self.assertEqual((world.effects.hitstop_timer, world.shake_timer), (0, 0))
        for _ in range(10):
            self.assertEqual(world.effects.update(0.05, paused=True), 0)
            world.advance_presentation(0.05)
        self.assertEqual(world.effects.hitstop_timer, 0)
        self.assertEqual(world.level_up.state.value, "LEVEL_UP_CARDS")
        self.assertEqual(world.elapsed, 0)
        self.assertEqual(sum(e.kind == "cards_show" for e in world.effects.consume_events()), 1)

    def test_apos_onda_ponto_quatro_posicoes_ficam_congeladas_nas_cartas(self):
        world = self.mundo()
        x, y = world.player.x, world.player.y
        world.enemies = [Enemy(x + 80, y, speed=0), Enemy(x + 80, y, speed=0)]
        world.grant_xp(100)
        for _ in range(40):
            world.advance_presentation(0.01)
        before = [(enemy.x, enemy.y) for enemy in world.enemies]
        world.advance_presentation(0.1)
        world.advance_presentation(2)
        self.assertEqual([(enemy.x, enemy.y) for enemy in world.enemies], before)

    def test_reinicio_cancela_intro_fila_e_eventos_sem_reviver(self):
        world = self.mundo()
        world.grant_xp(250)
        world.advance_presentation(0.2)
        world.restart()
        self.assertFalse(world.level_up.active)
        self.assertFalse(world.choosing_card)
        self.assertEqual((world.pending_levelups, world.card_choices), (0, []))
        self.assertEqual(world.effects.consume_events(), ())
        world.grant_xp(100)
        world.advance_presentation(0.8)
        world.player.progression.hp = 0
        self.assertFalse(world.choose_card(0))


if __name__ == "__main__":
    unittest.main()

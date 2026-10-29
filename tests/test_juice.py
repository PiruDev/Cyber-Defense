import pickle
import random
import unittest

from game.archer import Archer
from game.effects import EffectSystem
from game.enemies import Drop, Enemy
from game.settings import EffectSettings
from game.world import GameWorld
from game.worm import Worm


class JuiceTests(unittest.TestCase):
    def mundo(self):
        # Acertos e erros são disparados explicitamente para medir feedback.
        world = GameWorld(rng=random.Random(9), auto_attack=False)
        world.enemies.clear()
        world.drops.clear()
        world.player.x, world.player.y = 500, 400
        world.player.facing_x, world.player.facing_y = 1, 0
        world.effects.consume_events()
        return world

    def test_hitstop_residual_e_efeitos_usam_relogio_proprio(self):
        effects = EffectSystem()
        effects.emit("hit", 100, 100, damage=1)
        self.assertAlmostEqual(effects.hitstop_timer, 0.04)
        self.assertEqual(effects.update(0.02), 0)
        self.assertAlmostEqual(effects.update(0.03), 0.01)
        self.assertEqual(effects.hitstop_timer, 0)
        self.assertAlmostEqual(effects.update(0.1), 0.1)

    def test_pause_congela_arena_mas_ui_e_hitstop_continuam(self):
        effects = EffectSystem()
        effects.emit("hit", 100, 100, damage=2)
        effects.emit("newhead", 100, 100, enemy_id=123)
        effects.emit("levelup", 100, 100)
        effects.emit("card_select", 100, 100, name="Vitalidade")
        arena = pickle.dumps(([p for p in effects.particles if p.kind == "arena"], effects.texts))
        self.assertEqual(effects.update(0.5, paused=True), 0)
        self.assertEqual(pickle.dumps((effects.particles, effects.texts)), arena)
        self.assertEqual(effects.head_highlights, {123: 0.15})
        self.assertEqual(effects.shake_timer, 0.1)
        self.assertEqual(effects.hitstop_timer, 0)
        self.assertEqual((effects.card_transition_timer, effects.confirmation_timer), (0, 0))

    def test_hit_normal_e_forte_nao_somam_intensidade(self):
        effects = EffectSystem()
        for _ in range(3):
            effects.emit("hit", 100, 100, damage=1)
        self.assertEqual((effects.shake_amplitude, effects.shake_timer, effects.hitstop_timer), (3, 0.1, 0.04))
        effects.emit("hit", 100, 100, damage=10, strong=True)
        effects.emit("hit", 100, 100, damage=1)
        self.assertEqual((effects.shake_amplitude, effects.shake_timer, effects.hitstop_timer), (6, 0.16, 0.07))
        for _ in range(16):
            self.assertTrue(all(abs(value) <= 6 for value in effects.shake_offset))
            effects.update(0.01)
        self.assertEqual(effects.shake_offset, (0, 0))

    def test_capacidades_eventos_e_expiracao_sem_vazamento(self):
        effects = EffectSystem()
        for _ in range(200):
            effects.emit("hit", 100, 100, damage=1)
        self.assertEqual(len(effects.particles), 160)
        self.assertEqual(len(effects.texts), 32)
        self.assertEqual(len(effects.events), 128)
        self.assertEqual(len(effects.consume_events()), 128)
        self.assertEqual(effects.consume_events(), ())
        effects.update(1)
        self.assertEqual((effects.particles, effects.texts, effects.head_highlights), ([], [], {}))

    def test_particulas_e_textos_avancam_com_dt_equivalente(self):
        inteiro, parcelado = EffectSystem(), EffectSystem()
        for effects in (inteiro, parcelado):
            effects.emit("hit", 100, 100, damage=1.2)
        inteiro.update(0.1)
        for _ in range(10):
            parcelado.update(0.01)
        for primeiro, segundo in zip(inteiro.particles, parcelado.particles):
            self.assertAlmostEqual(primeiro.x, segundo.x)
            self.assertAlmostEqual(primeiro.y, segundo.y)
            self.assertAlmostEqual(primeiro.remaining, segundo.remaining)
        self.assertAlmostEqual(inteiro.texts[0].y, parcelado.texts[0].y)
        self.assertEqual(inteiro.texts[0].total_life, 0.65)
        inteiro.update(0.56)
        self.assertEqual(inteiro.texts, [])

    def test_settings_clamps_e_desativacao_de_efeitos(self):
        settings = EffectSettings(shake_scale=-10, particle_scale=10, max_particles=-1,
                                  max_texts=10**6, volume=2)
        self.assertEqual((settings.shake_scale, settings.particle_scale, settings.max_particles,
                          settings.max_texts, settings.volume), (0, 1, 0, 64, 1))
        effects = EffectSystem(EffectSettings(shake_scale=0, particle_scale=0, max_texts=0))
        effects.emit("hit", 100, 100, damage=1)
        self.assertEqual((effects.particles, effects.texts, effects.shake_offset), ([], [], (0, 0)))
        self.assertEqual(len(effects.consume_events()), 1)

    def test_world_hit_apenas_uma_vez_dano_efetivo_flash_e_barra(self):
        world = self.mundo()
        enemy = Enemy(545, 400, hp=0.2, max_hp=3, speed=0)
        self.assertEqual(enemy.hp_bar_timer, 0)
        world.enemies.append(enemy)
        world.update(0, attack=True)
        events = world.effects.consume_events()
        hits = [event for event in events if event.kind == "hit"]
        self.assertEqual(len(hits), 1)
        self.assertAlmostEqual(hits[0].payload["damage"], 0.2)
        self.assertEqual(enemy.hit_flash_timer, 0.1)
        self.assertEqual(enemy.hp_bar_timer, 0.35)
        self.assertEqual(world.effects.texts[0].text, "0.2")
        self.assertEqual(world.effects.texts[0].remaining, 0.65)
        self.assertEqual([e.kind for e in events].count("death"), 1)
        world.update(0, attack=True)
        self.assertFalse(any(e.kind in ("hit", "death") for e in world.effects.consume_events()))
        self.assertEqual((world.kills, world.player.progression.xp), (1, 25))

    def test_world_nao_avanca_fx_nem_consume_rng_visual_no_spawn(self):
        world = self.mundo()
        world.enemies.append(Enemy(545, 400, speed=0))
        rng_state = world.rng.getstate()
        world.update(0, attack=True)
        self.assertEqual(world.rng.getstate(), rng_state)
        remaining = world.effects.texts[0].remaining
        world.update(0.1)
        self.assertEqual(world.effects.texts[0].remaining, remaining)
        self.assertEqual(world.effects.hitstop_timer, 0.04)
        world.effects.update(0.1)
        self.assertEqual(world.effects.hitstop_timer, 0)

    def test_erros_ou_cooldown_nao_geram_feedback_de_acerto(self):
        world = self.mundo()
        world.enemies.append(Enemy(700, 400, speed=0))
        world.update(0, attack=True)
        self.assertFalse(any(e.kind == "hit" for e in world.effects.consume_events()))
        self.assertEqual((world.effects.hitstop_timer, world.shake_timer), (0, 0))
        world.enemies[0].x = 545
        world.update(0, attack=True)
        self.assertEqual(world.effects.consume_events(), ())

    def test_min_hoca_ruptura_nova_cabeca_e_morte_final_sem_xp_extra(self):
        world = self.mundo()
        worm = Worm(545, 400, speed=0)
        world.enemies = [worm]
        world.player.progression.dano = 1000
        for golpe in range(6):
            worm.x, worm.y = 545, 400
            for segment in worm.segments:
                segment.x, segment.y = 545, 400
            old_head = worm.head
            world.attack_cooldown = 0
            world.update(0, attack=True)
            events = world.effects.consume_events()
            self.assertEqual(sum(e.kind == "hit" for e in events), 1)
            self.assertEqual(sum(e.kind == "wormrupture" for e in events), 1)
            self.assertEqual(sum(e.kind == "newhead" for e in events), int(golpe < 5))
            rupture = next(e for e in events if e.kind == "wormrupture")
            self.assertEqual((rupture.x, rupture.y), (old_head.x, old_head.y))
            self.assertEqual((world.effects.hitstop_timer, world.shake_timer,
                              world.effects.shake_amplitude), (0.07, 0.16, 6))
            if golpe < 5:
                self.assertEqual(world.effects.head_highlights[id(worm)], 0.15)
        self.assertEqual((world.kills, world.player.progression.xp), (1, 25))
        self.assertEqual(sum(e.kind == "death" for e in events), 1)

    def test_pickup_score_texto_e_evento_sem_xp(self):
        world = self.mundo()
        world.player.inventory.potions = 5
        world.drops = [Drop(500, 400)]
        world.update(0)
        events = world.effects.consume_events()
        self.assertEqual([e.kind for e in events], ["pickup", "score"])
        self.assertEqual(world.effects.texts[0].text, "+10 pontos")
        self.assertEqual((world.score, world.player.progression.xp), (10, 0))
        world.update(0)
        self.assertEqual(world.effects.consume_events(), ())

    def test_arqueiro_disparo_evento_um_sem_hitstop(self):
        world = self.mundo()
        world.enemies = [Archer(700, 400, speed=0)]
        world.update(0)
        world.update(0.45)
        self.assertEqual([e.kind for e in world.effects.consume_events()], ["archerfire"])
        self.assertEqual(world.effects.hitstop_timer, 0)
        self.assertTrue(world.effects.particles)
        world.effects.update(0.07)
        self.assertFalse(world.effects.particles)

    def test_cartas_transicao_confirmacao_e_restart_preserva_settings(self):
        world = self.mundo()
        world.grant_xp(250)
        self.assertEqual([e.kind for e in world.effects.consume_events()], ["levelup"])
        # MISSÃO008: a entrada acontece após a introdução real de meio segundo.
        world.advance_presentation(0.5)
        self.assertEqual(world.effects.card_transition_timer, 0.28)
        self.assertEqual([e.kind for e in world.effects.consume_events()], ["cards_show"])
        world.advance_presentation(0.28)
        self.assertTrue(world.choose_card(0))
        events = world.effects.consume_events()
        self.assertEqual(sum(e.kind == "card_select" for e in events), 1)
        self.assertEqual(world.effects.confirmation_timer, 0.2)
        self.assertTrue(world.effects.confirmation_text)
        self.assertTrue(world.choosing_card)
        world.effects.update(0.21, paused=True)
        self.assertEqual(world.effects.confirmation_timer, 0)
        world.effects.settings.shake_scale = 0
        world.restart()
        self.assertEqual(world.effects.settings.shake_scale, 0)
        self.assertEqual((world.effects.particles, world.effects.texts, world.effects.events), ([], [], []))
        self.assertEqual((world.effects.hitstop_timer, world.shake_timer), (0, 0))

    def test_finale_decai_ate_pausado_e_origem_particula_permanece_estavel(self):
        effects = EffectSystem()
        effects.emit("levelup", 500, 400)
        origens = [(p.origin_x, p.origin_y) for p in effects.particles]
        effects.update(0.1, paused=True)
        self.assertEqual([(p.origin_x, p.origin_y) for p in effects.particles], origens)
        self.assertTrue(any((p.x, p.y) != (p.origin_x, p.origin_y) for p in effects.particles))
        effects.emit("death", 500, 400, strong=True)
        self.assertEqual(effects.finale_timer, 0.45)
        effects.update(0.46, paused=True)
        self.assertEqual(effects.finale_timer, 0)
        effects.reset()
        self.assertEqual(effects.finale_timer, 0)


if __name__ == "__main__":
    unittest.main()

import math
import random
import unittest

from game.enemies import Enemy
from game.world import GameWorld


class GameFeelTests(unittest.TestCase):
    def mundo(self):
        mundo = GameWorld(arena=(32, 154, 1036, 530), rng=random.Random(17))
        mundo.enemies.clear()
        mundo.drops.clear()
        mundo.player.x, mundo.player.y = 500, 400
        mundo.player.facing_x, mundo.player.facing_y = 1, 0
        return mundo

    def acertar(self, dx=45, dy=0):
        mundo = self.mundo()
        tamanho = math.hypot(dx, dy)
        mundo.player.facing_x, mundo.player.facing_y = dx / tamanho, dy / tamanho
        inimigo = Enemy(500 + dx, 400 + dy)
        mundo.enemies.append(inimigo)
        mundo.update(0, attack=True)
        return mundo, inimigo

    def test_hit_aplica_stun_flash_e_knockback_com_direcao_oposta(self):
        for dx, dy in ((45, 0), (-45, 0), (0, 45), (0, -45), (30, 30)):
            with self.subTest(direcao=(dx, dy)):
                mundo, inimigo = self.acertar(dx, dy)
                tamanho = math.hypot(dx, dy)
                self.assertEqual(inimigo.hp, 2)
                self.assertAlmostEqual(inimigo.stun_timer, 0.2)
                # MISSÃO006: flash ampliado; a regra de stun continua em 0,2 s.
                self.assertAlmostEqual(inimigo.hit_flash_timer, 0.1)
                self.assertAlmostEqual(inimigo.knockback_timer, 0.1)
                self.assertAlmostEqual(inimigo.knockback_vx, dx / tamanho * 200)
                self.assertAlmostEqual(inimigo.knockback_vy, dy / tamanho * 200)

    def test_knockback_total_vinte_pixels_independe_da_divisao_de_dt(self):
        inteiro, primeiro = self.acertar()
        parcelado, segundo = self.acertar()
        inteiro.update(0.1)
        for _ in range(10):
            parcelado.update(0.01)
        self.assertAlmostEqual(primeiro.x, 565)
        self.assertAlmostEqual(segundo.x, primeiro.x)
        self.assertAlmostEqual(primeiro.y, 400)
        self.assertAlmostEqual(segundo.y, primeiro.y)
        self.assertAlmostEqual(primeiro.knockback_timer, 0)
        self.assertAlmostEqual(primeiro.stun_timer, 0.1)

    def test_knockback_respeita_quatro_bordas(self):
        for px, py, ex, ey, fx, fy in (
            (80, 400, 49, 400, -1, 0),
            (1020, 400, 1051, 400, 1, 0),
            (500, 202, 500, 171, 0, -1),
            (500, 636, 500, 667, 0, 1),
        ):
            with self.subTest(direcao=(fx, fy)):
                mundo = self.mundo()
                mundo.player.x, mundo.player.y = px, py
                mundo.player.facing_x, mundo.player.facing_y = fx, fy
                inimigo = Enemy(ex, ey)
                mundo.enemies.append(inimigo)
                mundo.update(0, attack=True)
                mundo.update(0.1)
                self.assertEqual((inimigo.x, inimigo.y), (ex, ey))

    def test_sobreposicao_usa_facing_como_fallback_sem_divisao_por_zero(self):
        mundo = self.mundo()
        inimigo = Enemy(500, 400)
        mundo.enemies.append(inimigo)
        mundo.update(0, attack=True)
        self.assertGreater(inimigo.knockback_vx, 0)
        self.assertAlmostEqual(inimigo.knockback_vy, 0)
        self.assertEqual(mundo.player.progression.hp, 100)

    def test_stun_impede_perseguicao_e_contato_por_ponto_dois_segundos(self):
        mundo, inimigo = self.acertar()
        # Mantém contato de propósito, isolando o stun do efeito de afastamento.
        inimigo.knockback_timer = 0
        inimigo.x, inimigo.y = mundo.player.x, mundo.player.y
        mundo.update(0.19)
        self.assertEqual((inimigo.x, inimigo.y), (500, 400))
        self.assertEqual(mundo.player.progression.hp, 100)
        mundo.update(0.02)
        mundo.update(0.01)
        self.assertEqual(mundo.player.progression.hp, 90)

    def test_stun_expira_e_perseguicao_retorna(self):
        mundo, inimigo = self.acertar()
        mundo.update(0.1)
        depois_recuo = inimigo.x
        mundo.update(0.09)
        self.assertAlmostEqual(inimigo.x, depois_recuo)
        mundo.update(0.02)
        mundo.update(0.02)
        self.assertLess(inimigo.x, depois_recuo)

    def test_frame_que_atravessa_stun_usa_so_tempo_residual_para_perseguir(self):
        inteiro, primeiro = self.acertar()
        parcelado, segundo = self.acertar()
        inteiro.update(0.3)
        for _ in range(30):
            parcelado.update(0.01)
        self.assertAlmostEqual(primeiro.x, 545 + 20 - 85 * 0.1)
        self.assertAlmostEqual(segundo.x, primeiro.x)

    def test_shake_so_hit_e_offset_nao_consume_rng(self):
        mundo = self.mundo()
        estado_rng = mundo.rng.getstate()
        mundo.update(0, attack=True)
        self.assertEqual(mundo.shake_timer, 0)
        self.assertEqual(mundo.shake_offset, (0, 0))
        self.assertEqual(mundo.rng.getstate(), estado_rng)
        mundo, _ = self.acertar()
        estado_rng = mundo.rng.getstate()
        self.assertAlmostEqual(mundo.shake_timer, 0.1)
        for _ in range(5):
            offset = mundo.shake_offset
            self.assertEqual(len(offset), 2)
            self.assertTrue(all(isinstance(eixo, int) and abs(eixo) <= 3 for eixo in offset))
            mundo.effects.update(0.01)
            mundo.update(0.01)
        self.assertEqual(mundo.rng.getstate(), estado_rng)
        mundo.effects.update(0.06)
        mundo.update(0.06)
        self.assertEqual(mundo.shake_offset, (0, 0))

    def test_hit_fatal_e_multialvo_nao_somam_shake(self):
        mundo = self.mundo()
        mundo.enemies = [Enemy(545, 400, hp=1), Enemy(550, 405)]
        mundo.update(0, attack=True)
        self.assertAlmostEqual(mundo.shake_timer, 0.1)
        self.assertEqual(mundo.kills, 1)
        self.assertEqual(mundo.player.progression.xp, 25)
        # MISSÃO006: o relógio visual é avançado pelo main, não por world.update.
        mundo.effects.update(0.01)
        mundo.update(0.01, attack=True)
        self.assertAlmostEqual(mundo.shake_timer, 0.09)
        self.assertEqual(mundo.kills, 1)

    def test_cooldown_nao_reativa_shake_e_gameover_nao_desloca_cena(self):
        mundo, inimigo = self.acertar()
        mundo.effects.update(0.11)
        mundo.update(0.11, attack=True)
        self.assertEqual(inimigo.hp, 2)
        self.assertEqual(mundo.shake_timer, 0)
        self.assertEqual(mundo.shake_offset, (0, 0))
        mundo.shake_timer = 0.1
        mundo.player.progression.hp = 0
        mundo.update(0)
        self.assertTrue(mundo.game_over)
        self.assertEqual(mundo.shake_offset, (0, 0))

    def test_direcao_do_ataque_e_snapshot_e_duracao_temporaria(self):
        mundo = self.mundo()
        mundo.update(0, attack=True)
        self.assertEqual((mundo.attack_facing_x, mundo.attack_facing_y), (1, 0))
        self.assertAlmostEqual(mundo.attack_timer, 0.14)
        mundo.update(0.05, move_y=-1)
        self.assertEqual((mundo.player.facing_x, mundo.player.facing_y), (0, -1))
        self.assertEqual((mundo.attack_facing_x, mundo.attack_facing_y), (1, 0))
        mundo.update(0.1)
        self.assertEqual(mundo.attack_timer, 0)

    def test_pausa_congela_efeitos_e_restart_remove_estados_transitorios(self):
        mundo, inimigo = self.acertar()
        antes = (inimigo.x, inimigo.y, inimigo.stun_timer, inimigo.knockback_timer,
                 inimigo.hit_flash_timer, mundo.attack_timer, mundo.shake_timer)
        mundo.toggle_inventory()
        mundo.update(1)
        self.assertEqual(mundo.shake_offset, (0, 0))
        depois = (inimigo.x, inimigo.y, inimigo.stun_timer, inimigo.knockback_timer,
                  inimigo.hit_flash_timer, mundo.attack_timer, mundo.shake_timer)
        self.assertEqual(depois, antes)
        mundo.restart()
        self.assertEqual((mundo.attack_timer, mundo.shake_timer), (0, 0))
        self.assertEqual(mundo.shake_offset, (0, 0))
        for novo in mundo.enemies:
            self.assertEqual((novo.stun_timer, novo.knockback_timer, novo.hit_flash_timer), (0, 0, 0))


if __name__ == "__main__":
    unittest.main()

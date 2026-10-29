import math
import pickle
import unittest

from game.boss import Rootkit
from game.enemies import Enemy
from game.physics import SeparationSystem
from game.weapons import TrainingTarget
from game.worm import Worm


class SeparationTests(unittest.TestCase):
    arena = (32, 154, 1036, 530)

    def sistema(self, enemies):
        system = SeparationSystem()
        for enemy in enemies:
            system.register(enemy)
        return system

    def verificar_limites(self, enemies):
        left, top, width, height = self.arena
        for enemy in enemies:
            self.assertTrue(math.isfinite(enemy.x) and math.isfinite(enemy.y))
            self.assertGreaterEqual(enemy.x, left + enemy.radius - 1e-8)
            self.assertLessEqual(enemy.x, left + width - enemy.radius + 1e-8)
            self.assertGreaterEqual(enemy.y, top + enemy.radius - 1e-8)
            self.assertLessEqual(enemy.y, top + height - enemy.radius + 1e-8)

    def test_coincidentes_separam_suavemente_sem_divisao_por_zero(self):
        enemies = [Enemy(500, 400), Enemy(500, 400)]
        system = self.sistema(enemies)
        system.update(enemies, self.arena, 1 / 60)
        for enemy in enemies:
            self.assertLessEqual(math.hypot(enemy.x - 500, enemy.y - 400), 4 + 1e-8)
        self.assertGreater(math.hypot(enemies[0].x - enemies[1].x, enemies[0].y - enemies[1].y), 0)
        for _ in range(60):
            system.update(enemies, self.arena, 1 / 60)
        self.assertGreaterEqual(math.hypot(enemies[0].x - enemies[1].x,
                                         enemies[0].y - enemies[1].y), 33.49)
        self.verificar_limites(enemies)

    def test_raios_diferentes_respeitam_massa_e_distancia(self):
        grande, pequeno = Rootkit(500, 400), Enemy(544, 400)
        system = self.sistema([grande, pequeno])
        system.update([grande, pequeno], self.arena, 1 / 60)
        self.assertLess(math.hypot(grande.x - 500, grande.y - 400),
                        math.hypot(pequeno.x - 544, pequeno.y - 400))
        for _ in range(60):
            system.update([grande, pequeno], self.arena, 1 / 60)
        self.assertGreaterEqual(math.hypot(grande.x - pequeno.x, grande.y - pequeno.y), 48.49)

    def test_grupo_denso_em_cantos_converge_sem_sair_da_arena(self):
        for x, y in ((500, 400), (49, 171), (1051, 667)):
            with self.subTest(origem=(x, y)):
                enemies = [Enemy(x, y) for _ in range(10)]
                system = self.sistema(enemies)
                for _ in range(300):
                    system.update(enemies, self.arena, 1 / 60)
                    self.verificar_limites(enemies)
                for index, primeiro in enumerate(enemies):
                    for segundo in enemies[index + 1:]:
                        self.assertGreaterEqual(math.hypot(primeiro.x - segundo.x,
                                                          primeiro.y - segundo.y), 33.4)

    def test_parede_redistribui_correcao_para_corpo_livre(self):
        bloqueado, livre = Enemy(49, 400), Enemy(60, 400)
        system = self.sistema([bloqueado, livre])
        for _ in range(60):
            system.update([bloqueado, livre], self.arena, 1 / 60)
        self.verificar_limites([bloqueado, livre])
        self.assertGreaterEqual(livre.x - bloqueado.x, 33.49)

    def test_stun_e_knockback_nao_impedem_correcao_nem_perdem_timers(self):
        primeiro = Enemy(500, 400, stun_timer=0.2, knockback_timer=0.1,
                         knockback_vx=160, knockback_vy=120)
        segundo = Enemy(500, 400)
        system = self.sistema([primeiro, segundo])
        system.update([primeiro, segundo], self.arena, 1 / 60)
        self.assertEqual((primeiro.stun_timer, primeiro.knockback_timer,
                          primeiro.knockback_vx, primeiro.knockback_vy), (0.2, 0.1, 160, 120))
        self.assertNotEqual((primeiro.x, primeiro.y), (500, 400))
        self.assertEqual((primeiro.hp, segundo.hp), (3, 3))

    def test_alvos_de_treino_e_mortos_nao_participam(self):
        target, morto, vivo = TrainingTarget(500, 400), Enemy(500, 400, hp=0), Enemy(500, 400)
        system = self.sistema([target, morto, vivo])
        before = [(e.x, e.y) for e in (target, morto, vivo)]
        system.update([target, morto, vivo], self.arena, 0.1)
        self.assertEqual([(e.x, e.y) for e in (target, morto, vivo)], before)

    def test_verme_como_grupo_rigido_preserva_cauda_sem_autorrepulsao(self):
        worm = Worm(600, 400)
        worm._follow_segments(self.arena)
        outro = Enemy(600, 400)
        system = self.sistema([worm, outro])
        before = [(s.x, s.y) for s in worm.segments]
        system.update([worm, outro], self.arena, 1 / 60)
        delta = (worm.x - before[0][0], worm.y - before[0][1])
        self.assertNotEqual(delta, (0, 0))
        for segmento, (x, y) in zip(worm.segments, before):
            self.assertAlmostEqual(segmento.x - x, delta[0])
            self.assertAlmostEqual(segmento.y - y, delta[1])
        self.assertEqual((worm.x, worm.y), (worm.head.x, worm.head.y))
        before = [(s.x, s.y) for s in worm.segments]
        system.update([worm], self.arena, 0.1)
        self.assertEqual([(s.x, s.y) for s in worm.segments], before)

    def test_outro_inimigo_na_cauda_causa_separacao_entre_grupos(self):
        worm = Worm(600, 400)
        worm._follow_segments(self.arena)
        enemy = Enemy(worm.segments[-1].x, worm.segments[-1].y)
        system = self.sistema([worm, enemy])
        before = (enemy.x, enemy.y)
        system.update([worm, enemy], self.arena, 1 / 60)
        self.assertNotEqual((enemy.x, enemy.y), before)
        for a, b in zip(worm.segments, worm.segments[1:]):
            self.assertAlmostEqual(math.hypot(a.x - b.x, a.y - b.y), 32)

    def test_determinismo_com_ordem_registrada_e_dt_zero_sem_movimento(self):
        a = [Enemy(500, 400) for _ in range(4)]
        b = [Enemy(500, 400) for _ in range(4)]
        primeiro, segundo = self.sistema(a), self.sistema(b)
        before = [(e.x, e.y) for e in a]
        primeiro.update(a, self.arena, 0)
        self.assertEqual([(e.x, e.y) for e in a], before)
        for _ in range(30):
            primeiro.update(a, self.arena, 1 / 60)
            segundo.update(list(reversed(b)), self.arena, 1 / 60)
        for left, right in zip(a, b):
            self.assertAlmostEqual(left.x, right.x)
            self.assertAlmostEqual(left.y, right.y)


if __name__ == "__main__":
    unittest.main()

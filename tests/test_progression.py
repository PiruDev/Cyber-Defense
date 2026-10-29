import unittest

from game.progression import Progressao, XP_POR_INIMIGO


class ProgressaoTests(unittest.TestCase):
    def test_estado_inicial(self):
        jogador = Progressao()
        self.assertEqual(
            (jogador.nivel, jogador.xp, jogador.hp_maximo, jogador.hp, jogador.dano),
            (1, 0, 100, 100, 1),
        )
        self.assertEqual(jogador.xp_necessario, 100)
        self.assertEqual(XP_POR_INIMIGO, 25)

    def test_recompensas_por_inimigo_e_cura_no_quarto(self):
        jogador = Progressao(hp=30)
        for esperado in (25, 50, 75):
            self.assertEqual(jogador.registrar_inimigo_derrotado(), 0)
            self.assertEqual((jogador.nivel, jogador.xp, jogador.hp), (1, esperado, 30))
        self.assertEqual(jogador.registrar_inimigo_derrotado(), 1)
        self.assertEqual(
            (jogador.nivel, jogador.xp, jogador.hp_maximo, jogador.hp, jogador.dano),
            (2, 0, 120, 120, 2),
        )

    def test_fronteiras_excedente_e_multiplos_niveis(self):
        # XP total, niveis ganhos, nivel final, XP restante, proximo limiar.
        casos = (
            (0, 0, 1, 0, 100),
            (99, 0, 1, 99, 100),
            (100, 1, 2, 0, 150),
            (101, 1, 2, 1, 150),
            (125, 1, 2, 25, 150),
            (249, 1, 2, 149, 150),
            (250, 2, 3, 0, 200),
            (251, 2, 3, 1, 200),
            (300, 2, 3, 50, 200),
            (449, 2, 3, 199, 200),
            (450, 3, 4, 0, 250),
            (10000, 18, 19, 550, 1000),
        )
        for quantidade, ganhos, nivel, restante, limiar in casos:
            with self.subTest(quantidade=quantidade):
                jogador = Progressao(hp=37)
                self.assertEqual(jogador.ganhar_xp(quantidade), ganhos)
                self.assertEqual((jogador.nivel, jogador.xp), (nivel, restante))
                self.assertEqual(jogador.xp_necessario, limiar)
                self.assertEqual(jogador.hp_maximo, 100 + 20 * ganhos)
                self.assertEqual(jogador.dano, 1 + ganhos)
                self.assertEqual(jogador.hp, jogador.hp_maximo if ganhos else 37)

    def test_ganho_considera_xp_ja_acumulado(self):
        jogador = Progressao(nivel=2, xp=140, hp_maximo=120, hp=10, dano=2)
        self.assertEqual(jogador.ganhar_xp(215), 2)
        self.assertEqual(
            (jogador.nivel, jogador.xp, jogador.hp_maximo, jogador.hp, jogador.dano),
            (4, 5, 160, 160, 4),
        )
        self.assertEqual(jogador.xp_necessario, 250)

    def test_ganhos_parcelados_equivalem_ao_total(self):
        parcelado = Progressao()
        total = Progressao()
        for _ in range(40):
            parcelado.registrar_inimigo_derrotado()
        total.ganhar_xp(1000)
        self.assertEqual(vars(parcelado), vars(total))

    def test_instancias_independentes(self):
        primeiro = Progressao()
        segundo = Progressao()
        primeiro.ganhar_xp(100)
        self.assertEqual(
            (segundo.nivel, segundo.xp, segundo.hp_maximo, segundo.hp, segundo.dano),
            (1, 0, 100, 100, 1),
        )

    def test_xp_invalido_nao_altera_estado(self):
        casos = (
            (-1, ValueError),
            (-1000, ValueError),
            (True, TypeError),
            (False, TypeError),
            (25.0, TypeError),
            ("25", TypeError),
            (None, TypeError),
            ([], TypeError),
        )
        for quantidade, erro in casos:
            with self.subTest(quantidade=quantidade):
                jogador = Progressao(nivel=2, xp=140, hp_maximo=120, hp=10, dano=2)
                antes = vars(jogador).copy()
                with self.assertRaises(erro):
                    jogador.ganhar_xp(quantidade)
                self.assertEqual(vars(jogador), antes)


if __name__ == "__main__":
    unittest.main()

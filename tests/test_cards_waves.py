from collections import Counter
import itertools
import random
import unittest

from game.cards import CARDS, apply_card, offer_cards
from game.player import Player
from game.modes import GameMode
from game.waves import WaveManager


class CardsTests(unittest.TestCase):
    def test_catalogo_oito_cartas_e_limites(self):
        self.assertEqual({c.id: c.max_stacks for c in CARDS}, {
            "damage": 8, "max_hp": 8, "speed": 5, "cooldown": 8,
            "range": 6, "regen": 5, "kill_heal": 5, "reduction": 7,
        })
        self.assertTrue(all(c.name and c.description for c in CARDS))

    def test_ofertas_tres_distintas_sem_cartas_esgotadas(self):
        stacks = {"speed": 5, "damage": 8}
        for seed in range(30):
            escolhas = offer_cards(stacks, random.Random(seed))
            self.assertEqual(len(escolhas), 3)
            self.assertEqual(len({c.id for c in escolhas}), 3)
            self.assertTrue(all(c.id not in stacks for c in escolhas))

    def test_35_escolhas_garantem_tres_elegiveis(self):
        # Verifica todas as combinações de cartas saturadas até o orçamento da run.
        for tamanho in range(9):
            for saturadas in itertools.combinations(CARDS, tamanho):
                if sum(c.max_stacks for c in saturadas) <= 35:
                    stacks = {c.id: c.max_stacks for c in saturadas}
                    self.assertEqual(len(offer_cards(stacks, random.Random(7))), 3)

    def test_limite_de_stack_nao_aplica_efeito_extra(self):
        for carta in CARDS:
            with self.subTest(carta=carta.id):
                jogador = Player()
                for _ in range(carta.max_stacks):
                    self.assertTrue(apply_card(jogador, carta.id))
                antes = (jogador.upgrades.copy(), vars(jogador.progression).copy())
                self.assertFalse(apply_card(jogador, carta.id))
                self.assertEqual((jogador.upgrades, vars(jogador.progression)), antes)
        jogador = Player()
        self.assertFalse(apply_card(jogador, "inexistente"))
        self.assertEqual(jogador.upgrades, {})

    def test_atributos_derivados_e_hp_nao_cura_total(self):
        jogador = Player()
        jogador.progression.hp = 10
        for carta in ("damage", "speed", "cooldown", "range", "reduction"):
            apply_card(jogador, carta)
            apply_card(jogador, carta)
        self.assertAlmostEqual(jogador.damage, jogador.progression.dano * 1.2 ** 2)
        self.assertAlmostEqual(jogador.move_speed, 220 * 1.24)
        self.assertAlmostEqual(jogador.attack_interval, 0.35 * 0.9 ** 2)
        self.assertAlmostEqual(jogador.attack_range, 70 * 1.3)
        self.assertAlmostEqual(jogador.damage_multiplier, 0.9 ** 2)
        apply_card(jogador, "max_hp")
        self.assertEqual((jogador.progression.hp, jogador.progression.hp_maximo), (35, 125))


class WavesTests(unittest.TestCase):
    def test_cinco_ondas_finitas_composicao_escala_e_preparacao(self):
        ondas = WaveManager(mode=GameMode.LABORATORY)
        for numero, (swords, archers, worms) in enumerate(((6, 0, 0), (6, 2, 0), (7, 3, 0), (8, 4, 0), (9, 5, 1)), 1):
            self.assertEqual(ondas.number, numero)
            self.assertEqual(ondas.total, swords + archers + worms)
            self.assertAlmostEqual(ondas.stat_scale, 1 + 0.15 * (numero - 1))
            self.assertAlmostEqual(ondas.damage_scale, 1 + 0.1 * (numero - 1))
            tipos = [ondas.next_kind() for _ in range(ondas.total)]
            self.assertEqual(Counter(tipos), Counter({k: v for k, v in (
                ("swordsman", swords), ("archer", archers), ("worm", worms)) if v}))
            self.assertFalse(ondas.can_spawn)
            self.assertIsNone(ondas.next_kind())
            ondas.update(100, alive_count=ondas.total)
            self.assertFalse(ondas.complete)
            for _ in tipos:
                ondas.register_defeat()
            ondas.update(0, alive_count=1)
            self.assertFalse(ondas.complete)
            ondas.update(0, alive_count=0)
            self.assertTrue(ondas.complete)
            self.assertEqual(ondas.remaining, 0)
            if numero < 5:
                self.assertFalse(ondas.victory)
                self.assertAlmostEqual(ondas.preparation_timer, 3)
                ondas.update(2.99, alive_count=0)
                self.assertEqual(ondas.number, numero)
                self.assertFalse(ondas.can_spawn)
                ondas.update(0.02, alive_count=0)
                self.assertEqual(ondas.number, numero + 1)
                self.assertTrue(ondas.can_spawn)
        self.assertTrue(ondas.victory)
        ondas.update(1000, alive_count=0)
        self.assertEqual(ondas.number, 5)
        self.assertFalse(ondas.can_spawn)

    def test_derrotas_nao_ultrapassam_spawns(self):
        ondas = WaveManager()
        ondas.register_defeat()
        self.assertEqual(ondas.defeated, 0)
        ondas.next_kind()
        ondas.register_defeat()
        ondas.register_defeat()
        self.assertEqual(ondas.defeated, 1)
        self.assertEqual(ondas.remaining, 5)

    def test_entradas_temporais_invalidas_sem_mutacao(self):
        ondas = WaveManager()
        antes = vars(ondas).copy()
        for dt in (-1, float("inf"), float("nan")):
            with self.subTest(dt=dt), self.assertRaises(ValueError):
                ondas.update(dt, 0)
            self.assertEqual(vars(ondas), antes)


if __name__ == "__main__":
    unittest.main()

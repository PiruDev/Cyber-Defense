"""Cartas de equipamento, raridade e permanência dos upgrades gerais."""

from collections import Counter
from random import Random
import unittest

from game.balance import BalanceConfig
from game.player import Player
from game.weapon_cards import WeaponCard, eligible_weapons, offer_level_cards
from game.world import GameWorld


class WeaponCardsTests(unittest.TestCase):
    def test_chance_configurada8porcento_e_limites(self):
        self.assertEqual(BalanceConfig().weapon_card_chance, .08)
        self.assertEqual(BalanceConfig().evolved_weapon_weight, .25)
        for value in (-.1, 1.1, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                BalanceConfig(weapon_card_chance=value)

    def test_tres_cartas_distintas_com_no_maximo_uma_arma(self):
        player = Player()
        player.upgrades["speed"] = 5
        for chance in (0, 1):
            for seed in range(40):
                cards = offer_level_cards(player, Random(seed), "sword", chance=chance)
                self.assertEqual(len(cards), 3)
                self.assertEqual(len({card.id for card in cards}), 3)
                weapons = [card for card in cards if isinstance(card, WeaponCard)]
                self.assertEqual(len(weapons), chance)
                self.assertTrue(all(card.id != "speed" for card in cards))
                self.assertTrue(all(card.weapon_id != "sword" for card in weapons))

    def test_nao_oferece_atual_ou_downgrade_da_mesma_familia(self):
        self.assertNotIn("bow", eligible_weapons("longbow"))
        self.assertNotIn("spear", eligible_weapons("returning_spear"))
        for current in ("sword", "katana", "bow", "spear", "longbow", "returning_spear"):
            eligible = eligible_weapons(current)
            self.assertNotIn(current, eligible)
        self.assertIn("spear", eligible_weapons("longbow"))
        self.assertIn("bow", eligible_weapons("returning_spear"))

    def test_evoluidas_tem_menor_peso_e_chance_por_apresentacao(self):
        player = Player()
        counts = Counter()
        random = Random(12012)
        weapon_offers = 0
        for _ in range(6000):
            cards = offer_level_cards(player, random, "sword")
            weapons = [card for card in cards if isinstance(card, WeaponCard)]
            weapon_offers += bool(weapons)
        self.assertGreater(weapon_offers, 390)
        self.assertLess(weapon_offers, 570)
        for _ in range(4000):
            cards = offer_level_cards(player, random, "sword", chance=1)
            counts.update(card.weapon_id for card in cards if isinstance(card, WeaponCard))
        self.assertLess(counts["longbow"], counts["bow"] * .4)
        self.assertLess(counts["returning_spear"], counts["spear"] * .4)

    def test_escolha_de_arma_preserva_upgrade_e_limpa_pulso_antigo(self):
        world = GameWorld(rng=Random(12), config=BalanceConfig(weapon_card_chance=0))
        world.enemies.clear()
        world.weapons.switch("katana")
        world.weapons.start(world.player)
        self.assertTrue(world.weapons.pending)
        world.player.upgrades = {"speed": 2, "damage": 1}
        world.grant_xp(100)
        world.advance_presentation(.8)
        world.card_choices[0] = WeaponCard("longbow")
        self.assertTrue(world.choose_card(0))
        self.assertEqual(world.weapon_id, "longbow")
        self.assertEqual(world.weapons.pending, [])
        self.assertEqual(world.attack_timer, 0)
        self.assertEqual(world.player.upgrades, {"speed": 2, "damage": 1})
        self.assertFalse(world.choosing_card)

    def test_multiplos_niveis_enfileiram_escolhas_e_nao_retornam_ao_combate(self):
        world = GameWorld(rng=Random(13), config=BalanceConfig(weapon_card_chance=1))
        world.enemies.clear()
        world.grant_xp(250)
        self.assertEqual(world.pending_levelups, 2)
        for remaining in (1, 0):
            self.assertTrue(world.choosing_card)
            world.advance_presentation(.8)
            index = next(i for i, card in enumerate(world.card_choices) if isinstance(card, WeaponCard))
            self.assertTrue(world.choose_card(index))
            self.assertEqual(world.pending_levelups, remaining)
        self.assertFalse(world.choosing_card)

    def test_laboratorio_disponibiliza_seis_armas_com_mesmos9alvos_e45segundos(self):
        world = GameWorld(mode="laboratory", rng=Random(121))
        world.phase = "weapon_choice"
        self.assertTrue(world.choose_weapon("katana"))
        self.assertEqual(world.practice_remaining, 45)
        identities = set()
        families = {}
        for weapon in ("katana", "bow", "spear", "longbow", "returning_spear", "sword"):
            self.assertTrue(world.switch_weapon(weapon))
            self.assertEqual(world.weapon_id, weapon)
            identities.update(id(target) for target in world.enemies)
            families[weapon] = {id(target) for target in world.enemies}
        self.assertEqual(len(identities), 9)
        self.assertEqual(families["katana"], families["sword"])
        self.assertEqual(families["bow"], families["longbow"])
        self.assertEqual(families["spear"], families["returning_spear"])
        self.assertEqual(world.practice_remaining, 45)

    def test_todas_armas_atingem_alvo_real_no_laboratorio_sem_espaco(self):
        world = GameWorld(mode="laboratory", rng=Random(121))
        world.phase = "weapon_choice"
        self.assertTrue(world.choose_weapon("katana"))
        for weapon in ("katana", "bow", "spear", "longbow", "returning_spear", "sword"):
            with self.subTest(weapon=weapon):
                self.assertTrue(world.switch_weapon(weapon))
                world.attack_cooldown = 0
                target = world.enemies[0]
                world.player.x, world.player.y = target.x-40, target.y
                before = target.hp
                world.update(0)
                world.update(.12)
                self.assertLess(target.hp, before)
        self.assertEqual(world.player.progression.xp, 0)
        self.assertEqual(world.kills, 0)


if __name__ == "__main__":
    unittest.main()

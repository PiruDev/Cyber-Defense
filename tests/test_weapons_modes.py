import random
import unittest

from game.cards import apply_card
from game.drops import collect_drop
from game.balance import BalanceConfig
from game.player import Player
from game.projectiles import Projectile
from game.weapons import WeaponSystem


class WeaponSystemTests(unittest.TestCase):
    def jogador(self):
        player = Player()
        player.facing_x, player.facing_y = 1, 0
        return player

    def test_katana_dois_impactos_unicos_com_snapshot(self):
        player = self.jogador()
        weapon = WeaponSystem("katana")
        primeiro = weapon.start(player)
        self.assertEqual(len(primeiro), 1)
        self.assertAlmostEqual(primeiro[0].damage, 0.6)
        self.assertAlmostEqual(weapon.cooldown, 0.4)
        self.assertAlmostEqual(weapon.animation_timer, 0.24)
        player.facing_x, player.facing_y = 0, -1
        self.assertEqual(weapon.start(player), ())
        self.assertEqual(weapon.update(0.099), ())
        segundo = weapon.update(0.001)
        self.assertEqual(len(segundo), 1)
        self.assertEqual((segundo[0].facing_x, segundo[0].facing_y), (1, 0))
        self.assertEqual(primeiro[0].serial[0], segundo[0].serial[0])
        self.assertNotEqual(primeiro[0].serial, segundo[0].serial)
        self.assertEqual(weapon.update(0), ())
        self.assertEqual(weapon.update(0.3), ())
        proximo = weapon.start(player)
        self.assertEqual(len(proximo), 1)
        self.assertNotEqual(proximo[0].serial[0], primeiro[0].serial[0])

    def test_katana_cruzar_impacto_em_dt_grande_nao_duplica(self):
        weapon = WeaponSystem("katana")
        primeiro = weapon.start(self.jogador())
        segundo = weapon.update(1)
        self.assertEqual(len(primeiro) + len(segundo), 2)
        self.assertEqual(weapon.update(1), ())
        self.assertEqual(weapon.pending, [])

    def test_lanca_atraso_e_troca_nao_zera_cooldown(self):
        player = self.jogador()
        weapon = WeaponSystem("spear")
        self.assertEqual(weapon.start(player), ())
        self.assertEqual(weapon.update(0.079), ())
        pulse, = weapon.update(0.001)
        self.assertEqual((pulse.reach, pulse.width), (105, 14))
        self.assertAlmostEqual(pulse.damage, 1.2)
        restante = weapon.cooldown
        self.assertTrue(weapon.switch("bow"))
        self.assertEqual(weapon.cooldown, restante)
        self.assertEqual(weapon.start(player), ())
        self.assertFalse(weapon.switch("inexistente"))
        self.assertEqual(weapon.weapon_id, "bow")

    def test_armas_respeitam_melhorias_e_cancelamento_descarta_pulso(self):
        player = self.jogador()
        for card in ("damage", "range", "cooldown"):
            apply_card(player, card)
        weapon = WeaponSystem("katana")
        pulse, = weapon.start(player)
        self.assertAlmostEqual(pulse.damage, 0.6 * 1.2)
        self.assertAlmostEqual(pulse.reach, 70 * 1.15)
        self.assertAlmostEqual(weapon.cooldown, 0.4 * 0.9)
        weapon.cancel_pending()
        self.assertEqual(weapon.update(1), ())

    def test_proj_jogador_alcance_e_primeira_colisao(self):
        perto = Player(x=150, y=100)
        longe = Player(x=250, y=100)
        flecha = Projectile(100, 100, 400, 0, team="player", range_remaining=500)
        flecha.advance(1)
        self.assertLess(flecha.hit_fraction(perto), flecha.hit_fraction(longe))
        flecha.advance(10)
        self.assertEqual(flecha.x, 600)
        self.assertEqual(flecha.range_remaining, 0)
        self.assertEqual(flecha.team, "player")

    def test_overclock_multiplica_movimento_mas_nao_intervalo_ataque(self):
        player = self.jogador()
        apply_card(player, "speed")
        intervalo = player.attack_interval
        collect_drop(player, "overclock", BalanceConfig())
        self.assertAlmostEqual(player.move_speed, 220 * 1.12 * 1.25)
        self.assertEqual(player.attack_interval, intervalo)
        player.overclock_timer = 0.02
        x = player.x
        player.move(1, 0, 0.05, (32, 154, 1036, 530))
        self.assertAlmostEqual(player.x - x, 220 * 1.12 * (0.05 + 0.25 * 0.02))


if __name__ == "__main__":
    unittest.main()

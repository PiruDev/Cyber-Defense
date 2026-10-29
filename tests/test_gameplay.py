import math
import random
import unittest
from unittest.mock import patch

from game.combat import in_attack_range
from game.cards import apply_card
from game.enemies import Drop, Enemy
from game.world import GameWorld


class ArenaTests(unittest.TestCase):
    def mundo(self):
        mundo = GameWorld(arena=(32, 154, 1036, 530), rng=random.Random(42))
        mundo.enemies.clear()
        mundo.drops.clear()
        mundo.player.x, mundo.player.y = 500, 400
        mundo.player.facing_x, mundo.player.facing_y = 1, 0
        return mundo

    def inimigo(self, mundo, dx=45, dy=0, hp=3):
        inimigo = Enemy(mundo.player.x + dx, mundo.player.y + dy, hp=hp, speed=0)
        mundo.enemies.append(inimigo)
        return inimigo

    def avancar(self, mundo, segundos, **comandos):
        passos = math.ceil(segundos / 0.01)
        for _ in range(passos):
            mundo.update(segundos / passos, **comandos)

    def test_movimento_usa_dt_e_diagonal_normalizada(self):
        reto = self.mundo()
        diagonal = self.mundo()
        reto.update(0.05, move_x=1)
        diagonal.update(0.05, move_x=1, move_y=1)
        self.assertAlmostEqual(reto.player.x - 500, 220 * 0.05)
        self.assertAlmostEqual(reto.player.y, 400)
        self.assertAlmostEqual(math.hypot(diagonal.player.x - 500, diagonal.player.y - 400), 11)
        parcelado = self.mundo()
        parcelado.update(0.025, move_x=1)
        parcelado.update(0.025, move_x=1)
        self.assertAlmostEqual(reto.player.x, parcelado.player.x)

    def test_jogador_permanece_dentro_das_quatro_bordas(self):
        mundo = self.mundo()
        esquerda, topo, largura, altura = 32, 154, 1036, 530
        raio = mundo.player.radius
        for x, y, mx, my in (
            (esquerda + raio, topo + raio, -1, -1),
            (esquerda + largura - raio, topo + altura - raio, 1, 1),
        ):
            with self.subTest(direcao=(mx, my)):
                mundo.player.x, mundo.player.y = x, y
                mundo.update(0.05, move_x=mx, move_y=my)
                self.assertEqual((mundo.player.x, mundo.player.y), (x, y))

    def test_inimigo_persegue_jogador_com_dt(self):
        mundo = self.mundo()
        inimigo = Enemy(700, 400)
        mundo.enemies.append(inimigo)
        mundo.update(0.05)
        self.assertAlmostEqual(inimigo.x, 700 - 85 * 0.05)
        self.assertAlmostEqual(inimigo.y, 400)

    def test_contato_tem_cooldown_global_e_nao_empilha_dano(self):
        mundo = self.mundo()
        self.inimigo(mundo, dx=0)
        self.inimigo(mundo, dx=0)
        mundo.update(0.01)
        self.assertEqual(mundo.player.progression.hp, 90)
        self.avancar(mundo, 0.78)
        self.assertEqual(mundo.player.progression.hp, 90)
        self.avancar(mundo, 0.03)
        self.assertEqual(mundo.player.progression.hp, 80)

    def test_ataque_respeita_alcance_cone_e_cooldown(self):
        mundo = self.mundo()
        frente = self.inimigo(mundo)
        atras = self.inimigo(mundo, dx=-45)
        longe = self.inimigo(mundo, dx=150)
        lado = self.inimigo(mundo, dx=0, dy=60)
        mundo.update(0.01, attack=True)
        self.assertEqual((frente.hp, atras.hp, longe.hp, lado.hp), (2, 3, 3, 3))
        mundo.update(0.01, attack=True)
        self.assertEqual(frente.hp, 2)
        self.avancar(mundo, 0.36)
        mundo.update(0.01, attack=True)
        self.assertEqual(frente.hp, 1)

    def test_ataque_usa_dano_atual_e_morte_recompensa_uma_vez(self):
        mundo = self.mundo()
        # MISSÃO005: dano agora cresce por carta, sem bônus automático de nível.
        apply_card(mundo.player, "damage")
        alvo = self.inimigo(mundo, hp=1.2)
        mundo.update(0.01, attack=True)
        self.assertNotIn(alvo, mundo.enemies)
        self.assertEqual((mundo.kills, mundo.player.progression.xp), (1, 25))
        self.avancar(mundo, 0.4, attack=True)
        self.assertEqual((mundo.kills, mundo.player.progression.xp), (1, 25))

    def test_cone_tem_limite_de_cinquenta_graus_e_alcance_da_lamina(self):
        mundo = self.mundo()
        for angulo, esperado in ((49.9, True), (50, True), (50.1, False)):
            with self.subTest(angulo=angulo):
                radianos = math.radians(angulo)
                alvo = Enemy(500 + 60 * math.cos(radianos), 400 + 60 * math.sin(radianos))
                self.assertEqual(in_attack_range(mundo.player, alvo), esperado)
        self.assertTrue(in_attack_range(mundo.player, Enemy(587, 400)))
        self.assertFalse(in_attack_range(mundo.player, Enemy(587.01, 400)))

    def test_spawn_inicial_intervalo_distancia_e_limite(self):
        mundo = GameWorld(rng=random.Random(7))
        igual = GameWorld(rng=random.Random(7))
        self.assertEqual(len(mundo.enemies), 3)
        self.assertEqual([(e.x, e.y) for e in mundo.enemies], [(e.x, e.y) for e in igual.enemies])
        for inimigo in mundo.enemies:
            self.assertGreaterEqual(math.hypot(inimigo.x - mundo.player.x, inimigo.y - mundo.player.y), 220)
            inimigo.speed = 0
        # MISSÃO005: spawn a cada segundo e quota finita de seis na primeira onda.
        self.avancar(mundo, 0.99)
        self.assertEqual(len(mundo.enemies), 3)
        self.avancar(mundo, 0.02)
        self.assertEqual(len(mundo.enemies), 4)
        for _ in range(400):
            for inimigo in mundo.enemies:
                inimigo.speed = 0
            mundo.update(0.05)
            self.assertLessEqual(len(mundo.enemies), 10)
        self.assertEqual(len(mundo.enemies), 6)
        self.assertEqual(mundo.waves.spawned, 6)
        for inimigo in mundo.enemies:
            self.assertGreaterEqual(math.hypot(inimigo.x - mundo.player.x, inimigo.y - mundo.player.y), 220)

    def test_drop_controlado_por_probabilidade(self):
        # MISSÃO007: chance total passou a 20%, seguida da seleção do tipo.
        for sorteio, quantidade in ((0.199, 1), (0.20, 0), (0.99, 0)):
            with self.subTest(sorteio=sorteio):
                mundo = self.mundo()
                self.inimigo(mundo, hp=1)
                with patch.object(mundo.rng, "random", return_value=sorteio):
                    mundo.update(0.01, attack=True)
                self.assertEqual(len(mundo.drops), quantidade)

    def test_coleta_remove_drop_e_aumenta_estoque_so_uma_vez(self):
        mundo = self.mundo()
        estoque = mundo.player.inventory.potions
        mundo.drops.append(Drop(mundo.player.x, mundo.player.y))
        mundo.update(0.01)
        self.assertEqual(mundo.player.inventory.potions, estoque + 1)
        self.assertEqual(mundo.drops, [])
        mundo.update(0.01)
        self.assertEqual(mundo.player.inventory.potions, estoque + 1)

    def test_pocao_cura_35_respeita_teto_e_nao_gasta_com_hp_cheio(self):
        mundo = self.mundo()
        self.assertEqual(mundo.player.inventory.potions, 2)
        self.assertFalse(mundo.use_potion())
        self.assertEqual(mundo.player.inventory.potions, 2)
        mundo.player.progression.hp = 40
        self.assertTrue(mundo.use_potion())
        self.assertEqual((mundo.player.progression.hp, mundo.player.inventory.potions), (75, 1))
        self.assertTrue(mundo.use_potion())
        self.assertEqual((mundo.player.progression.hp, mundo.player.inventory.potions), (100, 0))
        mundo.player.progression.hp = 50
        self.assertFalse(mundo.use_potion())
        self.assertEqual(mundo.player.progression.hp, 50)

    def test_inventario_cheio_consome_drop_e_converte_em_score(self):
        mundo = self.mundo()
        mundo.player.inventory.potions = mundo.player.inventory.max_potions
        drop = Drop(mundo.player.x, mundo.player.y)
        mundo.drops.append(drop)
        mundo.update(0.01)
        # MISSÃO005: estoque cheio converte coleta em cura ou score e remove drop.
        self.assertNotIn(drop, mundo.drops)
        self.assertEqual(mundo.player.inventory.potions, 5)
        self.assertEqual(mundo.score, 10)
        self.assertEqual(mundo.player.progression.xp, 0)
        mundo.player.progression.hp = 50
        mundo.use_potion()
        mundo.update(0.01)
        self.assertEqual(mundo.drops, [])
        self.assertEqual(mundo.player.inventory.potions, 4)

    def test_inventario_pausa_mundo_mas_permite_pocao(self):
        mundo = self.mundo()
        inimigo = self.inimigo(mundo)
        mundo.player.progression.hp = 50
        mundo.toggle_inventory()
        self.assertTrue(mundo.inventory_open)
        antes = (mundo.player.x, mundo.player.y, inimigo.x, inimigo.y, inimigo.hp, mundo.elapsed)
        self.avancar(mundo, 2, move_x=1, attack=True)
        depois = (mundo.player.x, mundo.player.y, inimigo.x, inimigo.y, inimigo.hp, mundo.elapsed)
        self.assertEqual(antes, depois)
        self.assertEqual(len(mundo.enemies), 1)
        self.assertTrue(mundo.use_potion())
        self.assertEqual(mundo.player.progression.hp, 85)
        mundo.toggle_inventory()
        mundo.update(0.05, move_x=1)
        self.assertGreater(mundo.player.x, antes[0])

    def test_pausa_congela_cooldowns_e_spawn_timer(self):
        mundo = self.mundo()
        self.inimigo(mundo, dx=0, hp=10)
        mundo.update(0.01, attack=True)
        antes = (mundo.attack_timer, mundo.attack_cooldown, mundo.damage_cooldown, mundo.spawn_timer)
        mundo.toggle_inventory()
        mundo.update(10, move_x=1, attack=True)
        self.assertEqual(
            (mundo.attack_timer, mundo.attack_cooldown, mundo.damage_cooldown, mundo.spawn_timer), antes
        )
        mundo.toggle_inventory()
        mundo.update(0.01)
        self.assertLess(mundo.attack_cooldown, antes[1])

    def test_derrota_bloqueia_acoes_e_restart_restaura_estado(self):
        mundo = self.mundo()
        mundo.player.progression.hp = 1
        self.inimigo(mundo, dx=0)
        mundo.update(0.01)
        self.assertTrue(mundo.game_over)
        self.assertEqual(mundo.player.progression.hp, 0)
        posicao = (mundo.player.x, mundo.player.y)
        mundo.update(0.05, move_x=1, attack=True)
        self.assertEqual((mundo.player.x, mundo.player.y), posicao)
        self.assertFalse(mundo.use_potion())
        mundo.toggle_inventory()
        self.assertFalse(mundo.inventory_open)
        mundo.restart()
        self.assertFalse(mundo.game_over)
        self.assertFalse(mundo.inventory_open)
        self.assertFalse(mundo.victory)
        self.assertEqual((mundo.kills, mundo.player.progression.hp, mundo.player.progression.xp), (0, 100, 0))
        self.assertEqual(mundo.player.inventory.potions, 2)
        self.assertEqual(len(mundo.enemies), 3)

    def test_vinte_abates_nao_vencem_e_lab_exige_pratica_apos_cinco_ondas(self):
        mundo = self.mundo()
        for _ in range(20):
            mundo.enemies.clear()
            self.inimigo(mundo, hp=1)
            self.avancar(mundo, 0.36)
            mundo.update(0.01, attack=True)
            while mundo.choosing_card:
                mundo.advance_presentation(0.8)
                mundo.choose_card(0)
        self.assertEqual(mundo.kills, 20)
        # MISSÃO005: abates isolados não encerram a campanha; cinco ondas, sim.
        self.assertFalse(mundo.victory)
        self.assertFalse(mundo.game_over)
        antes = mundo.player.x
        mundo.update(0.05, move_x=1)
        self.assertGreater(mundo.player.x, antes)
        mundo = self.mundo()
        # Usa a quota real e registra mortes por update, incluindo a minhoca final.
        mundo.restart(mode="laboratory")
        for _ in range(200):
            for inimigo in mundo.enemies:
                inimigo.hp = 0
            mundo.update(1)
            while mundo.choosing_card:
                mundo.advance_presentation(0.8)
                mundo.choose_card(0)
            if mundo.choosing_weapon:
                break
        # MISSÃO007: conclusão das ondas oferece arma; vitória exige a prática.
        self.assertFalse(mundo.victory)
        self.assertTrue(mundo.choosing_weapon)
        self.assertEqual(mundo.waves.number, 5)
        self.assertEqual(mundo.kills, 51)
        self.assertTrue(mundo.choose_weapon("katana"))
        mundo.update(45)
        self.assertTrue(mundo.victory)
        posicao = (mundo.player.x, mundo.player.y, mundo.elapsed)
        mundo.update(1, move_x=1, attack=True)
        self.assertEqual((mundo.player.x, mundo.player.y, mundo.elapsed), posicao)


if __name__ == "__main__":
    unittest.main()

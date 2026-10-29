import pickle
import math
import random
import unittest

from game.archer import Archer
from game.cards import CARDS, apply_card
from game.combat import apply_enemy_hit
from game.enemies import Drop, Enemy
from game.projectiles import Projectile
from game.swordsman import Swordsman
from game.world import GameWorld
from game.worm import Worm


class RogueliteTests(unittest.TestCase):
    def mundo(self):
        mundo = GameWorld(arena=(32, 154, 1036, 530), rng=random.Random(31))
        mundo.enemies.clear()
        mundo.drops.clear()
        mundo.player.x, mundo.player.y = 500, 400
        mundo.player.facing_x, mundo.player.facing_y = 1, 0
        return mundo

    def resolver_escolhas(self, mundo):
        while mundo.choosing_card:
            mundo.advance_presentation(0.8)
            self.assertTrue(mundo.choose_card(0))

    def escolher_especifica(self, mundo, card_id):
        # Oferta controlada para isolar efeito e eventos posteriores à aquisição.
        mundo.pending_levelups = 1
        mundo._offer_next_card()
        mundo.card_choices = [next(c for c in CARDS if c.id == card_id)]
        mundo.advance_presentation(0.8)
        self.assertTrue(mundo.choose_card(0))

    def test_multiplos_niveis_fila_uma_carta_por_nivel_sem_bonus_automatico(self):
        mundo = self.mundo()
        mundo.player.progression.hp = 40
        self.assertEqual(mundo.grant_xp(300), 2)
        self.assertEqual((mundo.player.progression.nivel, mundo.player.progression.xp), (3, 50))
        self.assertEqual((mundo.player.progression.hp, mundo.player.progression.hp_maximo,
                          mundo.player.progression.dano), (40, 100, 1))
        self.assertEqual(mundo.pending_levelups, 2)
        self.assertEqual(len(mundo.card_choices), 3)
        mundo.advance_presentation(0.8)
        self.assertTrue(mundo.choose_card(1))
        self.assertEqual(mundo.pending_levelups, 1)
        self.assertTrue(mundo.choosing_card)
        mundo.advance_presentation(0.8)
        self.assertTrue(mundo.choose_card(2))
        self.assertEqual(sum(mundo.player.upgrades.values()), 2)
        self.assertEqual(mundo.pending_levelups, 0)
        self.assertFalse(mundo.choosing_card)
        self.assertFalse(mundo.choose_card(0))

    def test_escolha_pausa_total_e_indices_invalidos_nao_alteram_estado(self):
        mundo = self.mundo()
        mundo.enemies = [Archer(700, 400)]
        mundo.projectiles = [Projectile(350, 400, 180, 0)]
        mundo.player.progression.hp = 20
        mundo.attack_timer = mundo.shake_timer = 0.1
        mundo.inventory_open = True
        mundo.grant_xp(100)
        self.assertFalse(mundo.inventory_open)
        antes = pickle.dumps(mundo)
        for invalido in (-1, 3, True, 0.0, None, "0"):
            self.assertFalse(mundo.choose_card(invalido))
        mundo.update(10, move_x=1, attack=True)
        mundo.toggle_inventory()
        self.assertFalse(mundo.use_potion())
        self.assertEqual(pickle.dumps(mundo), antes)
        self.assertEqual(mundo.shake_offset, (0, 0))

    def test_teto36_oferece35_escolhas_sem_esgotar_catalogo(self):
        mundo = self.mundo()
        self.assertEqual(mundo.grant_xp(10**7), 35)
        for restante in range(35, 0, -1):
            self.assertEqual(mundo.pending_levelups, restante)
            self.assertEqual(len({c.id for c in mundo.card_choices}), 3)
            for c in mundo.card_choices:
                self.assertLess(mundo.player.upgrades.get(c.id, 0), c.max_stacks)
            mundo.advance_presentation(0.8)
            self.assertTrue(mundo.choose_card(0))
        self.assertEqual(mundo.player.progression.nivel, 36)
        self.assertFalse(mundo.choosing_card)
        self.assertEqual(mundo.grant_xp(10**7), 0)

    def test_carta_nao_reanima_morto_e_restart_limpa_run(self):
        mundo = self.mundo()
        mundo.grant_xp(250)
        mundo.advance_presentation(0.8)
        mundo.player.progression.hp = 0
        self.assertFalse(mundo.choose_card(0))
        mundo.score = 20
        mundo.projectiles.append(Projectile(100, 200, 180, 0))
        mundo.restart()
        self.assertEqual((mundo.score, mundo.pending_levelups, mundo.waves.number), (0, 0, 1))
        self.assertEqual(mundo.player.upgrades, {})
        self.assertEqual(mundo.projectiles, [])
        self.assertEqual(mundo.card_choices, [])
        self.assertEqual(mundo.player.inventory.max_potions, 5)

    def test_overflow_cura35_ou_score10_sem_xp_e_sem_recoleta(self):
        for hp, esperado_hp, score in ((30, 65, 0), (90, 100, 0), (100, 100, 10)):
            with self.subTest(hp=hp):
                mundo = self.mundo()
                mundo.player.inventory.potions = 5
                mundo.player.progression.hp = hp
                mundo.drops.append(Drop(500, 400))
                mundo.update(0)
                self.assertEqual(mundo.drops, [])
                self.assertEqual(mundo.player.inventory.potions, 5)
                self.assertEqual(mundo.player.progression.hp, esperado_hp)
                self.assertEqual((mundo.score, mundo.player.progression.xp), (score, 0))
                mundo.update(0)
                self.assertEqual(mundo.score, score)

    def test_regen_ciclo_cinco_segundos_e_pausa_sem_retroatividade(self):
        mundo = self.mundo()
        mundo.update(4.9)
        self.escolher_especifica(mundo, "regen")
        mundo.player.progression.hp = 50
        for e in mundo.enemies:
            e.speed = 0
        mundo.update(0.1)
        self.assertEqual(mundo.player.progression.hp, 50)
        mundo.toggle_inventory()
        mundo.update(50)
        self.assertEqual(mundo.player.progression.hp, 50)
        mundo.toggle_inventory()
        mundo.update(4.9)
        self.assertEqual(mundo.player.progression.hp, 51)

    def test_cura_por_cinco_abates_conta_apenas_apos_aquisicao(self):
        mundo = self.mundo()
        def resolver_sem_alterar_cura():
            while mundo.choosing_card:
                mundo.advance_presentation(0.8)
                index = next(i for i, c in enumerate(mundo.card_choices)
                             if c.id not in ("kill_heal", "regen", "max_hp"))
                mundo.choose_card(index)
        mundo.enemies = [Enemy(800, 400, hp=0) for _ in range(4)]
        mundo.update(0)
        resolver_sem_alterar_cura()
        self.escolher_especifica(mundo, "kill_heal")
        mundo.player.progression.hp = 50
        for _ in range(4):
            mundo.enemies.append(Enemy(800, 400, hp=0))
            mundo.update(0)
            resolver_sem_alterar_cura()
        self.assertEqual(mundo.player.progression.hp, 50)
        mundo.enemies.append(Enemy(800, 400, hp=0))
        mundo.update(0)
        resolver_sem_alterar_cura()
        self.assertEqual(mundo.player.kill_heal, 2)
        self.assertEqual(mundo.player.progression.hp, 52)

    def test_reducao_dano_aplica_uma_vez(self):
        mundo = self.mundo()
        apply_card(mundo.player, "reduction")
        apply_card(mundo.player, "reduction")
        mundo.enemies = [Enemy(500, 400, speed=0)]
        mundo.update(0)
        self.assertAlmostEqual(mundo.player.progression.hp, 100 - 10 * 0.9**2)

    def test_espadachim_antecipa_sem_dano_contato_e_atinge_so_no_fim(self):
        mundo = self.mundo()
        espada = Swordsman(455, 400, speed=0)
        mundo.enemies = [espada]
        mundo.update(0)
        self.assertEqual(espada.state, "windup")
        self.assertAlmostEqual(espada.telegraph_timer, 0.35)
        mundo.update(0.34)
        self.assertEqual(mundo.player.progression.hp, 100)
        mundo.update(0.02)
        self.assertEqual(mundo.player.progression.hp, 90)
        self.assertEqual(espada.state, "recover")
        self.assertAlmostEqual(espada.attack_cooldown, 1.1)
        mundo.update(0.05)
        self.assertEqual(mundo.player.progression.hp, 90)

    def test_espadachim_cone_fixo_permite_esquiva_e_stun_bloqueia(self):
        mundo = self.mundo()
        espada = Swordsman(455, 400, speed=0)
        mundo.enemies = [espada]
        mundo.update(0)
        direcao = (espada.facing_x, espada.facing_y)
        mundo.player.x = 410
        mundo.update(0.36)
        self.assertEqual((espada.facing_x, espada.facing_y), direcao)
        self.assertEqual(mundo.player.progression.hp, 100)
        espada.state = "windup"
        espada.telegraph_timer = 0.01
        espada.stun_timer = 0.2
        mundo.player.x = 500
        mundo.update(0.19)
        self.assertEqual(mundo.player.progression.hp, 100)
        self.assertEqual(espada.telegraph_timer, 0.01)

    def test_arqueiro_antecipa_disparo_direcional_e_respeita_cooldown(self):
        mundo = self.mundo()
        arqueiro = Archer(700, 400, speed=0)
        mundo.enemies = [arqueiro]
        mundo.update(0)
        self.assertAlmostEqual(arqueiro.telegraph_timer, 0.45)
        mundo.update(0.44)
        self.assertEqual(mundo.projectiles, [])
        mundo.update(0.02)
        self.assertEqual(len(mundo.projectiles), 1)
        flecha = mundo.projectiles[0]
        self.assertEqual((flecha.vx, flecha.vy, flecha.damage, flecha.ttl), (-180, 0, 8, 4))
        self.assertAlmostEqual(arqueiro.attack_cooldown, 2.2)
        mundo.update(0.05)
        self.assertEqual(len(mundo.projectiles), 1)

    def test_flecha_colisao_varrida_e_remocao_uma_vez(self):
        mundo = self.mundo()
        mundo.projectiles = [Projectile(400, 400, 1000, 0)]
        mundo.update(0.2)
        self.assertEqual(mundo.player.progression.hp, 92)
        self.assertEqual(mundo.projectiles, [])
        mundo.update(0.01)
        self.assertEqual(mundo.player.progression.hp, 92)

    def test_flechas_multiplas_removidas_sem_pular_elementos(self):
        mundo = self.mundo()
        mundo.projectiles = [Projectile(400, 400, 1000, 0) for _ in range(4)]
        mundo.projectiles.append(Projectile(100, 200, 0, 0, ttl=0.01))
        mundo.projectiles.append(Projectile(1100, 200, 100, 0))
        mundo.update(0.2)
        self.assertEqual(mundo.projectiles, [])
        self.assertEqual(mundo.player.progression.hp, 92)

    def test_ttl_limita_deslocamento_e_erro_lateral_nao_colide(self):
        mundo = self.mundo()
        flecha = Projectile(400, 450, 1000, 0, ttl=0.1)
        flecha.advance(1)
        self.assertEqual((flecha.x, flecha.ttl), (500, 0))
        self.assertFalse(flecha.hits(mundo.player))

    def test_min_hoca_descarta_overkill_e_transfere_cabeca(self):
        verme = Worm(700, 400)
        self.assertEqual((len(verme.segments), verme.hp), (6, 60))
        primeira = verme.head
        segunda = verme.segments[1]
        self.assertEqual(verme.receive_damage(1000), 10)
        self.assertEqual((len(verme.segments), verme.hp), (5, 50))
        self.assertNotIn(primeira, verme.segments)
        self.assertIs(verme.head, segunda)
        self.assertEqual(verme.head.hp, 10)

    def test_hit_cancela_antecipacao_de_espada_e_flecha(self):
        mundo = self.mundo()
        for classe in (Swordsman, Archer):
            with self.subTest(classe=classe.__name__):
                inimigo = classe(545, 400, state="windup", telegraph_timer=0.01)
                self.assertTrue(apply_enemy_hit(mundo.player, inimigo))
                self.assertEqual(inimigo.state, "recover")
                self.assertEqual(inimigo.telegraph_timer, 0)
                self.assertEqual(inimigo.attack_timer, 0)
                self.assertGreaterEqual(inimigo.attack_cooldown, 0.3)

    def verificar_corpo(self, verme, arena):
        left, top, width, height = arena
        for segmento in verme.segments:
            self.assertGreaterEqual(segmento.x, left + segmento.radius - 1e-8)
            self.assertLessEqual(segmento.x, left + width - segmento.radius + 1e-8)
            self.assertGreaterEqual(segmento.y, top + segmento.radius - 1e-8)
            self.assertLessEqual(segmento.y, top + height - segmento.radius + 1e-8)
        # MISSÃO011: 32 unidades ao longo da trajetória, não da corda da curva.
        for indice, segmento in enumerate(verme.segments):
            esperado = verme.sample_trail(indice * verme.segment_spacing)
            self.assertAlmostEqual(segmento.x, esperado[0])
            self.assertAlmostEqual(segmento.y, esperado[1])
        for primeiro, segundo in zip(verme.segments, verme.segments[1:]):
            self.assertLessEqual(math.hypot(primeiro.x - segundo.x, primeiro.y - segundo.y), 32 + 1e-7)
        self.assertEqual((verme.x, verme.y), (verme.head.x, verme.head.y))

    def test_corpo_min_hoca_continuo_em_curvas_bordas_e_troca_cabeca(self):
        mundo = self.mundo()
        verme = Worm(1050, 660)
        verme.advance_feedback(0, mundo.arena)
        self.verificar_corpo(verme, mundo.arena)
        destinos = ((1040, 650), (1040, 180), (60, 180), (60, 650), (500, 400))
        for x, y in destinos:
            mundo.player.x, mundo.player.y = x, y
            for _ in range(60):
                livre = verme.advance_feedback(0.05, mundo.arena)
                verme.move_towards(mundo.player, livre)
                self.verificar_corpo(verme, mundo.arena)
        verme.receive_damage(1000)
        verme.advance_feedback(0, mundo.arena)
        self.verificar_corpo(verme, mundo.arena)

    def test_spawn_real_quinta_onda_escala_e_preserva_espacamento_do_verme(self):
        for seed in range(10):
            with self.subTest(seed=seed):
                mundo = GameWorld(rng=random.Random(seed))
                for _ in range(4):
                    while mundo.waves.can_spawn:
                        mundo.waves.next_kind()
                    while mundo.waves.defeated < mundo.waves.total:
                        mundo.waves.register_defeat()
                    mundo.waves.update(0, 0)
                    mundo.waves.update(3, 0)
                mundo.enemies.clear()
                tipos = []
                while mundo.waves.can_spawn:
                    mundo._spawn_enemy()
                    inimigo = mundo.enemies.pop()
                    tipos.append(inimigo.kind)
                    if isinstance(inimigo, Worm):
                        self.verificar_corpo(inimigo, mundo.arena)
                        self.assertEqual(inimigo.hp, 60)
                    else:
                        self.assertAlmostEqual(inimigo.hp, 3 * 1.6)
                        self.assertAlmostEqual(inimigo.damage, (8 if isinstance(inimigo, Archer) else 10) * 1.4)
                self.assertEqual((tipos.count("swordsman"), tipos.count("archer"), tipos.count("worm")), (9, 5, 1))

    def test_limpar_onda_remove_flechas_antes_da_oferta_de_carta(self):
        mundo = self.mundo()
        mundo.waves.spawned = mundo.waves.total
        mundo.waves.defeated = mundo.waves.total - 1
        mundo.player.progression.xp = 75
        mundo.enemies = [Enemy(800, 400, hp=0)]
        mundo.projectiles = [Projectile(500, 400, 180, 0)]
        mundo.update(0)
        self.assertTrue(mundo.choosing_card)
        self.assertEqual(mundo.projectiles, [])
        self.assertEqual(mundo.player.progression.hp, 100)

    def test_atingir_varios_segmentos_remove_uma_cabeca_e_xp_so_no_fim(self):
        mundo = self.mundo()
        mundo.player.progression.dano = 1000
        verme = Worm(700, 400, speed=0)
        mundo.enemies = [verme]
        for golpe in range(6):
            # Todas as partes entram no golpe; a entidade recebe um só impacto.
            verme.x, verme.y = 545, 400
            for segmento in verme.segments:
                segmento.x, segmento.y = 545, 400
            mundo.attack_cooldown = 0
            mundo.update(0, attack=True)
            self.assertEqual(len(verme.segments), 5 - golpe)
            self.assertEqual(mundo.kills, int(golpe == 5))
            self.assertEqual(mundo.player.progression.xp, 25 if golpe == 5 else 0)
        mundo.update(0)
        self.assertEqual(mundo.kills, 1)

    def test_mortes_simultaneas_nao_pulam_recompensas_ou_listas(self):
        mundo = self.mundo()
        mundo.enemies = [Enemy(800, 400, hp=0) for _ in range(3)]
        mundo.update(0)
        self.assertEqual(mundo.enemies, [])
        self.assertEqual((mundo.kills, mundo.player.progression.xp), (3, 75))
        mundo.update(0)
        self.assertEqual((mundo.kills, mundo.player.progression.xp), (3, 75))


if __name__ == "__main__":
    unittest.main()

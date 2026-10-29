import importlib.util
import random
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from game.balance import BalanceConfig, WEAPON_CONFIGS
from game.drops import collect_drop, roll_drop
from game.modes import GameMode
from game.music import MusicPlayer
from game.player import Player
from game.waves import WaveManager


class ModesDropsTests(unittest.TestCase):
    def test_modes_finitos_rootkit_apenas_sexta_defesa(self):
        for mode, ultima in ((GameMode.DEFENSE, 6), (GameMode.LABORATORY, 5)):
            with self.subTest(mode=mode):
                waves = WaveManager(mode=mode)
                self.assertEqual(waves.max_waves, ultima)
                for numero in range(1, ultima + 1):
                    tipos = [waves.next_kind() for _ in range(waves.total)]
                    if numero == 6:
                        self.assertEqual(tipos, ["rootkit"])
                    else:
                        self.assertNotIn("rootkit", tipos)
                    for _ in tipos:
                        waves.register_defeat()
                    waves.update(0, 0)
                    if numero < ultima:
                        self.assertFalse(waves.victory)
                        waves.update(3, 0)
                self.assertTrue(waves.victory)

    def test_config_armas_e_balanco_iniciais(self):
        config = BalanceConfig()
        self.assertEqual((config.drop_chance, config.repair_share), (0.2, 0.5))
        self.assertEqual((config.overclock_multiplier, config.overclock_duration), (1.25, 5))
        self.assertEqual(set(WEAPON_CONFIGS), {"sword", "katana", "bow", "spear", "longbow", "returning_spear"})
        self.assertEqual(WEAPON_CONFIGS["katana"].impact_times, (0, 0.1))
        self.assertEqual(WEAPON_CONFIGS["spear"].impact_times, (0.08,))
        self.assertEqual(WEAPON_CONFIGS["bow"].projectile_speed, 400)

    def test_drop_vinte_porcento_e_sorteio_condicional_cinquenta(self):
        for valores, esperado, chamadas in (
            ([0.1999, 0.4999], "repair", 2),
            ([0.1999, 0.5], "overclock", 2),
            ([0.2], None, 1), ([0.99], None, 1),
        ):
            with self.subTest(valores=valores):
                rng = Mock()
                rng.random.side_effect = valores
                self.assertEqual(roll_drop(rng, BalanceConfig()), esperado)
                self.assertEqual(rng.random.call_count, chamadas)

    def test_reparo_cap_e_overclock_refresh_sem_somar(self):
        player = Player()
        config = BalanceConfig()
        result = collect_drop(player, "repair", config)
        self.assertEqual((result.potions, result.score), (1, 0))
        player.inventory.potions = 5
        player.progression.hp = 90
        result = collect_drop(player, "repair", config)
        self.assertEqual((result.healed, result.score), (10, 0))
        self.assertEqual(collect_drop(player, "repair", config).score, 10)
        self.assertTrue(collect_drop(player, "overclock", config).overclock)
        self.assertEqual(player.overclock_timer, 5)
        player.overclock_timer = 1
        self.assertTrue(collect_drop(player, "overclock", config).overclock)
        self.assertEqual(player.overclock_timer, 5)
        self.assertEqual(player.progression.xp, 0)
        player.progression.hp = 0
        player.overclock_timer = 0
        self.assertFalse(collect_drop(player, "overclock", config).overclock)
        self.assertEqual(player.overclock_timer, 0)

    def test_roll_seed_reproduzivel(self):
        primeiro, segundo = random.Random(9), random.Random(9)
        config = BalanceConfig()
        self.assertEqual([roll_drop(primeiro, config) for _ in range(100)],
                         [roll_drop(segundo, config) for _ in range(100)])


class MusicMissingTests(unittest.TestCase):
    def test_arquivo_ausente_e_musica_desativada_sao_opcionais(self):
        with patch("game.music.Path.is_file", return_value=False) as existe:
            music = MusicPlayer(SimpleNamespace(music_enabled=True, music_volume=0.15))
            self.assertFalse(music.start())
            self.assertIn("ausente", music.status.lower())
            chamadas = existe.call_count
            self.assertFalse(music.start())
            self.assertEqual(existe.call_count, chamadas)
            music.updatevolume()
            music.close()
            music.close()
        with patch("game.music.Path.is_file", side_effect=AssertionError("Não buscar quando desativada")):
            music = MusicPlayer(SimpleNamespace(music_enabled=False))
            self.assertFalse(music.start())

    @unittest.skipUnless(importlib.util.find_spec("pygame"), "Pygame não instalado")
    def test_musica_load_loop_uma_vez_e_falha_de_arquivo_segura(self):
        import pygame
        settings = SimpleNamespace(music_enabled=True, music_volume=0.15)
        with patch("game.music.Path.is_file", return_value=True), \
             patch.object(pygame.mixer, "get_init", return_value=(22050, -16, 2)), \
             patch.object(pygame.mixer.music, "load") as load, \
             patch.object(pygame.mixer.music, "play") as play, \
             patch.object(pygame.mixer.music, "set_volume") as volume, \
             patch.object(pygame.mixer.music, "stop") as stop:
            music = MusicPlayer(settings)
            self.assertTrue(music.start())
            self.assertTrue(music.start())
            self.assertEqual(load.call_count, 1)
            play.assert_called_once_with(loops=-1)
            settings.music_volume = 0.3
            music.updatevolume()
            volume.assert_called_with(0.3)
            settings.music_enabled = False
            music.updatevolume()
            volume.assert_called_with(0)
            music.close()
            music.close()
            stop.assert_called_once()
        settings.music_enabled = True
        with patch("game.music.Path.is_file", return_value=True), \
             patch.object(pygame.mixer, "get_init", return_value=(22050, -16, 2)), \
             patch.object(pygame.mixer.music, "load", side_effect=pygame.error("arquivo inválido")):
            music = MusicPlayer(settings)
            self.assertFalse(music.start())
            self.assertFalse(music.enabled)
            music.close()


if __name__ == "__main__":
    unittest.main()

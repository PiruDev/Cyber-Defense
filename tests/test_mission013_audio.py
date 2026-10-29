"""Música fornecida pelo usuário: formato distribuível e falhas opcionais."""

from array import array
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import wave

from game.music import MusicPlayer


ROOT = Path(__file__).resolve().parents[1]


class ThemeTests(unittest.TestCase):
    def test_wav_pcm_valido_nao_vazio_e_emenda_sem_salto_abrupto(self):
        with wave.open(str(ROOT / 'assets/audio/theme.wav'), 'rb') as track:
            self.assertEqual(track.getsampwidth(), 2)
            self.assertIn(track.getnchannels(), (1, 2))
            self.assertGreaterEqual(track.getframerate(), 22050)
            self.assertGreater(track.getnframes() / track.getframerate(), 10)
            channels = track.getnchannels()
            samples = array('h', track.readframes(track.getnframes()))
        self.assertGreater(max(abs(sample) for sample in samples), 100)
        for channel in range(channels):
            seam_jump = abs(samples[channel] - samples[-channels + channel])
            self.assertLess(seam_jump, 3277, f'Canal {channel}: salto de {seam_jump}/32768')

    def test_player_prioriza_ogg_distribuido_e_mantem_reproducao_unica(self):
        import pygame
        settings = SimpleNamespace(music_enabled=True, music_volume=.15)
        with patch.object(pygame.mixer, 'get_init', return_value=(44100, -16, 2)), \
             patch.object(pygame.mixer.music, 'load') as load, \
             patch.object(pygame.mixer.music, 'play') as play, \
             patch.object(pygame.mixer.music, 'set_volume'), \
             patch.object(pygame.mixer.music, 'stop'):
            player = MusicPlayer(settings)
            self.assertTrue(player.start())
            self.assertEqual(Path(load.call_args.args[0]).name, 'theme.ogg')
            player.update_volume()
            player.start()
            self.assertEqual(load.call_count, 1)
            play.assert_called_once_with(loops=-1)
            player.close()


if __name__ == '__main__':
    unittest.main()

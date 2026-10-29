"""Regressões de mixer/canais e redução de chamadas; sem audição simulada."""
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from game.audio import AudioBus
from game.audio_config import buffer_from_query, preconfigure, requested_buffer
from game.music import MusicPlayer
from game.settings import EffectSettings


class MixerConfigTests(unittest.TestCase):
    def test_tres_buffers_validos_e_query_invalida(self):
        for buffer in (512, 1024, 2048):
            self.assertEqual(buffer_from_query(f"?audio_buffer={buffer}"), buffer)
            window = SimpleNamespace(location=SimpleNamespace(search=f"?audio_buffer={buffer}"))
            with patch.dict(os.environ, CYBER_AUDIO_BUFFER=""), patch("platform.window", window, create=True):
                self.assertEqual(requested_buffer(browser=True), buffer)
        for query in ("", "?audio_buffer=999", "?audio_buffer=-1", "?audio_buffer=texto"):
            self.assertEqual(buffer_from_query(query), 512)

    def test_preinit_respeita_buffer_explicitado_sem_abrir_device(self):
        for buffer in (512, 1024, 2048):
            pygame = Mock()
            with patch.dict(os.environ, CYBER_AUDIO_BUFFER=str(buffer)):
                self.assertEqual(preconfigure(pygame), buffer)
            pygame.mixer.pre_init.assert_called_once_with(frequency=44100, size=-16, channels=2, buffer=buffer)
            pygame.mixer.init.assert_not_called()

    def test_backend_sem_preinit_e_env_invalida_nao_impedem_jogo(self):
        pygame = Mock()
        pygame.mixer.pre_init.side_effect = RuntimeError("sem backend")
        with patch.dict(os.environ, CYBER_AUDIO_BUFFER="invalid"):
            self.assertEqual(requested_buffer(), 512)
            self.assertEqual(preconfigure(pygame), 512)


class BusTests(unittest.TestCase):
    def create_bus(self, web):
        import pygame
        voices = [Mock() for _ in range(8)]
        for voice in voices:
            voice.get_busy.return_value = False
        with patch.object(sys, "platform", "emscripten" if web else "win32"), \
             patch.object(pygame.mixer, "get_init", return_value=(44100, -16, 2)), \
             patch.object(pygame.mixer, "get_num_channels", return_value=8), \
             patch.object(pygame.mixer, "Channel", side_effect=lambda i: voices[i]), \
             patch.object(pygame.mixer, "Sound", side_effect=lambda **kw: Mock()) as load:
            bus = AudioBus(EffectSettings())
            self.assertEqual(load.call_count, 8)
        return bus, voices[:len(bus._channels)]

    def test_efeitos_precarregados_sem_load_ou_amostras_durante_eventos(self):
        import pygame
        bus, voices = self.create_bus(True)
        with patch.object(pygame.mixer, "Sound", side_effect=AssertionError("load por quadro")), \
             patch.object(bus, "_samples", side_effect=AssertionError("DSP por quadro")), \
             patch("game.audio.monotonic", return_value=10):
            for _ in range(100):
                bus.play_events([{"kind": "hit"}])
        self.assertEqual(sum(voice.play.call_count for voice in voices), 1)

    def test_web_deduplica_aliases_e_respeita_intervalo_curto(self):
        bus, voices = self.create_bus(True)
        events = [{"kind": name} for name in ("death", "wormrupture", "hit", "player_hit")]
        with patch("game.audio.monotonic", side_effect=(10, 10.01, 10.04)):
            bus.play_events(events)
            self.assertEqual(sum(voice.play.call_count for voice in voices), 2)
            bus.play_events(events)
            self.assertEqual(sum(voice.play.call_count for voice in voices), 2)
            bus.play_events(events)
            self.assertEqual(sum(voice.play.call_count for voice in voices), 4)

    def test_limites_web_e_desktop_sem_reusar_canal_no_mesmo_quadro(self):
        for web, channel_count, limit in ((True, 4, 2), (False, 8, 4)):
            bus, voices = self.create_bus(web)
            self.assertEqual(len(voices), channel_count)
            bus.play_events([{"kind": name} for name in ("hit", "death", "pickup", "score", "select")])
            self.assertEqual(sum(voice.play.call_count for voice in voices), limit)
            self.assertTrue(all(voice.play.call_count <= 1 for voice in voices))

    def test_canal_ocupado_nao_e_interrompido_e_volume_nao_repete(self):
        bus, voices = self.create_bus(True)
        for voice in voices:
            voice.get_busy.return_value = True
        for _ in range(50):
            bus.play_events([{"kind": "hit"}])
        self.assertFalse(any(voice.play.called for voice in voices))
        self.assertTrue(all(voice.set_volume.call_count == 1 for voice in voices))
        bus.settings.volume = .1
        bus.play_events([])
        self.assertTrue(all(voice.set_volume.call_count == 2 for voice in voices))


class MusicAndLoopTests(unittest.TestCase):
    def test_volume_musica_so_atualiza_quando_muda(self):
        settings = SimpleNamespace(music_volume=.15, music_enabled=True)
        player = MusicPlayer(settings)
        player._pygame = Mock()
        for _ in range(500):
            player.updatevolume()
        player._pygame.mixer.music.set_volume.assert_called_once_with(.15)
        settings.music_enabled = False
        player.updatevolume()
        self.assertEqual(player._pygame.mixer.music.set_volume.call_count, 2)
        player._pygame.mixer.music.set_volume.assert_called_with(0)
        player._pygame.mixer.music.play.assert_not_called()

    def test_preinit_antes_de_init_no_desktop(self):
        script = '''
import asyncio
import pygame
from unittest.mock import patch
from game import main as app
order=[]
initialize=pygame.init
configure=pygame.mixer.pre_init
def pre(*args,**kwargs):
    order.append('pre');return configure(*args,**kwargs)
def init():
    order.append('init');return initialize()
with patch.object(pygame.mixer,'pre_init',side_effect=pre), patch.object(pygame,'init',side_effect=init):
    app.main(max_frames=2,start_mode='defense')
assert order[:2]==['pre','init'],order
assert not pygame.get_init()
'''
        env = dict(os.environ, SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy", PYGAME_HIDE_SUPPORT_PROMPT="1")
        result = subprocess.run([sys.executable, "-c", script], cwd=Path(__file__).resolve().parents[1],
                                env=env, capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

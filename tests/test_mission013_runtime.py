"""Contratos desktop/web da M013, executados sem janela ou dispositivo real."""

import os
from pathlib import Path
import subprocess
import sys
import textwrap
import unittest


ROOT = Path(__file__).resolve().parents[1]


class RuntimeAsyncTests(unittest.TestCase):
    def run_script(self, script):
        env = os.environ.copy()
        env.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy",
                   PYGAME_HIDE_SUPPORT_PROMPT="1")
        result = subprocess.run([sys.executable, "-c", textwrap.dedent(script)],
                                cwd=ROOT, env=env, capture_output=True,
                                text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_importacao_expoe_coroutine_sem_importar_pygame(self):
        self.run_script('''
            import builtins
            import inspect
            original = builtins.__import__
            def checked(name, *args, **kwargs):
                if name == 'pygame' or name.startswith('pygame.'):
                    raise AssertionError('importacao inicializou Pygame')
                return original(name, *args, **kwargs)
            builtins.__import__ = checked
            from game.main import main, main_async
            assert callable(main)
            assert inspect.iscoroutinefunction(main_async)
        ''')

    def test_wrapper_desktop_encaminha_argumentos_e_executa_coroutine(self):
        self.run_script('''
            from unittest.mock import AsyncMock, patch
            from game import main as app
            with patch.object(app, 'main_async', new_callable=AsyncMock) as run:
                app.main(max_frames=2, capture_path='frame.png', start_mode='defense')
                run.assert_awaited_once_with(max_frames=2, capture_path='frame.png', start_mode='defense')
        ''')

    def test_loop_web_cede_controle_e_nao_bloqueia_clock(self):
        self.run_script('''
            import asyncio
            import sys
            import pygame
            from unittest.mock import AsyncMock, Mock, patch
            from game import main as app
            async def check():
                clock = Mock()
                clock.tick.return_value = 17
                sleep = asyncio.sleep
                turns = []
                async def observer():
                    for index in range(3):
                        turns.append(index)
                        await sleep(0)
                with patch.object(sys, 'platform', 'emscripten'), patch.object(pygame.time, 'Clock', return_value=clock), patch.object(app.asyncio, 'sleep', new_callable=AsyncMock, wraps=sleep) as yielded:
                    task = asyncio.create_task(observer())
                    await app.main_async(max_frames=4)
                    assert yielded.await_count >= 4, yielded.await_count
                    assert all(0 <= call.args[0] <= 1/60 for call in yielded.await_args_list)
                    assert len(turns) == 3, turns
                    assert clock.tick.call_count == 4
                    assert all(call.args == (0,) for call in clock.tick.call_args_list)
                    await task
                assert not pygame.get_init()
            asyncio.run(check())
        ''')

    def test_desktop_mantem_limite_60fps_e_loop_de_musica_unico(self):
        self.run_script('''
            import pygame
            from unittest.mock import Mock, patch
            from game import main as app
            clock = Mock()
            clock.tick.return_value = 17
            with patch.object(pygame.time, 'Clock', return_value=clock), patch.object(pygame.mixer.music, 'play') as play:
                app.main(max_frames=3, start_mode='defense')
                assert clock.tick.call_count == 3
                assert all(call.args == (60,) for call in clock.tick.call_args_list)
                play.assert_called_once_with(loops=-1)
            assert not pygame.get_init()
        ''')

    def test_sem_dispositivo_audio_ainda_renderiza_e_encerra(self):
        self.run_script('''
            import asyncio
            import pygame
            from unittest.mock import patch
            from game import main as app
            with patch.object(pygame.mixer, 'get_init', return_value=None), patch.object(pygame.mixer, 'init', side_effect=pygame.error('dispositivo ausente')):
                asyncio.run(app.main_async(max_frames=2, start_mode='laboratory'))
            assert not pygame.get_init()
        ''')

    def test_web_inicia_musica_apos_gesto_e_nao_reinicia_a_cada_tecla(self):
        self.run_script('''
            import asyncio
            import sys
            import pygame
            from unittest.mock import patch
            from game import main as app
            frames = 0
            def events():
                global frames
                frames += 1
                if frames <= 2:
                    assert play.call_count == 0
                else:
                    assert play.call_count == 1
                if frames in (2, 3):
                    return [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)]
                return []
            async def check():
                with patch.object(sys, 'platform', 'emscripten'), patch.object(pygame.event, 'get', side_effect=events):
                    await app.main_async(max_frames=4)
            with patch.object(pygame.mixer.music, 'play') as play:
                asyncio.run(check())
                play.assert_called_once_with(loops=-1)
            assert not pygame.get_init()
        ''')


if __name__ == '__main__':
    unittest.main()

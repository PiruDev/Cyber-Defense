import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import Mock

from game.main import desenhar_hud
from game.progression import Progressao


class HudTests(unittest.TestCase):
    def test_hud_mostra_estado_atual_e_atualiza_apos_subir(self):
        jogador = Progressao(hp=35)
        tela = Mock()
        fonte = Mock()
        desenhar_hud(tela, fonte, jogador)
        self.assertEqual(
            [chamada.args[0] for chamada in fonte.render.call_args_list],
            ["Nível: 1", "XP: 0/100", "HP: 35/100", "Dano: 1"],
        )
        self.assertEqual(tela.blit.call_count, 4)
        self.assertEqual(jogador.hp, 35)

        fonte.reset_mock()
        tela.reset_mock()
        jogador.ganhar_xp(125)
        desenhar_hud(tela, fonte, jogador)
        self.assertEqual(
            [chamada.args[0] for chamada in fonte.render.call_args_list],
            ["Nível: 2", "XP: 25/150", "HP: 120/120", "Dano: 2"],
        )
        self.assertEqual(tela.blit.call_count, 4)
        self.assertEqual((jogador.nivel, jogador.xp, jogador.hp), (2, 25, 120))

    def test_importacao_independe_de_pygame_e_nao_abre_loop(self):
        script = (
            "import builtins\n"
            "original = builtins.__import__\n"
            "def verificar(nome, *args, **kwargs):\n"
            "    if nome == 'pygame' or nome.startswith('pygame.'):\n"
            "        raise AssertionError('pygame importado fora de main')\n"
            "    return original(nome, *args, **kwargs)\n"
            "builtins.__import__ = verificar\n"
            "import game.main\n"
            "assert callable(game.main.main)\n"
        )
        resultado = subprocess.run(
            [sys.executable, "-c", script],
            cwd=Path(__file__).resolve().parents[1],
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(resultado.returncode, 0, resultado.stderr)


@unittest.skipUnless(importlib.util.find_spec("pygame"), "Pygame não instalado")
class IntegracaoPygameTests(unittest.TestCase):
    def test_main_renderiza_e_encerra_com_quit_em_modo_headless(self):
        # Processo isolado e timeout impedem um loop infinito de prender a suíte.
        script = (
            "import pygame\n"
            "from unittest.mock import patch\n"
            "from game import main as aplicativo\n"
            "desenhar = aplicativo.desenhar_hud\n"
            "with patch.object(pygame.event, 'get', side_effect=[[], [pygame.event.Event(pygame.QUIT)]]) as eventos, "
            "patch.object(aplicativo, 'desenhar_hud', wraps=desenhar) as hud:\n"
            "    aplicativo.main(start_mode='defense')\n"
            "    assert eventos.call_count == 2\n"
            "    assert hud.call_count >= 1\n"
            "assert not pygame.get_init()\n"
            "assert not pygame.display.get_init()\n"
        )
        ambiente = os.environ.copy()
        ambiente.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy", PYGAME_HIDE_SUPPORT_PROMPT="1")
        resultado = subprocess.run(
            [sys.executable, "-c", script],
            cwd=Path(__file__).resolve().parents[1],
            env=ambiente,
            capture_output=True,
            text=True,
            timeout=15,
        )
        self.assertEqual(resultado.returncode, 0, resultado.stdout + resultado.stderr)


if __name__ == "__main__":
    unittest.main()

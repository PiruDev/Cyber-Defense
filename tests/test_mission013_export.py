"""A exportação publica apenas código e assets necessários ao jogo."""

import importlib.util
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


def builder():
    spec = importlib.util.spec_from_file_location('mission013_build', ROOT / 'scripts/build_web.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class WebExportTests(unittest.TestCase):
    def test_stage_preserva_paths_runtime_e_exclui_arquivos_privados(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            project = base / 'project'
            staging = project / 'build/web-src'
            # Usa um projeto real como base; os arquivos privados são sentinelas.
            import shutil
            for directory in ('game', 'assets', 'web'):
                shutil.copytree(ROOT / directory, project / directory)
            # Exportação deve preservar o caminho, sem depender do DSP da faixa.
            (project / 'assets/audio/theme.ogg').write_bytes(b'OGG_TEST_AUDIO_FIXTURE')
            private = ('.env', '.env.production', 'credentials.json', 'reports/private.md',
                       '.git/config', '.codex/auth.json', 'game/__pycache__/main.pyc',
                       'game/private/token.txt', 'assets/audio/private.key')
            for name in private:
                path = project / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('PRIVATE_SENTINEL_DO_NOT_EXPORT', encoding='utf-8')
            exported = builder().stage_project(project, staging)
            self.assertIn('game/main.py', exported)
            self.assertIn('assets/audio/theme.ogg', exported)
            self.assertNotIn('assets/audio/theme.wav', exported)
            self.assertIn('assets/sprites/enemies/manifest.json', exported)
            self.assertTrue(any(name.endswith('.png') for name in exported))
            for name in exported:
                self.assertNotIn('\\', name)
                self.assertFalse(Path(name).is_absolute())
                self.assertNotIn('..', Path(name).parts)
                self.assertNotIn(name, private)
            for path in staging.rglob('*'):
                if path.is_file():
                    self.assertNotIn(b'PRIVATE_SENTINEL_DO_NOT_EXPORT', path.read_bytes(), str(path))

    def test_export_inexistente_e_recusado(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises((ValueError, RuntimeError, FileNotFoundError)):
                builder().validate_export(Path(temporary))

    def test_stage_recusa_limpeza_fora_diretorio_gerado(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            valuable = root / 'meus-arquivos'
            valuable.mkdir()
            sentinel = valuable / 'preservar.txt'
            sentinel.write_text('preservar', encoding='utf-8')
            with self.assertRaises(ValueError):
                builder().stage_project(root, valuable)
            self.assertEqual(sentinel.read_text(encoding='utf-8'), 'preservar')


if __name__ == '__main__':
    unittest.main()

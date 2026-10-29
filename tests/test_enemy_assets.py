"""Contrato físico dos recursos inimigos, independente da integração gráfica."""

import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import unittest


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets/sprites/enemies"
KINDS = {"basic", "swordsman", "archer", "worm_head", "worm_body", "worm_tail", "rootkit"}
PLAYER_SHA256 = "1b6ba716b67876fa32fedde73ab1a38352d08991a2e3acbe58473b13884dde35"
REQUIRED_STATES = {
    "basic": {"idle", "move", "hurt", "death"},
    "swordsman": {"idle", "move", "windup", "attack", "hurt", "death"},
    "archer": {"idle", "move", "windup", "attack", "hurt", "death"},
    "worm_head": {"move", "hurt", "rupture", "new_head", "death"},
    "worm_body": {"move", "hurt", "rupture"},
    "worm_tail": {"move", "hurt", "rupture"},
    "rootkit": {"idle", "move", "windup", "attack", "hurt", "death"},
}


class EnemyManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ASSETS / "manifest.json").read_text(encoding="utf-8"))

    def test_manifesto_cobre_tipos_e_caminhos_reais_sem_escapar_da_pasta(self):
        self.assertEqual(self.manifest["version"], 1)
        self.assertEqual(set(self.manifest["types"]), KINDS)
        files = set()
        for kind, spec in self.manifest["types"].items():
            with self.subTest(kind=kind):
                width, height = spec["frame_size"]
                self.assertEqual(width, height)
                expected = (96,) if kind == "rootkit" else (64,) if kind.startswith("worm_") else (48, 64) if kind == "swordsman" else (48,)
                self.assertIn(width, expected)
                self.assertEqual(spec["pivot"], [width // 2, height // 2])
                self.assertEqual(spec["facing"], "east")
                self.assertGreaterEqual(len(spec["palette"]), 4)
                self.assertTrue(all(isinstance(color, str) and len(color) == 7 and color.startswith("#")
                                    for color in spec["palette"]))
                self.assertTrue(spec["states"])
                for state, clip in spec["states"].items():
                    path = (ASSETS / clip["file"]).resolve()
                    self.assertTrue(path.is_relative_to(ASSETS.resolve()))
                    self.assertEqual(path.suffix, ".png")
                    self.assertTrue(path.is_file(), str(path))
                    files.add(path)
                    self.assertIsInstance(clip["frames"], int)
                    self.assertGreaterEqual(clip["frames"], 2)
                    self.assertEqual(len(clip["durations_ms"]), clip["frames"])
                    self.assertTrue(all(isinstance(t, (int, float)) and t > 0 for t in clip["durations_ms"]))
                    self.assertIsInstance(clip["loop"], bool)
        self.assertEqual(files, set(path.resolve() for path in ASSETS.rglob("*.png")))

    def test_estados_cobrem_animacoes_reais_sem_inventar_ataque_do_virus(self):
        for kind, required in REQUIRED_STATES.items():
            with self.subTest(kind=kind):
                self.assertTrue(required.issubset(self.manifest["types"][kind]["states"]))
        self.assertNotIn("attack", self.manifest["types"]["basic"]["states"])
        self.assertNotIn("windup", self.manifest["types"]["basic"]["states"])

    def test_png_jogador_original_preservado_sem_depender_de_reports(self):
        # A arte do jogador ainda aguarda aprovação; reports/ não é versionado.
        player = ROOT / "assets/sprites/player/sentinel_idle.png"
        self.assertEqual(hashlib.sha256(player.read_bytes()).hexdigest(), PLAYER_SHA256)

    @unittest.skipUnless(importlib.util.find_spec("pygame"), "Pygame não instalado")
    def test_png_rgba_alfa_binario_frames_preenchidos_e_margens(self):
        import pygame

        for kind, spec in self.manifest["types"].items():
            width, height = spec["frame_size"]
            palette = {tuple(bytes.fromhex(color[1:])) for color in spec["palette"]}
            for state, clip in spec["states"].items():
                with self.subTest(kind=kind, state=state):
                    path = ASSETS / clip["file"]
                    data = path.read_bytes()
                    self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
                    self.assertEqual(struct.unpack(">IIBB", data[16:26]), (width * clip["frames"], height, 8, 6))
                    sheet = pygame.image.load(str(path))
                    self.assertEqual(sheet.get_size(), (width * clip["frames"], height))
                    frame_signatures = set()
                    for index in range(clip["frames"]):
                        frame = sheet.subsurface((index * width, 0, width, height))
                        frame_signatures.add(hashlib.sha256(pygame.image.tostring(frame, "RGBA")).digest())
                        pixels = {tuple(frame.get_at((x, y))) for x in range(width) for y in range(height)}
                        alphas = {pixel[3] for pixel in pixels}
                        self.assertEqual(alphas, {0, 255})
                        opaque_colors = {pixel[:3] for pixel in pixels if pixel[3]}
                        self.assertTrue(opaque_colors.issubset(palette), "Cores fora da paleta declarada")
                        bounds = frame.get_bounding_rect()
                        self.assertGreater(bounds.width, 0)
                        self.assertGreater(bounds.height, 0)
                        self.assertGreater(bounds.left, 0)
                        self.assertGreater(bounds.top, 0)
                        self.assertLess(bounds.right, width)
                        self.assertLess(bounds.bottom, height)
                    self.assertGreater(len(frame_signatures), 1, "A animação repete apenas um frame estático")


if __name__ == "__main__":
    unittest.main()

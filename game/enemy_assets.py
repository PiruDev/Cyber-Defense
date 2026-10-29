"""Biblioteca lazy de PNGs; falhas locais usam o fallback do renderizador."""

import json
from math import cos, isfinite, pi, sin
from pathlib import Path

from .enemy_animation import direction_quantized, frame_index


class AssetLibrary:
    """Cache por sheet/frame/direção/tint: nenhum carregamento por quadro."""

    def __init__(self, manifest_path=None):
        self.manifest_path = (Path(manifest_path).resolve() if manifest_path is not None else
                              Path(__file__).resolve().parents[1] / "assets/sprites/enemies/manifest.json")
        self.clear()

    def clear(self):
        self._specs = None
        self._sheets = {}
        self._images = {}

    def _load_manifest(self):
        if self._specs is not None:
            return
        self._specs = {}
        try:
            document = json.loads(self.manifest_path.read_text(encoding="utf-8-sig"))
            if (not isinstance(document, dict) or document.get("version") != 1
                    or not isinstance(document.get("types"), dict)):
                return
            for kind, definition in document["types"].items():
                try:
                    if (not isinstance(definition, dict)
                            or not isinstance(definition.get("states"), dict)):
                        continue
                    width, height = definition["frame_size"]
                    pivot = tuple(definition["pivot"])
                    if (any(isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 512
                            for value in (width, height)) or len(pivot) != 2
                            or not all(isfinite(value) for value in pivot)
                            or not 0 <= pivot[0] < width or not 0 <= pivot[1] < height
                            or definition.get("facing") != "east"):
                        continue
                    for state, entry in definition["states"].items():
                        count = entry["frames"]
                        durations = tuple(entry["durations_ms"])
                        path = (self.manifest_path.parent / entry["file"]).resolve()
                        if (isinstance(count, bool) or not isinstance(count, int) or not 1 <= count <= 64
                                or len(durations) != count or not all(isfinite(value) and value > 0 for value in durations)
                                or not isinstance(entry["loop"], bool)
                                or not path.is_relative_to(self.manifest_path.parent)):
                            continue
                        self._specs[kind, state] = (width, height, pivot, path, count, durations, entry["loop"])
                except (KeyError, TypeError, ValueError, OverflowError):
                    continue
        except (OSError, ValueError, TypeError):
            # O jogo continua mesmo se o manifesto inteiro estiver indisponível.
            return

    def duration(self, kind, state):
        self._load_manifest()
        entry = self._specs.get((kind, state))
        return sum(entry[5]) if entry is not None else 0.0

    def _load_sheet(self, key, definition):
        if key in self._sheets:
            return self._sheets[key]
        self._sheets[key] = None
        try:
            import pygame

            width, height, _, path, count, _, _ = definition
            sheet = pygame.image.load(str(path))
            if sheet.get_size() != (width * count, height):
                return None
            if pygame.display.get_surface() is not None:
                sheet = sheet.convert_alpha()
            self._sheets[key] = tuple(sheet.subsurface((index * width, 0, width, height)).copy()
                                      for index in range(count))
        except (OSError, ValueError, RuntimeError, ImportError):
            return None
        except Exception:
            # pygame.error pode variar entre erro de codec e de dispositivo.
            return None
        return self._sheets[key]

    def frame(self, kind, state, phase_ms, angle, *, flash=False, scale=1.0):
        self._load_manifest()
        definition = self._specs.get((kind, state))
        if (definition is None or not isfinite(phase_ms) or not isfinite(angle)
                or not isfinite(scale) or scale <= 0 or scale > 4):
            return None
        images = self._load_sheet((kind, state), definition)
        if images is None:
            return None
        width, height, pivot, _, _, durations, loop = definition
        index, direction = frame_index(phase_ms, durations, loop), direction_quantized(angle)
        cache_key = kind, state, index, direction, bool(flash), scale
        if cache_key not in self._images:
            import pygame

            image = images[index]
            if flash:
                # Soma luz sem tocar no alfa binário nem na superfície original.
                image = image.copy()
                image.fill((95, 95, 95, 0), special_flags=pygame.BLEND_RGB_ADD)
            radians = direction * pi / 4
            if direction:
                image = pygame.transform.rotate(image, -direction * 45)
            dx, dy = pivot[0] - width / 2, pivot[1] - height / 2
            rotated_pivot = (image.get_width() / 2 + dx * cos(radians) - dy * sin(radians),
                             image.get_height() / 2 + dx * sin(radians) + dy * cos(radians))
            if scale != 1:
                old_width, old_height = image.get_size()
                image = pygame.transform.scale(image, (round(old_width * scale), round(old_height * scale)))
                rotated_pivot = (rotated_pivot[0] * image.get_width() / old_width,
                                 rotated_pivot[1] * image.get_height() / old_height)
            self._images[cache_key] = image, rotated_pivot
        return self._images[cache_key]


_library = None


def get_library():
    global _library
    if _library is None:
        _library = AssetLibrary()
    return _library

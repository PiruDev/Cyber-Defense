r"""Prepara a arte original gerada em um PNG de jogo 48x48, sem janela.

Usa somente Pygame já disponível no projeto. Não altera a imagem-fonte.
Execute da raiz: .\.venv\Scripts\python.exe assets/references/prepare_sentinel.py
Os dois destinos devem estar ausentes; use --overwrite apenas para regenerá-los.
"""

from argparse import ArgumentParser
from pathlib import Path

import pygame


PALETTE = (
    (7, 16, 31), (16, 35, 59), (30, 61, 90), (54, 91, 125),
    (61, 115, 184), (73, 233, 245), (172, 247, 255), (226, 247, 255),
    (112, 69, 166), (172, 114, 219), (52, 35, 79), (20, 44, 70),
)


def prepare(*, overwrite=False):
    references = Path(__file__).resolve().parent
    root = references.parents[1]
    source_path = references / "sentinel_idle_generated.png"
    sprite_path = root / "assets" / "sprites" / "player" / "sentinel_idle.png"
    preview_path = references / "sentinel_idle_preview.png"
    for destination in (sprite_path, preview_path):
        if destination.exists() and not overwrite:
            raise FileExistsError(f"Destino existente preservado: {destination}")
    source = pygame.image.load(str(source_path))
    bounds = source.get_bounding_rect(min_alpha=128)
    if not bounds.width or not bounds.height:
        raise ValueError("A imagem-fonte não contém uma silhueta opaca.")
    ratio = min(36 / bounds.width, 40 / bounds.height)
    fitted = (max(1, round(bounds.width * ratio)), max(1, round(bounds.height * ratio)))
    # scale usa nearest-neighbor; não usar smoothscale em arte de pixel.
    reduced = pygame.transform.scale(source.subsurface(bounds), fitted)
    sprite = pygame.Surface((48, 48), pygame.SRCALPHA, 32)
    offset_x, offset_y = (48 - fitted[0]) // 2, (48 - fitted[1]) // 2
    for y in range(fitted[1]):
        for x in range(fitted[0]):
            pixel = reduced.get_at((x, y))
            if pixel.a < 128:
                continue
            nearest = min(PALETTE, key=lambda color:
                2 * (pixel.r - color[0]) ** 2
                + 3 * (pixel.g - color[1]) ** 2
                + (pixel.b - color[2]) ** 2)
            sprite.set_at((x + offset_x, y + offset_y), (*nearest, 255))
    sprite_path.parent.mkdir(parents=True, exist_ok=True)
    pygame.image.save(sprite, str(sprite_path))
    preview = pygame.transform.scale(sprite, (384, 384))
    pygame.image.save(preview, str(preview_path))
    opaque = {tuple(sprite.get_at((x, y))) for y in range(48) for x in range(48)
              if sprite.get_at((x, y)).a}
    print(f"Sprite: {sprite_path.relative_to(root).as_posix()} / 48x48 RGBA")
    print(f"Prévia: {preview_path.relative_to(root).as_posix()} / 384x384 nearest 8x")
    print(f"Silhueta: {sprite.get_bounding_rect()} / {len(opaque)} cores opacas")


if __name__ == "__main__":
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--overwrite", action="store_true")
    prepare(overwrite=parser.parse_args().overwrite)

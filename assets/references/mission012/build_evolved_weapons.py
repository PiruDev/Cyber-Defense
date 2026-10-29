"""Original procedural pixel art for Cyber Defense; uses only installed Pygame."""

import json
from pathlib import Path

import pygame


ROOT = Path(__file__).resolve().parents[3]
OUTPUT = ROOT / "assets/sprites/weapons"
REFERENCE = Path(__file__).resolve().parent
OUTLINE = (7, 16, 31)
NAVY = (16, 35, 59)
ARMOR = (30, 61, 90)
STEEL = (54, 91, 125)
CYAN = (73, 233, 245)
ICE = (172, 247, 255)
WHITE = (226, 247, 255)
PURPLE = (112, 69, 166)
VIOLET = (172, 114, 219)


def longbow():
    image = pygame.Surface((54, 54), pygame.SRCALPHA)
    upper = [(19, 4), (26, 7), (30, 13), (34, 18), (36, 24)]
    lower = [(36, 29), (34, 35), (30, 40), (26, 46), (19, 49)]
    for points in (upper, lower):
        pygame.draw.lines(image, OUTLINE, False, points, 7)
        pygame.draw.lines(image, ARMOR, False, points, 5)
        pygame.draw.lines(image, CYAN, False, points, 2)
    # Recurved digital tips and separate narrow string.
    pygame.draw.lines(image, VIOLET, False, [(17, 8), (17, 3), (22, 3)], 2)
    pygame.draw.lines(image, VIOLET, False, [(17, 45), (17, 50), (22, 50)], 2)
    pygame.draw.lines(image, PURPLE, False, [(19, 5), (12, 26), (19, 48)], 1)
    pygame.draw.line(image, ICE, (19, 6), (19, 47), 1)
    # Grip and recovery-data coils, kept detached from the string silhouette.
    pygame.draw.rect(image, OUTLINE, (31, 20, 10, 14))
    pygame.draw.rect(image, NAVY, (32, 21, 8, 12))
    pygame.draw.rect(image, PURPLE, (35, 22, 4, 10))
    pygame.draw.line(image, VIOLET, (36, 22), (36, 30), 1)
    pygame.draw.rect(image, CYAN, (32, 25, 3, 4))
    pygame.draw.rect(image, WHITE, (33, 26, 2, 2))
    # Terminal circuitry signals piercing capability without a broad glow.
    for x, y in ((26, 9), (30, 15), (30, 39), (26, 44)):
        pygame.draw.rect(image, OUTLINE, (x-2, y-2, 5, 5))
        pygame.draw.rect(image, PURPLE, (x-1, y-1, 3, 3))
        image.set_at((x, y), ICE)
    return image


def returning_spear():
    image = pygame.Surface((112, 22), pygame.SRCALPHA)
    # Constant-width shaft and segmented copperless cyber grip.
    pygame.draw.rect(image, OUTLINE, (4, 7, 85, 9))
    pygame.draw.rect(image, NAVY, (6, 8, 80, 7))
    pygame.draw.line(image, STEEL, (10, 8), (83, 8), 1)
    pygame.draw.line(image, CYAN, (13, 10), (84, 10), 2)
    for x in (19, 25, 31, 37):
        pygame.draw.line(image, PURPLE, (x, 8), (x, 14), 2)
        image.set_at((x, 9), VIOLET)
    # Return transmitter at the butt, visually distinct from the common spear.
    pygame.draw.polygon(image, OUTLINE, [(2,11),(7,5),(14,5),(18,11),(14,17),(7,17)])
    pygame.draw.polygon(image, PURPLE, [(4,11),(8,7),(13,7),(16,11),(13,15),(8,15)])
    pygame.draw.line(image, VIOLET, (7, 10), (13, 10), 2)
    pygame.draw.rect(image, ICE, (8, 10, 3, 3))
    # Pronged energy blade; clear east-facing point and hooked return collar.
    outline = [(76,5),(86,5),(92,1),(110,11),(92,20),(86,16),(76,16),(82,11)]
    pygame.draw.polygon(image, OUTLINE, outline)
    pygame.draw.polygon(image, PURPLE, [(79,6),(87,6),(92,3),(106,11),(92,18),(87,15),(79,15),(85,11)])
    pygame.draw.polygon(image, CYAN, [(88,7),(93,5),(106,11),(93,16),(88,14),(94,11)])
    pygame.draw.line(image, WHITE, (93, 7), (105, 11), 1)
    pygame.draw.line(image, ICE, (90, 9), (102, 11), 2)
    pygame.draw.line(image, ARMOR, (84, 7), (84, 14), 2)
    return image


def validate(image, size):
    assert image.get_size() == size
    colors = {tuple(image.get_at((x, y))) for x in range(size[0]) for y in range(size[1])}
    assert {color[3] for color in colors} == {0, 255}
    assert len({color[:3] for color in colors if color[3]}) <= 12
    assert image.get_at((0, 0)).a == 0
    bounds = image.get_bounding_rect()
    assert 0 < bounds.left and 0 < bounds.top
    assert bounds.right < size[0] and bounds.bottom < size[1]


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    assets = [("longbow.png", longbow(), (54, 54), (27, 27)),
              ("returning_spear.png", returning_spear(), (112, 22), (56, 11))]
    entries = []
    for name, image, size, pivot in assets:
        validate(image, size)
        path = OUTPUT / name
        pygame.image.save(image, str(path))
        loaded = pygame.image.load(str(path))
        validate(loaded, size)
        entries.append({"file": path.relative_to(ROOT).as_posix(), "size": size,
                        "pivot": pivot, "facing": "east", "frames": 1,
                        "alpha": [0, 255], "nearest_neighbor": True})
    (REFERENCE / "asset_manifest.json").write_text(
        json.dumps({"author": "AgentOS pixel_artist", "assets": entries}, indent=2), encoding="utf-8")
    preview = pygame.Surface((800, 450))
    preview.fill((5, 9, 22))
    preview.blit(pygame.transform.scale(assets[0][1], (216, 216)), (34, 26))
    preview.blit(pygame.transform.scale(assets[1][1], (448, 88)), (300, 90))
    # Native-size counterparts show the expected in-game detail.
    preview.blit(assets[0][1], (112, 320))
    preview.blit(assets[1][1], (470, 336))
    pygame.image.save(preview, str(REFERENCE / "evolved_weapons_preview.png"))
    print(json.dumps(entries))


if __name__ == "__main__":
    main()

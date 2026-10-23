#!/usr/bin/env python3
"""Generate the original pixel-art textures and icons used by TI-ConnectMC.

Everything here is drawn procedurally (no game assets). Re-run after tweaking:

    python3 webtilp/mc/tools/make_textures.py

Outputs 16x16 tiles in webtilp/mc/textures/ (scaled up in CSS with
image-rendering: pixelated) and replaces the favicon / app icons in webtilp/.
"""

from pathlib import Path
import random

from PIL import Image

HERE = Path(__file__).resolve().parent
WEBTILP = HERE.parent.parent
TEXTURES = WEBTILP / 'mc' / 'textures'

SIZE = 16


def hex_rgb(value):
    value = value.lstrip('#')
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def speckle(seed, base, palette, weights, clump=0.35):
    """Noise tile: pick palette colours, then let neighbours bleed for clumps."""
    rng = random.Random(seed)
    colors = [hex_rgb(c) for c in palette]
    grid = [[hex_rgb(base) for _ in range(SIZE)] for _ in range(SIZE)]
    for y in range(SIZE):
        for x in range(SIZE):
            grid[y][x] = rng.choices(colors, weights)[0]
    for y in range(SIZE):
        for x in range(SIZE):
            if rng.random() < clump:
                nx, ny = (x + rng.choice((-1, 1))) % SIZE, (y + rng.choice((-1, 0, 1))) % SIZE
                grid[y][x] = grid[ny][nx]
    return grid


def to_image(grid):
    img = Image.new('RGBA', (SIZE, SIZE))
    for y, row in enumerate(grid):
        for x, color in enumerate(row):
            img.putpixel((x, y), color + (255,) if len(color) == 3 else color)
    return img


def dirt():
    return speckle(1, '#7a5638',
                   ['#866043', '#79553a', '#5e412b', '#9a7454', '#6b4b31', '#4f3624'],
                   [30, 28, 14, 10, 14, 4])


def deepslate():
    rng = random.Random(7)
    grid = speckle(2, '#3d3d44',
                   ['#3d3d44', '#34343a', '#474750', '#2b2b30', '#505058'],
                   [34, 26, 18, 12, 6], clump=0.15)
    # Horizontal strata streaks.
    for y in (3, 8, 12):
        start = rng.randrange(SIZE)
        for i in range(rng.randrange(5, 10)):
            grid[y][(start + i) % SIZE] = hex_rgb('#29292e')
    return grid


def stone():
    return speckle(3, '#7d7d7d',
                   ['#828282', '#777777', '#8f8f8f', '#6d6d6d', '#9a9a9a'],
                   [30, 30, 16, 16, 8], clump=0.3)


def blackstone():
    return speckle(4, '#2e2c33',
                   ['#2e2c33', '#28262c', '#38353d', '#222025', '#413e47'],
                   [32, 26, 18, 14, 10], clump=0.3)


def grass_edge():
    """Grass-topped dirt, used as the header's bottom strip."""
    rng = random.Random(6)
    grid = dirt()
    greens = [hex_rgb(c) for c in ('#5c9a37', '#4f8a2e', '#6aad40', '#447a27')]
    for x in range(SIZE):
        depth = 3 + (1 if rng.random() < 0.5 else 0) + (1 if rng.random() < 0.2 else 0)
        for y in range(depth):
            grid[y][x] = rng.choice(greens)
    return grid


def calculator_icon():
    """16x16 grass-topped calculator: the TI-ConnectMC app icon."""
    o = None  # transparent
    body, edge, lcd, ink = '#3b3c46', '#24252c', '#a9c46c', '#2f4a1c'
    key, key_hi, enter = '#71727f', '#9b9ca8', '#d9a13a'
    g1, g2, g3 = '#5c9a37', '#4f8a2e', '#6aad40'
    rows = [
        [o,  g1, g3, g1, g2, g3, g1, g1, g2, g3, g1, g2, g3, g1, g2, o],
        [g2, g1, g2, g3, g1, g1, g2, g3, g1, g1, g2, g3, g1, g1, g3, g1],
        [g1, g3, body, g1, g2, body, g3, g1, body, g2, g1, body, g3, g1, body, g2],
        [edge, body, body, body, body, body, body, body, body, body, body, body, body, body, body, edge],
        [edge, body, lcd, lcd, lcd, lcd, lcd, lcd, lcd, lcd, lcd, lcd, lcd, lcd, body, edge],
        [edge, body, lcd, ink, lcd, lcd, lcd, lcd, lcd, lcd, lcd, lcd, ink, lcd, body, edge],
        [edge, body, lcd, lcd, ink, lcd, lcd, lcd, lcd, lcd, lcd, ink, lcd, lcd, body, edge],
        [edge, body, lcd, lcd, lcd, ink, ink, lcd, lcd, ink, ink, lcd, lcd, lcd, body, edge],
        [edge, body, lcd, lcd, lcd, lcd, lcd, ink, ink, lcd, lcd, lcd, lcd, lcd, body, edge],
        [edge, body, body, body, body, body, body, body, body, body, body, body, body, body, body, edge],
        [edge, body, key_hi, key, body, key_hi, key, body, key_hi, key, body, enter, enter, enter, body, edge],
        [edge, body, body, body, body, body, body, body, body, body, body, body, body, body, body, edge],
        [edge, body, key_hi, key, body, key_hi, key, body, key_hi, key, body, key_hi, key, key, body, edge],
        [edge, body, body, body, body, body, body, body, body, body, body, body, body, body, body, edge],
        [edge, body, key_hi, key, body, key_hi, key, body, key_hi, key, body, key_hi, key, key, body, edge],
        [o,  edge, edge, edge, edge, edge, edge, edge, edge, edge, edge, edge, edge, edge, edge, o],
    ]
    img = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    for y, row in enumerate(rows):
        for x, color in enumerate(row):
            if color:
                img.putpixel((x, y), hex_rgb(color) + (255,))
    return img


def scaled(img, size):
    return img.resize((size, size), Image.NEAREST)


def main():
    TEXTURES.mkdir(parents=True, exist_ok=True)
    tiles = {
        'dirt': dirt(), 'deepslate': deepslate(), 'stone': stone(),
        'blackstone': blackstone(), 'grass-edge': grass_edge(),
    }
    for name, grid in tiles.items():
        to_image(grid).save(TEXTURES / f'{name}.png', optimize=True)

    icon = calculator_icon()
    icon.save(TEXTURES / 'calculator.png', optimize=True)
    scaled(icon, 16).save(WEBTILP / 'favicon-16x16.png', optimize=True)
    scaled(icon, 32).save(WEBTILP / 'favicon-32x32.png', optimize=True)
    scaled(icon, 192).save(WEBTILP / 'android-chrome-192x192.png', optimize=True)
    scaled(icon, 512).save(WEBTILP / 'android-chrome-512x512.png', optimize=True)
    # Apple touch icons should be opaque: put the icon on a dirt backdrop.
    touch = to_image(dirt()).convert('RGBA')
    touch.alpha_composite(icon)
    scaled(touch, 180).convert('RGB').save(WEBTILP / 'apple-touch-icon.png', optimize=True)
    scaled(icon, 48).save(WEBTILP / 'favicon.ico', sizes=[(16, 16), (32, 32), (48, 48)])
    print(f'Wrote {len(tiles) + 1} textures to {TEXTURES} and app icons to {WEBTILP}')


if __name__ == '__main__':
    main()

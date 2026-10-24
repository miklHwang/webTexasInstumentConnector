#!/usr/bin/env python3
"""Generate the per-theme app icons for TI-ConnectMC.

Each icon set shows the same simple calculator glyph in its theme's style.
The page links the set that matches the user's default theme (see
app-icon.js); the Minecraft set is the pixel-art icon at the site root,
made by mc/tools/make_textures.py. Everything is drawn here, so re-run after
tweaking:

    python3 webtilp/themes/tools/make_icons.py

Writes themes/icons/<set>/ with the same file names as the root icons, plus
a site.webmanifest that points at them. Needs Pillow.
"""

import json
import math
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
WEBTILP = HERE.parent.parent
ICONS = WEBTILP / 'themes' / 'icons'

S = 1024  # drawing size; every output is a downscale of this


def rgba(value, alpha=255):
    value = value.lstrip('#')
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4)) + (alpha,)


# ---------- Shapes (L-mode masks at S x S) ----------

def squircle(margin, n=5.0):
    """Superellipse, the shape of Apple app icons."""
    half = S / 2 - margin
    points = []
    for i in range(720):
        t = i / 720 * 2 * math.pi
        c, s = math.cos(t), math.sin(t)
        x = abs(c) ** (2 / n) * half * (1 if c >= 0 else -1)
        y = abs(s) ** (2 / n) * half * (1 if s >= 0 else -1)
        points.append((S / 2 + x, S / 2 + y))
    mask = Image.new('L', (S, S), 0)
    ImageDraw.Draw(mask).polygon(points, fill=255)
    return mask


def rounded(margin, radius):
    mask = Image.new('L', (S, S), 0)
    ImageDraw.Draw(mask).rounded_rectangle((margin, margin, S - 1 - margin, S - 1 - margin), radius=radius, fill=255)
    return mask


def bevel_points(margin, cut):
    """Square with the top-left and bottom-right corners cut, like the Cyberpunk frames."""
    a, b = margin, S - 1 - margin
    return [(a + cut, a), (b, a), (b, b - cut), (b - cut, b), (a, b), (a, a + cut)]


def bevel(margin, cut):
    mask = Image.new('L', (S, S), 0)
    ImageDraw.Draw(mask).polygon(bevel_points(margin, cut), fill=255)
    return mask


def full():
    return Image.new('L', (S, S), 255)


# ---------- Fills ----------

def solid(color):
    return Image.new('RGBA', (S, S), rgba(color))


def gradient(start, end, diagonal=False):
    """Top-to-bottom (or top-left to bottom-right) linear gradient."""
    a, b = rgba(start), rgba(end)
    ramp = Image.linear_gradient('L')  # 256 x 256, black at the top
    if diagonal:
        ramp = ramp.rotate(45, resample=Image.BICUBIC, expand=True)
        w, h = ramp.size
        ramp = ramp.crop((w // 4, h // 4, w - w // 4, h - h // 4))
    ramp = ramp.resize((S, S), Image.BICUBIC)
    return Image.composite(Image.new('RGBA', (S, S), b), Image.new('RGBA', (S, S), a), ramp)


# ---------- The calculator glyph ----------

def glyph(color, stroke, scale=0.6, accent=None, keys=True):
    """A line-art calculator on a 24-unit grid (Feather style), centred."""
    layer = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    unit = S * scale / 24
    ox = oy = (S - 24 * unit) / 2

    def box(x0, y0, x1, y1):
        return (ox + x0 * unit, oy + y0 * unit, ox + x1 * unit, oy + y1 * unit)

    width = max(1, round(stroke * unit))
    draw.rounded_rectangle(box(4.5, 1.5, 19.5, 22.5), radius=2.6 * unit, outline=rgba(color), width=width)
    draw.rounded_rectangle(box(7.5, 5, 16.5, 9.5), radius=1.2 * unit, outline=rgba(color), width=width)
    if keys:
        dot = 1.25 if stroke < 2.4 else 1.55
        for row, y in enumerate((13.75, 18.25)):
            for col, x in enumerate((8.5, 12, 15.5)):
                fill = rgba(accent) if accent and row == 1 and col == 2 else rgba(color)
                draw.ellipse(box(x - dot, y - dot, x + dot, y + dot), fill=fill)
    return layer


def shift(layer, dx):
    return ImageChops.offset(layer, round(dx), 0)


def tint(layer, color):
    """Recolour a glyph layer, keeping its alpha."""
    out = Image.new('RGBA', layer.size, rgba(color))
    out.putalpha(layer.getchannel('A'))
    return out


def shape_layer(fill, mask):
    out = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    out.paste(fill, (0, 0), mask)
    return out


# ---------- Icon sets ----------
# variant: 'any' (app icons, transparent corners), 'touch' (opaque, full bleed,
# for iOS which applies its own mask), 'small' (16-48 px favicons: no margin,
# heavier strokes).

def modern(variant):
    margin = {'any': 0.055 * S, 'small': 0, 'touch': 0}[variant]
    mask = full() if variant == 'touch' else squircle(margin)
    icon = shape_layer(gradient('#5ac8fa', '#007aff'), mask)
    stroke = 2.6 if variant == 'small' else 1.6
    icon.alpha_composite(glyph('#ffffff', stroke, scale=0.62 if variant != 'small' else 0.74))
    return icon


def cyberpunk(variant):
    margin = {'any': 0.04 * S, 'small': 0, 'touch': 0}[variant]
    cut = 0.2 * S
    mask = full() if variant == 'touch' else bevel(margin, cut)
    icon = shape_layer(solid('#0a0b10'), mask)
    small = variant == 'small'
    if not small:
        # A yellow HUD frame with a tab on top; too fussy for a 16 px favicon.
        draw = ImageDraw.Draw(icon)
        inset = margin + 0.06 * S
        frame = max(2, round(0.022 * S))
        points = bevel_points(inset, cut * 0.75)
        draw.line(points + [points[0]], fill=rgba('#fcee0a'), width=frame, joint='curve')
        draw.rectangle((inset + cut * 0.75 + 0.05 * S, inset - frame * 2, inset + cut * 0.75 + 0.27 * S, inset - frame * 0.5), fill=rgba('#fcee0a'))
    stroke = 2.6 if small else 1.9
    scale = 0.74 if small else 0.5
    base = glyph('#fcee0a', stroke, scale=scale)
    offset = 0.012 * S
    icon.alpha_composite(tint(shift(base, -offset), '#00f0ff'))
    icon.alpha_composite(tint(shift(base, offset), '#ff003c'))
    icon.alpha_composite(base)
    return icon


def aurora(variant):
    margin = {'any': 0.055 * S, 'small': 0, 'touch': 0}[variant]
    mask = full() if variant == 'touch' else rounded(margin, 0.22 * S)
    fill = gradient('#5bd2c3', '#5a8cff', diagonal=True)
    glow = Image.new('RGBA', (S, S), (255, 255, 255, 0))
    ImageDraw.Draw(glow).ellipse((-0.2 * S, -0.35 * S, 0.8 * S, 0.45 * S), fill=(255, 255, 255, 38))
    fill.alpha_composite(glow.filter(ImageFilter.GaussianBlur(0.12 * S)))
    icon = shape_layer(fill, mask)
    stroke = 2.6 if variant == 'small' else 1.8
    icon.alpha_composite(glyph('#0b0f14', stroke, scale=0.62 if variant != 'small' else 0.74))
    return icon


def retro(variant):
    margin = {'any': 0.055 * S, 'small': 0, 'touch': 0}[variant]
    mask = full() if variant == 'touch' else rounded(margin, 0.1 * S)
    icon = shape_layer(solid('#050805'), mask)
    stroke = 2.6 if variant == 'small' else 1.8
    line = glyph('#2fff8f', stroke, scale=0.62 if variant != 'small' else 0.74)
    icon.alpha_composite(tint(line, '#2fff8f').filter(ImageFilter.GaussianBlur(0.025 * S)))
    icon.alpha_composite(line)
    scan = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    draw = ImageDraw.Draw(scan)
    step = max(4, S // 128)
    for y in range(0, S, step):
        draw.rectangle((0, y, S, y + step // 3), fill=(0, 0, 0, 90))
    clipped = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    clipped.paste(scan, (0, 0), mask)
    icon.alpha_composite(clipped)
    return icon


def professional(variant):
    margin = {'any': 0.055 * S, 'small': 0, 'touch': 0}[variant]
    mask = full() if variant == 'touch' else rounded(margin, 0.09 * S)
    icon = shape_layer(solid('#245da8'), mask)
    stroke = 2.6 if variant == 'small' else 1.8
    icon.alpha_composite(glyph('#ffffff', stroke, scale=0.62 if variant != 'small' else 0.74))
    return icon


def minimal(variant):
    margin = {'any': 0.055 * S, 'small': 0, 'touch': 0}[variant]
    mask = full() if variant == 'touch' else rounded(margin, 0.2 * S)
    icon = shape_layer(solid('#2c2d33'), mask)
    inner = full() if variant == 'touch' else rounded(margin + 0.012 * S, 0.19 * S)
    icon.alpha_composite(shape_layer(solid('#1a1b1f'), inner))
    stroke = 2.6 if variant == 'small' else 1.6
    icon.alpha_composite(glyph('#e7e7ea', stroke, scale=0.62 if variant != 'small' else 0.74, accent='#8fa8c4'))
    return icon


# set name -> (drawing function, manifest theme_color, manifest background_color)
SETS = {
    'modern': (modern, '#f5f5f7', '#f5f5f7'),
    'cyberpunk': (cyberpunk, '#07080c', '#07080c'),
    'aurora': (aurora, '#0d1117', '#0d1117'),
    'retro': (retro, '#050805', '#050805'),
    'professional': (professional, '#245da8', '#f3f4f6'),
    'minimal': (minimal, '#121316', '#121316'),
}


def down(img, size):
    return img.resize((size, size), Image.LANCZOS)


def main():
    root_manifest = json.loads((WEBTILP / 'site.webmanifest').read_text(encoding='utf-8'))
    for name, (draw, theme_color, background) in SETS.items():
        out = ICONS / name
        out.mkdir(parents=True, exist_ok=True)
        app = draw('any')
        small = draw('small')
        down(small, 16).save(out / 'favicon-16x16.png', optimize=True)
        down(small, 32).save(out / 'favicon-32x32.png', optimize=True)
        down(small, 48).save(out / 'favicon.ico', sizes=[(16, 16), (32, 32), (48, 48)])
        down(app, 192).save(out / 'android-chrome-192x192.png', optimize=True)
        down(app, 512).save(out / 'android-chrome-512x512.png', optimize=True)
        down(draw('touch'), 180).convert('RGB').save(out / 'apple-touch-icon.png', optimize=True)
        # Same app identity as the root manifest (no id, so the start URL is
        # the id); only the icons and colours change.
        manifest = dict(root_manifest)
        manifest['start_url'] = '../../../' + root_manifest['start_url']
        manifest['theme_color'] = theme_color
        manifest['background_color'] = background
        (out / 'site.webmanifest').write_text(json.dumps(manifest, separators=(',', ':')), encoding='utf-8')
    print(f'Wrote {len(SETS)} icon sets to {ICONS}')


if __name__ == '__main__':
    main()

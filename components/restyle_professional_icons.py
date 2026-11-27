#!/usr/bin/python3
"""Restyle the unbranded Professional icon plates for a light desktop.

The Professional themes ship a dark plate behind every icon. On the light
Professional wallpapers that reads as a black tile, so the plate gradients are
recoloured to the theme surface and the accent pair is swapped to the active
family. Icon geometry is untouched: only the plate and accent colours change.
"""
import re
import subprocess
import sys
from pathlib import Path

from PIL import Image

# Dark plate colours used by the shipped Professional artwork.
PLATE = {
    '#070a10': '#ffffff',
    '#07060b': '#ffffff',
    '#0b0e14': '#ffffff',
    '#101720': '#fbfcfc',
    '#15232a': '#f2f5f3',
    '#1b0c21': '#e9eeec',
    '#24332c': '#dfe7e3',
}
ACCENT = ('#326d59', '#60877a')

SIZES = (16, 24, 32, 48, 64, 96, 128, 256)
HEX = re.compile(r'#[0-9a-fA-F]{6}')


def restyle_svg(text, accent, accent_light):
    def swap(match):
        value = match.group().lower()
        if value in PLATE:
            return PLATE[value]
        if value == ACCENT[0]:
            return accent
        if value == ACCENT[1]:
            return accent_light
        return match.group()
    return HEX.sub(swap, text)


def whiten_plate(image):
    """Replace the dark Professional plate with the light theme surface."""
    from PIL import ImageChops
    image = image.convert('RGBA')
    red, green, blue, alpha = image.split()
    peak = ImageChops.lighter(ImageChops.lighter(red, green), blue)
    plate = peak.point(lambda value: 255 if value < 102 else 0)
    visible = alpha.point(lambda value: 255 if value >= 8 else 0)
    mask = ImageChops.multiply(plate, visible)
    tone = peak.point(lambda value: 229 + int(value / 102 * 26))
    light = Image.merge('RGBA', (tone, tone, tone, alpha))
    return Image.composite(light, image, mask)


def whiten_theme_pngs(theme: Path):
    """Whiten raster app plates, skipping artwork whose plate is not dark."""
    from PIL import ImageChops
    changed = 0
    for png in sorted(theme.rglob('*.png')):
        if 'apps' not in png.parts:
            continue
        with Image.open(png) as source:
            image = source.convert('RGBA')
        red, green, blue, alpha = image.split()
        peak = ImageChops.lighter(ImageChops.lighter(red, green), blue)
        plate = peak.point(lambda value: 255 if value < 102 else 0)
        opaque = alpha.point(lambda value: 255 if value >= 200 else 0)
        coverage = ImageChops.multiply(plate, opaque)
        dark = coverage.histogram()[255]
        visible = opaque.histogram()[255]
        if not visible or dark / visible < 0.45:
            continue
        whiten_plate(image).save(png)
        changed += 1
    return changed


def render(svg, size, output):
    subprocess.run(['rsvg-convert', '-w', str(size), '-h', str(size), '-o', str(output), str(svg)],
                   check=True, capture_output=True)


def restyle_theme(theme: Path, accent: str, accent_light: str):
    changed = rendered = 0
    for svg in sorted(theme.glob('scalable/*/*.svg')):
        original = svg.read_text()
        updated = restyle_svg(original, accent, accent_light)
        if updated != original:
            svg.write_text(updated)
            changed += 1
        targets = [size for size in SIZES if (theme / f'{size}x{size}' / svg.parent.name / (svg.stem + '.png')).is_file()]
        if not targets:
            continue
        master = theme / '.restyle-master.png'
        render(svg, 256, master)
        image = Image.open(master).convert('RGBA')
        for size in targets:
            target = theme / f'{size}x{size}' / svg.parent.name / (svg.stem + '.png')
            image.resize((size, size), Image.LANCZOS).save(target)
            rendered += 1
        master.unlink(missing_ok=True)
    return changed, rendered


def main(argv):
    if len(argv) < 4:
        print('usage: restyle_professional_icons.py <theme-dir> <accent> <accent-light>')
        return 2
    theme = Path(argv[1])
    changed, rendered = restyle_theme(theme, argv[2], argv[3])
    whitened = whiten_theme_pngs(theme)
    print(f'{argv[1]}: {changed} SVGs recoloured, {rendered} PNGs rendered, {whitened} plates whitened')
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))

#!/usr/bin/env python3
"""Check palette contrast, generated package coverage and icon transparency."""
import argparse
import configparser
import importlib.util
import json
from pathlib import Path
import tempfile
from PIL import Image

parser = argparse.ArgumentParser()
parser.add_argument('source', type=Path)
parser.add_argument('--desktop', type=Path)
parser.add_argument('--artwork', type=Path)
args = parser.parse_args()
palettes = json.loads((args.source / 'theme-palettes.json').read_text(encoding='utf-8'))


def luminance(value):
    channels = [int(value[i:i+2], 16)/255 for i in (1, 3, 5)]
    channels = [c/12.92 if c <= .04045 else ((c+.055)/1.055)**2.4 for c in channels]
    return sum(c*w for c, w in zip(channels, (.2126, .7152, .0722)))


def contrast(a, b):
    a, b = luminance(a), luminance(b)
    return (max(a, b)+.05)/(min(a, b)+.05)


for name, palette in palettes.items():
    assert contrast(palette['foreground'], palette['background']) >= 7, name
    assert contrast(palette['accent'], palette['background']) >= 4.5, name
assert luminance(palettes['white-silver-gold']['background']) > .85
assert luminance(palettes['woodland']['background']) < .05
spec = importlib.util.spec_from_file_location('shadow_palette', args.source / 'shadow_palette.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
with tempfile.TemporaryDirectory() as temporary:
    folder = Path(temporary)
    module.write_active_palette(folder, 'woodland', palettes['woodland'])
    config = configparser.ConfigParser()
    config.read(folder / 'active-palette.ini')
    assert config['Palette']['mode'] == 'woodland'
    previous = (folder / 'active-palette.ini').read_bytes()
    try:
        module.write_active_palette(folder, 'invalid', dict(palettes['woodland'], accent='not-a-color'))
    except ValueError:
        pass
    else:
        raise AssertionError('Invalid color accepted')
    assert (folder / 'active-palette.ini').read_bytes() == previous

if args.desktop and args.artwork:
    payload = args.desktop / 'usr/share/shadowrealm-os/desktop'
    modes = json.loads((payload / 'appearance-modes.json').read_text())
    assert len([r for r in modes.values() if not r.get('variant_of')]) == 9
    assert len([r for r in modes.values() if r.get('variant_of') == 'professional']) == 3
    for mode, record in modes.items():
        assert (payload / 'runtime/icons' / mode / Path(record['logo']).name).is_file(), mode
        assert (payload / 'wallpapers' / Path(record['wallpaper']).name).is_file(), mode
        share = args.artwork / 'usr/share'
        assert (share / 'themes' / record['theme'] / 'gtk-3.0/gtk.css').is_file(), mode
        assert (share / 'themes' / record['wm'] / 'xfwm4/themerc').is_file(), mode
        assert (share / 'icons' / record['icons'] / 'index.theme').is_file(), mode
        progress = share / 'shadowrealm-os/branding' / f"Progress-Fill-{record['wallpaper_palette']}.png"
        with Image.open(progress) as image:
            assert image.size == (360, 6), mode
        icon = payload / 'runtime/icons' / mode / 'orbital-dock-terminal.png'
        if mode in palettes:
            with Image.open(icon).convert('RGBA') as image:
                assert image.getpixel((0, 0))[3] < 16, mode
        if record.get('unbranded'):
            walls = [payload / 'wallpapers' / f"{record['wallpaper_palette']}-{style}.png"
                     for style in ('Satin-Bloom', 'Flowing-Glass', 'Sculpted-Silk')]
            assert all(p.is_file() for p in walls), mode
            assert len({p.read_bytes() for p in walls}) == 3, mode
    print('PASS generated coverage: nine styles, four Professional accents, distinct Professional scenes')
print('PASS palette contrast, light/dark separation and atomic native palette configuration')

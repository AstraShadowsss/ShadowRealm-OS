#!/usr/bin/env python3
"""Build a labeled web gallery from the tested wallpaper collection."""
import argparse
import hashlib
import html
import json
from pathlib import Path
from PIL import Image

parser = argparse.ArgumentParser()
parser.add_argument('assets', type=Path)
parser.add_argument('repository', type=Path)
args = parser.parse_args()
repo = args.repository.resolve()
output = repo / 'screenshots/wallpapers'
output.mkdir(parents=True, exist_ok=True)
modes = json.loads((args.assets / 'appearance-modes.json').read_text())
styles = json.loads((repo / 'components/wallpaper-collections.json').read_text(encoding='utf-8'))
public = 'https://raw.githubusercontent.com/AstraShadowsss/ShadowRealm-OS/main/'
entries = []
for mode, record in modes.items():
    family = record['wallpaper_palette']
    candidates = []
    for key, label in styles.items():
        if record.get('unbranded') and key not in ('Satin-Bloom','Flowing-Glass','Sculpted-Silk'):
            continue
        name = f'{family}-{key}.png' if key in ('Satin-Bloom','Flowing-Glass','Sculpted-Silk') else f'ShadowRealm-OS-{family}-{key}.png'
        candidates.append((args.assets / 'wallpapers' / name, label))
    for path, label in candidates:
        if not path.is_file():
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        filename = f'{mode}-{path.stem.removeprefix("ShadowRealm-OS-" + family + "-").lower()}-{digest[:10]}.webp'
        destination = output / filename
        with Image.open(path) as source:
            image = source.convert('RGB')
            image.thumbnail((1440, 960), Image.Resampling.LANCZOS)
            image.save(destination, 'WEBP', quality=85, method=6)
            width, height = image.size
        entries.append(dict(theme=mode, theme_label=record['label'] + (' — Emerald' if mode == 'professional' else ''), style=label,
                            image=public + 'screenshots/wallpapers/' + filename,
                            width=width, height=height, source_sha256=digest))
manifest = output / 'collection.json'
manifest.write_text(json.dumps(entries, indent=2) + '\n', encoding='utf-8')
retained = {entry['image'].rsplit('/', 1)[-1] for entry in entries}
for obsolete in output.glob('*.webp'):
    if obsolete.name not in retained:
        obsolete.unlink()
cards = []
for index, entry in enumerate(entries):
    label = html.escape(entry['theme_label'] + ' — ' + entry['style'])
    cards.append(f'''<figure class="gallery-card" data-theme="{html.escape(entry['theme'])}" data-theme-label="{html.escape(entry['theme_label'])}" data-style="{html.escape(entry['style'])}">
<a href="{entry['image']}" target="_blank" rel="noopener" aria-label="Open {label}"><img src="{entry['image']}" alt="{label}" width="{entry['width']}" height="{entry['height']}" loading="{'eager' if index == 0 else 'lazy'}" decoding="async"></a>
<figcaption><strong>{html.escape(entry['style'])}</strong><span>{html.escape(entry['theme_label'])}</span></figcaption></figure>''')
template = (repo / 'website/gallery-template.html').read_text(encoding='utf-8')
fragment = template.replace('<!-- GALLERY CARDS -->', '\n'.join(cards))
page = repo / 'website/index.html'
text = page.read_text(encoding='utf-8')
start, end = '<!-- APPEARANCE GALLERY START -->', '<!-- APPEARANCE GALLERY END -->'
if start in text:
    before, rest = text.split(start, 1)
    _, after = rest.split(end, 1)
else:
    before, rest = text.split('<h2>Wallpaper collection</h2>', 1)
    _, after = rest.split('<h2>Control Center</h2>', 1)
    after = '<h2>Control Center</h2>' + after
page.write_text(before + start + '\n' + fragment + '\n' + end + after, encoding='utf-8')
print(f'Built {len(entries)} labeled previews across {len({e["theme"] for e in entries})} themes.')

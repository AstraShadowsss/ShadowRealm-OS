#!/usr/bin/env python3
"""Keep widget descriptions and captures consistent across project pages."""
from pathlib import Path
import json,html,re

root=Path(__file__).resolve().parent.parent
items=json.loads((root/'website/widgets.json').read_text(encoding='utf-8'))
public='https://raw.githubusercontent.com/AstraShadowsss/ShadowRealm-OS/main/'
intro='Eight independent widgets, shown together in Professional styling. They follow your desktop theme and can be moved, resized and customized separately.'
cards=[]
for item in items:
    path='screenshots/widgets/'+item['id']+'.png'
    assert (root/path).is_file(),path
    title=html.escape(item['title']);description=html.escape(item['description'])
    cards.append(f'<article class="card"><h3>{title}</h3><a href="{public+path}" target="_blank" rel="noopener"><img style="display:block;width:100%;max-width:270px;height:auto;border-radius:12px;margin:16px auto" src="{public+path}" alt="{title} widget" loading="lazy"></a><p>{description}</p></article>')
details='<details class="card widget-customization"><summary>Arrange and customize your widgets</summary><p>Choose which panels appear, adjust their text, graph and bar colors, and set background transparency. Theme follows the shared background setting in Appearance.</p><img class="screen" src="'+public+'screenshots/widget-customization.png?v=20261127weather" alt="Current widget controls in the Professional desktop" loading="lazy"></details>'
section='<section id="widgets"><h2>Desktop widgets</h2><p>'+intro+'</p><section class="grid widget-grid">'+''.join(cards)+'</section>'+details+'<p><a href="https://astrashadowsss.github.io/ShadowRealm-OS/docs/widgets.html">Explore the widget controls</a></p></section>'
page=root/'website/index.html';text=page.read_text(encoding='utf-8')
text,count=re.subn(r'<section id="widgets">.*?</section>(?=<h2>System tools)',lambda _:section,text,count=1,flags=re.S)
assert count==1
text=text.replace('minmax(min(100%,240px),1fr)','minmax(min(100%,280px),1fr)')
page.write_text(text,encoding='utf-8')
rows=['### Widgets and system tools','',intro,'']
for group in (items[:4],items[4:]):
    rows.extend(['| '+' | '.join(x['title'] for x in group)+' |','| '+' | '.join('---' for _ in group)+' |','| '+' | '.join(f"![{x['title']}](screenshots/widgets/{x['id']}.png)" for x in group)+' |','| '+' | '.join(x['description'] for x in group)+' |',''])
rows+=['<details>','<summary>Arrange and customize your widgets</summary>','','Choose which panels appear, adjust their text, graph and bar colors, and set background transparency. Theme follows the shared background setting in Appearance.','','![Current widget controls](screenshots/widget-customization.png?v=20261127weather)','','</details>','','[Desktop widgets guide](docs/widgets.md)','','![Network, Shadow Shield and Software & Updates](screenshots/system-tools.png)','','']
page=root/'README.md';text=page.read_text(encoding='utf-8');start=text.index('### Widgets and system tools');end=text.index('### Apps and games',start)
page.write_text(text[:start]+'\n'.join(rows)+text[end:],encoding='utf-8')
print('Built the same eight-widget showcase for website and README.')

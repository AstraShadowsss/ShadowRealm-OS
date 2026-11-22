"""Build coordinated palette variants from the existing Neon geometry."""
import base64
import colorsys
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import re
import shutil
import subprocess
import tarfile
import xml.etree.ElementTree as ET
from pathlib import Path

_rendered = {}


def render_svg(svg):
    data = svg.encode()
    key = hashlib.sha256(data).digest()
    if key not in _rendered:
        _rendered[key] = subprocess.run(['rsvg-convert'], input=data, capture_output=True, check=True).stdout
    return _rendered[key]


def professional_folder_svg(source, palette):
    from PIL import Image
    with Image.open(source) as image:
        width, height = image.size
    channels = [int(palette['accent'][i:i+2], 16)/255 for i in (1, 3, 5)]
    transfer = ''.join(f'<feFunc{role} type="table" tableValues="{c*.35} {c*.5+.5}"/>'
                       for role, c in zip('RGB', channels))
    encoded = base64.b64encode(source.read_bytes()).decode()
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"><defs><filter id="folder"><feColorMatrix type="saturate" values="0"/><feComponentTransfer>{transfer}</feComponentTransfer></filter></defs><image width="{width}" height="{height}" href="data:image/png;base64,{encoded}" filter="url(#folder)"/></svg>'


def recolor_text(text, palette):
    def rgb(value):
        return tuple(int(value[i:i + 2], 16) / 255 for i in (1, 3, 5))

    def replace(match):
        value = match.group()
        if len(value) == 4:
            value = '#' + ''.join(c * 2 for c in value[1:])
        source = rgb(value)
        hue, light, saturation = colorsys.rgb_to_hls(*source)
        if saturation < .12 and light > .85:
            target = rgb(palette['foreground'])
        elif light < .15:
            base = rgb(palette['background'])
            target = tuple(min(1., c + max(0., light - .045)) for c in base)
        elif saturation < .12:
            return match.group()
        else:
            key = 'accent' if .35 <= hue <= .65 else 'secondary'
            h, target_light, s = colorsys.rgb_to_hls(*rgb(palette[key]))
            adjusted = target_light + (light - .5) * .65
            target = colorsys.hls_to_rgb(h, max(.12, min(.92, adjusted)), s)
        return '#' + ''.join(f'{round(c * 255):02x}' for c in target)

    return re.sub(r'#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b', replace, text)


def render_png(source, target, palette):
    # Apply the same cyan/magenta palette matrix used by the branding builder.
    from PIL import Image
    with Image.open(source) as image:
        width, height = image.size
    c = [int(palette['accent'][i:i + 2], 16) / 255 for i in (1, 3, 5)]
    m = [int(palette['secondary'][i:i + 2], 16) / 255 for i in (1, 3, 5)]
    matrix = ' '.join(' '.join(map(str, [1-c[i], 1-m[i], c[i]+m[i]-1, 0, 0])) for i in range(3)) + ' 0 0 0 1 0'
    encoded = base64.b64encode(source.read_bytes()).decode()
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"><defs><filter id="palette" color-interpolation-filters="sRGB"><feColorMatrix values="{matrix}"/></filter></defs><image width="{width}" height="{height}" filter="url(#palette)" href="data:image/png;base64,{encoded}"/></svg>'
    target.write_bytes(render_svg(svg))


def wallpaper_palette(palette):
    return dict(palette, accent=palette.get('wallpaper_accent', palette['accent']),
                secondary=palette.get('wallpaper_secondary', palette['secondary']))


def render_wallpaper(source, target, palette):
    palette = wallpaper_palette(palette)
    if palette.get('family') == 'WhiteSilverGold':
        from PIL import Image
        with Image.open(source) as image:
            width, height = image.size
        data = base64.b64encode(source.read_bytes()).decode()
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">
<defs><filter id="silver"><feColorMatrix type="saturate" values="0"/></filter>
<filter id="gold" color-interpolation-filters="sRGB"><feColorMatrix type="saturate" values="0"/><feComponentTransfer>
<feFuncR type="table" tableValues="0 .20 .65 .95 1"/><feFuncG type="table" tableValues="0 .16 .48 .82 1"/><feFuncB type="table" tableValues="0 .05 .12 .40 1"/>
</feComponentTransfer></filter><linearGradient id="fade"><stop offset=".15" stop-color="black"/><stop offset=".85" stop-color="white"/></linearGradient>
<mask id="blend"><rect width="100%" height="100%" fill="url(#fade)"/></mask></defs>
<image width="{width}" height="{height}" href="data:image/png;base64,{data}" filter="url(#gold)"/>
<g mask="url(#blend)"><image width="{width}" height="{height}" href="data:image/png;base64,{data}" filter="url(#silver)"/></g></svg>'''
        target.write_bytes(render_svg(svg))
        return
    if not palette.get('wallpaper_light'):
        render_png(source, target, palette)
        return
    from PIL import Image
    with Image.open(source) as image:
        width, height = image.size
    def rgb(value):
        return [int(value[i:i+2], 16)/255 for i in (1, 3, 5)]
    background, ink = rgb('#f5f7fa'), rgb('#556274')
    primary, secondary = rgb(palette['accent']), rgb(palette['secondary'])
    matrix = ' '.join(' '.join(map(str, [ink[i]-primary[i], ink[i]-secondary[i],
                         primary[i]+secondary[i]-ink[i]-background[i], 0, background[i]]))
                      for i in range(3)) + ' 0 0 0 1 0'
    encoded = base64.b64encode(source.read_bytes()).decode()
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"><defs><filter id="light" color-interpolation-filters="sRGB"><feColorMatrix values="{matrix}"/></filter></defs><image width="{width}" height="{height}" href="data:image/png;base64,{encoded}" filter="url(#light)"/></svg>'
    target.write_bytes(render_svg(svg))


def recolor_svg(text, palette):
    if 'id="plate"' in text and 'id="rim"' in text:
        from shadow_icon_style import signature_dock_svg
        return signature_dock_svg(text,palette)
    text = recolor_text(text, palette)
    if 'data:image/' not in text:
        return text
    root = ET.fromstring(text)
    namespace = '{http://www.w3.org/2000/svg}'
    defs = ET.SubElement(root, namespace + 'defs')
    filter_node = ET.SubElement(defs, namespace + 'filter',
                               {'id': 'sr-palette-image', 'color-interpolation-filters': 'sRGB'})
    c = [int(palette['accent'][i:i + 2], 16) / 255 for i in (1, 3, 5)]
    m = [int(palette['secondary'][i:i + 2], 16) / 255 for i in (1, 3, 5)]
    matrix = ' '.join(' '.join(map(str, [1-c[i], 1-m[i], c[i]+m[i]-1, 0, 0])) for i in range(3)) + ' 0 0 0 1 0'
    ET.SubElement(filter_node, namespace + 'feColorMatrix', {'values': matrix})
    for image in root.iter(namespace + 'image'):
        if not image.get('filter'):
            image.set('filter', 'url(#sr-palette-image)')
    return ET.tostring(root, encoding='unicode')


def render_wallpaper_master(source, target, palette):
    palette = wallpaper_palette(palette)
    from PIL import Image
    with Image.open(source) as image:
        width, height = image.size
    filters = []
    for role in ('accent', 'secondary'):
        color = [int(palette[role][i:i + 2], 16) / 255 for i in (1, 3, 5)]
        if palette.get('wallpaper_light'):
            matrix = ' '.join(f'0 {0.45-c} {c-0.96} 0 0.96' for c in color) + ' 0 0 0 1 0'
        else:
            neutral = .2 if palette.get('wallpaper_palette') == 'Neon' else 1.0
            matrix = ' '.join(f'0 {(1-c)*neutral} {c} 0 0' for c in color) + ' 0 0 0 1 0'
        filters.append(f'<filter id="{role}" color-interpolation-filters="sRGB"><feColorMatrix values="{matrix}"/></filter>')
    encoded = base64.b64encode(source.read_bytes()).decode()
    image = f'<image width="{width}" height="{height}" href="data:image/png;base64,{encoded}"'
    stops = '<stop offset=".45" stop-color="black"/><stop offset=".55" stop-color="white"/>' if palette.get('wallpaper_palette') == 'Neon' else '<stop stop-color="black"/><stop offset="1" stop-color="white"/>'
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">
<defs>{''.join(filters)}<linearGradient id="blend">{stops}</linearGradient><mask id="fade"><rect width="100%" height="100%" fill="url(#blend)"/></mask></defs>
{image} filter="url(#accent)"/>
<g mask="url(#fade)">{image} filter="url(#secondary)"/></g></svg>'''
    target.write_bytes(render_svg(svg))


def professional_wallpaper(style, palette):
    background, accent, secondary = palette['background'], palette['accent'], palette['secondary']
    definitions = f'''<defs><linearGradient id="paper" x2="1" y2="1"><stop stop-color="{background}"/><stop offset="1" stop-color="white"/></linearGradient>
<linearGradient id="ribbon" x2="1" y2="1"><stop stop-color="{accent}"/><stop offset="1" stop-color="{secondary}"/></linearGradient>
<radialGradient id="light"><stop stop-color="{secondary}" stop-opacity=".18"/><stop offset="1" stop-color="{secondary}" stop-opacity="0"/></radialGradient></defs>'''
    if style == 'Misty-Ridges':
        shapes = f'''<circle cx="1420" cy="320" r="370" fill="url(#light)"/>
<path d="M0 765 330 580 560 700 840 500 1180 720 1450 550 1920 740V1080H0Z" fill="{secondary}" opacity=".16"/>
<path d="M0 870 420 750 740 835 1100 655 1450 800 1920 690V1080H0Z" fill="{accent}" opacity=".20"/>
<path d="M0 980Q420 790 810 930T1600 900L1920 865V1080H0Z" fill="{accent}" opacity=".36"/>'''
    elif style == 'Coastal-Layers':
        shapes = '''<path d="M-100 920C420 180 850 1320 2020 40L2070 500C980 1530 470 650-100 1200Z" fill="url(#ribbon)" opacity=".22"/>
<path d="M-100 800C540 150 910 1230 2020-70" fill="none" stroke="url(#ribbon)" stroke-width="90" opacity=".45"/>
<path d="M-100 630C530 80 980 1100 2020-150" fill="none" stroke="url(#ribbon)" stroke-width="15" opacity=".35"/>
<path d="M-100 900C430 300 1000 1400 2020 100" fill="none" stroke="white" stroke-width="6" opacity=".8"/>'''
    else:
        contours = []
        for radius in range(110, 1250, 34):
            contours.append(f'<ellipse cx="1450" cy="520" rx="{radius}" ry="{radius*.63}" transform="rotate(-24 1450 520)" fill="none" stroke="{accent}" stroke-opacity=".19" stroke-width="2"/>')
        shapes = '<circle cx="1450" cy="520" r="510" fill="url(#light)"/>' + ''.join(contours)
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080">{definitions}<rect width="1920" height="1080" fill="url(#paper)"/>{shapes}</svg>'


def professional_walk(source, target, palette):
    from PIL import Image
    with Image.open(source) as image:
        width, height = image.size
    def hls(value):
        return colorsys.rgb_to_hls(*(int(value[i:i+2], 16)/255 for i in (1, 3, 5)))
    hue, _, saturation = hls(palette['accent'])
    original_hue, _, original_saturation = hls('#326d59')
    degrees = (hue-original_hue)*360
    saturation = min(1.4, saturation/original_saturation)
    encoded = base64.b64encode(source.read_bytes()).decode()
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"><defs><filter id="accent"><feColorMatrix type="hueRotate" values="{degrees}"/><feColorMatrix type="saturate" values="{saturation}"/></filter></defs><image width="{width}" height="{height}" href="data:image/png;base64,{encoded}" filter="url(#accent)"/></svg>'
    target.write_bytes(render_svg(svg))


def write_progress_assets(branding, modes):
    if not branding.is_dir():
        return
    for palette in modes.values():
        colors = wallpaper_palette(palette)
        primary, secondary = colors['accent'], colors['secondary']
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="360" height="6"><defs><linearGradient id="fill"><stop stop-color="{primary}"/><stop offset="1" stop-color="{secondary}"/></linearGradient></defs><rect width="360" height="6" rx="3" fill="url(#fill)"/></svg>'
        (branding / f"Progress-Fill-{palette['wallpaper_palette']}.png").write_bytes(render_svg(svg))


def clone_tree(source, target, palette):
    if not source.is_dir():
        return
    target.mkdir(parents=True, exist_ok=True)
    def copy_one(original):
        donor = palette.get('source_family', 'Neon')
        relative = str(original.relative_to(source)).replace(donor, palette['family'])
        destination = target / relative
        if original.is_symlink():
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.unlink(missing_ok=True)
            destination.symlink_to(str(original.readlink()).replace(donor, palette['family']))
        elif original.is_dir():
            destination.mkdir(parents=True, exist_ok=True)
        elif original.name != 'icon-theme.cache':
            destination.parent.mkdir(parents=True, exist_ok=True)
            if original.suffix == '.png':
                sibling = original.with_suffix('.svg')
                if palette.get('unbranded') and 'places' in original.parts and original.stem.startswith(('folder', 'user-home')):
                    destination.write_bytes(render_svg(professional_folder_svg(original, palette)))
                elif sibling.is_file():
                    svg = recolor_svg(sibling.read_text(), palette)
                    destination.write_bytes(render_svg(svg))
                else:
                    render_png(original, destination, palette)
            else:
                try:
                    text = original.read_text()
                except UnicodeError:
                    shutil.copy2(original, destination)
                else:
                    text = text.replace('ShadowRealm-OS-' + donor, palette.get('theme_name', 'ShadowRealm-OS-' + palette['family']))
                    if palette.get('light'):
                        text = text.replace('gtk-contained-dark.css', 'gtk-contained.css')
                    sibling = original.with_suffix('.png')
                    if original.suffix == '.svg' and sibling.is_file() and palette.get('unbranded') and 'places' in original.parts and original.stem.startswith(('folder', 'user-home')):
                        destination.write_text(professional_folder_svg(sibling, palette))
                    else:
                        destination.write_text(recolor_svg(text, palette) if original.suffix == '.svg'
                                               else recolor_text(text, palette))
    with ThreadPoolExecutor(max_workers=3) as pool:
        list(pool.map(copy_one, sorted(source.rglob('*'))))


def build_variants(root, source, include_icons=True):
    root, source = Path(root), Path(source)
    palettes = json.loads((source / 'theme-palettes.json').read_text())
    desktop = root / 'usr/share/shadowrealm-os/desktop'
    for mode, palette in palettes.items():
        family = palette['family']
        theme_name = palette.get('theme_name', 'ShadowRealm-OS-' + family)
        donor = palette.get('source_family', 'Neon')
        if include_icons:
            for group in ('icons', 'themes'):
                clone_tree(root / f'usr/share/{group}/ShadowRealm-OS-{donor}',
                           root / f'usr/share/{group}/{theme_name}', palette)
            theme = root / f'usr/share/themes/{theme_name}'
            controls = f'''
    @define-color accent_color {palette['accent']};
@define-color theme_bg_color {palette['background']};
    @define-color theme_fg_color {palette['foreground']};
    @define-color theme_base_color {palette['background']};
    @define-color theme_text_color {palette['foreground']};
    @define-color theme_selected_bg_color mix({palette['background']}, {palette['accent']}, 0.25);
    @define-color theme_selected_fg_color {palette['foreground']};
    window, dialog, .background, headerbar, .titlebar,
    entry, textview, textview text, treeview.view, iconview.view,
    menu, .menu, popover {{ background-color: {palette['background']}; color: {palette['foreground']}; }}
    button {{ background: {palette['background']}; color: {palette['foreground']}; border-color: {palette['accent']}; }}
    button:hover, button:checked, button:active,
    menuitem:hover, selection, *:selected {{ background: mix({palette['background']}, {palette['accent']}, 0.25); color: {palette['foreground']}; border-color: {palette['secondary']}; box-shadow: inset 0 -2px {palette['accent']}; }}
    check, radio {{ background: {palette['background']}; border: 1px solid {palette['accent']}; color: {palette['foreground']}; }}
    check:checked, radio:checked {{ background: {palette['accent']}; color: {palette['background']}; }}
    '''
            for toolkit in ('gtk-3.0', 'gtk-4.0'):
                css = theme / toolkit / 'gtk.css'
                if css.is_file():
                    css.write_text(css.read_text() + controls)
            clone_tree(desktop / 'runtime/icons' / palette.get('source_mode', 'neon'), desktop / 'runtime/icons' / mode, palette)
        walls = desktop / 'wallpapers'
        if walls.exists() and not palette.get('unbranded'):
            for original in sorted(walls.glob('ShadowRealm-OS-Neon-*.png')):
                render_wallpaper(original, walls / original.name.replace('Neon', family), palette)
        if walls.exists() and palette.get('variant_of') == 'professional':
            walk = walls / 'ShadowRealm-OS-Professional-Circuit-Walker.png'
            if walk.is_file():
                professional_walk(walk, walls / f'ShadowRealm-OS-{family}-Circuit-Walker.png', palette)
        backgrounds = root / 'usr/share/backgrounds/shadowrealm-os'
        if not palette.get('unbranded'):
            for original in sorted(backgrounds.glob('*/ShadowRealm-OS-Neon.png')):
                render_wallpaper(original, original.with_name(f'ShadowRealm-OS-{family}.png'), palette)
        elif palette.get('variant_of') == 'professional':
            walk = backgrounds / 'circuit-walker/ShadowRealm-OS-Professional.png'
            if walk.is_file():
                professional_walk(walk, walk.with_name(f'ShadowRealm-OS-{family}.png'), palette)
        branding = root / 'usr/share/shadowrealm-os/branding'
        for original in sorted(branding.glob('*-Neon.png')):
            render_png(original, original.with_name(original.name.replace('Neon', family)), wallpaper_palette(palette))
    modes_file = desktop / 'appearance-modes.json'
    modes = {}
    if modes_file.is_file():
        modes = json.loads(modes_file.read_text())
        for mode, palette in palettes.items():
            entry = dict(modes[palette.get('source_mode', 'neon')])
            entry.update(palette)
            name = palette.get('theme_name', 'ShadowRealm-OS-' + palette['family'])
            entry.update(theme=name, icons=name, wm=name, wallpaper_palette=palette['family'],
                         wallpaper='ShadowRealm-OS-' + palette['family'] +
                         '-seated-city.png')
            if palette.get('unbranded'):
                entry['wallpaper'] = palette['family'] + '-Satin-Bloom.png'
            modes[mode] = entry
        modes_file.write_text(json.dumps(modes, indent=2) + '\n')
    else:
        with tarfile.open(source / 'shadowrealm-os-desktop-defaults-source.tar.gz') as archive:
            member = next(m for m in archive if m.name.endswith('/appearance-modes.json'))
            modes = json.loads(archive.extractfile(member).read())
        for mode, palette in palettes.items():
            modes[mode] = dict(palette, wallpaper_palette=palette['family'])
    modes['professional'].update(accent_label='Emerald', widget_background='#172521',
                                 widget_foreground='#edf3ef', widget_accent='#9ec6b7',
                                 widget_secondary='#b8d6c9', wallpaper='Professional-Satin-Bloom.png')
    if modes_file.is_file():
        modes_file.write_text(json.dumps(modes, indent=2) + '\n')
    write_progress_assets(root / 'usr/share/shadowrealm-os/branding', modes)
    for mode, palette in modes.items():
        if not palette.get('unbranded'):
            continue
        family = palette['wallpaper_palette']
        professional_masters = source.parent / 'branding/professional-masters'
        if not professional_masters.is_dir():
            professional_masters = source / 'professional-masters'
        for style in ('Satin-Bloom', 'Flowing-Glass', 'Sculpted-Silk'):
            original = professional_masters / (style + '.png')
            if not original.is_file():
                raise FileNotFoundError(original)
            targets = []
            if desktop.is_dir():
                targets.append(desktop / 'wallpapers' / f'{family}-{style}.png')
            if backgrounds.is_dir():
                targets.append(backgrounds / 'professional' / f'{family}-{style}.png')
            for target in targets:
                target.parent.mkdir(parents=True, exist_ok=True)
                if mode == 'professional':
                    shutil.copy2(original, target)
                else:
                    professional_walk(original, target, palette)
        for old_style in ('Misty-Ridges', 'Coastal-Layers', 'Dune-Contours'):
            (desktop / 'wallpapers' / f'{family}-{old_style}.png').unlink(missing_ok=True)
            (backgrounds / 'professional' / f'{family}-{old_style}.png').unlink(missing_ok=True)
        (desktop / 'wallpapers' / f'ShadowRealm-OS-{family}-Circuit-Walker.png').unlink(missing_ok=True)
        (backgrounds / 'circuit-walker' / f'ShadowRealm-OS-{family}.png').unlink(missing_ok=True)
    masters = source.parent / 'branding/wallpaper-masters'
    if not masters.is_dir():
        masters = source / 'wallpaper-masters'
    if masters.is_dir():
        for original in sorted(masters.glob('*.png')):
            name = original.stem.replace(' ', '-')
            for mode, palette in modes.items():
                if palette.get('unbranded'):
                    continue
                family = palette['wallpaper_palette']
                targets = []
                if desktop.is_dir():
                    targets.append(desktop / 'wallpapers' / f'ShadowRealm-OS-{family}-{name}.png')
                if backgrounds.is_dir():
                    targets.append(backgrounds / name.lower() / f'ShadowRealm-OS-{family}.png')
                for target in targets:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    if mode == 'purple-black':
                        shutil.copy2(original, target)
                    else:
                        render_wallpaper_master(original, target, palette)
    seated = source.parent / 'branding/background-seated.png'
    if not seated.is_file():
        seated = source / 'background-seated.png'
    if seated.is_file():
        for mode, palette in modes.items():
            if palette.get('unbranded'):
                continue
            family = palette['wallpaper_palette']
            targets = []
            if desktop.is_dir():
                targets.append(desktop / 'wallpapers' / f'ShadowRealm-OS-{family}-seated-city.png')
            if backgrounds.is_dir():
                targets.append(backgrounds / 'seated-city' / f'ShadowRealm-OS-{family}.png')
            for target in targets:
                target.parent.mkdir(parents=True, exist_ok=True)
                if mode == 'neon':
                    shutil.copy2(seated, target)
                else:
                    override = source.parent / 'branding/palette-overrides' / family / 'seated-city.png'
                    if not override.is_file():
                        override = source / 'palette-overrides' / family / 'seated-city.png'
                    if override.is_file():
                        shutil.copy2(override, target)
                    else:
                        render_wallpaper(seated, target, palette)
    wraith = source.parent / 'branding/wraith-master.png'
    if wraith.is_file():
        for mode, palette in modes.items():
            if palette.get('unbranded'):
                continue
            family = palette['wallpaper_palette']
            targets = []
            if desktop.is_dir():
                targets.append(desktop / 'wallpapers' / f'ShadowRealm-OS-{family}-full-artwork.png')
            if backgrounds.is_dir():
                targets.append(backgrounds / 'full-artwork' / f'ShadowRealm-OS-{family}.png')
            for target in targets:
                target.parent.mkdir(parents=True, exist_ok=True)
                render_wraith(wraith, target, palette)
    apply_wallpaper_finish(root, source, modes)
    if include_icons:
        from professional_icons import build_professional_icons
        build_professional_icons(root, modes, source)
        if modes_file.is_file():
            modes_file.write_text(json.dumps(modes, indent=2) + '\n')
    for record in modes.values():
        if not record.get('unbranded'):
            continue
        frame=root/'usr/share/themes'/record['wm']/'xfwm4/themerc'
        if frame.is_file():
            text=frame.read_text()
            for key,value in [('active_text_color',record['foreground']),('inactive_text_color',record['foreground']),('title_shadow_active','false'),('title_shadow_inactive','false')]:
                text=re.sub(r'^'+key+r'=.*$',key+'='+value,text,flags=re.M)
            frame.write_text(text)


def render_wraith(source, target, palette):
    """Keep the charcoal master intact while rendering colored emission."""
    if palette['wallpaper_palette'] == 'RedBlack':
        shutil.copy2(source, target)
        return
    from PIL import Image
    with Image.open(source) as image:
        width, height = image.size
    palette = wallpaper_palette(palette)
    filters = []
    for role in ('accent', 'secondary'):
        color = [int(palette[role][i:i+2], 16)/255 for i in (1,3,5)]
        matrix = ' '.join(f'{c} {1-c} 0 0 0' for c in color) + ' 0 0 0 1 0'
        filters.append(f'<filter id="{role}" color-interpolation-filters="sRGB"><feColorMatrix values="{matrix}"/></filter>')
    data = base64.b64encode(source.read_bytes()).decode()
    element = f'<image width="{width}" height="{height}" href="data:image/png;base64,{data}"'
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"><defs>{''.join(filters)}<linearGradient id="fade"><stop offset=".25" stop-color="black"/><stop offset=".75" stop-color="white"/></linearGradient><mask id="blend"><rect width="100%" height="100%" fill="url(#fade)"/></mask></defs>{element} filter="url(#accent)"/><g mask="url(#blend)">{element} filter="url(#secondary)"/></g></svg>'''
    target.write_bytes(render_svg(svg))


def apply_wallpaper_finish(root, source, modes):
    """Render coordinated wallpaper lighting, then apply approved art masters."""
    from PIL import Image
    desktop = root / 'usr/share/shadowrealm-os/desktop/wallpapers'
    backgrounds = root / 'usr/share/backgrounds/shadowrealm-os'
    overrides = source.parent / 'branding/palette-overrides'
    if not overrides.is_dir():
        overrides = source / 'palette-overrides'
    for mode, palette in modes.items():
        family = palette['wallpaper_palette']
        (desktop / f'ShadowRealm-OS-{family}-Circuit-Walker.png').unlink(missing_ok=True)
        (backgrounds / 'circuit-walker' / f'ShadowRealm-OS-{family}.png').unlink(missing_ok=True)
        if palette.get('unbranded'):
            for old in desktop.glob(f'ShadowRealm-OS-{family}-*.png'):
                old.unlink()
            for old in backgrounds.glob(f'*/ShadowRealm-OS-{family}.png'):
                old.unlink()
        strength = 1.0 if palette.get('unbranded') or family in ('BlackWhite','WhiteSilverGold') else 1.65
        targets = list(desktop.glob(f'ShadowRealm-OS-{family}-*.png'))
        targets += list(backgrounds.glob(f'*/ShadowRealm-OS-{family}.png'))
        for target in targets:
            style = (target.stem.removeprefix(f'ShadowRealm-OS-{family}-')
                     if target.parent == desktop else target.parent.name)
            if style.lower() == 'full-artwork' and (source.parent / 'branding/wraith-master.png').is_file():
                continue
            override = overrides / family / (style + '.png')
            if not override.is_file():
                override = next((p for p in (overrides / family).glob('*.png')
                                 if p.stem.casefold() == style.casefold()), override)
            if override.is_file():
                shutil.copy2(override, target)
                continue
            if strength == 1.0:
                continue
            with Image.open(target) as image:
                width, height = image.size
            data = base64.b64encode(target.read_bytes()).decode()
            svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">
<defs><filter id="chroma" color-interpolation-filters="sRGB"><feColorMatrix type="saturate" values="{strength}"/></filter></defs>
<image width="{width}" height="{height}" href="data:image/png;base64,{data}" filter="url(#chroma)"/></svg>'''
            target.write_bytes(render_svg(svg))


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('root', type=Path)
    parser.add_argument('source', type=Path)
    parser.add_argument('--wallpapers-only', action='store_true')
    args = parser.parse_args()
    build_variants(args.root, args.source, include_icons=not args.wallpapers_only)

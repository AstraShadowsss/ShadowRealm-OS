"""Render the unbranded desktop's coordinated vector icon family."""
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import tarfile
import base64

PREFIXES = ('orbital-dock-', 'shadow-panel-', 'shadowrealm-os-release-', 'shadowrealm-os-app-', 'shadow-')


def build_professional_icons(root, modes, source=None):
    from theme_variants import render_svg
    root = Path(root)
    runtime = root / 'usr/share/shadowrealm-os/desktop/runtime/icons'
    donor = runtime / 'neon'
    glyphs = {}
    def normalized(tree):
        viewbox = [float(value) for value in tree.get('viewBox','0 0 64 64').split()]
        x,y,width,height=viewbox
        drawing=''.join(ET.tostring(c,encoding='unicode') for c in tree)
        return f'<g transform="scale({64/width} {64/height}) translate({-x} {-y})">{drawing}</g>'
    for p in donor.glob('shadow-panel-*.svg'):
        tree = ET.fromstring(p.read_text())
        glyphs[p.stem.removeprefix('shadow-panel-')] = normalized(tree)
    if not glyphs and source:
        with tarfile.open(Path(source)/'shadowrealm-os-desktop-defaults-source.tar.gz') as archive:
            for member in archive:
                if '/runtime/icons/neon/shadow-panel-' in member.name and member.name.endswith('.svg'):
                    tree=ET.fromstring(archive.extractfile(member).read())
                    glyphs[Path(member.name).stem.removeprefix('shadow-panel-')]=normalized(tree)
    if not glyphs:
        return
    glyphs.setdefault('software','<g fill="none" stroke="#000000" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"><path d="m12 21 20-10 20 10v26L32 57 12 47Z M12 21l20 10 20-10 M32 31v26 M22 16l20 10"/></g>')
    glyphs.setdefault('task-manager','<g fill="none" stroke="#000000" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="12" width="46" height="34" rx="5"/><path d="M20 54h24 M32 46v8 M15 33h8l6-12 7 18 5-9h8"/></g>')
    glyphs.setdefault('home','<g fill="none" stroke="#000000" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"><path d="m9 30 23-19 23 19 M15 26v28h34V26 M26 54V37h12v17"/></g>')
    for mode, palette in modes.items():
        if not palette.get('unbranded'):
            continue
        accent, ink = palette['accent'], palette['foreground']
        folder = runtime / mode
        if runtime.parent.is_dir():
            folder.mkdir(parents=True, exist_ok=True)

        def icon(role, tiled=True, size=64):
            drawing = glyphs.get(role, glyphs.get('settings', glyphs.get('menu', '')))
            drawing = re.sub(r'#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b', accent if tiled else ink, drawing)
            tile = '''<defs><linearGradient id="surface" x2="0" y2="1"><stop stop-color="#ffffff"/><stop offset="1" stop-color="#e3e9e7"/></linearGradient></defs><rect x="5" y="6" width="54" height="54" rx="14" fill="#172622" opacity=".10"/><rect x="5" y="4" width="54" height="54" rx="14" fill="url(#surface)" stroke="#bfccc7" stroke-width="1"/>''' if tiled else ''
            return f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 64 64">{tile}<g transform="translate(6 5) scale(.8125)">{drawing}</g></svg>'

        for role in (glyphs if runtime.parent.is_dir() else {}):
            for prefix in ('orbital-dock-', 'shadow-', 'shadow-panel-'):
                tiled = prefix != 'shadow-panel-'
                size = 24 if not tiled else 64
                svg = icon(role, tiled, size)
                (folder / (prefix+role+'.svg')).write_text(svg)
                (folder / (prefix+role+'.png')).write_bytes(render_svg(svg))
        theme = root / 'usr/share/icons' / palette['icons']
        brand_names = {'shadow-dock-launcher', 'shadowrealm-os-dock-menu',
                       'shadowrealm-os-release-shadow-menu', 'distributor-logo',
                       'shadowrealm-os-logo'}
        originals = list((root / 'usr/share/icons/ShadowRealm-OS-Neon').rglob('shadow-dock-launcher.png'))
        if originals:
            original = max(originals, key=lambda p: p.stat().st_size)
            encoded = base64.b64encode(original.read_bytes()).decode('ascii')
            rgb = [int(accent[i:i+2], 16)/255 for i in (1, 3, 5)]
            matrix = ' '.join(f'0 0 0 0 {c}' for c in rgb) + ' 0 0 0 1 0'
            for p in theme.rglob('*'):
                if p.stem not in brand_names or p.suffix not in ('.png', '.svg') or not p.is_file():
                    continue
                match = re.search(r'/(\d+)x\d+/', p.as_posix())
                size = int(match[1]) if match else 64
                svg = f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{size}" height="{size}" viewBox="0 0 64 64"><defs><filter id="tint" color-interpolation-filters="sRGB"><feColorMatrix values="{matrix}"/></filter></defs><rect x="5" y="4" width="54" height="54" rx="14" fill="#f4f7f6" stroke="#bfccc7"/><image x="10" y="9" width="44" height="44" filter="url(#tint)" xlink:href="data:image/png;base64,{encoded}"/></svg>'
                p.write_text(svg) if p.suffix == '.svg' else p.write_bytes(render_svg(svg))
        for p in theme.rglob('*'):
            if p.suffix not in ('.svg', '.png') or not p.is_file() or 'apps' not in p.parts:
                continue
            stem=p.stem.removeprefix('shadowrealm-os-release-').removeprefix('shadowrealm-os-app-')
            prefix = next((v for v in PREFIXES if stem.startswith(v)), None)
            if not prefix:
                continue
            role = stem.removeprefix(prefix)
            if role not in glyphs:
                continue
            match = re.search(r'/(\d+)x\d+/', p.as_posix())
            size = int(match[1]) if match else 64
            svg = icon(role, not prefix.startswith('shadow-panel'), size)
            p.write_text(svg) if p.suffix == '.svg' else p.write_bytes(render_svg(svg))
        places = {
            'folder': '', 'folder-documents': 'notes', 'folder-download': 'download',
            'folder-downloads': 'download', 'folder-music': 'music', 'folder-pictures': 'image',
            'folder-videos': 'video', 'folder-templates': 'document', 'folder-publicshare': 'users',
            'user-home': 'home', 'user-trash': 'trash', 'user-trash-full': 'trash',
            'user-trash-empty': 'trash', 'trashcan_full': 'trash', 'trashcan_empty': 'trash',
            'gnome-fs-trash-full': 'trash', 'gnome-fs-trash-empty': 'trash',
            'drive-harddisk': 'disk',
        }
        for p in theme.rglob('*'):
            if p.suffix not in ('.svg', '.png') or not p.is_file() or p.stem not in places:
                continue
            role = places[p.stem]
            if p.stem.startswith('folder'):
                badge=re.sub(r'#[0-9a-fA-F]{6}\b','#ffffff',glyphs.get(role,glyphs.get('notes','')))
                detail = f'<g transform="translate(28 26) scale(.42)">{badge}</g>' if role else ''
                svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64"><path d="M7 20q0-4 4-4h15l6 6h21q4 0 4 4v25q0 4-4 4H11q-4 0-4-4Z" fill="{accent}"/><path d="M7 27h50v4H7Z" fill="#ffffff" opacity=".2"/>{detail}</svg>'
            else:
                svg = icon(role)
            p.write_text(svg) if p.suffix == '.svg' else p.write_bytes(render_svg(svg))
        palette['custom_system_icons'] = True
        frame=root/'usr/share/themes'/palette['wm']/'xfwm4'
        for p in frame.glob('*.xpm'):
            colors={'.':'#edf3f0','m':'#70877c','c':accent,'g':'#c4d1cb','w':ink}
            text=p.read_text()
            text=re.sub(r'"([.mcgw]) c #[0-9a-fA-F]{6}"',lambda m:'"'+m[1]+' c '+colors[m[1]]+'"',text)
            p.write_text(text)
        css=root/'usr/share/themes'/palette['theme']/'gtk-3.0/gtk.css'
        if css.is_file():
            marker='/* Professional selection controls */'
            text=css.read_text().split(marker)[0]
            text+=f'\n{marker}\n@define-color accent_color {accent};\ncheck:checked, radio:checked {{background-image:none; background-color:{accent}; border-color:{accent}; color:#ffffff;}}\n'
            css.write_text(text)

from pathlib import Path
import re
import xml.etree.ElementTree as ET


def signature_dock_svg(text, mode):
    root=ET.fromstring(text)
    namespace='{http://www.w3.org/2000/svg}'
    for gradient in root.iter(namespace+'linearGradient'):
        stops=list(gradient)
        colors=([mode['accent'],mode['foreground'],mode['secondary']] if gradient.get('id')=='rim'
                else ['#252734','#090a12','#11121a'] if gradient.get('id')=='plate' else None)
        if colors:
            for stop,color in zip(stops,colors):stop.set('stop-color',color)
    for node in root.iter():
        stroke=node.get('stroke','')
        if stroke.startswith('#'):node.set('stroke',mode['foreground'] if node.get('stroke-opacity') else mode['accent'])
    return ET.tostring(root,encoding='unicode')


def selected_icons(modes, desktop_id, config, requested=None):
    choice = requested
    if choice is None:
        try:
            choice = (Path(config) / 'icon-style').read_text().strip()
        except FileNotFoundError:
            choice = 'default'
    if choice != 'default' and choice not in modes:
        if requested is not None:
            raise ValueError('Unknown icon style')
        choice = 'default'
    identity = desktop_id if choice == 'default' else choice
    result = dict(modes[identity], id=identity)
    return choice, result


def repair_panel_glyphs(mode, base):
    import gi
    gi.require_version('GdkPixbuf','2.0')
    from gi.repository import GdkPixbuf
    base = Path(base)
    target = base / 'icons' / mode['id']
    theme = Path.home() / '.local/share/icons' / mode['icons']
    donor = base / 'icons/neon'
    sources = list(donor.glob('shadow-panel-*.svg')) if mode.get('unbranded') else []
    roles = {p.stem: p for p in sources}
    roles['shadow-panel-bluetooth'] = None
    roles['shadow-panel-bluetooth-off'] = None
    ink = mode['foreground'] if mode.get('unbranded') else mode['accent']
    rgb = [int(ink[i:i+2], 16)/255 for i in (1, 3, 5)]
    matrix = ' '.join(f'0 0 0 0 {c}' for c in rgb) + ' 0 0 0 1 0'
    for name, source in roles.items():
        if name.startswith('shadow-panel-bluetooth'):
            viewbox = '0 0 24 24'
            extra = '<path d="M3 3l18 18"/>' if name.endswith('-off') else ''
            body = f'<g fill="none" stroke="{ink}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M11 2v20l7-6-13-12m0 16 13-12-7-6"/>{extra}</g>'
        else:
            root = ET.fromstring(source.read_text())
            viewbox = root.get('viewBox', '0 0 24 24')
            drawing = ''.join(ET.tostring(child, encoding='unicode') for child in root)
            body = f'<defs><filter id="panel-ink" color-interpolation-filters="sRGB"><feColorMatrix values="{matrix}"/></filter></defs><g filter="url(#panel-ink)">{drawing}</g>'
        def svg(size):
            return f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="{viewbox}">{body}</svg>'
        paths = [target / (name+'.svg'), target / (name+'.png')]
        if theme.is_dir():
            paths.extend(p for p in theme.rglob(name+'.*') if p.suffix in ('.svg','.png'))
        for path in paths:
            path.parent.mkdir(parents=True, exist_ok=True)
            match = re.search(r'/(\d+)x\d+/', path.as_posix())
            size = int(match[1]) if match else 24
            temp = path.with_name(path.name+'.glyph-new')
            data = svg(size).encode()
            if path.suffix == '.svg':
                temp.write_bytes(data)
            else:
                loader = GdkPixbuf.PixbufLoader.new_with_type('svg')
                loader.write(data)
                loader.close()
                loader.get_pixbuf().savev(str(temp), 'png', [], [])
            temp.replace(path)


def repair_dock_family(mode, base):
    if mode.get('unbranded'):
        return
    import gi
    gi.require_version('GdkPixbuf','2.0')
    from gi.repository import GdkPixbuf
    base=Path(base)
    donor=Path('/usr/share/shadowrealm-os/desktop/runtime/icons/neon')
    palette=base/'icons'/mode['id']
    theme=Path.home()/'.local/share/icons'/mode['icons']
    for role in ('browser','control-center','files','shield','task-manager','terminal'):
        name='orbital-dock-'+role
        source=donor/(name+'.svg')
        if not source.is_file():continue
        text=signature_dock_svg(source.read_text(),mode)
        paths=[palette/(name+'.svg'),palette/(name+'.png')]
        if theme.is_dir():
            paths.extend(p for p in theme.rglob('*') if p.is_file() and
                         p.stem in (name,'shadowrealm-os-release-'+name,'shadowrealm-os-app-'+name)
                         and p.suffix in ('.png','.svg'))
        for path in paths:
            path.parent.mkdir(parents=True,exist_ok=True)
            match=re.search(r'/(\d+)x\d+/',path.as_posix());size=int(match[1]) if match else 64
            data=re.sub(r'width="64" height="64"',f'width="{size}" height="{size}"',text,count=1).encode()
            temp=path.with_name(path.name+'.dock-new')
            if path.suffix=='.svg':temp.write_bytes(data)
            else:
                loader=GdkPixbuf.PixbufLoader.new_with_type('svg');loader.write(data);loader.close()
                loader.get_pixbuf().savev(str(temp),'png',[],[])
            temp.replace(path)


def repair_icons(mode, base):
    repair_dock_family(mode,base)
    repair_panel_glyphs(mode,base)


def migrate_icon_families(base):
    import json,subprocess
    base=Path(base)
    marker=Path.home()/'.local/state/shadowrealm-os/icon-families-v1'
    if marker.exists():return
    modes=json.loads((base/'appearance-modes.json').read_text())
    for identity,record in modes.items():
        repair_icons(dict(record,id=identity),base)
        subprocess.run(['gtk-update-icon-cache','-q','-f',str(Path.home()/'.local/share/icons'/record['icons'])],check=True)
    marker.parent.mkdir(parents=True,exist_ok=True)
    marker.write_text('1\n')

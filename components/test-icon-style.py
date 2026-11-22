from pathlib import Path
import tempfile
import xml.etree.ElementTree as ET
from shadow_icon_style import selected_icons, signature_dock_svg

modes={'neon':{'icons':'Neon'},'blue':{'icons':'Blue'}}
with tempfile.TemporaryDirectory() as folder:
    config=Path(folder)
    assert selected_icons(modes,'blue',config)[1]['icons']=='Blue'
    (config/'icon-style').write_text('neon\n')
    assert selected_icons(modes,'blue',config)[1]['icons']=='Neon'
    assert selected_icons(modes,'blue',config,'default')[1]['icons']=='Blue'
    try:selected_icons(modes,'blue',config,'../../other')
    except ValueError:pass
    else:raise AssertionError('Unrecognized icon style accepted')
    (config/'icon-style').write_text('removed-theme\n')
    assert selected_icons(modes,'blue',config)[1]['icons']=='Blue'

source='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><defs><linearGradient id="plate"><stop stop-color="#c60011"/><stop/><stop/></linearGradient><linearGradient id="rim"><stop/><stop/><stop/></linearGradient></defs><path d="M1 2L3 4" stroke="#00eafb"/></svg>'
ns='{http://www.w3.org/2000/svg}'
for accent in ['#ff0000','#00ff00','#0000ff']:
    root=ET.fromstring(signature_dock_svg(source,{'accent':accent,'secondary':'#ffffff','foreground':'#eeeeee'}))
    assert next(root.iter(ns+'path')).get('d')=='M1 2L3 4'
    plate=next(g for g in root.iter(ns+'linearGradient') if g.get('id')=='plate')
    assert [s.get('stop-color') for s in plate]==['#252734','#090a12','#11121a']
print('PASS icon override selection, invalid/retired choices and shared dock geometry/surface')

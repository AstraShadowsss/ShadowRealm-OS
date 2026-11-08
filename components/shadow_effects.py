"""Background-only effects for ShadowRealm-OS GTK windows; never fades widgets/text."""
from pathlib import Path
import json,subprocess
import gi
gi.require_version('Gtk','3.0')
from gi.repository import Gtk,Gio
_provider=None
_controls=None
_monitor=None
def attach(window):
 global _provider,_monitor,_controls
 visual=window.get_screen().get_rgba_visual()
 if visual:window.set_visual(visual)
 window.set_app_paintable(False);window.set_name('shadow-settings-window')
 if _provider:return
 folder=Path.home()/'.config/shadowrealm-os';folder.mkdir(parents=True,exist_ok=True);path=folder/'transparency.css'
 _provider=Gtk.CssProvider();_controls=Gtk.CssProvider()
 modes=Path.home()/'.local/share/shadow-link/appearance-modes.json'
 def refresh(*args):
  if path.exists():_provider.load_from_path(str(path))
  try:
   mode=(folder/'appearance-mode').read_text().strip()
   accent=json.loads(modes.read_text())[mode]['accent']
   if len(accent)!=7 or accent[0]!='#':return
   rgb=[int(accent[i:i+2],16)/255 for i in (1,3,5)]
   linear=[c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4 for c in rgb]
   foreground='#111115' if sum(c*w for c,w in zip(linear,(.2126,.7152,.0722)))>.18 else '#ffffff'
   css=(
    f'@define-color shadow_control_accent {accent};'
    f'@define-color shadow_control_ink {foreground};'
    '#shadow-settings-window entry:focus, #shadow-settings-window combobox button:focus, '
    '#shadow-settings-window button:focus { outline-color:@shadow_control_accent; }'
    '#shadow-settings-window entry:focus { border-color:@shadow_control_accent; '
    'box-shadow:inset 0 0 0 1px @shadow_control_accent; }'
    '#shadow-settings-window check:checked, #shadow-settings-window radio:checked, '
    '#shadow-settings-window switch:checked, #shadow-settings-window scale highlight { '
    'background-image:none; background-color:@shadow_control_accent; border-color:@shadow_control_accent; '
    'color:@shadow_control_ink; }'
    '#shadow-settings-window button:checked, #shadow-settings-window button.suggested-action { '
    'background-image:none; background-color:@shadow_control_accent; border-color:@shadow_control_accent; '
    'color:@shadow_control_ink; }'
   )
   _controls.load_from_data(css.encode())
  except (OSError,ValueError,KeyError):return
 refresh()
 Gtk.StyleContext.add_provider_for_screen(window.get_screen(),_provider,Gtk.STYLE_PROVIDER_PRIORITY_USER)
 Gtk.StyleContext.add_provider_for_screen(window.get_screen(),_controls,Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION+10)
 _monitor=Gio.File.new_for_path(str(folder)).monitor_directory(Gio.FileMonitorFlags.NONE,None);_monitor.connect('changed',refresh)
def panel_opacity(panel,value):
 def set_value(prop,values,types):
  args=['xfconf-query','-c','xfce4-panel','-p',f'/panels/panel-{panel}/'+prop]
  if len(values)>1:args+=['--force-array']
  for kind,entry in zip(types,values):args+=['-t',kind,'-s',str(entry)]
  result=subprocess.run(args,capture_output=True)
  if result.returncode:subprocess.run(args+['--create'],capture_output=True,check=True)
 if value==100:set_value('background-style',[0],['int']);return
 home=Path.home();modes=json.loads((home/'.local/share/shadow-link/appearance-modes.json').read_text());mode=(home/'.config/shadowrealm-os/appearance-mode').read_text().strip();record=modes[mode]
 rgb=[int(record['background'][i:i+2],16)/255 for i in (1,3,5)]
 if record.get('plain'):
  accent=[int(record['accent'][i:i+2],16)/255 for i in (1,3,5)];rgb=[a*.8+b*.2 for a,b in zip(rgb,accent)]
 set_value('background-rgba',rgb+[max(0,min(100,value))/100],['double']*4);set_value('background-style',[1],['int'])
def sync_panels():
 cfg=Path.home()/'.config/shadowrealm-os/transparency.ini'
 values=dict(line.split('=',1) for line in cfg.read_text().splitlines() if '=' in line) if cfg.exists() else {}
 for key,panel in [('panel-opacity',1),('dock-opacity',2)]:
  value=int(values.get(key,100))
  panel_opacity(panel,value)

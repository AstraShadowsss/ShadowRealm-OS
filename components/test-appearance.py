#!/usr/bin/python3
"""Open every Appearance page and test a theme round-trip in a test desktop."""
from pathlib import Path
import importlib.util,sys,time,subprocess
from importlib.machinery import SourceFileLoader
source=Path(sys.argv[1]).resolve();sys.path.insert(0,str(source.parent));spec=importlib.util.spec_from_loader('appearance_test',SourceFileLoader('appearance_test',str(source)));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
from gi.repository import Gtk,GLib
app=module.Backgrounds();app.register(None);app.activate()
assert app.window.get_visible() and app.tabs.get_n_pages()==4
assert len(app.style_buttons)==sum(not entry.get('variant_of') for entry in app.modes.values())
assert len(app.style_buttons)==9
for mode in ('professional-ocean','professional-graphite','professional-plum'):
 assert app.modes[mode].get('variant_of')=='professional'
assert 'black-white' in app.modes and 'blue-white' not in app.modes
for i in range(4):
 app.tabs.set_current_page(i)
 while Gtk.events_pending():Gtk.main_iteration_do(False)
original=(Path.home()/'.config/shadowrealm-os/appearance-mode').read_text().strip();targets=['black-white',original];results=[];started=time.monotonic();loop=GLib.MainLoop();failure=[]
def apply(mode):
 app.style_choice=mode;app.apply_style_button.emit('clicked')
def poll():
 try:
  if time.monotonic()-started>80:raise AssertionError('Appearance apply timed out')
  if app.apply_style_button.get_sensitive():
   expected=targets[len(results)];actual=(Path.home()/'.config/shadowrealm-os/appearance-mode').read_text().strip()
   assert actual==expected,(actual,expected,app.style_status.get_text())
   assert app.style_status.get_text().startswith('Complete theme applied.'),app.style_status.get_text()
   results.append(expected)
   if len(results)==2:app.window.close();loop.quit();return False
   apply(targets[1])
  return True
 except Exception as error:failure.append(str(error));app.window.close();loop.quit();return False
apply(targets[0]);GLib.timeout_add(250,poll);loop.run();assert not failure,failure
print('PASS Appearance: all four pages, nine theme groups, Professional accents, Black & White apply and original-theme restore')

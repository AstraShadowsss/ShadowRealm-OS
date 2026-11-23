#!/usr/bin/python3
"""Check local theme migration without replacing unrelated custom styles."""
from pathlib import Path
import importlib.util,tempfile,sys
from importlib.machinery import SourceFileLoader
source=sys.argv[1] if len(sys.argv)>1 else '/usr/bin/shadowrealm-os-desktop'
spec=importlib.util.spec_from_loader('desktop',SourceFileLoader('desktop',source));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
with tempfile.TemporaryDirectory(prefix='sr-control-finish-') as tmp:
 root=Path(tmp);home=root/'home';share=root/'share';relative=Path('ShadowRealm-OS-Test/gtk-3.0/gtk.css');factory=share/'themes'/relative;local=home/'.themes'/relative
 factory.parent.mkdir(parents=True);local.parent.mkdir(parents=True);prefix='/* User choice */ label {font-size:15px;}\n';local.write_text(prefix)
 start='/* ShadowRealm control finish */';end='/* End ShadowRealm control finish */';factory.write_text('/* base */\n'+start+'\nbutton {border-radius:7px;}\n'+end)
 module.refresh_control_finish(home,share);assert local.read_text().startswith(prefix);assert 'border-radius:7px' in local.read_text();first=local.read_bytes();module.refresh_control_finish(home,share);assert local.read_bytes()==first
 suffix='\n/* More user styles */ entry {font-size:16px;}';local.write_text(local.read_text()+suffix);factory.write_text(factory.read_text().replace('7px','8px'));module.refresh_control_finish(home,share);assert local.read_text().startswith(prefix) and local.read_text().endswith(suffix);assert 'border-radius:8px' in local.read_text() and 'border-radius:7px' not in local.read_text()
 outside=root/'outside';outside.write_text('unchanged');local.unlink();local.symlink_to(outside);module.refresh_control_finish(home,share);assert outside.read_text()=='unchanged'
print('PASS: control styles updated idempotently; custom prefix/suffix and symlink targets preserved')

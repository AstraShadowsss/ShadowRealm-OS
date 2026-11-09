#!/usr/bin/python3
"""Exercise fresh provisioning and an existing account's asset migration."""
from pathlib import Path
import importlib.util,tempfile,json
p=Path('/usr/bin/shadowrealm-os-desktop');spec=importlib.util.spec_from_file_location('desktop',str(p))
# Extensionless executable: load through SourceFileLoader.
from importlib.machinery import SourceFileLoader
spec=importlib.util.spec_from_loader('desktop',SourceFileLoader('desktop',str(p)));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
with tempfile.TemporaryDirectory(prefix='sr-assets-test-') as td:
 home=Path(td);base=module.provision(home)
 cfg=home/'.config/shadowrealm-os';settings=cfg/'transparency.ini';settings.write_text('[Appearance]\nterminal-opacity=73\n')
 photo=home/'Pictures/Backgrounds/my-own-wallpaper.png';photo.write_bytes(b'preserve-user-file')
 (cfg/'appearance-mode').write_text('blue-white\n')
 module.provision(home)
 assert (cfg/'appearance-mode').read_text().strip()=='black-white'
 assert settings.read_text().endswith('terminal-opacity=73\n') and photo.read_bytes()==b'preserve-user-file'
 modes=json.loads((base/'appearance-modes.json').read_text());assert 'black-white' in modes and 'blue-white' not in modes
 for mode,record in modes.items():assert Path(record['logo']).is_file() and Path(record['wallpaper']).is_file()
 module.provision(home)
 assert settings.read_text().endswith('terminal-opacity=73\n')
for folder in [Path('/usr/share/shadowrealm-os/desktop/runtime/bin'),Path('/usr/bin')]:
 for f in folder.iterdir():
  if not f.is_file() or f.is_symlink() or (folder.name=='bin' and folder.parent==Path('/usr') and not f.name.startswith('shadowrealm-os')):continue
  data=f.read_bytes()
  if data.startswith(b'#!'):assert b'\r' not in data.split(b'\n',1)[0],f
print('PASS: fresh provision, existing-account palette migration, custom settings/files preserved, valid Linux launchers')

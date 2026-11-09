#!/usr/bin/python3
from pathlib import Path
import sys
root=Path(sys.argv[1])
assert (root/'var/lib/dpkg/status').is_file()
for p in list((root/'usr/share/icons').glob('ShadowOS-*')) + list((root/'usr/share/icons').glob('ShadowRealm-OS-BlueWhite')):
 if p.is_symlink() or not p.is_dir():continue
 entries=list(p.iterdir())
 if all(f.name=='icon-theme.cache' and f.is_file() for f in entries):
  for f in entries:f.unlink()
  p.rmdir()
print('Removed only orphaned old icon-cache directories; live themes are preserved.')

#!/usr/bin/python3
"""Read-only checks for credentials and personal state in a factory root."""
import argparse
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('root', type=Path)
p.add_argument('--forbid-text', action='append', default=[])
a = p.parse_args()
root = a.root.resolve()
assert (root/'etc/passwd').is_file(), 'Not a mounted Linux root'
bad = set()
for pattern in (
    'root/.bash_history', 'root/.lesshst', 'root/.viminfo',
    'root/.ssh/*', 'root/.gnupg/private-keys-v1.d/*', 'root/.aws/credentials',
    'root/.config/rclone/rclone.conf', 'etc/skel/.ssh/*',
    'etc/skel/.gnupg/private-keys-v1.d/*', 'etc/skel/.aws/credentials',
    'etc/ssh/ssh_host_*_key', 'etc/NetworkManager/system-connections/*',
    'var/lib/NetworkManager/secret_key', 'var/lib/NetworkManager/seen-bssids',
    'var/lib/NetworkManager/timestamps',
):
    for f in root.glob(pattern):
        if f.is_symlink() or (f.is_file() and f.stat().st_size):
            bad.add(str(f.relative_to(root)))
for f in [root/'etc/apt/auth.conf', *(root/'etc/apt/auth.conf.d').glob('*.conf')]:
    if f.is_symlink():
        bad.add(str(f.relative_to(root)))
    elif f.is_file() and any(line.strip() and not line.lstrip().startswith('#') for line in f.read_text().splitlines()):
        bad.add(str(f.relative_to(root)))
for subtree in ('etc', 'root', 'usr/local', 'usr/share/shadowrealm-os', 'var/lib'):
    if not a.forbid_text:
        break
    for f in (root/subtree).rglob('*'):
        if f.is_symlink() or not f.is_file() or f.stat().st_size > 4*1024*1024:
            continue
        data = f.read_bytes()
        if any(text.encode() in data for text in a.forbid_text):
            bad.add(str(f.relative_to(root)))
if bad:
    raise SystemExit('Factory privacy audit failed (paths only):\n'+'\n'.join(sorted(bad)))
print('PASS factory root: no saved credentials, private host keys or personal network/history files found.')

#!/usr/bin/env python3
"""Exercise Windows line endings and a restrictive package-build umask."""
from pathlib import Path
import tempfile,os,stat
from package_files import prepare_package

with tempfile.TemporaryDirectory() as temporary:
    root=Path(temporary)/'package'
    original=os.umask(0o077)
    try:
        for folder in ['usr/share/example','usr/bin','etc/xdg/autostart','etc/private','DEBIAN']:
            (root/folder).mkdir(parents=True,exist_ok=True)
        script=root/'usr/bin/example';script.write_bytes(b'#!/bin/sh\r\necho ready\r\n');script.chmod(0o700)
        data=root/'usr/share/example/data';data.write_text('readable')
        (root/'DEBIAN/control').write_text('Package: example\n')
        private=root/'etc/private/key';private.write_text('private');private.chmod(0o600)
        outside=Path(temporary)/'outside';outside.write_text('unchanged');outside.chmod(0o600)
        (root/'usr/share/example/link').symlink_to(outside)
    finally:os.umask(original)
    prepare_package(root)
    assert script.read_bytes()==b'#!/bin/sh\necho ready\n'
    assert stat.S_IMODE(script.stat().st_mode)==0o755
    assert stat.S_IMODE(data.stat().st_mode)==0o644
    assert stat.S_IMODE((root/'DEBIAN').stat().st_mode)==0o755
    assert stat.S_IMODE((root/'etc/xdg/autostart').stat().st_mode)==0o755
    assert stat.S_IMODE(private.stat().st_mode)==0o600
    assert stat.S_IMODE(outside.stat().st_mode)==0o600
print('PASS package permissions, private configuration, symlinks and script line endings')

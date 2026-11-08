"""Rebuild desktop defaults from the existing curated release package."""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from panel_defaults import LAUNCHERS, seed_panel

source, output = map(Path, sys.argv[1:])
if output.exists():
    raise SystemExit(f"Output already exists: {output}")
here = Path(__file__).resolve().parent
with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    subprocess.run(["dpkg-deb", "--raw-extract", source, root], check=True)
    seed_panel(root)
    desktop = root / "usr/share/shadowrealm-os/desktop"
    modes = json.loads((desktop / "appearance-modes.json").read_text())
    for mode, record in modes.items():
        target = root / "usr/share/icons" / record["icons"] / "48x48/apps"
        target.mkdir(parents=True, exist_ok=True)
        for _, _, icon in LAUNCHERS.values():
            shutil.copyfile(desktop / "runtime/icons" / mode / f"{icon}.png",
                            target / f"shadowrealm-os-release-{icon}.png")
    shutil.copyfile(here / "shadowrealm-os-desktop.py", root / "usr/bin/shadowrealm-os-desktop")
    control = root / "DEBIAN/control"
    original = control.read_text()
    assert "Version: 0.1.1\n" in original
    control.write_text(original.replace("Version: 0.1.1\n", "Version: 0.1.2\n", 1))
    if (root / "DEBIAN/md5sums").exists():
        (root / "DEBIAN/md5sums").unlink()
    subprocess.run(["dpkg-deb", "--root-owner-group", "--build", root, output], check=True)

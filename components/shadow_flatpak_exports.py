#!/usr/bin/python3
"""Expose canonical Flatpak launchers to the existing XFCE session."""

from pathlib import Path
import re
import subprocess


def sync_exports():
    home = Path.home()
    data = home / ".local/share"
    roots = (data / "flatpak/exports/share", Path("/var/lib/flatpak/exports/share"))
    apps = data / "applications"
    apps.mkdir(parents=True, exist_ok=True)
    for root in roots:
        for entry in sorted((root / "applications").glob("*.desktop")):
            if not entry.is_file() or not re.fullmatch(r"[A-Za-z0-9_.-]+\.desktop", entry.name):
                continue
            target = apps / entry.name
            if not target.exists():
                if target.is_symlink():
                    old = target.readlink()
                    if not any(old.is_relative_to(known) for known in roots):
                        continue
                    target.unlink()
                try:
                    target.symlink_to(entry)
                except FileExistsError:
                    pass
        icons = root / "icons/hicolor"
        for icon in icons.glob("*/apps/*"):
            if not icon.is_file():
                continue
            target = data / "icons/hicolor" / icon.relative_to(icons)
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                if target.is_symlink():
                    old = target.readlink()
                    if not any(old.is_relative_to(known) for known in roots):
                        continue
                    target.unlink()
                try:
                    target.symlink_to(icon)
                except FileExistsError:
                    pass
    for entry in apps.glob("*.desktop"):
        if entry.is_symlink() and not entry.exists():
            if any(entry.readlink().is_relative_to(root) for root in roots):
                entry.unlink()


if __name__ == "__main__":
    sync_exports()

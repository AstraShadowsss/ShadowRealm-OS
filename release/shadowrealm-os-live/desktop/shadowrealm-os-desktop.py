#!/usr/bin/python3
"""Install ShadowRealm-OS defaults for an individual desktop account."""
import json
import fcntl
import tempfile
import time
import os
import shutil
import sys
from pathlib import Path

PAYLOAD = Path("/usr/share/shadowrealm-os/desktop")
COMMANDS = {
    "control-center": ("shadow-link", "--control-center"),
    "appearance": ("shadow-appearance",),
    "network": ("shadow-link", "--network"),
    "shield": ("shadow-link", "--shield"),
    "audio": ("shadow-link", "--audio"),
    "account": ("shadow-account",),
    "software": ("shadow-software",),
    "terminal": ("shadow-terminal",),
    "files": ("shadow-files",),
    "browser": ("shadow-browser",),
    "bluetooth": ("shadow-link", "--bluetooth"),
    "menu": ("shadow-link", "--menu"),
    "widgets": ("shadow-link", "--widgets"),
    "session": ("shadow-xfce-session",),
}


def copy_defaults(source, target):
    for path in sorted(source.rglob("*")):
        if source.name == "runtime" and path.relative_to(source).parts[0] == "bin":
            continue
        if path.is_symlink():
            continue
        dest = target / path.relative_to(source)
        if path.is_dir():
            dest.mkdir(parents=True, exist_ok=True)
        elif not os.path.lexists(dest):
            dest.parent.mkdir(parents=True, exist_ok=True)
            fd, temporary = tempfile.mkstemp(prefix=".shadow-default-", dir=dest.parent)
            os.close(fd)
            try:
                shutil.copy2(path, temporary)
                try:
                    os.link(temporary, dest)
                except FileExistsError:
                    pass
            finally:
                Path(temporary).unlink(missing_ok=True)


def write_default(path, text):
    if os.path.lexists(path):
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8") as file:
            file.write(text)
    except FileExistsError:
        pass


def _provision_unlocked(home, payload=PAYLOAD, system_share=Path("/usr/share")):
    base = home / ".local/share/shadow-link"
    cfg = home / ".config/shadowrealm-os"
    marker = home / ".local/state/shadowrealm-os/desktop-defaults-v1"
    # Managed code is shared and replaced atomically by dpkg on upgrades.
    # Existing custom regular files are deliberately left for explicit migration.
    programs = base / "bin"
    programs.mkdir(parents=True, exist_ok=True)
    for source in (payload / "runtime/bin").iterdir():
        target = programs / source.name
        if source.is_file() and not os.path.lexists(target):
            target.symlink_to(source)
    if marker.is_file():
        return base
    copy_defaults(payload / "runtime", base)
    copy_defaults(payload / "wallpapers", home / "Pictures/Backgrounds")
    modes = json.loads((payload / "appearance-modes.json").read_text())
    for mode, record in modes.items():
        name = record["icons"]
        copy_defaults(system_share / "icons" / name, home / ".local/share/icons" / name)
        name = record["theme"]
        copy_defaults(system_share / "themes" / name, home / ".themes" / name)
        record["logo"] = str(base / "icons" / mode / Path(record["logo"]).name)
        record["wallpaper"] = str(home / "Pictures/Backgrounds" / Path(record["wallpaper"]).name)
        if not Path(record["logo"]).is_file() or not Path(record["wallpaper"]).is_file():
            raise RuntimeError(f"Missing artwork for {mode}.")
    write_default(base / "appearance-modes.json", json.dumps(modes, indent=2) + "\n")
    write_default(cfg / "appearance-mode", "neon\n")
    current = base / "icons/current"
    if not os.path.lexists(current):
        current.symlink_to((cfg / "appearance-mode").read_text().strip(), target_is_directory=True)
    write_default(marker, "1\n")
    return base


def provision(home, payload=PAYLOAD, system_share=Path("/usr/share")):
    state = home / ".local/state/shadowrealm-os"
    state.mkdir(parents=True, exist_ok=True)
    with (state / "provision.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        return _provision_unlocked(home, payload, system_share)


def seed_wallpaper(home, base):
    marker = home / ".local/state/shadowrealm-os/desktop-wallpaper-v1"
    if marker.is_file():
        return True
    sys.path.insert(0, str(base / "bin"))
    from shadow_appearance_desktop import query, set_wallpaper, wallpaper_properties

    properties = wallpaper_properties()
    defaults = []
    for prop in properties:
        current = query("xfce4-desktop", prop)
        if not current or Path(current).is_relative_to("/usr/share/backgrounds/xfce") or Path(current).is_relative_to("/usr/share/desktop-base"):
            defaults.append(prop)
    if defaults:
        modes = json.loads((base / "appearance-modes.json").read_text())
        mode = (home / ".config/shadowrealm-os/appearance-mode").read_text().strip()
        set_wallpaper(modes[mode]["wallpaper"], defaults)
    if properties:
        write_default(marker, "1\n")
    return bool(properties)


def main():
    if os.geteuid() == 0:
        raise SystemExit("Start ShadowRealm-OS Desktop as your regular account.")
    action = sys.argv[1] if len(sys.argv) == 2 else ""
    if action not in COMMANDS and action != "prepare":
        raise SystemExit("Choose a valid ShadowRealm-OS desktop action.")
    base = provision(Path.home())
    if action == "prepare":
        for attempt in range(30):
            if seed_wallpaper(Path.home(), base):
                break
            time.sleep(0.5)
        return
    command, *args = COMMANDS[action]
    binary = base / "bin" / command
    os.environ["PATH"] = str(base / "bin") + ":" + os.environ.get("PATH", "/usr/bin:/bin")
    os.execv(binary, [str(binary), *args])


if __name__ == "__main__":
    main()

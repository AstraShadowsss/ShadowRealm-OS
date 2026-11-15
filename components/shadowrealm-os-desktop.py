#!/usr/bin/python3
"""Install ShadowRealm-OS defaults for an individual desktop account."""
import hashlib
import json
import fcntl
import tempfile
import time
import os
import shutil
import subprocess
import sys
from pathlib import Path

PAYLOAD = Path("/usr/share/shadowrealm-os/desktop")
COMMANDS = {
    "clock": ("gnome-clocks",),
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


def copy_file_default(source, destination):
    if os.path.lexists(destination):
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".shadow-default-", dir=destination.parent)
    os.close(fd)
    try:
        shutil.copy2(source, temporary)
        try:
            os.link(temporary, destination)
        except FileExistsError:
            pass
    finally:
        Path(temporary).unlink(missing_ok=True)


def copy_defaults(source, target):
    for path in sorted(source.rglob("*")):
        if source.name == "runtime" and path.relative_to(source).parts[0] == "bin":
            continue
        if path.is_symlink():
            continue
        dest = target / path.relative_to(source)
        if path.is_dir():
            dest.mkdir(parents=True, exist_ok=True)
        else:
            copy_file_default(path, dest)


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
    # Package-owned assets have a separate version from user settings. Refresh
    # only shipped filenames; never replace unrelated user wallpapers or icons.
    asset_marker = home / ".local/state/shadowrealm-os/icon-catalog-v3"
    if marker.is_file() and not asset_marker.is_file():
        def refresh_owned(source, destination):
            for original in source.rglob("*"):
                if original.is_symlink() or not original.is_file():
                    continue
                dest = destination / original.relative_to(source)
                if not dest.parent.resolve().is_relative_to(home.resolve()):
                    continue
                dest.parent.mkdir(parents=True, exist_ok=True)
                fd, temporary = tempfile.mkstemp(prefix=".shadow-assets-", dir=dest.parent)
                os.close(fd)
                try:
                    shutil.copy2(original, temporary)
                    os.replace(temporary, dest)
                finally:
                    Path(temporary).unlink(missing_ok=True)
        for source, destination in (
            (payload / "runtime/icons", base / "icons"),
            (payload / "wallpapers", home / "Pictures/Backgrounds"),
        ):
            refresh_owned(source, destination)
        modes = json.loads((payload / "appearance-modes.json").read_text())
        for mode, record in modes.items():
            for category, local, name in (
                ("icons", home / ".local/share/icons", record["icons"]),
                ("themes", home / ".themes", record["theme"]),
            ):
                refresh_owned(system_share / category / name, local / name)
            record["logo"] = str(base / "icons" / mode / Path(record["logo"]).name)
            record["wallpaper"] = str(home / "Pictures/Backgrounds" / Path(record["wallpaper"]).name)
        (base / "appearance-modes.json").write_text(json.dumps(modes, indent=2) + "\n")
        selected = cfg / "appearance-mode"
        if selected.exists() and selected.read_text().strip() == "blue-white":
            selected.write_text("black-white\n")
        # Remove only the retired package-provided theme, never arbitrary files.
        for retired in (home / ".themes/ShadowRealm-OS-BlueWhite",
                        home / ".local/share/icons/ShadowRealm-OS-BlueWhite",
                        base / "icons/blue-white"):
            if retired.is_dir() and not retired.is_symlink():
                shutil.rmtree(retired)
        for retired in (home / "Pictures/Backgrounds").glob("ShadowRealm-OS-BlueWhite-*.png"):
            retired.unlink()
        current = base / "icons/current"
        if current.is_symlink() and os.readlink(current) == "blue-white":
            current.unlink()
            current.symlink_to("black-white")
        write_default(asset_marker, "2\n")
    professional = Path("ShadowRealm-OS-Professional/gtk-3.0/gtk.css")
    local_theme = home / ".themes" / professional
    shipped_theme = system_share / "themes" / professional
    # Update copies of the previous factory stylesheet. Keep local edits.
    factory_hash = "fc2a4d0085f1dc9a3ce46303082ab1b77497e61b81172b67b4c8c763fe25faa7"
    if (local_theme.is_file() and shipped_theme.is_file() and
            local_theme.resolve().is_relative_to(home.resolve())):
        installed = local_theme.read_bytes()
        updated = shipped_theme.read_bytes()
        if installed != updated and hashlib.sha256(installed).hexdigest() == factory_hash:
            with tempfile.NamedTemporaryFile(dir=local_theme.parent, delete=False) as temp:
                temp.write(updated)
                os.chmod(temp.name, 0o644)
            try:
                os.replace(temp.name, local_theme)
            finally:
                Path(temp.name).unlink(missing_ok=True)
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


def seed_wallpaper(home, base, *, early=False):
    marker = home / ".local/state/shadowrealm-os/desktop-wallpaper-v1"
    if marker.is_file():
        return True
    from shadow_appearance_desktop import query, set_wallpaper, wallpaper_properties

    properties = wallpaper_properties()
    defaults = []
    for prop in properties:
        current = query("xfce4-desktop", prop)
        if not current or Path(current).is_relative_to("/usr/share/backgrounds/xfce") or Path(current).is_relative_to("/usr/share/desktop-base"):
            defaults.append(prop)
    if defaults:
        selection = home / ".config/shadowrealm-os/appearance-mode"
        mode = selection.read_text().strip() if selection.is_file() else "neon"
        manifest = (PAYLOAD if early else base) / "appearance-modes.json"
        modes = json.loads(manifest.read_text())
        wallpaper = Path(modes[mode]["wallpaper"])
        if early:
            wallpaper = PAYLOAD / "wallpapers" / wallpaper.name
        set_wallpaper(wallpaper, defaults)
    if properties:
        write_default(marker, "1\n")
    return bool(properties)


def launch_widgets(home, payload=PAYLOAD):
    # The separate first-login action still provisions the complete account.
    # Live status panels need their launcher and logo, not the theme catalog.
    base = home / ".local/share/shadow-link"
    runtime = payload / "runtime"
    copy_file_default(runtime / "logo.png", base / "logo.png")
    local_bin = base / "bin"
    package_bin = runtime / "bin"
    binary = local_bin / "shadow-link"
    if not binary.is_file():
        binary = package_bin / "shadow-link"
    os.environ["PATH"] = os.pathsep.join(
        [str(local_bin), str(package_bin), os.environ.get("PATH", "/usr/bin:/bin")]
    )
    os.execv(binary, [str(binary), "--widgets"])


def main():
    if os.geteuid() == 0:
        raise SystemExit("Start ShadowRealm-OS Desktop as your regular account.")
    action = sys.argv[1] if len(sys.argv) == 2 else ""
    if action == "sync-widgets":
        home = Path.home()
        mode = home / ".config/shadowrealm-os/appearance-mode"
        sys.path.insert(0, str(PAYLOAD / "runtime/bin"))
        from shadow_whole_theme import set_widgets
        set_widgets(mode.is_file() and mode.read_text().strip() == "professional",
                    home / ".local/share/shadow-link")
        return
    if action not in COMMANDS and action != "prepare":
        raise SystemExit("Choose a valid ShadowRealm-OS desktop action.")
    if action == "widgets":
        launch_widgets(Path.home())
        return
    if action == "prepare":
        # The packaged wallpaper is already usable while the profile's
        # wallpapers, themes and icons are being copied into the home folder.
        # Display discovery may still be unavailable at this point.
        sys.path.insert(0, str(PAYLOAD / "runtime/bin"))
        try:
            seed_wallpaper(Path.home(), PAYLOAD, early=True)
        except (OSError, ValueError, KeyError, RuntimeError, subprocess.SubprocessError) as error:
            print(f"Desktop wallpaper startup will retry after setup: {error}", file=sys.stderr)
    base = provision(Path.home())
    if action == "prepare":
        # Keep Print consistent with the installed screenshot application.
        # Preserve deliberately chosen shortcuts on existing accounts.
        sys.path.insert(0, str(base / 'bin'))
        from shadow_appearance_desktop import query, set_property
        shortcut_marker = Path.home() / '.local/state/shadowrealm-os/screenshot-default-v1'
        if not shortcut_marker.exists():
            binding = query('xfce4-keyboard-shortcuts', '/commands/custom/Print')
            if not binding or 'xfce4-screenshooter' in binding:
                set_property('xfce4-keyboard-shortcuts', '/commands/custom/Print', '/usr/bin/shutter -s')
            write_default(shortcut_marker, '1\n')
        for attempt in range(30):
            try:
                if seed_wallpaper(Path.home(), base):
                    break
            except (RuntimeError, subprocess.SubprocessError):
                pass
            time.sleep(0.5)
        # Installation is offered only in the temporary live session.
        if Path('/run/live/medium/live/filesystem.squashfs').is_file():
            shortcut = Path.home() / 'Desktop/Install ShadowRealm-OS.desktop'
            # Trust only the unchanged launcher supplied by the installed package.
            # Xfce 4.20 checks a content SHA256, not GNOME's boolean alone.
            import hashlib
            packaged = Path('/usr/share/applications/org.shadowrealm_os.install.desktop')
            if packaged.is_file():
                content = packaged.read_bytes()
                write_default(shortcut, content.decode('utf-8'))
                if shortcut.read_bytes() == content:
                    shortcut.chmod(0o755)
                    for attribute, value in [('metadata::trusted', 'true'),
                        ('metadata::xfce-exe-checksum', hashlib.sha256(content).hexdigest())]:
                        subprocess.run(['gio', 'set', '-t', 'string', str(shortcut), attribute, value],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return
    command, *args = COMMANDS[action]
    binary = base / "bin" / command
    os.environ["PATH"] = str(base / "bin") + ":" + os.environ.get("PATH", "/usr/bin:/bin")
    os.execv(binary, [str(binary), *args])


if __name__ == "__main__":
    main()

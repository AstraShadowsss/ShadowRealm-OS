#!/usr/bin/python3
"""Scale the ShadowRealm-OS desktop to the current display size.

The desktop is laid out in pixels.  On a 1920x1080 screen the same 46 px
panel, 10 pt label and 56 px desktop icon that look normal at 1280x800 are
visibly small.  This module keeps one scale factor for the whole shell and
writes it to XFCE, the window manager, the desktop icon view and the Shadow
Link menu.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

HOME = Path.home()
STATE = HOME / ".local/state/shadowrealm-os/display-scale.json"
MENU_SCALE = HOME / ".config/shadowrealm-os/display-scale"
GTK_CSS = HOME / ".config/gtk-3.0/gtk.css"

# Reference sizes at 1280x800.  Every setting below is derived from these so
# the same proportions are kept on larger and smaller displays.
BASE_PANEL_1 = 46
BASE_PANEL_2 = 75
BASE_PANEL_1_ICON = 32
BASE_PANEL_2_ICON = 48
BASE_SYSTRAY_ICON = 24
BASE_FONT = 10
BASE_CLOCK = 10
BASE_DATE = 8
BASE_DESKTOP_ICON = 56
BASE_PAGER = 15
MIN_SCALE = 0.9
MAX_SCALE = 2.0

CSS_START = "/* ShadowRealm display scale */"
CSS_END = "/* End ShadowRealm display scale */"


def run(args):
    return subprocess.run(args, capture_output=True, text=True)


def xfquery(channel, prop):
    result = run(["xfconf-query", "-c", channel, "-p", prop])
    return result.stdout.strip() if result.returncode == 0 else None


def xfset(channel, prop, kind, value):
    result = run(["xfconf-query", "-c", channel, "-p", prop, "--create",
                  "--type", kind, "--set", str(value)])
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or f"Could not set {channel} {prop}")


def systray_plugins():
    result = run(["xfconf-query", "-c", "xfce4-panel", "-l", "-v"])
    plugins = []
    for line in result.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[1] == "systray":
            match = re.match(r"^/plugins/(plugin-\d+)$", parts[0])
            if match:
                plugins.append(match.group(1))
    return plugins


def screen_size():
    result = run(["xrandr", "--current"])
    if result.returncode:
        return None
    match = re.search(r"current\s+(\d+)\s*x\s*(\d+)", result.stdout)
    return (int(match.group(1)), int(match.group(2))) if match else None


def factor_for(width, height):
    return max(MIN_SCALE, min(MAX_SCALE, min(width / 1280.0, height / 800.0)))


def scaled_font(current, base, fallback):
    family = fallback
    if current:
        match = re.match(r"^(.*?)\s+\d+(?:\.\d+)?$", current)
        if match:
            family = match.group(1)
    return f"{family} {max(1, round(base * factor))}"


def write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".new")
    temporary.write_text(text)
    os.replace(temporary, path)


def update_pager_css(pixels):
    text = GTK_CSS.read_text() if GTK_CSS.is_file() else ""
    if CSS_START in text:
        before, _, rest = text.partition(CSS_START)
        text = before + rest.partition(CSS_END)[2]
    block = f"{CSS_START}\n#pager-4 button {{ font-size: {pixels}px; }}\n{CSS_END}\n"
    text = text.rstrip("\n") + "\n\n" + block
    write_text(GTK_CSS, text)


def menu_scale_percent():
    if not MENU_SCALE.is_file():
        return 100
    try:
        return max(60, min(220, int(MENU_SCALE.read_text().strip())))
    except (OSError, ValueError):
        return 100


def apply_scale(force=False, restart=True, verbose=False):
    global factor
    size = screen_size()
    if not size:
        return 1.0
    width, height = size
    factor = factor_for(width, height)
    previous = {}
    if STATE.is_file():
        try:
            previous = json.loads(STATE.read_text())
        except (OSError, ValueError):
            previous = {}
    if not force and previous.get("width") == width and previous.get("height") == height:
        return factor

    panel_1 = max(28, round(BASE_PANEL_1 * factor))
    panel_2 = max(40, round(BASE_PANEL_2 * factor))
    xfset("xfce4-panel", "/panels/panel-1/size", "uint", panel_1)
    xfset("xfce4-panel", "/panels/panel-2/size", "uint", panel_2)
    xfset("xfce4-panel", "/panels/panel-1/icon-size", "uint", max(16, round(BASE_PANEL_1_ICON * factor)))
    xfset("xfce4-panel", "/panels/panel-2/icon-size", "uint", max(24, round(BASE_PANEL_2_ICON * factor)))
    tray_icon = max(16, round(BASE_SYSTRAY_ICON * factor))
    for plugin in systray_plugins():
        xfset("xfce4-panel", f"/plugins/{plugin}/icon-size", "int", tray_icon)

    gtk_font = scaled_font(xfquery("xsettings", "/Gtk/FontName"), BASE_FONT, "DejaVu Sans")
    mono_font = scaled_font(xfquery("xsettings", "/Gtk/MonospaceFontName"), BASE_FONT,
                            "DejaVu Sans Mono")
    title_font = scaled_font(xfquery("xfwm4", "/general/title_font"), BASE_FONT,
                             "DejaVu Sans Bold")
    clock_font = scaled_font(xfquery("xfce4-panel", "/plugins/plugin-8/digital-time-font"),
                             BASE_CLOCK, "DejaVu Sans Bold")
    date_font = scaled_font(xfquery("xfce4-panel", "/plugins/plugin-8/digital-date-font"),
                            BASE_DATE, "DejaVu Sans Bold Italic")
    xfset("xsettings", "/Gtk/FontName", "string", gtk_font)
    xfset("xsettings", "/Gtk/MonospaceFontName", "string", mono_font)
    xfset("xfwm4", "/general/title_font", "string", title_font)
    xfset("xfce4-panel", "/plugins/plugin-8/digital-time-font", "string", clock_font)
    xfset("xfce4-panel", "/plugins/plugin-8/digital-date-font", "string", date_font)
    xfset("xfce4-desktop", "/desktop-icons/icon-size", "uint",
          max(32, round(BASE_DESKTOP_ICON * factor)))

    percent = max(60, min(220, round(100 * factor)))
    write_text(MENU_SCALE, f"{percent}\n")
    update_pager_css(max(10, round(BASE_PAGER * factor)))
    write_text(STATE, json.dumps({"width": width, "height": height,
                                  "scale": factor, "panel": panel_1,
                                  "dock": panel_2, "font": gtk_font,
                                  "menu_scale": percent}, indent=2) + "\n")
    if verbose:
        print(f"Display {width}x{height}: {factor:.2f}x, panels {panel_1}/{panel_2}, "
              f"systray {tray_icon}, fonts {gtk_font}, menu {percent}%")
    if restart:
        run(["xfce4-panel", "--restart"])
        run(["xfdesktop", "--reload"])
    return factor


def watch():
    last = None
    while True:
        size = screen_size()
        if size and size != last:
            try:
                apply_scale(force=True)
            except Exception as error:  # Keep watching after a transient XFCE error.
                print(f"Display scale: {error}", file=sys.stderr)
            last = size
        time.sleep(2)


def main():
    parser = argparse.ArgumentParser(description="Scale the ShadowRealm-OS desktop")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--watch", action="store_true")
    parser.add_argument("--print", action="store_true")
    args = parser.parse_args()
    if args.watch:
        watch()
        return
    if args.print:
        size = screen_size()
        print(json.dumps({"screen": size, "scale": factor_for(*size) if size else None,
                          "menu": menu_scale_percent()}))
        return
    apply_scale(force=True, verbose=True)


if __name__ == "__main__":
    main()

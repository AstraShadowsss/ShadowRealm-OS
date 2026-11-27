#!/usr/bin/python3
"""Install the ShadowRealm-OS family messenger icon into every palette.

The icon is not drawn here. It is the same vector plate and the same
``email`` glyph that the desktop's icon engine renders for the dock and
menu messenger role (``orbital-dock-email`` / ``shadow-messenger``), so the
application icon matches the twelve shipped theme icon sets exactly.

Rasterising needs GTK/GdkPixbuf (python3-gi), so run this on a desktop or
build machine:

    python3 messenger/packaging/build-icons.py \
        components/icon-studio/engine/palettes.json \
        messenger/packaging/icons

The release package ships the generated files; building the .deb does not
need this script.
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

SIZES = (16, 24, 32, 48, 64, 96, 128, 256)
NAME = "shadow-messenger-app"
ENGINE = Path(__file__).resolve().parents[2] / "components" / "icon-studio" / "engine"
FALLBACK_PALETTE = "neon"


def raster(svg: bytes, size: int) -> bytes:
    import gi

    gi.require_version("GdkPixbuf", "2.0")
    from gi.repository import GdkPixbuf

    loader = GdkPixbuf.PixbufLoader.new_with_type("svg")
    loader.set_size(size, size)
    loader.write(svg)
    loader.close()
    ok, data = loader.get_pixbuf().save_to_bufferv("png", [], [])
    if not ok:
        raise RuntimeError(f"could not encode {size}px icon")
    return data


def write_icon(mode: dict, render, theme: Path) -> Path:
    svg = render.icon(mode, role="email")
    for size in SIZES:
        target = theme / f"{size}x{size}" / "apps" / f"{NAME}.png"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raster(svg, size))
    target = theme / "scalable" / "apps" / f"{NAME}.svg"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(svg)
    return theme


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: build-icons.py ENGINE_PALETTES_JSON OUTPUT_DIR")
    sys.path.insert(0, str(ENGINE))
    import render  # noqa: PLC0415 - engine path is resolved at runtime

    modes = json.loads(Path(sys.argv[1]).read_text())
    if FALLBACK_PALETTE not in modes:
        raise SystemExit(f"palette manifest has no {FALLBACK_PALETTE!r} entry")
    output = Path(sys.argv[2])
    output.mkdir(parents=True, exist_ok=True)
    for mode in modes.values():
        write_icon(mode, render, output / mode["icons"])
    write_icon(modes[FALLBACK_PALETTE], render, output / "hicolor")
    print(f"Installed the family messenger icon for {len(modes)} palettes plus hicolor in {output}")


if __name__ == "__main__":
    main()

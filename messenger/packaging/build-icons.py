#!/usr/bin/python3
"""Render the Shadow Messenger app icon for every ShadowRealm-OS palette.

The release package ships the generated files, so building the .deb does not
need Pillow or rsvg-convert. Re-run this only when the palette list or the
icon design changes:

    python3 messenger/packaging/build-icons.py \
        branding/palettes.json messenger/packaging/icons
"""
from __future__ import annotations

import base64
import io
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

SCALE = 4
SIZE = 256 * SCALE
SIZES = (16, 24, 32, 48, 64, 96, 128, 256)
THEME_NAMES = {"WhiteSilverGold": "ShadowRealm-OS-White-Silver-Gold"}


def rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def gradient(stops: list[tuple[float, tuple[int, int, int]]]) -> Image.Image:
    """Vertical RGB gradient, rendered at a low resolution and upscaled."""
    column = Image.new("RGB", (1, SIZE))
    for y in range(SIZE):
        position = y / (SIZE - 1)
        left = stops[0]
        right = stops[-1]
        for index in range(len(stops) - 1):
            if stops[index][0] <= position <= stops[index + 1][0]:
                left, right = stops[index], stops[index + 1]
                break
        span = max(1e-9, right[0] - left[0])
        amount = min(1.0, max(0.0, (position - left[0]) / span))
        color = tuple(round(a + (b - a) * amount) for a, b in zip(left[1], right[1]))
        column.putpixel((0, y), color)
    return column.resize((SIZE, SIZE), Image.Resampling.BICUBIC)


def rounded_mask(box: tuple[int, int, int, int], radius: int) -> Image.Image:
    mask = Image.new("L", (SIZE, SIZE))
    ImageDraw.Draw(mask).rounded_rectangle(box, radius=radius, fill=255)
    return mask


def compose(accent: str, secondary: str) -> Image.Image:
    accent_rgb, secondary_rgb = rgb(accent), rgb(secondary)
    outer = rounded_mask((16 * SCALE, 16 * SCALE, SIZE - 16 * SCALE, SIZE - 16 * SCALE), 56 * SCALE)
    plate = rounded_mask((25 * SCALE, 25 * SCALE, SIZE - 25 * SCALE, SIZE - 25 * SCALE), 50 * SCALE)

    rim = gradient([(0.0, accent_rgb), (0.46, (236, 250, 255)), (1.0, secondary_rgb)])
    canvas = Image.new("RGBA", (SIZE, SIZE))
    canvas.paste(rim, mask=outer)

    glow = Image.new("RGBA", (SIZE, SIZE), (*accent_rgb, 0))
    glow.putalpha(outer.filter(ImageFilter.GaussianBlur(10 * SCALE)).point(lambda value: value // 4))
    canvas.alpha_composite(glow)

    dark = gradient([(0.0, (37, 37, 37)), (0.48, (9, 9, 9)), (1.0, (17, 17, 17))]).convert("RGBA")
    canvas.paste(dark, mask=plate)

    # A fine top highlight, matching the rest of the icon family.
    highlight = Image.new("RGBA", (SIZE, SIZE))
    ImageDraw.Draw(highlight).rounded_rectangle(
        (36 * SCALE, 33 * SCALE, SIZE - 36 * SCALE, 42 * SCALE), radius=5 * SCALE,
        fill=(255, 255, 255, 38),
    )
    highlight.putalpha(Image.composite(highlight.getchannel("A"), Image.new("L", (SIZE, SIZE)), plate))
    canvas.alpha_composite(highlight)

    # Filled speech bubble with a tail and three cut-out dots: distinct from
    # the generic email envelope at menu sizes, and legible down to 16 px.
    bubble = Image.new("L", (SIZE, SIZE))
    draw = ImageDraw.Draw(bubble)
    draw.rounded_rectangle(
        (62 * SCALE, 76 * SCALE, 194 * SCALE, 164 * SCALE), radius=27 * SCALE, fill=255,
    )
    draw.polygon(
        [(84 * SCALE, 154 * SCALE), (73 * SCALE, 192 * SCALE), (120 * SCALE, 163 * SCALE)],
        fill=255,
    )
    bubble = bubble.filter(ImageFilter.GaussianBlur(0.6 * SCALE))
    bubble = bubble.point(lambda value: 255 if value > 100 else 0)

    glyph = gradient([(0.0, accent_rgb), (0.55, (236, 250, 255)), (1.0, secondary_rgb)]).convert("RGBA")
    glyph.putalpha(bubble)
    canvas.alpha_composite(glyph)

    dots = Image.new("RGBA", (SIZE, SIZE))
    dot = ImageDraw.Draw(dots)
    for x in (100, 128, 156):
        dot.ellipse(
            ((x - 9) * SCALE, 111 * SCALE, (x + 9) * SCALE, 129 * SCALE),
            fill=(9, 9, 13, 255),
        )
    canvas.alpha_composite(dots)

    outline = Image.new("RGBA", (SIZE, SIZE))
    line = ImageDraw.Draw(outline)
    line.rounded_rectangle(
        (62 * SCALE, 76 * SCALE, 194 * SCALE, 164 * SCALE), radius=27 * SCALE,
        outline=(255, 255, 255, 72), width=max(1, SCALE),
    )
    canvas.alpha_composite(outline)
    return canvas


def render(accent: str, secondary: str, output: Path) -> None:
    master = compose(accent, secondary)
    for size in SIZES:
        target = output / f"{size}x{size}" / "apps" / "shadow-messenger-app.png"
        target.parent.mkdir(parents=True, exist_ok=True)
        master.resize((size, size), Image.Resampling.LANCZOS).save(target, optimize=True)
    buffer = io.BytesIO()
    master.resize((256, 256), Image.Resampling.LANCZOS).save(buffer, "PNG", optimize=True)
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
        'width="256" height="256" viewBox="0 0 256 256"><image width="256" height="256" '
        f'xlink:href="data:image/png;base64,{encoded}"/></svg>'
    )
    target = output / "scalable" / "apps" / "shadow-messenger-app.svg"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(svg, encoding="ascii")


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: build-icons.py PALETTES_JSON OUTPUT_DIR")
    palettes = json.loads(Path(sys.argv[1]).read_text())
    output = Path(sys.argv[2])
    output.mkdir(parents=True, exist_ok=True)
    sheet = Image.new("RGBA", (4 * 176, 3 * 176), (20, 20, 26, 255))
    for index, (family, colors) in enumerate(palettes.items()):
        theme = THEME_NAMES.get(family, "ShadowRealm-OS-" + family)
        render(colors[0], colors[1], output / theme)
        icon = Image.open(output / theme / "128x128/apps/shadow-messenger-app.png").convert("RGBA")
        sheet.alpha_composite(icon, ((index % 4) * 176 + 24, (index // 4) * 176 + 24))
    sheet.save(output / "contact-sheet.png", optimize=True)
    fallback = output / "hicolor"
    render("#00eafb", "#ff27d5", fallback)
    print(f"Rendered {len(palettes)} palette icons plus hicolor fallback in {output}")


if __name__ == "__main__":
    main()

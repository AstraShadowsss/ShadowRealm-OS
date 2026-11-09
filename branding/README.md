# Brand assets

The approved SR monogram and shared ShadowRealm-OS wordmark are raster masters. Preserve their geometry, spelling and letter spacing. The monogram master and background plates were prepared with the built-in image generator from the supplied design; palette composition uses the editable SVG templates in build-branding.py.

Use Debian 13 with librsvg2-bin and python3-pil. From the repository root:

```sh
python3 branding/build-branding.py branding /tmp/sr-rendered
python3 branding/install-branding-inputs.py components /tmp/sr-rendered
python3 branding/build-walker-wallpapers.py branding /tmp/sr-walkers
python3 branding/install-walker-wallpapers.py components /tmp/sr-walkers
```

The source archives already include the complete catalog. To regenerate role
aliases after editing SVG masters, use:

```sh
TMPDIR=/var/tmp python3 branding/synchronize-monochrome.py components
TMPDIR=/var/tmp python3 branding/reconcile-icon-aliases.py .
python3 branding/install-branding-inputs.py components /tmp/sr-rendered
TMPDIR=/var/tmp python3 branding/complete-dock-families.py .
TMPDIR=/var/tmp python3 branding/neutralize-black-white.py components
python3 branding/check-icon-catalog.py components
```

`extend-icon-catalog.py` records the additional common system-role geometry.
The catalog covers 89 roles per theme; inherited Adwaita icons remain available
for additional standard names. Third-party applications retain their native
icons. Dock PNGs and tile-free panel glyphs are exported separately.

This updates the three owned source archives before building DEBs. Native third-party application icons and upstream license attribution must stay intact. Generated SVG/PNG output is intermediate; the editable masters, templates and packaged source archives are the rebuild authority.

Release launcher aliases are owned by the desktop package. The artwork package must not duplicate those paths. `complete-dock-families.py` retains the canonical installed dock PNGs and creates missing roles in the same family. `neutralize-black-white.py` removes chromatic remnants from the replacement monochrome theme.

Walking wallpapers use a cleaned plate and the exact SR insert. Regenerate with `python3 branding/build-walker-wallpapers.py branding /tmp/sr-walkers` then `python3 branding/install-walker-wallpapers.py components /tmp/sr-walkers`. The shared walker archive is consumed by both package builders to avoid duplicating it in the large source archives. Professional receives an unbranded variant.

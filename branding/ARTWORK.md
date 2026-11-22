# Artwork masters

The branding build renders theme assets from the supplied raster masters and its SVG templates. The approved SR monogram includes the orbit, outer ring and glints. The shared wordmark spells ShadowRealm-OS with a single hyphen and uses consistent letter spacing in each palette.

The abstract waves, circuit corridor and hooded artwork have clean background plates for the shared branding. The corridor traces extend behind the emblem. The Neon master starts in cyan and magenta, and the build renders the other six branded palettes from that layout. The seated city keeps the approved SR mark on the tower; the seated figure’s jacket is unbranded. The walking figure's jacket plate is unbranded. `build-walker-wallpapers.py` places the same SR emblem on each of the seven branded variants and leaves Professional unbranded.

`palettes.json` matches the desktop's accent settings. Icon PNGs are rendered from SVG masters with transparency. Preserve the separate masters so palette and placement changes can be rebuilt without editing exported images.

## Wallpaper palettes

The White, Silver & Gold Digital Wraith, Circuit Corridor and Waves masters are in palette-overrides/WhiteSilverGold. These take precedence over generated palette variants. Other branded wallpapers use a coordinated chroma pass; Black & White and Professional retain neutral rendering. Red & Black uses crimson accents, without an orange secondary. The gallery and desktop chooser share components/wallpaper-collections.json; only catalogued styles appear in the gallery.

Professional uses three unbranded rendered masters: Satin Bloom, Flowing Glass and Sculpted Silk. The originals live in professional-masters; Emerald, Ocean, Graphite and Plum variants share the same material detail and geometry. The retired landscape and walking-figure options are excluded from the Professional collection.

# Raster master specifications

The included masters are the editable build inputs; rendering the themed outputs does not require an image-generation service.

- SR logo: extract the supplied intertwined SR monogram, orbit, outer ring and glints onto transparency, preserving geometry and cyan/magenta gradients.
- Wordmark: extract the supplied blue wallpaper lettering, ShadowRealm-OS, preserving squared letterforms, spacing and a single hyphen. Remove surrounding environment and symbols.
- Focused background: remove the old S/orbit from the abstract cyan/magenta waves; preserve the landscape and keep the center dark.
- Corridor background: remove old emblem and text from the blue circuit corridor; preserve architecture and perspective.
- Artwork background: remove old name and slogan from the hooded-skull fantasy scene; preserve skull, halo, waterfalls and towers.
- Seated city: replace both old S marks on the figure and tower with the approved SR mark, preserving the scene.

The supplied masters were prepared with the built-in image tool. Theme colors, logo placement and repeated wordmark geometry are controlled by build-branding.py's SVG templates.

2026-11-08: Conservatively reconstructed the hooded artwork cloak folds beneath the shared wordmark to remove the previous smooth lettering-removal patch. Composition and neon colors preserved. `palettes.json` now uses the desktop manifest accents; role PNG exports are rendered from native SVG masters with alpha.

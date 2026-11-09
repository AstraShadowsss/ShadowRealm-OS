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

## Walking-figure jacket cleanup

Built-in image edit, using the existing Neon Circuit Walker wallpaper:

Precise local cleanup of this existing wallpaper. Keep the entire original 16:9 landscape composition, hooded walking figure position/pose/size, cyan and magenta rim lighting, black clothing folds, reflective circuit floor, rain and background unchanged. Remove ONLY the small cyan/magenta orbital S emblem on the upper back of the walking figure's jacket, and restore continuous natural black jacket fabric and folds in that tiny area. The jacket must have NO logo, lettering, symbol or patch after the cleanup. No other image changes, no crop, no borders, no added objects. This clean master will receive an exact approved logo through our existing graphics pipeline afterward.

The resulting background-walker.png is the editable clean plate. The approved SR insert is composed deterministically by build-walker-wallpapers.py; it is not redrawn by the image generator. Seven branded variants use the same insert geometry; Professional remains unbranded.

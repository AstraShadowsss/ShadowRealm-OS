# Brand assets

The approved SR monogram and shared ShadowRealm-OS wordmark are raster masters. Preserve their geometry, spelling and letter spacing. The monogram master and background plates were prepared with the built-in image generator from the supplied design; palette composition uses the editable SVG templates in build-branding.py.

Use Debian 13 with librsvg2-bin and python3-pil. From the repository root:

```sh
python3 branding/build-branding.py branding /tmp/sr-rendered
python3 branding/install-branding-inputs.py components /tmp/sr-rendered
```

This updates the three owned source archives before building DEBs. Native third-party application icons and upstream license attribution must stay intact. Generated SVG/PNG output is intermediate; the editable masters, templates and packaged source archives are the rebuild authority.

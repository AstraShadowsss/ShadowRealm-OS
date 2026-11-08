# Third-party software and source

The root MIT license covers original project work identified as MIT. It does **not** cover the whole operating system under one license.

| Component | Terms and location |
| --- | --- |
| Original desktop utilities, terminal code, games and original project assets | MIT, except where a file or embedded upstream notice says otherwise |
| GNOME Clocks, Drawing and XFCE Screensaver | Their upstream licenses and exact corresponding Debian source are included in the release source and notice archives |
| Original session chimes and screensaver animations | MIT; editable generator and animation code are in `components/` |
| Modified Xfce panel | Upstream GPL-2.0-or-later; full upstream source, Debian packaging, patch and build script are in `components/` |
| GNOME-derived icon artwork | Upstream terms and credits retained in `components/adwaita-COPYRIGHT` and packaged icon notices |
| Calamares settings and installer framework | Upstream notices retained with the source/settings archive and installed package documentation |
| Linux, Debian packages, libraries, applications, fonts and firmware | Their individual licenses; consult the exact release's package notice archive and inventory |

Every release must distribute its matching package notice archive, package/source-version inventory and corresponding source files alongside the ISO. The release folder contains those materials. The ISO also includes notices under `LICENSES`; installed packages normally keep documentation under `/usr/share/doc`.

The full third-party source distribution is large and is hosted with the ISO on [SourceForge](https://sourceforge.net/projects/shadowrealm-os/files/), rather than committed to this repository. Publish the matching source materials at the same time as the binary release, with clear links and checksums. A general link to upstream projects is not a substitute for supplying the required corresponding source. Original custom sources and modified-panel build inputs are in this repository; the release source bundle must include them too.

The inventory records packages actually included in the image, not every package available in Debian. Preserve upstream copyright notices and license texts when modifying or redistributing the project.

MIT and many bundled free-software licenses permit commercial redistribution under their conditions. The MIT license does not imply that every component has identical redistribution obligations. See the [MIT license](https://opensource.org/license/mit) and [GNU source distribution guidance](https://www.gnu.org/licenses/gpl-faq.html#SourceAndBinaryOnDifferentSites).

VirtualBox is linked as an optional host application, not included in the ISO source repository. Its Extension Pack is a separate product and license. No rights to third-party product names or trademarks are granted here.

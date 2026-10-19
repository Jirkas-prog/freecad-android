# Source, attribution and redistribution

The Android host, its bootstrap and tests are copyright FusionFlow contributors,
licensed **GPL-3.0-only**. The assembled application includes independently licensed
components. Their notices and licence texts remain in the packaged runtime.

| Component | Source and licence |
| --- | --- |
| Android host and integration | This repository, GPL-3.0-only |
| FreeCAD WebAssembly port, frontend, build patches | [Virtastic/freecad-web at 8b11c37](https://github.com/Virtastic/freecad-web/tree/8b11c37a9cb59db582f691e3ab90c7fce7350d1b), LGPL-2.1-or-later; GPL-3.0-only Qt loader |
| FusionFlow 0.20.0 | [Source](https://github.com/Jirkas-prog/freecad-fusion/tree/v0.20.0), LGPL-2.1-or-later, with MIT navigation add-on and LGPL OpenTheme |
| AndroidX WebKit 1.18.0-rc01 | [AndroidX](https://android.googlesource.com/platform/frameworks/support/), Apache-2.0 |
| FreeCAD, Open CASCADE, Qt, CPython, Coin3D and other engine dependencies | Full component list and retained licences in [upstream NOTICE](https://github.com/Virtastic/freecad-web/blob/8b11c37a9cb59db582f691e3ab90c7fce7350d1b/NOTICE) and the APK's `assets/engine/NOTICE` / `LICENSES` |

The original engine notice also describes optional external solvers and
3Dconnexion modules. **Gmsh, CalculiX and 3Dconnexion scripts are not included in
this APK.** The installed Android WebView provider is supplied by the device; no
Chromium/WebView provider APK is redistributed here.

## Source for the shipped components

`runtime/versions.json` pins the engine commit and SHA-256 hashes. The
[upstream patches](https://github.com/Virtastic/freecad-web/tree/8b11c37a9cb59db582f691e3ab90c7fce7350d1b/patches)
and [build instructions](https://github.com/Virtastic/freecad-web/blob/8b11c37a9cb59db582f691e3ab90c7fce7350d1b/BUILD-WEH.md)
describe the engine modifications and dependencies. That upstream document also
records incomplete dependency-version pinning; do not interpret this as a claim
that the complete engine build is reproducible.

All Android-side adaptations are visible in `tools/prepare_runtime.py` and
`runtime/`: offline startup, removal of telemetry/network bootstrap, disabling
cursor recentering, tablet input selection, and the native file bridge. The
preparation script retrieves the public add-on sources and retains their licences.
APK assembly does not require a private service or proprietary CAD library. Use
your own signing key for modified builds; a private release key is not required to
run a modified version under a different application ID or after uninstalling the
original application. Export documents before uninstalling.

FreeCAD, Autodesk Fusion and Samsung names are used only to identify compatibility
or interaction references. This project is not affiliated with or endorsed by
those organisations. The bundled FusionFlow SVG icons are original artwork, not
assets extracted from Autodesk software.

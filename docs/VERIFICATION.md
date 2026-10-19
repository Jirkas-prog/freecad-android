# Verification record

Test date: 2026-10-20. All test models were generated specifically for this project;
no user CAD document or personal FreeCAD profile is included.

## Runtime

| Component | Tested version |
| --- | --- |
| FreeCAD | 1.1.3, engine build 20261009 |
| FusionFlow | 0.20.0 |
| Android | API 35 / Android 15, x86_64 emulator, 1600 × 1000 |
| WebView | Chromium SystemWebView 158.0.8113.0 |
| Host library | AndroidX WebKit 1.18.0-rc01 (initial geometry run used alpha01) |
| Isolation | `crossOriginIsolated === true`, SharedArrayBuffer and JSPI available |

No physical Galaxy Tab S9, ARM64 tablet, S Pen or DeX device was available for this
verification. The development WebView provider was installed **only in the test
emulator**; it is not included in the release APK.

## Completed checks

- FreeCAD and the FusionFlow ribbon, grouped browser and history started inside
  the Android APK with packaged engine assets.
- The CAD model regression in `tests/model_smoke.py` passed in the Android
  interpreter: selective multi-body cut, excluded body unchanged, transaction
  rollback, extrusion from a solid face, associative offset plane, sketch attached
  to that plane, extrusion, section-edge computation, native save/reopen and a
  visible history panel.
- Resulting volumes were approximately **500, 1200, 500 and 50.26548246 mm³**.
  Every checked solid remained valid after saving and reopening.
- Export through `ACTION_CREATE_DOCUMENT` wrote a `.FCStd` file into Android
  Downloads. The resulting archive contained 135 entries and valid Document.xml.
- Import through `ACTION_OPEN_DOCUMENT` reopened that exported file as a second
  FreeCAD document with all **50 objects**.
- Native Android screenshots confirmed that the 3D scene and FusionFlow widgets
  were rendered. CDP screenshots alone were insufficient: the accelerated WebView
  sometimes returned a black capture despite correct on-device rendering.
- An Android-injected one-finger swipe changed the view's camera quaternion in
  Touch mode. Switching through the DESIGN input actions set Mouse mode correctly;
  the measured rotations are in [input-smoke.json](input-smoke.json).
- After a force-stop and restart, the recovery model reopened with all 50 objects
  and volumes 500, 1200, 500 and 50.265482 mm³; the Mouse input preference survived.
  See [restart-smoke.json](restart-smoke.json).
- Release/debug runtime assets matched. Android lint completed with no errors;
  remaining warnings concern the intentionally enabled JavaScript/shared-memory
  APIs and a feature annotation. Both required WebView features are checked.
- The release APK passed `apksigner verify` with an RSA-3072 certificate and APK
  Signature Scheme v3. It installed successfully in the test emulator. Its
  manifest requests no Internet or storage permissions.
- The signed release opened the full FusionFlow interface and imported the
  exported `TabletSmoke.FCStd` through Android's document picker. WebView remote
  debugging was disabled in that release.

Release signing certificate SHA-256:
`a6560c8f9a2d5cfb1613f377ca263fe6728406679d6482d7e006b0f312701051`.
The private key is not part of this repository or the release.

The machine-readable geometry results are in
[model-smoke.json](model-smoke.json). The 3D screenshot is from the emulator, not
from a physical Samsung tablet.

## Repeating the CAD test

Build/install a **debug APK in a dedicated test emulator**, enable its supported
WebView provider and wait for FusionFlow to start. Find the app's
`webview_devtools_remote_<PID>` socket and forward it with ADB:

```sh
adb -s <test-device> forward tcp:9224 localabstract:webview_devtools_remote_<PID>
npm install --no-save playwright
node tools/test_runtime.cjs http://127.0.0.1:9224
```

The runner creates a synthetic model and writes results under `build/qa`. It must
not be attached to a user's active CAD session. Release APKs do not enable WebView
debugging. A successful script verifies geometry and selected UI state; it does
not certify all possible gestures, dialogs, workbenches or long-term stability.

## Remaining verification work

- Physical ARM64 hardware and stock-provider compatibility across Android versions.
- S Pen/palm rejection, accessibility, keyboard layouts and DeX window resizing.
- Long sessions, large models and memory-pressure recovery.
- A wider UI regression suite for sketch editing, analysis visuals and third-party
  workbenches. The section check above tests section geometry, not all section-view
  rendering controls.

# Photon 26969 — ONE three-stage vscode.dev handoff

**Status: PREPARED FOR ACTIONS only if local seals pass. Not BUILD-PROVEN.**

26969 is based exclusively on **successful compiled 26968**, never stale app/src
from repository HEAD. The unique 26969 builder downloads *only* successful
26968 artifact 14601236629 and verifies its exact Actions run, branch, commit,
artifact SHA, source TAR SHA, actually executed builder/workflow, APK and every
compiled source file before applying the 14-path source allowlist.

## User upload — exactly three stages, in this order

Open the permitted `experimental-clean-photon-rebuild` branch in vscode.dev.
These are file uploads, **not user-run scripts**. Do not alter or push `dev`.
Do not upload an APK or source TAR; only the files in the stage lists.

1. **Stage 1**: upload files from `26969_STAGE_1_UPLOAD_PATHS.txt`, keeping
   all paths (including `handoff_payload_26969/app/...`) and existing historical
   checkout infrastructure. Confirm the full file upload commits successfully.
2. **Stage 2**: upload `.github/workflows/build-26969-change-aware.yml` alone.
   Confirm workflow file upload commit succeeds. Do not trigger yet.
3. **Stage 3**: upload `TRIGGER_26969.txt` alone, causing the build. No other
   path in this handoff can trigger 26969 build.

If using GitHub web vscode.dev upload, preserve nested paths exactly; do not
flatten the tree or stage a parent folder as an extra directory. Preserve all
existing historical validators and the original successful 26968 handoff.

### Fixed real-build authority

- Predecessor: 26968 successful Actions run **44673285126**, job
  **136079028533**, commit **7b0d6684d25ce97242717d3a67f6d143ca3c51c8**.
- Artifact **14601236629** SHA256
  `877aa61115b3765411867a3fc603b7b8fd05a6502b0486025e0411756b9434b2`.
- Compiled source TAR SHA256
  `d2fce934984815a47e1b10a3cd76348ef3a26fecb8d2fee77b3353050d8e3c99`.
- Actually executed 26968 builder SHA256
  `4b041348ea83896de290e619453146792e08721840d2f968b7c4b00e315e7c24`.
- Actually executed 26968 workflow SHA256
  `76a025b5b96ad09096769e0a24692fe0aafff93280aa2f187f59087b6002408c`.
- Predecessor APK SHA256
  `08cce4479b65825323ffa7905f9bdb735a1b9155c000232c3b8eb2c742b2d339`.
- Source 26968: **2,055** files; candidate 26969: **2,059** files;
  **10 changed** and **4 added**, **2,045 protected byte-for-byte**;
  no source deletions, native/vendor/config changes, or app Gradle changes.
- Infrastructure: ONE new 26969 workflow, its independent stage/guard tools;
  historical successful 26968 workflow remains untouched. Original executed
  26968 historical prefix preserved byte-for-byte.

### New 26969 features

**Experiment B, Super Res OFF only**: RAWR-inspired, app-owned Camera2 AE (not
continuous HAL AE), native RAW frame histogram keyed by exact sensor timestamp,
scene-referred meter and highlights, exposure smoothing, analog sensor ISO cap,
2EV maximum matched digital gain, 1/14s (`71,428,571 ns`) default slowest photo
shutter, 50/60Hz flicker snapping when known. Runtime skips user-manual
sensor exposure, B ON, A, Night, video. Captures carry selected NORMAL frame
post-RAW gain into preview/JPEG; DNG baseline interpretation is not independently
validated on a device.

**Experiment B, Super Res OFF only**: one new 1/8-resolution camera-linear
post-AMaZE grain map + four multiscale luminance/chroma neighboring-grain
attenuations; do not copy Rexture's effective frame support semantics. Genuine
small texture may soften by user choice. Preserves coarse brightness and color,
no changes to HDRQ native 4-pass merge, UHDR colors, white balance, or
Experiment A/Night/Super Res ON. **Visual quality is NOT build-proven**.

### Regression/compilation sequence

Original 26968 historical prefix with all 26886/26887, 26903,
26904 V2 optimizer and V3 Spektra CMake targeted regressions; exact 26968
compiled-source reconciliation; historical original 26968 real GLSL/SPIR-V;
new 26969 production ESSL300 and ESSL310 fragments extracted from Kotlin,
OpenGL SPIR-V validation+optimization, unchanged HDRQ Vulkan 1.1 compute
shaders and mandatory dual ABI NDK/CMake, Kotlin and Java, full Gradle
`:app:assembleDebug`; exact source and LKR ABI hash closure; publish exactly
one verified 26969 APK and the *actual* compiled source TAR only after PASS.

Any missing artifact, missing file, historical test failure, shader optimizer
failure, incompatible Kotlin/Java, failed native compile, missing APK, source
hash mismatch or stage mismatch **fails closed**. No weakening or skipped compile
allowed to save time. No commits or pushes performed by the assistant.

### License/provenance

RAWR's public reference source is GPL-3.0:
https://github.com/adityawarmanfw/rawr (commit
`5b9f5cef0f03dbef2dab7fdc9d2664bbcc518078`). Review distribution
obligations, including notices and source availability, before distributing an
APK. The Iris implementation is Java/GLES adapted to its own HDRQ pipeline,
not a verbatim copy of Rexture binary or shader.

# PHOTON 26946 — exact successful 26945 V2 three-stage front UHDR geometry correction

**Status: PREPARED FOR ACTIONS, NOT BUILD-PROVEN for 26946; device image quality NOT RUN.**

Use only this ZIP in vscode.dev/GitHub on `experimental-clean-photon-rebuild`. Do not upload it as a single archive into the repository. **Upload the contents of its three stage directories in this order**: Stage 1 files to repository root (including nested `handoff_payload_26946/`), Stage 2 workflow to `.github/workflows/`, Stage 3 `TRIGGER_26946.txt` committed/pushed *only after* Stages 1 and 2 have landed. Do not touch `dev`, create backup branches, or upload APKs.

## Why

26945 V2 successfully built but front UHDR landscape 180-degree gain-map highlights were misplaced. The final SDR shader `addwatermark_rotate.glsl` applies **Y-axis mirror for cameraRotation 0°/180° and X-axis mirror for 90°/270°**, whereas 26945 front Motion UHDR incorrectly applied X-axis mirror at every rotation. The live front 13:19:42 JPEG logged rotation 180°; 13:19:28 was 270° and correct. Gainmap now uses shader-equivalent front geometry, including the shader's high-Y source crop and high-X crop at 180°/270° where applicable. The SDR pixels/gain algorithm/color, rear Motion, Night, front/rear preview handoff, shaders/native/vendor and all other camera paths are protected.

## Latest actual successful runtime authority

- 26945 V2 successful Actions run `43924432132`, commit `34e22c52fb293142445a373dbb7e0b536d3f14e1`, published artifact `14256995952`.
- Published artifact ZIP SHA-256 `7d55577c36fbd8d0d29a09ab2cad0a12ed0f38cf0187a955861c2ef547b80399`.
- Actual compiled-candidate TAR SHA-256 `e8f1ee7d02e93a989d25dc7b29df5fb0ba8c5944a256a63e09e802f9a77153ce`.
- Actual executed 26945 V2 builder SHA-256 `f9ef403d74e28349510407f4e7b62d991186d76977e21063ec5c8f050b3a7eea`.
- Actual executed workflow SHA-256 `a104c62da64932cd488120c6559554136998e5c1a9109ae4b690d22251810fd8`.
- Actual successful APK SHA-256 `9593f8e4fea976da860cecbf081ea5839fb2af8a2b7ed9bfaba3defb2ef4d56c`.

## Exact runtime scope

- 2,054 actual compiled source files.
- Three changed runtime files: `MotionV2UltraHdr.java`, `PostPipeline.java`, `app/version.properties` (exact paths in allowlist).
- **2,051 protected files byte-for-byte unchanged**. Added source 0, deleted source 0.
- **No** rear camera runtime changes, including its UHDR code path; **no** changes to front/rear preview handoff proven in 26945; no shader source change, native/NDK/vendor change, DNG, Night, Experiment A/B, Motion architecture, or unrelated IQ changes.

## Safety and verification

The 26946 workflow keeps the original successful 26945 V2 job prefix byte-for-byte, including the exact SHA-locked **141 inherited historical commands** and mandatory historical regressions. Its actions use the actual successful 26945 published artifact, verify SHA/compiled TAR/manifest/executed builder/workflow/APK receipts, deterministically reconstruct source, apply precisely three changes, prove forward and rollback full-index patches at Git abbrev 7/12/40, then repeat original pinned GLSL/SPIR-V, native dual ABI, real Kotlin/Java/NDK/Gradle `:app:assembleDebug`, complete provenance and source guards, and publish one APK with source TAR/receipts. Do not loosen any gate for a faster build.

The local geometric tests independently compare real-shader formulas with the actual modified Java `Bitmap` transform pixel-by-pixel across 0/90/180/270, 4:3, 16:9 and high-X/Y crop cases. Host `javac` compiles the actual modified class with Android API stubs; this is **not a substitute for** the real Actions Android compiler.

**Do not use V1 26945 or stale repository app/src as authority.** No source was committed or pushed from this handoff preparation. The front-camera device visual result remains uncertain until the 26946 APK is built and photographed in both portrait and landscape orientations.

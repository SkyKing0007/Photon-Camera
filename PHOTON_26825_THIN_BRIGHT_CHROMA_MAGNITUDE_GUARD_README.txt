PHOTON 26825 — THIN BRIGHT CHROMA MAGNITUDE GUARD

STATUS BEFORE ACTIONS: PREPARED / UPLOAD-READY ONLY.
Real 26825 GLSL/Kotlin/Java/NDK/full assemble are NOT RUN locally. GitHub Actions is authoritative.
No backup branch. No source commit/push performed by ChatGPT. Do not push APKs.

RUNTIME AUTHORITY
- successful 26824
- commit 87331b162b7370ebfa942ecfb0eed701d6b08cfb
- Actions run 38332544574
- artifact 11783108647 photon-26824-adaptive-body-s-curve
- artifact SHA-256 affa3dbd346895f019a8dd30523cc0629541037aea8cf6c05e740cfbdbb3cf0d
- candidate TAR SHA-256 50fd1ab0d843b5bf15766c5b666b9a74a4a66495cbf282ffb4d94b17c7e56f72

VERIFICATION MECHANICS
Exact successful 26824 17-stage procedure, unchanged. Successful 26821 remains root mechanics reference.

RUNTIME CHANGED-FILE ALLOWLIST — EXACTLY 2 MODIFIED
1. app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt
2. app/version.properties

INTENT
- Keep all successful 26824 tone/saturation and current chrome/highlight false-color cleanup unchanged.
- Do not neutralize or replace real color.
- Prevent the 26728 pre-VGN magnitude restoration from amplifying a small phase-colored residual into saturated cyan/teal/yellow on thin bright high-gradient structure.
- Full restoration remains available to broad coherent real color with physically-valid same-hue support in both image axes.
- Low-gain restores and dark/non-edge regions are unchanged.
- Guarded pixels retain the already-cleaned VGN hue/direction and receive only bounded extra magnitude.

UPLOAD IN VSCODE.DEV — EXACTLY THREE STAGES
1. Upload/replace everything inside STAGE_1_UPLOAD_FIRST/ at repository root, preserving paths.
   Commit/push exactly: 26825: prepare thin bright chroma magnitude guard
   This must NOT launch the 26825 workflow.
2. Upload STAGE_2_UPLOAD_SECOND/.github/workflows/build-26825-thin-bright-chroma-magnitude-guard.yml.
   Commit/push exactly: 26825: add thin bright chroma magnitude guard workflow
   This must NOT launch the build.
3. Upload both files inside STAGE_3_UPLOAD_LAST/ at repository root.
   Commit/push exactly: 26825: activate thin bright chroma magnitude guard build
   Only this stage launches the intended workflow.

Expected workflow: Build 26825 Thin Bright Chroma Magnitude Guard
Expected artifact: photon-26825-thin-bright-chroma-magnitude-guard
Expected APK: IrisCamera-0.9726825-26825-thin-bright-chroma-magnitude-guard-debug.apk

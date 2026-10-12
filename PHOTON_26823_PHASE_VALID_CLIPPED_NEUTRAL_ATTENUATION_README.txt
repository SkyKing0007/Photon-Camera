PHOTON 26823 — PHASE-VALID CLIPPED NEUTRAL ATTENUATION

STATUS BEFORE ACTIONS: PREPARED / UPLOAD-READY ONLY.
Real 26823 GLSL/Kotlin/Java/NDK/full assemble are NOT RUN locally. GitHub Actions is authoritative.
No backup branch. No source commit/push performed by ChatGPT. Do not push APKs.

RUNTIME AUTHORITY
- successful 26822
- commit 4c4824f3ce2ef850c640207f5af341bba3e2270c
- Actions run 38307699961
- artifact 11772764787 photon-26822-single-owner-false-color-attenuation
- artifact SHA-256 973de9c3a5846ccabe625711c4405df4c2638a70ef379e10696dcd5209c31b92
- candidate TAR SHA-256 5e09fc81cfb9b2d59d731afeab149d806189f9cc28fd06a9579325c9c4be4d0e

VERIFICATION MECHANICS
Exact successful 26821 17-stage procedure, unchanged. Successful 26812 remains root mechanics reference.

RUNTIME CHANGED-FILE ALLOWLIST — EXACTLY 2 MODIFIED
1. app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt
2. app/version.properties

INTENT
- Fix the 26822 surviving cyan/teal/yellow false color on bright clipped neutral rails before VGN, where exact consumed-CFA validity still exists.
- Require asymmetric IRIS_26614 validity loss + bright-highlight domain + BOTH neutral median and neutral material-baseline proof + visible center chroma + inherited high-contrast gate.
- Keep broad 26783 clipped-neutral restoration retired.
- Pass 1 only; attenuate only center chroma magnitude toward neutral; no neighboring hue donation; restore luma exactly.
- Preserve exact successful 26822 downstream single-owner false-color path, successful 26819 Sabre, successful 26818 VGN, successful 26821 DNG, LCA, alignment/merge, exposure/HDR, denoise, SR, UHDR, native/vendor and GPU lifecycle.

UPLOAD IN VSCODE.DEV — EXACTLY THREE STAGES
1. Upload/replace everything inside STAGE_1_UPLOAD_FIRST/ at repository root, preserving paths.
   Commit/push exactly: 26823: prepare phase-valid clipped neutral attenuation
   This must NOT launch the 26823 workflow.
2. Upload STAGE_2_UPLOAD_SECOND/.github/workflows/build-26823-phase-valid-clipped-neutral-attenuation.yml.
   Commit/push exactly: 26823: add phase-valid clipped neutral attenuation workflow
   This must NOT launch the build.
3. Upload both files inside STAGE_3_UPLOAD_LAST/ at repository root.
   Commit/push exactly: 26823: activate phase-valid clipped neutral attenuation build
   Only this stage launches the intended workflow.

Expected workflow: Build 26823 Phase-Valid Clipped Neutral Attenuation
Expected artifact: photon-26823-phase-valid-clipped-neutral-attenuation
Expected APK: IrisCamera-0.9726823-26823-phase-valid-clipped-neutral-attenuation-debug.apk

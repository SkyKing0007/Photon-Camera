PHOTON 26710 — ONE-SHOT HAL REFERENCE + HAL-BASELINED LONG

Runtime authority: exact successful 26709 Actions compiled candidate, commit 196be5aaaef28383ccea8446328658b2e6336d0d, run 36245295705, artifact 10907700264, artifact SHA-256 d2548ab2b544004c5e13d66fc6a34d89345ec5be20807cb11d35a81bf3a68d42, candidate TAR SHA-256 b0bc41bbd2721a701fd7d0e3d731812a0990c7827694e8f6342a35a00e313f53. No backup created, per user request.
Verification-mechanics authority: exact successful 26709 procedure. Its stage order, Java 17, real project Kotlin/Java compilers, both NDK ABIs, pinned glslang 16.5.0 dual handoff, deterministic patch proof, PRE-BUILD gate, one-APK proof, and post-build invariance are retained without reordering.
Runtime changes: exactly 2 files in handoff_payload_26710: CaptureController.java and app/version.properties.
Infrastructure changes: exactly 9 files listed in 26710_INFRASTRUCTURE_CHANGED_PATHS.txt. They advance authority/version/names and add 26710 semantic/regression checks; build stage order is unchanged from successful 26709.

Behavior contract:
- HAL/System AE observes and settles each new camera scene first.
- Iris uses only that untouched HAL-baseline RAW evidence to compute one final NORMAL highlight-protection target (0 EV or underexposure only).
- Iris applies the target once as an AE-OFF manual repeating shutter/ISO request, then locks it. Post-adjustment RAWs cannot vote on NORMAL exposure.
- Subject motion, TV/content changes, flicker, and luminance changes cannot unlock NORMAL. Only inherited sustained physical-camera reframe evidence can end the scene epoch.
- On true reframe, Iris releases manual ownership back to HAL/System AE; after the new HAL scene settles, one new decision is allowed.
- Existing successful 26709 frame-exact viewfinder presentation path is unchanged; zero exposure pumping is a permanent regression requirement.
- LONG is calculated independently from the frozen untouched HAL baseline and frozen shadow/SNR evidence, not from the deliberately underexposed NORMAL. LONG may therefore be more than +2.5 EV relative to NORMAL when needed, while its target remains 0.5..2.5 EV over HAL baseline. Shutter is spent first up to ~1/15 s, then ISO. Motion blur is allowed; NORMAL owns highlights/moving detail and LONG supplies shadow/body SNR.
- Sabre, MotionV2 downstream exposure/tone, UHDR/render, 26707 chroma/tail safeguards, preview renderer/shader, native/vendor/DNG owners are protected unchanged.

TWO-STEP VSCODE.DEV UPLOAD:
STEP 1: upload/replace every path in 26710_UPLOAD_PATHS.txt EXCEPT .github/workflows/build-26710-one-shot-reference-hal-long.yml, then commit/push.
STEP 2: upload only .github/workflows/build-26710-one-shot-reference-hal-long.yml, then commit/push. This activates the authoritative Actions build.

Real GLSL/Kotlin/Java/NDK/full assemble are Actions-only. Before successful Actions, this handoff is prepared/upload-ready, not build-proven.

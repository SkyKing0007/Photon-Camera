PHOTON / IRIS 26582 V1 — SCENE-ADAPTIVE GLOBAL TONE HANDOFF

STATUS BEFORE ACTIONS: PREPARED / UPLOAD-READY ONLY.
No backup branch was created, per explicit user request.

RUNTIME AUTHORITY
- branch: experimental-clean-photon-rebuild
- successful 26581 commit: f24f815ee3a34467641d184b029eae8dca5948cb
- Actions run: 33643933451
- job: 100293694453
- artifact: 9852109713 photon-26581-v1-gap-edge-envelope
- artifact digest: sha256:933667371f114faa8f82a51c158fb7f5115185ae596870b7cc15a388c4f4d8d4
- compiled candidate tar SHA-256: b64ec98a6f79aed8a6f0457654c1ca01753e666b99b6d809351fb2d1e4c12618

VERIFICATION-MECHANICS AUTHORITY
Successful 26581 V1. Its authority-seeded candidate-first order is preserved.

TARGET
0.9726582 / 26582

EXACT RUNTIME CHANGED-FILE ALLOWLIST
1 app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java
2 app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java
3 app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java
4 app/version.properties

IMPLEMENTATION
- Uses the existing low-resolution viewfinder/candidate probe; no new full-resolution readback/histogram.
- Measures P95/P99 highlight guide and predicted fraction that would hit the successful-26581 scene-white endpoint.
- Leaves the exact 26581 scene-white decision unchanged when there is no meaningful HDR tail.
- Values at/below the existing linear 0.50 shoulder start remain mathematically unchanged.
- With a meaningful HDR tail, sceneWhite expands smoothly; fully engaged robust P99 targets about 0.97 SDR so recoverable cloud/window ordering does not collapse to a white plateau.
- Approximately 2.3% predicted clipping engages strongly; isolated speculars below 0.2% do not globally alter the scene.
- Viewfinder solver now models the exact scalar render shoulder/gamut behavior; stale solver-only neutral-to-white/overflow-to-white approximations are retired.
- Adds minimal decision telemetry IRIS_26582_SCENE_ADAPTIVE_TONE_DECISION.
- Global only; no local tone mapping, sharpening, saturation boost or per-channel highlight operation.

FROZEN/PROTECTED
- 26581 VGN false-color/micro-color/gap owner bytes unchanged.
- 26581 true2x SR chroma and material-separated edge-envelope bytes unchanged.
- motionv2/render.glsl unchanged SHA-256 e0a438e51e12df5e6d8b53dc92892078ba7659791725cee54700869a6bc62b71.
- motionv2/gainmap.glsl unchanged.
- motionv2_jpeg444_jni.cpp unchanged SHA-256 d73cd24452280958f089e9124545a81461939e8fa0c9c95272b2825942e4b43d.
- Sabre/alignment/flow/phase, HDR capture policy, DNG, Night ownership and GPU publication transport unchanged.

UPLOAD
Replace/add the files from this ZIP in vscode.dev on experimental-clean-photon-rebuild, commit once, and push. Do not copy any runtime app/src directly outside the sealed handoff payload; Actions reconstructs runtime source from the exact successful 26581 compiled candidate plus these four payload files.

ACTIONS MUST PROVE
sealed hashes/scope; exact 26581 artifact/tar authority; deterministic candidate; semantic/regression/ownership gates; six inherited active shader scans + pinned Khronos glslangValidator 16.5.0; authority-seeded live byte equality; Kotlin/Java; both NDK ABIs; 7/12/40 full-index forward/rollback proof; PRE-BUILD SAFETY; full assemble; exactly one APK; post-build protected/DNG/native/vendor invariance; deterministic final candidate export.

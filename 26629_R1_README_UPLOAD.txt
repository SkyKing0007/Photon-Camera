PHOTON 26629 R1 — LUMINANCE-LOCKED COLOR + ANDROID UHDR LUMINANCE POP

UPLOAD TARGET
- Branch: experimental-clean-photon-rebuild
- Expected branch HEAD before this handoff commit: feeced352582866975009edc6b113d6151418c98
- Successful runtime authority: 26628 R3 commit feeced352582866975009edc6b113d6151418c98
- Successful Actions run: 34643414499
- Successful artifact: 10281080928 / photon-26628-r3-bjzhou-color-motion-night-superres-lens-ui
- Successful artifact SHA-256: 5934180f54b51f947d61580344dc74c9e396174a475a70570e2e73be1cce8d12
- Exact compiled-candidate TAR SHA-256: 464890911b315f262f1173d2e25e7df96c2d55b369461553f31e09a49b4993ca
- Verification-mechanics authority: exact successful 26628 R3 build/workflow/transform ordering and compiler/NDK/patch/assemble/invariance mechanics.
- Backup: NO NEW BACKUP. Existing backup-26627-pre-bjzhou-color-motion-night-superres remains untouched.

IMPORTANT UPLOAD METHOD
1. In vscode.dev Explorer, upload/replace the contents of this ZIP at repository root, preserving paths.
2. DO NOT manually copy handoff_payload_26629_r1 into app/. The Actions build script reconstructs the exact candidate from the successful 26628 R3 artifact and the canonical patch.
3. Source Control should show this sealed handoff/infrastructure package only; it must not show direct live app/ source replacements.
4. Commit and push to experimental-clean-photon-rebuild.
5. Suggested commit message: 26629 R1 color restore and UHDR luminance
6. Expected workflow: Build 26629 R1 Luminance-Locked Color + UHDR Pop

INTENDED RUNTIME CHANGED-FILE ALLOWLIST — EXACTLY 5
app/src/main/assets/shaders/motionv2/gainmap.glsl
app/src/main/assets/shaders/motionv2/render.glsl
app/src/main/cpp/motionv2_jpeg444_jni.cpp
app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java
app/version.properties

RUNTIME INTENT
- Preserve successful 26628 R3 reconstruction, Sabre/Motion merge, denoise, SHORT/CFA/highlight protections, DNG color solve, 0.95 upstream presentation behavior, lens UI repair, legacy Photon routing, DNG ownership, and Night post-Jin UHDR ownership.
- Add one final Iris-owned adaptive chroma restoration after the existing 26628 tone/gamut result and before sRGB transfer.
- The restoration expands only the neutral-axis chroma vector at fixed Display-P3 luminance. It protects deepest blacks, near-neutrals, already-strong colors and bright pixels, with maximum requested restoration 1.20.
- Add Motion/true2x UHDR body luminance floor 1.25 (1.00 / existing 0.80 SDR presentation) using the existing single-channel Android gain map. Completed SDR remains the sole detail/color/tone image; UHDR adds scalar display luminance only. Genuine higher source headroom may exceed 1.25 within existing safe capacity.
- Night UHDR path is unchanged.

INFRASTRUCTURE CHANGED-FILE LIST
26629_R1_README_UPLOAD.txt
REGRESSION_R1_26629_COLOR_UHDR.txt
R1_26629_* manifests/patches/shader pin/handoff hashes
build_26629_r1_color_uhdr.sh
transform_26629_r1.py
validate_26629_r1.py
verify_26629_r1_authority.py
verify_26629_r1_infrastructure.py
verify_26629_r1_patches.py
verify_26629_r1_regressions.py
verify_26629_r1_shaders.py
handoff_payload_26629_r1/**
.github/workflows/build-26629-r1-color-uhdr.yml

INFRASTRUCTURE DIFFERENCE VS SUCCESSFUL 26628 R3
- Build identity, successful-artifact authority, version, exact five-path allowlist/manifests, and color/UHDR-specific validators/regressions only.
- Core build/verification ordering, Java 17, Python 3.12, ubuntu-24.04, Gradle invocation, pinned glslang 16.5.0, Kotlin/Java compiler step, both NDK ABI steps, patch proof, PRE-BUILD proof, assemble, exactly-one-APK gate, post-build invariance and deterministic candidate export remain the successful 26628 R3 mechanics.

VERSION
VERSION_NAME=0.9726629
VERSION_BUILD=26629

STATUS AT HANDOFF PREPARATION
- Exact successful 26628 R3 artifact/candidate authority replay: PASS locally.
- Deterministic candidate reconstruction: PASS locally.
- Semantic/ownership/domain gates: PASS locally.
- Runtime-expanded modified-shader reserved scan: PASS locally.
- Deterministic full-index forward/rollback patches at core.abbrev 7/12/40: PASS locally.
- Exact successful 26628 R3 infrastructure diff audit: PASS locally.
- Real pinned glslang compile: NOT RUN locally; Actions required.
- Real project Kotlin/Java compile: NOT RUN locally; Actions required.
- Real NDK compile both ABIs: NOT RUN locally; Actions required.
- Full :app:assembleDebug: NOT RUN locally; Actions required.
- Final Actions authority remains successful 26628 R3 until 26629 succeeds.

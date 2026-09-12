PHOTON CAMERA 26631 R1 — CONTINUOUS UHDR GAIN MAP

STATUS WHEN DELIVERED:
PREPARED / UPLOAD-READY ONLY. GitHub Actions real compiler/build proof is still required.

RUNTIME AUTHORITY:
successful 26630 R1
commit 74b2d0eb127dd0a3a81a6f85a01343e4c4e84f35
Actions run 34673292313
artifact 10291068441
artifact name photon-26630-r1-adaptive-color-fixed-policy-uhdr
artifact ZIP SHA-256 6d95e135feaff48f0b0ad04eae3b1ee1c4a7c08ff12fd258b722ee4c8b78abd1
compiled candidate TAR SHA-256 fec1ed4181178878a522c6a832deeb950e99342e873b862b8b09201e9d1e06b9
candidate universe 1713 app files

VERIFICATION-MECHANICS AUTHORITY:
Exact successful 26630 R1 ordering/toolchain/isolation/compiler/NDK/patch/PRE-BUILD/assemble/postbuild mechanics.
No backup was created, per user instruction.
No source was pushed or committed by ChatGPT.

26631 RUNTIME CHANGED-FILE ALLOWLIST (EXACTLY 4):
app/src/main/assets/shaders/motionv2/gainmap.glsl
app/src/main/cpp/motionv2_jpeg444_jni.cpp
app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java
app/version.properties

RUNTIME INTENT:
- Preserve the completed 26630 SDR primary exactly.
- Preserve 26630 render/local-laplacian/adaptive-color/viewfinder owners byte-for-byte.
- Remove the 26630 hard Motion UHDR 1.00 -> 1.25 gain cliff.
- Derive Motion UHDR as a full-resolution scalar linear-light luminance quotient between a matched HDR rendition intent and the exact completed SDR primary.
- Anchor the HDR intent at source-guide 0.65, the unchanged upper-tone entry where the inherited SDR map still equals its body map.
- Allow genuine upper-range scene energy, including sub-source-white ceiling/chandelier structure compressed by SDR, to gain smoothly.
- Preserve ratioMax=8, logarithmic R8 coding, same-resolution one-gain-sample-per-primary-pixel authority, and existing JPEG-R packaging/metadata.
- No fixed body gain, no nominal-white gate, no channel-specific gain, no gainmap blur/downsample/smoothing.
- True-2x CPU and embedded GPU publication use the same quotient semantics.
- Non-Motion/Night quotient branch is unchanged.

PERMANENT REAL-DEVICE REGRESSION ADDED:
The exact 26630 failure formula (unity through 1.0+epsilon, then forced >=1.25) is forbidden in 1x and true2x. Numerical replay checks continuity around 0.65 and nominal white, monotonic upper gain across representative display gains including the measured ~3.72x case, and forbids hard-coded former code-27/1.2462963 behavior.

UPLOAD USING VSCODE.DEV:
1. Confirm branch is experimental-clean-photon-rebuild at successful 26630 commit 74b2d0eb127dd0a3a81a6f85a01343e4c4e84f35 before the new handoff commit.
2. Extract this ZIP locally.
3. Upload/replace the extracted files into repository root, preserving directories including .github/workflows/ and handoff_payload_26631_r1/.
4. Do NOT copy payload files manually into live app/src; the sealed Actions build reconstructs the candidate from the exact successful 26630 compiled artifact.
5. Source Control should contain only the handoff package files, not direct live app/* runtime replacements.
6. Commit message suggestion: 26631 R1: continuous UHDR gain map
7. Push experimental-clean-photon-rebuild.
8. Only the 26631 workflow should trigger from these 26631-specific paths.
9. GitHub Actions is authoritative for pinned real GLSL, Kotlin, Java, both NDK ABIs, full :app:assembleDebug, one-APK proof, and post-build invariance.

TARGET VERSION:
VERSION_NAME 0.9726631
VERSION_BUILD 26631

DO NOT:
- modify dev;
- push an APK;
- add direct live app/src changes to the handoff commit;
- revive the 1.25 UHDR body floor or nominal-white epsilon switch;
- tune SDR tone/local-laplacian/color to hide a gainmap defect;
- weaken exact allowlist/protected/DNG/native/vendor invariance.

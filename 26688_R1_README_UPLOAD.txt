PHOTON 26688 R1 — SPEKTRA CPU RAW FRONTEND

RUNTIME AUTHORITY
- Exact successful 26687 R1.1 Actions compiled candidate.
- Branch: experimental-clean-photon-rebuild
- Commit: 641fa7062cf70e53aef9e72bf56c0f2b5bc96b0b
- Actions run: 35777496614
- Artifact ID: 10717405771
- Artifact name: photon-26687-r1-spektra-isolated-mode-owner
- Artifact SHA-256: 40204ba0ecdb9a041915ddd6a998faaf7e85788f4357b09b71f5f50f244d565f
- Compiled-candidate TAR SHA-256: 19295a3b333e6820e4d15817dedc95b8951bf6b13581e0f8bce31a3a12c583bd
- Exact base candidate: 1768 files.

VERIFICATION-MECHANICS AUTHORITY
- Exact successful 26687 R1.1 procedure.
- Build script Git blob: 2ef3d5a0e90f8b912a29d49427a94895fec12d57
- Workflow Git blob: 0d2de3abab3086d96876bfbb0bb393c7fbef46b9
- Order preserved: sealed package/scope -> exact Actions authority -> deterministic candidate -> semantics/regressions/authority -> successful-mechanics audit -> pinned glslang -> frozen live candidate -> real Kotlin/Java -> both NDK ABIs -> deterministic patch proof -> PRE-BUILD SAFETY PROOF -> full :app:assembleDebug -> exactly one APK -> post-build invariance/export.
- R1_26688_INFRASTRUCTURE_DIFF_AUDIT.txt contains the exact diff audit against successful 26687 R1.1.

BACKUP
- NONE, per user instruction.
- Exact prior hashes + deterministic full-index rollback patch are rollback authority.

TARGET
- VERSION_NAME=0.9726688
- VERSION_BUILD=26688

EXACT RUNTIME CHANGED-FILE ALLOWLIST
10 paths = 8 modified + 2 added, 0 deleted:
1. app/src/main/cpp/CMakeLists.txt
2. app/src/main/cpp/spektra/SpektraNativeJni.cpp
3. app/src/main/cpp/spektra/SpektraRawCpuOwner.cpp [ADDED]
4. app/src/main/cpp/spektra/SpektraRawCpuOwner.h [ADDED]
5. app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraCameraOwner.java
6. app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraPreviewRenderer.java
7. app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraProcessor.java
8. app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraRawFrame.java
9. app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraRawProcessor.java
10. app/version.properties

INFRASTRUCTURE CHANGED-FILE LIST
- .github/workflows/build-26688-r1-spektra-cpu-raw-frontend.yml
- build_26688_r1_spektra_cpu_raw_frontend.sh
- transform_26688.py
- validate_26688.py
- verify_26688_authority.py
- verify_26688_infrastructure.py
- verify_26688_patches.py
- verify_26688_regressions.py
- 26688 manifests/patches/hash/upload/readme/diff-audit files.

INFRASTRUCTURE DIFFERENCE FROM LAST SUCCESS
- Compiler/build ordering: ZERO change.
- Toolchain sequence: ZERO change.
- Pinned glslang 16.5.0: unchanged.
- Java 17: unchanged.
- Kotlin/Java compile stage: unchanged.
- both NDK ABIs stage: unchanged.
- deterministic patch proof before PRE-BUILD: unchanged.
- full assemble / one APK / post-build invariance: unchanged.
- Runtime CMakeLists.txt is intentionally in the candidate allowlist solely to replace SpektraRawVulkanOwner.cpp with SpektraRawCpuOwner.cpp in the existing spektra_iris target; this is not an infrastructure/workflow change.

26688 RUNTIME CORRECTION
- Preserves the 26687 package-private SpektraCameraOwner + public SpektraModeController isolation boundary.
- Preserves Spektra-owned Camera2/session/job/executor/handoff behavior.
- Removes the pre-camera RAW-GPU warm-up from mode entry. Selecting Spektra proceeds directly to openForPreview/Camera2.
- Profile schema advances to 26688 so prior failed discovery/runtime state does not contaminate this generation.
- Active JNI/native target no longer references SpektraRawVulkanOwner.
- Old SpektraRawVulkanOwner and SpektraRawDevelop.comp remain byte-identical historical/dormant source only; CMake excludes the old owner from spektra_iris.
- New SpektraRawCpuOwner owns packed RAW10/RAW12/RAW_SENSOR unpack, black/white normalization, Bayer/CFA phase, lens shading, bilinear RGB reconstruction, saved highlight recovery, sensor-to-linear Rec.709 matrix, saved chroma cleanup, and RGBA16F output.
- Preview uses one source-lattice reconstruction at the center of each 640x480 VF-S footprint and drops when saved work owns the RAW developer rather than queueing.
- Saved full-resolution RAW reconstruction has priority and uses up to four bounded CPU workers.
- Camera2 preview RAW is still copied to Spektra-owned reusable direct staging and Image.close() occurs before native RAW work.
- Existing public SPEKTRA film/print Vulkan renderer, color solver, JPEG publisher, Photo/Motion/Night, DNG, asset shader universe and protected/vendor code are unchanged.

AUTHORITY / INVARIANCE COUNTS
- 1768 successful-26687 base files.
- 1770 26688 candidate files.
- 10 changed, 2 added, 0 deleted.
- 1760 protected unchanged.
- complete native universe: 817 base -> 819 candidate, exact native changed set = CMakeLists + SpektraNativeJni + two new CPU-owner files.
- inherited native-protected universe: 804 unchanged.
- vendor-protected: 778 unchanged.
- DNG: 7 unchanged.
- asset shaders: 271 unchanged.

LOCAL PRE-UPLOAD EVIDENCE
- Exact successful 26687 Actions artifact/candidate authority: PASS.
- Deterministic authority-seeded reconstruction twice: PASS.
- Exact 10-path allowlist: PASS.
- 26688 semantic ownership/RAW-stage validation: PASS.
- Permanent 26681-26687 regressions including the 26687 warm-up/zombie Vulkan failure: PASS.
- Complete native/protected/vendor/DNG/asset-shader manifests: PASS.
- Full-index forward/rollback patches core.abbrev 7/12/40, fuzz=0 exact replay: PASS.
- Host C++ syntax for SpektraRawCpuOwner: PASS (supplementary only).
- Synthetic native preview + saved RAW execution: PASS (supplementary only).
- Local synthetic 4096x3072 -> 640x480 CPU preview benchmark with lens shading: ~42 ms on the local host; this is NOT a Xiaomi performance claim.
- Real pinned glslang in the authoritative Android build: NOT RUN locally; Actions required.
- Real project Kotlin compiler: NOT RUN locally; Actions required.
- Real project Java compiler: NOT RUN locally; Actions required.
- Real Android NDK/CMake both ABIs: NOT RUN locally; Actions required.
- Full :app:assembleDebug: NOT RUN locally; Actions required.

STATUS BEFORE ACTIONS
- PREPARED / UPLOAD-READY only after final clean-extract replay.
- Final Actions/build authority remains successful 26687 R1.1 until 26688 Actions succeeds.
- Device functional acceptance remains unproven until Xiaomi test: fresh launch -> Spektra -> prompt live preview -> capture -> JPEG -> preview resume -> second capture -> Photo -> Spektra re-entry -> capture -> exit.

PHOTON 26687 R1 — SPEKTRA ISOLATED MODE OWNER

Runtime authority:
- exact successful 26686 R1 Actions compiled candidate
- branch experimental-clean-photon-rebuild
- commit b0620bfc0b750db35b8737e46aa0c5e92083be29
- run 35760774779
- artifact 10710700200
- artifact SHA-256 eb4dc9ac0af4131954a84089738f123e13ab172e55d46dbea66714bd7347cf6e
- compiled-candidate TAR SHA-256 5bc93c328a5f4f9837e600f1f18be4bfa36a8d32409a54fc71ade70c142d1dd9

Verification-mechanics authority:
- exact successful 26686 R1 build/workflow mechanics
- build script Git blob 85222dd3d3d05c60f37771ae12bd56c3fa3328e4
- workflow Git blob 8dcdaa6bc131443417563fc1a37d0c6dca3eaa52
- compiler/build ordering is unchanged: authority -> deterministic candidate -> semantics/regressions -> pinned glslang -> frozen live candidate -> real Kotlin/Java -> both NDK ABIs -> patches -> PRE-BUILD SAFETY PROOF -> full assemble -> one APK -> post-build invariance/export

Backup:
- NONE, per user instruction. Exact prior hashes + deterministic binary rollback patch are the rollback authority.

Exact runtime changed-file allowlist: 14 paths = 13 modified + 1 added, 0 deleted.
- app/src/main/cpp/spektra/SpektraNativeJni.cpp
- app/src/main/cpp/spektra/SpektraRawVulkanOwner.cpp
- app/src/main/cpp/spektra/SpektraRawVulkanOwner.h
- app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java
- app/src/main/java/com/particlesdevs/photoncamera/control/TouchFocus.java
- app/src/main/java/com/particlesdevs/photoncamera/manual/ParamController.java
- app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraCameraOwner.java
- app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraModeController.java [ADDED]
- app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraPreviewRenderer.java
- app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraRawFrame.java
- app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraRawProcessor.java
- app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java
- app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIController.java
- app/version.properties

Infrastructure changed-file list:
- .github/workflows/build-26687-r1-spektra-isolated-mode-owner.yml
- build_26687_r1_spektra_isolated_mode_owner.sh
- transform_26687.py
- validate_26687.py
- verify_26687_authority.py
- verify_26687_infrastructure.py
- verify_26687_patches.py
- verify_26687_regressions.py
- sealed manifests/patches/README/upload list/hashes
Infrastructure difference from successful 26686 implementation: wrapper identities, authority/version/scope and new 26687 regression checks only. Runtime CMake, Gradle, shader compilation phase, compiler order, assemble phase and artifact proof ordering are unchanged.

26687 Spektra ownership correction:
- SpektraCameraOwner is package-private behind one public SpektraModeController facade.
- Iris may request enter/restart/shutter/controls/exit and host presentation; it cannot access the camera owner internals.
- Spektra no longer writes CaptureController.isProcessing and owns its saved-photo executor/job state.
- Shutter readiness requires a verified stream, an actually presented current-generation Spektra frame, and no active Spektra saved job.
- Processor/GPU failures cannot poison RAW10/RAW_SENSOR discovery; profile schema 26687 invalidates poisoned 26686 cache.
- Camera2 preview RAW is detached into reusable Spektra-owned direct staging and Image.close() happens before Vulkan/native meter work.
- Native Vulkan preview/saved fences are finite; stats are lock-free and native release is nonblocking.
- Before Camera2 opens, Spektra initializes Vulkan and executes a tiny real compute self-test through the same shader/descriptor/queue/fence path.
- Failed Spektra retirement is fail-contained; it no longer throws into Iris mode switching.
- CameraFragment terminal destruction shuts Spektra down before Iris legacy background teardown.
- No active Iris GLContext/GLProg/GLTexture or Motion RCD ownership is reintroduced.
- Successful 26686 RAW geometry/CFA/LSC/matrix/shader behavior remains byte-identical where protected.

Protected/invariance scope:
- 1767 exact successful-26686 base files
- 1768 final 26687 candidate files
- 1754 protected unchanged files
- 804 native-protected files byte-identical
- 778 vendor files byte-identical
- 7 DNG files byte-identical
- 271 asset shaders byte-identical
- SpektraRawDevelop.comp byte-identical to successful 26686 and still recompiled with pinned glslang 16.5.0 in the same successful order

Local package status before upload:
- exact successful 26686 artifact/candidate authority: PASS
- deterministic candidate reconstruction: PASS after clean replay
- exact 14-path allowlist: PASS
- ownership/lifecycle/processor-discovery/RAW-lifetime/native-containment semantics: PASS
- 26681-26686 permanent regressions plus 26687 self-test/teardown regressions: PASS
- deterministic full-index forward/rollback at core.abbrev 7/12/40 with exact fuzz=0 replay: PASS after clean replay
- real pinned glslang 16.5.0: NOT RUN locally; GitHub Actions required
- real Kotlin/Java: NOT RUN locally; GitHub Actions required
- real NDK both ABIs: NOT RUN locally; GitHub Actions required
- full :app:assembleDebug: NOT RUN locally; GitHub Actions required

Status before Actions: PREPARED / UPLOAD-READY only after final clean-extract replay. Final build authority remains 26686 until 26687 Actions succeeds.

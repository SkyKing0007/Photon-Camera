PHOTON 26686 R1 — SPEKTRA NATIVE RAW VULKAN OWNER

Runtime authority:
- exact successful 26685 R1 Actions compiled candidate
- branch experimental-clean-photon-rebuild
- commit 2b3b5cabb3726e52758756e1db81fd4646e1823c
- run 35735608607
- artifact 10697832130
- artifact SHA-256 486f5719d1f20cff2baa12d95d82d8f067ca657b0c9aa1d37b869db60768ed45
- compiled-candidate TAR SHA-256 7d35ca857c262e07725d2045618e5a19a2cebb1ebac10e434abf46efbcec6eda

Verification-mechanics authority:
- exact successful 26685 R1 guarded build/workflow ordering, itself inheriting successful 26684 mechanics
- no redesign/reordering of compiler/build sequence
- candidate-first reconstruction, exact allowlist, authority-seeded manifests, deterministic full-index forward/rollback patches at core.abbrev 7/12/40, protected/native/vendor/DNG invariance, pinned real glslang 16.5.0, real Kotlin/Java, both NDK ABIs, full :app:assembleDebug, one APK, post-build invariance

Backup:
- NONE, per user instruction. Exact prior hashes + canonical rollback patch are the rollback mechanism.

Exact runtime/native changed-file allowlist: 14 paths = 11 modified + 3 added, 0 deleted.
- app/src/main/cpp/CMakeLists.txt
- app/src/main/cpp/spektra/EmbedSpektraSpirv.cmake
- app/src/main/cpp/spektra/SpektraNativeJni.cpp
- app/src/main/cpp/spektra/SpektraRawDevelop.comp [ADDED]
- app/src/main/cpp/spektra/SpektraRawVulkanOwner.cpp [ADDED]
- app/src/main/cpp/spektra/SpektraRawVulkanOwner.h [ADDED]
- app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraCameraOwner.java
- app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraFrameMetadata.java
- app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraPreviewRenderer.java
- app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraProcessor.java
- app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraRawFrame.java
- app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraRawProcessor.java
- app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraShotStore.java
- app/version.properties

No Photo/Motion/Night runtime source changes.
No global Iris lens-discovery source changes.
No DNG changes.

26686 architecture:
- Spektra owns packed Camera2 RAW from preview/still through one persistent native Vulkan RAW/GPU owner.
- VF-S keeps the live Camera2 Image open while native code consumes the original packed RAW plane; preview frames drop before expensive work if saved processing owns the GPU.
- Saved processing stores durable packed RAW bytes + stride/format + complete geometry/metadata recipe; Java never expands a full Bayer image.
- rawBounds, sourceCrop, and activeRawDomain are carried in one RAW-raster coordinate system Java -> JNI -> Vulkan.
- Bayer origin remains fail-closed when sensor->RAW active-array mapping cannot establish an exact phase.
- CFA/black levels are phase-shifted consistently.
- Camera2 lens shading is interpolated over activeRawDomain; G-even/G-odd is selected from sensor Bayer-row parity recovered through the verified Bayer offset.
- Demosaic border taps remain inside activeRawDomain while preserving Bayer phase.
- sensor->linear-sRGB is applied with explicit row-major dot products; the prior GLES transpose ambiguity is gone.
- Preview uses native RAW develop -> scene-linear RGB -> reduction -> public Spektra film/print renderer.
- Saved path uses full source crop -> native RAW develop -> public Spektra film/print -> SDR sRGB -> JPEG100.
- No active Spektra Iris GLContext/GLProg/GLTexture ownership.
- No Motion RCD26498 ownership or CPU full-resolution Bayer display/saved fallback.
- Persistent Vulkan buffers/device/pipeline are reused; saved work has priority; preview queues are not allowed to build up.

Authority/manifests:
- 1764 exact successful-26685 base files
- 1767 final 26686 candidate files
- 1753 protected unchanged files
- inherited 804 native-protected files byte-identical
- inherited 778 vendor files byte-identical
- 7 DNG files byte-identical
- 271 inherited asset shaders byte-identical
- 1 new native compute shader, SpektraRawDevelop.comp, separately reserved-identifier scanned and scheduled for pinned real glslang 16.5.0 compile before language/native compilers

Infrastructure:
- Outer handoff/workflow/build/validator wrappers are 26686-specific but preserve successful 26685 invocation order.
- app/src/main/cpp/CMakeLists.txt and spektra/EmbedSpektraSpirv.cmake intentionally differ from 26685 only to compile/embed the new Spektra RAW compute shader and add the SpektraRawVulkanOwner.cpp source to the existing spektra_iris target.
- No new native target and no new build phase.

Local package status before upload:
- exact successful 26685 artifact/candidate authority: PASS
- deterministic candidate reconstruction: PASS
- exact 14-path allowlist: PASS
- RAW-domain/ownership/geometry semantic checks: PASS
- 26681-26685 permanent regressions: PASS
- complete reserved-identifier scan on modified shader: PASS
- deterministic full-index forward/rollback 7/12/40 and exact rollback: PASS
- real pinned glslang 16.5.0: NOT RUN locally; GitHub Actions required
- real Kotlin/Java: NOT RUN locally; GitHub Actions required
- real NDK both ABIs: NOT RUN locally; GitHub Actions required
- full :app:assembleDebug: NOT RUN locally; GitHub Actions required

Therefore this package may be called PREPARED / UPLOAD-READY only after its final clean-extract replay passes. It is not Actions/build proven until the workflow succeeds.

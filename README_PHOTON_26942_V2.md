# Photon 26942 V2 — three-stage vscode.dev Actions handoff

**Status: PREPARED FOR ACTIONS, NOT BUILD-PROVEN.** 26942 Vulkan/NDK/GLSL/SPIR-V/Kotlin/Java/assemble require real GitHub Actions compilation. Device speed and visual/image quality NOT RUN. Do not upload an APK.

## EXACT latest successful source/runtime authority: 26941 V1

- Repository: SkyKing0007/Photon-Camera, experimental-clean-photon-rebuild
- Successful run: `43744946760`
- Commit: `05af6b7c0eb9ddeff59cf4947f8469b384cc8ed2`
- Published artifact: `14174631230`, SHA-256 `24069acd5c83482471e72f8af8211775335072e3876e93cd72a5de4cb71971f2`
- ACTUAL compiled source TAR SHA-256 `ba1d5ce75a2a5dbc01fb0f6ed3b94193d9fbbf24fe033adc6c59ee6a46e31aa5`
- ACTUAL executed builder SHA-256 `bb86f4a5e65e07a0c1312b4efdc5c9f2866d056de87a7c9de0788dcd99072024`
- ACTUAL executed workflow SHA-256 `18578ec9f6682cc35255691f66a8b8d41311609041c164835e8847d561e049d6`
- Prior successful APK SHA-256 `8fce2c03d78fcea209e86b47d75d25b0a010dca604e987ce3074298e02583648`
- Original successfully compiled app universe: **2050 files**

## Corrected V2 native linking and unchanged original 26942 HDR+ implementation

26942 V1 run `43750385496`, job `132922810186`, failed the authentic arm64 NDK compiler: `Iris26888BOffHdrqCoordinator.cpp:992` used `iris26941BOffHdrqLazyPoolReset` without a declaration. This V2 adds the namespace-scoped `extern thread_local bool` in the B-only coordinator, referencing exactly the unchanged successful 26941 executor TLS definition. **No vendor, CMake, Gradle, shader, JNI, or control-flow change.** The native-host gate now compiles and links separate translation units with negative missing-declaration and wrong-namespace probes to prevent V1 recurrence. The original historical and build sequence remains immutable.

## SINGLE SPECIFIC 26942 runtime change

Strict allowlist exactly 2 files, no additions/deletions: `app/src/main/cpp/iris26864/bridge/Iris26888BOffHdrqCoordinator.cpp` and `app/version.properties`. **2048 protected files byte-identical**. No vendor, GLSL, Java/Kotlin, Gradle, CMake, native libraries, visual SDR/UHDR, Super Res ON, Spektra, Night, A, A+B, Motion, LONG or DNG behavior changed.

Photo Experiment B, Super Res OFF, physical-lens-relative zoom strictly below 1.10x only: RAWR's native HDR+ Frequency code retains 15 RAW frames, four half-tile-shifted passes, all per-frame normalization/noise/alignment/frequency shaders and exact sequence, original pass-0 split coarse/fine alignment (preview fairness) and all frame-consumption fences. When align-once is enabled, **passes 1–3** pad each companion RAW then record its unchanged frequency merge **in the same Vulkan command buffer/queue submission**. Pinned vendor `recordPrepare()` already records compute-write-to-compute-read barrier; it remains intact. This eliminates a potential **3 × 14 = 42** separate Vulkan submissions/fence waits for a 15-frame capture (one prior padding submit per later-pass companion), without bypassing a necessary GPU dependency. Original independent scheduling is unchanged for other modes, bracketed and non-align-once.

The fix addresses real queue scheduling rather than another pipeline-startup adjustment. **No numerical FPS/latency improvement is claimed before device testing.** Saved SDR/UHDR matched rendering and removed fallback settings from successful 26941 remain fully protected.

## Upload exactly three stages to vscode.dev

Upload only the files in the enclosed three stage lists, preserving relative paths and exact bytes:

1. `26942_V2_STAGE_1_UPLOAD_PATHS.txt` — all runtime payload, builder, guardrail validators, source/protected manifests, complete forward/rollback and handoff receipts. Do not upload a ZIP as a repository file.
2. `26942_V2_STAGE_2_UPLOAD_PATHS.txt` — `.github/workflows/build-26942-change-aware.yml`
3. `26942_V2_STAGE_3_UPLOAD_PATHS.txt` — **`TRIGGER_26942.txt` last** to start Actions on `experimental-clean-photon-rebuild`.

Do **not** modify dev, create a backup branch, push an APK, or compile an earlier candidate from stale `app/src`. No commit/push is performed by the handoff itself.

## Mandatory verification inherited, never weakened

- Original **141 historical Actions executable commands hash-pinned**; preserve 26886/26887, 26903 V3 receipt, 26904 V1 SPIR-V reserved-token/optimizer and V2/V3 Spektra CMake, all 26925/26938/26940/26941 regressions.
- SHA-lock the **published exact successful 26941 artifact**, compiled 2050-source TAR and prior executed builder/workflow and APK; reconstruct candidate first and verify 2048 protected sources.
- Actual C++17 guard test for B OFF, 4-pass scheduling, 42 avoided submissions at 15 frames, timestamp mapping; original RAWR alignment+merge verbatim under fallback branch; strict source SHA, Git full-index patch forward/reverse/independent rollback with core.abbrev=7,12,40; negative tamper tests.
- Pinned real glslang 16.5 + SPIR-V optimizer/validator (all five 26942 current shader inputs, 26904 historical gates), mandatory both-ABI NDK/CMake, Kotlin, Java, exactly one full `:app:assembleDebug` and exactly one published output artifact.
- SHA-verified offline original RawLens 2.2.86 dual-ABI binaries from **successful 26941 APK** and real ELF/linkage checks, actual APK hashes, original 26906 native cache provenance, full source TAR/runner receipts and final seal.

**Local status (V2):** source allowlist/protection PASS; actual 26941 archive/TAR/manifest authenticity PASS; C++17 scheduler host PASS; GLSL reserved-identifier and arity static checks PASS; historical workflow/141 command seal PASS; 2-file forward/reverse/independent rollback PASS; negative/clean ZIP checks PASS. **26942 pinned real GLSL/SPIR-V, dual ABI native, Kotlin, Java, APK assembly, published artifact, new APK hash, device image quality, and device timings = NOT RUN until Actions/device.**

Commit message is in `26942_COMMIT_MESSAGE.txt`.

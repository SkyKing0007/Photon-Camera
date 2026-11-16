# Photon 26943 V5 — correct Vulkan HDRq descriptor layouts (capture-error repair)

**Status: LOCALLY VALIDATED / PREPARED FOR ACTIONS. NOT BUILD-PROVEN and NOT DEVICE-PROVEN.** No repo commit/push has been performed. Upload one three-stage vscode.dev ZIP only; do not upload APKs or run local user scripts.

## Device failure actually reproduced

Your `26943.zip` logs show two Photo Experiment B, Super Res OFF, 1.0x attempts; each collected all **15 RAW frames** but failed on the processing thread at `mf compute pipeline shader=hdrq_mismatch variant=prod ... VkResult=-13`. The 26943 source added GLSL binding **5** (`hdrq_motion_min`) to `Iris26888BOffHdrqMismatch.comp`, while the unchanged executor only declared bindings 0–4. The same error would occur later in `hdrq_border`: shader has binding **2**, executor had only 0–1. The recorder already binds both resources, with 100-byte mismatch and 16-byte border push constants. Khronos Vulkan requires shader/descriptor-layout compatibility at pipeline creation; this is a concrete fix for the identified integration defect, but device capture must verify the result. The -13 driver code cannot independently prove no other runtime defect exists.

## Exact latest successful compiled runtime authority — 26943

- Successful Actions run **43799170615**; commit **85b4f794e44254e9dde61b03540cff7d0794fdc4**; artifact ID **14195478145**.
- Published ZIP SHA-256 **9d0ba6e30ddfc92c32da49516dc269b246d53772649841c187d506e6ccd4af21**; 26943 actual compiled candidate TAR SHA-256 **e7c923439e964ee16c39d6737fd3ff47e8b89589df6e5f508e22df6b32af93f9**.
- Actual successful 26943 executed builder SHA **ad7250f5249d7c5e3def108e034a712068bdeb7c26cf9ad04c224e2bf736e620**; actual 26943 executed workflow SHA **0d0126034275b4e82bc2b822bc6b10c0d04e574071e11d1140d14188e4574d51**; compiled 26943 APK SHA-256 **cb39df30033fafbcaa95941872f3c7280267fb79e4ca28c83bcf661c9a97e0c7**.
- Source comparison against latest successful compiled 26943: **1 changed existing C++ file, 2 added Vulkan descriptor declarations, 2053 exact SHA-protected files, no additions or deletions**. No vendor, original 26942 scheduler, shaders, Camera2/Java/Kotlin, Gradle, or other native changes.
- The unchanged successful-26943 build procedure still reconstructs exact successful 26942 V2 compiled source (run **43772082845**, artifact **14185016520**, source TAR SHA **91ad16f7f4e1b529124c60b09ceacaf6b600cd9ebca0f7ca0224636aaaf98b91**). Its resulting candidate must be byte-identical to successful 26943 on all files except the corrected executor. 26942->candidate patch scope thus becomes **18 modified existing + 4 added, 2032 protected**, from 2050 to 2054 files; the extra modified source is explicitly authorized.

## Targeted repair

Exactly two additions in `app/src/main/cpp/iris26864/bridge/Iris26888BOffVulkanExecutor.cpp`:

1. `hdrq_mismatch`: add `binding 5` as `VK_DESCRIPTOR_TYPE_STORAGE_IMAGE` to the descriptor specification (bindings 0–5).
2. `hdrq_border`: add `binding 2` as `VK_DESCRIPTOR_TYPE_STORAGE_IMAGE` (bindings 0–2).

The existing `vkCreateDescriptorSetLayout`, `VkDescriptorPool`, `record()` missing/duplicate checks and descriptor writes automatically consume `Spec::b`. No shader source/motion maths/vendor files need modification. The existing mandatory `test_26943_source.py` now extracts **shader binding declarations, executor binding/type layouts and recorder bindings** and rejects missing mismatch-5, border-2, type mismatch, recorder mismatch and shader omission. It also tests the exact executor against the published 26942 compiled authority with **only the two approved additions**, and retains API26 CMake linker/Java scope regressions. Original pinned glslang/SPIR-V, both native ABI CMake/NDK, Kotlin, Java, assemble, all historical 141 workflow commands, 211 executable references, 26886/26887, 26903 and 26904 V1/V2/V3 regressions are unchanged and mandatory.

## Mandatory upload/verification sequence

Stage 1: upload all files within **STAGE_1_REPLACE_CURRENT_26943** to their matching paths on `experimental-clean-photon-rebuild` (the staged runtime C++ is under `handoff_payload_26943/`, not `app/src`). Commit Stage 1 with the included commit message. Stage 2: the `.github/workflows/build-26943-change-aware.yml` in **STAGE_2_UNCHANGED_WORKFLOW_REFERENCE_ONLY** is **reference only, DO NOT reupload**; its existing V2 R1 title is historical and preserved to avoid workflow deviation. Stage 3: upload `TRIGGER_26943.txt` from **STAGE_3_TRIGGER_LAST**, commit last to trigger the unchanged full guarded Actions run.

Actions must pass original 26942 and 26943 seals, full actual 26942->26943 source reconstruction, the new descriptor ABI fail-closed negative regressions, pinned shader compiler and optimizer, two ABI native/CMake and Kotlin/Java compilers, real assembleDebug, APK and source TAR publication; verify resulting published artifact SHA and device Photo B OFF 15-frame JPEG save **before** claiming the capture defect is resolved. Build success alone cannot establish successful capture/image quality. **No user-triggered build result exists for this V5 at packaging time.**

**Historical file naming:** `README_PHOTON_26943_V1.md`, `26943_V1_STAGE_*` and the V2 R1 workflow name remain path-stable on purpose; their contents/active tests are updated accurately, not stale V1 source.

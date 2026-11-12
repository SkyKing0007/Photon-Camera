# Photon 26920 V4 — Fix native Vulkan descriptor ABI crash, preserve active per-lens Lucas–Kanade SR

**DELIVERY STATUS: LOCALLY VALIDATED / PREPARED FOR ACTIONS. NOT BUILD-PROVEN.**
This is a standalone replacement for 26920 V3, for the user's existing **three-stage vscode.dev upload**.
It contains the exact revised source, strict allowlist/patch/manifests, builder, verifier and workflow;
**it does not contain a compiled 26920 V4 APK** or a successful V4 Actions artifact.

## Device failure evidence and concrete repair

The user's `26920.zip` contains two failed Experiment B Super Res ON captures,
22:46:45 with Lucas–Kanade SR **OFF** and 22:47:01 with it **ON**.
Both admitted 15 frames before native processing failed with:

    mf compute pipeline VkResult=-13

The prior V3 shaders add two unconditional descriptor declarations:
- `lk_refine.comp`: `set=0,binding=4`, `VK_DESCRIPTOR_TYPE_STORAGE_BUFFER`;
- `robust_photometric.comp`: `set=0,binding=9`, `VK_DESCRIPTOR_TYPE_STORAGE_BUFFER`.

V3's native `VulkanExecutor.cpp` still had the successful 26917 layout without
these bindings. `VulkanExecutor::initialize` creates *all* shader pipelines,
even when the per-lens toggle is OFF; thus both OFF and ON crashed before
fusion. This is a concrete source-level shader/native ABI mismatch; the Vulkan
error alone does not identify the failed shader, so a secondary driver failure
cannot be ruled out without a V4 device capture.

**V4's only runtime change relative to V3** is:

    app/src/main/cpp/iris26864/vendor/rawr/native/multiframe/pipeline/src/VulkanExecutor.cpp

It adds storage-buffer descriptors 4 and 9 with the exact types of the active
shader interfaces, and on any remaining pipeline-creation failure names the
failed shader and `prod`/`trace` variant, rather than only `VkResult=-13`.
The existing `MultiframeRecorder` already supplies both buffers in OFF and ON
and is byte-identical to V3. **All 16 existing V3 changed runtime paths are
byte-identical in V4**, including the active LK math, confidence math, per-lens
Settings switch, capture snapshot, logs and JNI integration.

## Runtime source and guarded build authority

- Repository: `SkyKing0007/Photon-Camera`; branch: `experimental-clean-photon-rebuild` only.
- Successful **26917 runtime/image authority**: Actions run `42859946714`,
  commit `83ad93725baf8de8fa7653235e93e4fc0ffeaebb`, published artifact
  `13786011058`, artifact SHA-256
  `ae09ca810fee66057f173ccc65efbe18772c2561b0c96e8931763da748b2e57b`.
- Exact successful 26917 compiled candidate TAR SHA-256
  `d82d550362b22a5486098335a41e3817b1417256205c356c6ef837aceb7d68a1`.
- Exact executed 26917 builder SHA-256
  `31eebc26fa69a71da1c82bd7a304bd7d8c4e8158d598df12a92a5b8e21a535bf`;
  workflow SHA-256 `8d75c66c70ab0c2a6be029a5707e52fea05d3c4a1075ec8be70c04e27ea4afcb`;
  APK SHA-256 `3846787d39e59084098d1771f7b8084fd12c86e36157cc098c0961fdf9773c18`.
- Verification mechanics inherited unchanged from last successful **26919**
  Actions run `42947897865`, commit `22a389f9c61396979fc5ba7a9b312244e85ffc5b`,
  artifact `13823509427`, and from the previous 26920 V3 guarded procedure.
  The compiled 26919 *source* is NOT the active runtime base for V4.
- Separate historical failure: 26920 V2 run `43144114124`, job
  `130937798460`, failed on `spirv-opt --target-env vulkan1.1`. Its fixed
  `spirv-opt --target-env=vulkan1.1` remains mandatory in V4.

## Source allowlist / protected invariance

Successful 26917 compiled authority: **2,036 source files**.
V4 exact candidate: **2,038 files**, **17 changed paths including two added
Java files**, zero deletions, **2,021 original files byte-identical**.
Every intended runtime change is in `26920_CHANGED_RUNTIME_ALLOWLIST.txt`;
additional protected files (including native/vendor code) are SHA-256 frozen.
The seven 26917 physical-Bayer-border components are explicitly checked by
`26920_FROZEN_26917_BORDER.sha256` and remain bit-identical, including JNI,
AMaZE and `amaze_import.spv`. The 26917 440,800 border checks remain in the
inherited workflow. The entire 17-path full-index Git patch must apply/reverse
with zero fuzz at `core.abbrev=7,12,40`.

## Actual image-processing semantics (not a diagnostic-only APK)

The **Lucas-Kanade SR** AndroidX switch sits directly below the per-physical-lens
**Reconstruction experiment** setting, using the same native Settings style,
icon spacing, font and toggle. Default OFF, persisted by physical lens.

- **B Photo, Super Res ON, LK OFF:** original clean 26917 Wronski true-2× math
  with no extra alignment/weight correction. Shader buffers remain *declared*
  and *bound* but their new branches are not executed.
- **B Photo, Super Res ON, LK ON:** active existing Wronski true-2× path with
  RAW-derived consistency gating, bounded confidence reductions for already
  valid contributors, and one additional at-most-0.125-sensor-pixel subpixel
  Lucas–Kanade correction on stationary tiles only when independent held-out
  measurements improve. These actually modify flow and fusion weights before
  output. No separate full-frame reconstruction or neural SR model.
- Experiment A, Night, DNG, UHDR, Spektra, B Super Res OFF, genuine color,
  original 50MP output and physical borders preserve their previous ownership.
- If an **ON** capture suffers a native/GPU infrastructure failure, it fails
  explicitly rather than silently routing the whole capture back to OFF.
  Local noisy/moving/clipped regions reject unsafe refinements as an inherent
  part of the algorithm, not an opaque entire-image fallback.
- Existing `log.txt` and `motiontrace.txt` emit `IRIS_26920_B_ON_LK`, lens,
  frame/ref provenance, toggles, GPU timings, accepted/rejected LK candidates,
  sampled contributor confidence updates, and reasons for zero accepted work.

## Additional targeted V4 regression, without weakening previous gates

New `test_26920_vulkan_abi.py` verifies the *four-way contract* for each
new shader: GLSL interface, VulkanExecutor `VkDescriptorSetLayoutBinding`
types, exact MultiframeRecorder runtime bindings and resource lifetime.
The script also independently reflects **real binary SPIR-V** via
`OpDecorate Binding`/`DescriptorSet` and `OpVariable`/`OpTypePointer` storage
classes, comparing it to the native descriptor table:

1. Before the Android build, the pinned glslang 16.5.0 compiles the **actual**
   production and trace shaders (`lk_refine`, `robust_photometric`). The
   existing real `spirv-val -> spirv-opt --target-env=vulkan1.1 -O -> spirv-val`
   chain remains mandatory. The new script checks all **four compiled SPIR-V
   binaries and four optimized binaries**, including trace binding 31.
2. After full native CMake compilation, the script independently validates
   **all eight** actual CMake-generated SPIR-V binaries for **arm64-v8a** and
   **armeabi-v7a**, production and trace. A missing, duplicated, mis-typed
   or stale descriptor causes a hard FAIL, without publishing the APK.
3. Static source gate and a consistently resealed hostile mutation reproduce
   the previous V3 missing/wrong `binding=4` error and require rejection.
   The V2 malformed optimizer CLI is separately reseal-tested and rejected.

All existing 26919/26920 V3 steps stay: exact run/artifact/TAR/builder
receipts, strict protected-source scan, prior 26886/26887, 26903, 26904
V1 optimizer/V2 Spektra CMake/V3 success, 26914 Kotlin, 26915 tele/normal,
26916 colors, 26917 border, 26918 and 26919 regressions, pinned GLSL,
SPIR-V, real two-ABI NDK and Spektra CMake, real Java/Kotlin compilation,
`./gradlew --no-daemon --build-cache :app:assembleDebug --stacktrace`,
source-matched cache provenance, clean-extract/patch/mutation proofs and
successful APK+receipt publication **only after real compilation passes**.
Do not substitute an old compiled binary or disable optimization to pass.

## Exactly three vscode.dev upload stages — no user-run scripts

**Stage 1:** Upload exactly all **35 paths** in `26920_STAGE1_PATHS.txt` to
the corresponding repository-relative locations. Replace any existing 26920
V2/V3 staging paths. This adds the new native `VulkanExecutor.cpp` payload
and `test_26920_vulkan_abi.py`. Do **not** upload the ZIP, README, APK,
authority TAR or temporary workspace.

**Stage 2:** Replace ONLY
`.github/workflows/build-26920-change-aware.yml` with the included new
workflow. Retain older successful workflows untouched.

**Stage 3:** Upload ONLY `TRIGGER_26920.txt` to the repository root **LAST**.
Exact bytes are the ASCII line (with one terminating newline):

    RUN_26920_V4_B_ON_LK_DESCRIPTOR_ABI_REPAIR_FROM_SUCCESSFUL_26917

**Suggested commit message for the user:**

    Photon 26920 V4: fix eager Vulkan descriptor ABI for Lucas-Kanade SR ON and OFF

Never modify or push `dev`, create backup branches, push APKs, or commit/push
source from the assistant without explicit approval. The user performs the
usual three-stage upload and commits only after all three stages are staged.

## Verified/unknown state and how to judge device results

**LOCALLY VALIDATED:** exact compiled 26917 source, full 2,038-file V4
candidate, 17-path allowlist/2,021 protected and seven frozen border SHA
checks, real full-index patch forward/reverse at 7/12/40, source-level
Vulkan-executor/recorder/shader ABI, 100,000 host LK math cases, hostile
sealed package mutations and clean-extracted handoff proof.

**PREPARED FOR ACTIONS, NOT BUILD-PROVEN:** Real pinned GLSL+SPIR-V binary
reflection, both Android ABIs' actual CMake shaders, Kotlin, Java, NDK,
Spektra CMake and full APK assembly are **NOT RUN locally** (the required
Android SDK/pinned GLSL toolchain is not installed). No V4 APK, V4 APK SHA,
new successful Actions artifact or successful V4 Actions job is claimed.

**Physical device not verified:** Even a successful APK cannot establish
no crash on the user's Vulkan driver, no halo/ghost/color/border regression,
or better real-world IQ without matched OFF/ON captures and logs.

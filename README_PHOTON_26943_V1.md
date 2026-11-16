# Photon 26943 V3 — Android API-26 Vulkan instance dispatch repair

**Status: LOCALLY VALIDATED / PREPARED FOR ACTIONS, NOT BUILD-PROVEN.** This supersedes the failed 26943 V1, V2 R1, V2 R2 handoffs. The filename `README_PHOTON_26943_V1.md` is a **historic sealed repository key** required by the original 26943 builder; the content and candidate are V3, not V1.

## Verified failure and constrained correction

- Failed V2 R2 GitHub Actions run `43793999818`, job `133058564037`, commit `8036ad0acddfe6c9e06183ace6d503d283dae933`: the 26943 GPU ring reached the arm64-v8a NDK API-26 native shared-library linker. `ld.lld` rejected a direct undefined `vkGetPhysicalDeviceImageFormatProperties2` reference from `Iris26943RawAhbIngress.cpp:95`. This is a Vulkan 1.1 *instance* command not exported as a linked global function by the API-26 NDK Vulkan stub. GLSL/SPIR-V and all preceding project/history gates PASSED; no APK or artifact published.
- V3 changes **only four already-allowlisted 26943 files**, not unrelated image processing, vendor source, A/Night/SR ON, native libraries, Kotlin/Java, NDK versions, shader math or Actions workflow. `VulkanDeviceOwner` exposes its existing live Vulkan 1.1 `VkInstance`. The GPU ring forwards that instance to the existing uploader and its ingress worker. `importDirect` resolves `PFN_vkGetPhysicalDeviceImageFormatProperties2` with `vkGetInstanceProcAddr(instance, ...)`, checks for null and falls back to the existing GPU-buffer/CPU-worker or known post-shutter 26942 path. **No direct Vulkan 1.1 link-time call remains.** The original Vulkan 1.1 instance and physical-device admission checks are unchanged.
- New `test_26943_source.py` regression rejects direct Vulkan1.1 link-time usage, missing instance ownership, null dispatch without fallback, API29 `lockPlanes`, and duplicate AHB descriptors. It also compiles and links positive and negative host shared-library loader fixtures with `--no-undefined`, checking null function pointer behavior. **Host fixture is NOT Android NDK proof.**
- New forward and independent rollback full SHA-40-index patches are generated from exact successful 26942 compiled source, all 21 source paths, and each passes actual original `test_26943_patch_proof.py` at `core.abbrev=7,12,40` including deletion of all 4 additions. No missing/stale references or new workflow executable paths; original historical 141 command graph and 211 executable references retained.

## Latest successful compiled runtime authority — 26942 V2

Run `43772082845`; commit `514c3caca5f56b3fe289ec2220be520eb61fa096`; published artifact `14185016520`; archive SHA-256 `08ed272d964bc0f0e3987ddf5315abb74c9dc8cf6a22a8ade108527f9a571040`; actual compiled source TAR SHA-256 `91ad16f7f4e1b529124c60b09ceacaf6b600cd9ebca0f7ca0224636aaaf98b91`; successful builder SHA-256 `602bac28864953f5c819beee5df799132ff0ecdc2b3d1361f3a6295987de6af7`.

Current 26943 builder remains byte-identical SHA-256 `ad7250f5249d7c5e3def108e034a712068bdeb7c26cf9ad04c224e2bf736e620`. Existing Actions workflow remains byte-identical SHA-256 `0d0126034275b4e82bc2b822bc6b10c0d04e574071e11d1140d14188e4574d51`. Workflow display/artifact label still says V2 R1 **by deliberate unchanged infrastructure identity only**; effective V3 runtime is determined by SHA-locked 2054-source manifest, not the label. Do not adjust this workflow name or skip any build gate.

## Invariance and outstanding checks

Successful 26942 = **2050** source files; prepared V3 = **2054** source files, **17 modified existing + 4 added**, exactly **2033 protected SHA-identical**, zero source deletions. The 26943 V3 delta from failed V2 R2 is exactly **four source files**. No changes to `app/build.gradle`, toolchain/CMake config, pinned native vendor, shaders, Kotlin or Java.

**PASS locally**: actual full manifests, 2033 protected, four-source delta, direct Vulkan1.1 API26 link-negative/instance-dispatch-positive host regression, five intentional negative source mutations, `test_26943_source.py --payload/--live`, strict original patch verifier `--payload/--base` and 7/12/40 full-index reversible replay, all 48 file-seal entries and clean ZIP extraction. **PASS on failed V2 R2 Actions**, unchanged by V3: 26904 original GLSL optimizer and V3 CMake handoff, pinned real GLSL/SPIR-V 26943, original 141 historical commands, 211 reference checks and 26942 compiled authority extraction. **V3 real dual ABI NDK shared linking, Kotlin, Java, assembleDebug, APK/artifact/publication, and device capture/IQ are NOT RUN.** Only successful Actions full compile plus published artifact establishes BUILD-PROVEN; device tests must separately verify photo quality.

No source commit/push, backup branch or APK distribution was performed by the assistant.

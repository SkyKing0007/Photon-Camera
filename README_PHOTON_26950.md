# Photon 26950 V4 — corrected SPIR-V optimizer CLI and vendor-free preseed, original RAWR HDR+ Quality 11, B SDR highlight separation

Upload **STAGE_1**, then **STAGE_2**, then **STAGE_3** on `experimental-clean-photon-rebuild`. Do not modify dev, push source, or upload APKs without approval. Use `26950_COMMIT_MESSAGE.txt`.

Successful authority: 26949 V3 Actions run 44011825852, commit 8de5746d0538b1c1db8d0eae8c43fa6205eeef9a, artifact 14296379634, artifact SHA f1aab9609fb433c0801214eae38f140d5da62495ea8ed55c1ef244435973c183, exact compiled TAR SHA f0ee025dc99e672564ffc8cc1638d07cb83e7902457cf73b3f3c157819945463, executed builder SHA 0671bfa844be74a0058d20fa4a9e2f4e703e57386e2bf7bbe2b35bcd538f5239; workflow SHA 2e269b44b79b0c9c7e5030bf64232c49083944fb04c68d926d4315f67be9a58a.

Ten intentional runtime files, 2,044 protected. V3 changes NO runtime file bytes from V2. Original 26950 RAWR HDRq Fourier merge restoration at strength 11 for B OFF and B Night retained. Three additional changed files: MotionV2Render.java and matched motionv2 render/gainmap GLSL. Only B HDRq OFF and B Night limit surplus HDR-derived SDR highlight uplift (pointwise and monotone, unchanged at <=0.82 or >=2.70). Original white-shoulder function, UHDR HDR numerator, source reconstruction, A, B ON, native/vendor, AMaZE, FCC, DNG and Spektra are protected. No semantic or spatial edge mask.

Successful 26949 V3 historical workflow prefix, all pinned historical compilers and regression scripts remain. Historical 26948 GLSL compiler is replayed using original sealed 26948 payload for the version-specific checker, but its entire real compiler body runs on live current shaders, plus a second current 26950 V2 ESSL300/310 + SPIR-V compiler and new numeric/source parity checks. Never substitute static checks for real compilation.

PREPARED FOR ACTIONS only until successful Android NDK/Kotlin/Java/shader/assemble and published APK. Device visual quality NOT proven by build alone.

### V3 exact Actions correction (failed run 44102586828)

The 26950 V2 source preflight at checkout incorrectly read `app/src/main/cpp/iris26864/vendor/rawr/native/multiframe/merge_hdrplus/shaders/hdrq_merge.comp` BEFORE the authentic compiled 26949 source TAR was downloaded/extracted. Vendor bytes are absent from the lightweight checkout until successful authority reconstruction. V3 checks the four staged original RAWR shaders against original SHA-256 entries in the sealed 26949/26950 protected source manifests during `--payload`, without relying on the vendor tree on disk. `--live` still requires the actual vendor files and checks each byte after reconstruction. The isolated `--preseed` test copies only staged source, confirms the original missing-vendor environment, succeeds, and rejects a forged/resealed vendor hash. It executes BEFORE artifact download in Actions. Historical checks and all real pinned compiler stages are unchanged.

26950 V2 failed at source preflight; no 26950 Kotlin/Java/NDK/assemble/APK was produced. V3 remains only prepared until successful Actions and published APK.

### V4 actual GitHub Actions failure and exact correction (run 44106717762)

The real 26950 V3 Vulkan shader stage failed AFTER glslang and spirv-val on the first of four native shaders because the current **spirv-opt** CLI incorrectly used `--target-env vulkan1.1 -O`. SPIRV-Tools requires `--target-env=vulkan1.1 -O`, as corrected previously by 26904 V3. The 26950 SDR shader compiler already used the correct `--target-env=opengl4.5` form and is kept unchanged. V4 corrects the failing Vulkan command, preserving real glslang 16.5, both Vulkan/GLSL compilers, pre/post spirv-val, optimizer -O, two-ABI NDK, Kotlin, Java, complete assemble and all historical checks. The successful 26949 workflow prefix and the ENTIRE 26950 V3 workflow are byte-for-byte identical.

A new mandatory early check within the existing Actions-invoked `test_26950_workflow_refs.py` requires both corrected SPIRV-Tools argument forms and valid Bash syntax. Its two negative tests deliberately reintroduce the exact positional 26904 V2 error and reject it, even when the staged files are otherwise valid. V4 has ZERO runtime source modifications relative to 26950 V3; all ten changed source SHA-256 values and all 2,044 protected source hashes remain unchanged. Real Android compilation remains mandatory and unproven until a successful Actions job publishes an APK.

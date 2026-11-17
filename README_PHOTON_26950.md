# Photon 26950 V2 — original RAWR HDR+ Quality 11, B SDR highlight separation

Upload **STAGE_1**, then **STAGE_2**, then **STAGE_3** on `experimental-clean-photon-rebuild`. Do not modify dev, push source, or upload APKs without approval. Use `26950_COMMIT_MESSAGE.txt`.

Successful authority: 26949 V3 Actions run 44011825852, commit 8de5746d0538b1c1db8d0eae8c43fa6205eeef9a, artifact 14296379634, artifact SHA f1aab9609fb433c0801214eae38f140d5da62495ea8ed55c1ef244435973c183, exact compiled TAR SHA f0ee025dc99e672564ffc8cc1638d07cb83e7902457cf73b3f3c157819945463, executed builder SHA 0671bfa844be74a0058d20fa4a9e2f4e703e57386e2bf7bbe2b35bcd538f5239; workflow SHA 2e269b44b79b0c9c7e5030bf64232c49083944fb04c68d926d4315f67be9a58a.

Ten intentional runtime files, 2,044 protected. Original 26950 RAWR HDRq Fourier merge restoration at strength 11 for B OFF and B Night retained. Three additional changed files: MotionV2Render.java and matched motionv2 render/gainmap GLSL. Only B HDRq OFF and B Night limit surplus HDR-derived SDR highlight uplift (pointwise and monotone, unchanged at <=0.82 or >=2.70). Original white-shoulder function, UHDR HDR numerator, source reconstruction, A, B ON, native/vendor, AMaZE, FCC, DNG and Spektra are protected. No semantic or spatial edge mask.

Successful 26949 V3 historical workflow prefix, all pinned historical compilers and regression scripts remain. Historical 26948 GLSL compiler is replayed using original sealed 26948 payload for the version-specific checker, but its entire real compiler body runs on live current shaders, plus a second current 26950 V2 ESSL300/310 + SPIR-V compiler and new numeric/source parity checks. Never substitute static checks for real compilation.

PREPARED FOR ACTIONS only until successful Android NDK/Kotlin/Java/shader/assemble and published APK. Device visual quality NOT proven by build alone.

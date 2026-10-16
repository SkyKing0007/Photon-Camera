26845 — adaptive LONG low-frequency shadow luminance / shadow SNR correction.
Runtime authority: successful 26844 Actions run 38840327696, commit 284429b4eb92fe380163e0a287dc444926295840, artifact 12021062254.
Verification mechanics: exact successful 26844 17-stage procedure; no stage/compiler/native/assemble deviation.
Runtime allowlist: exactly 3 modified files, 0 additions, 0 deletions.
No backup branch.
26844 highlight/color/exposure/UI/DNG/UHDR/SR behavior is protected. LONG remains post-VGN luminance-only and cannot own RGB/chroma/detail/motion structure. 26845 adds bounded low-frequency LONG/NORMAL radiometric gain plus trust-gated flat-shadow residual luma cleanup with coherent NORMAL/LONG detail protection.
Upload folder 1, commit; folder 2, commit; folder 3, commit to trigger Actions.
Real Kotlin/Java/GLSL/NDK/full assemble are Actions authority; package is PREPARED/UPLOAD-READY until success.

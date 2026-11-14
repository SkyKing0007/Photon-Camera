# Photon 26934 V1 — original RawLens LKR brightness-driven highlights (B Super Res ON only)

## Start authority — LATEST SUCCESSFUL GitHub Actions artifact, never stale repo source

- Repository: SkyKing0007/Photon-Camera, branch `experimental-clean-photon-rebuild`
- **26933 V1 R2 successful Actions run:** `43648163655`; commit `bd60c7165e1df061bf139e5a2ad319a8df48c4ba`
- **26933 published artifact ID:** `14134754933`; SHA-256: `6cfefee31c96d7d8fb564f819e7033995ffd5f5bc619f66be434636c2cd2dd51`
- **Successful compiled-source TAR SHA-256:** `c64daa8305e3cc6e2e3ed44f83fa4cd67fdef9bfac50cd08029cddd11f3c1e28`; source files: **2048**
- **Actually executed 26933 runner SHA-256:** `37ce48534081392b67764ade0205c802648f771c6e5109f51446bcb86bd35e73`
- **Actually executed 26933 workflow SHA-256:** `cc5732ddc4fc03f8751e66b4f0e45f1e54cccb632f3534c724b9920f95b7568b`
- **Previously built 26933 APK SHA-256:** `2bf94d52fdafc06470c37baadeaa2d68b86e03228e6a9cc1bbb05d8816719e50`

## Intentional change and preserved scope

1. Experiment B, **Super Res ON** LKR only: replace 26933's chromaticity/third-channel-gated highlight fade with the **RawLens brightness-led 0.70–0.99 smooth-white convergence** in the existing *single* fused temporary-WB finishing shader.
2. White-balanced brightness drives the fade even if the highlight was corrupted to magenta. The physical original Bayer binary clip mask can accelerate actual clipped highlight cores, never veto earlier white shoulder.
3. The existing WB-inverse is applied once, with local achromatic target, not individual color clamps.
4. Leave native RawLens LKR **3 iterations × 2 steps**, AMaZE bypass, 50MP, Iris defringe, RawLens one-pass 3×3 chroma median, calibrated color, HDR, DNG and photo saving unchanged.
5. **Experiment B / Super Res OFF** source and SDR brightness/UHDR gainmap unchanged, along with all A, A+B, Night, LONG, Spektra and native/vendor code.
6. Exactly **2 modified, 0 added, 2046 protected unchanged**. No previous APK rebuild.

## vscode.dev THREE stages — upload at one relative repository root

- **Stage 1:** Upload files in `26934_V1_STAGE_1_UPLOAD_PATHS.txt`, preserving the internal directories and replacing matching scripts/manifests. Do not directly upload any APK or `.so` or use `handoff_payload_26934/app/...` as live app/src; the Actions runner applies the SHA-sealed source overlay against the successful 26933 TAR.
- **Stage 2:** Upload `.github/workflows/build-26934-change-aware.yml` exactly (from `26934_V1_STAGE_2_UPLOAD_PATHS.txt`).
- **Stage 3:** Upload `TRIGGER_26934.txt` last (from `26934_V1_STAGE_3_UPLOAD_PATHS.txt`), then commit once on `experimental-clean-photon-rebuild`.

**Suggested commit message:** Photon 26934 V1: B SR ON RawLens brightness-driven smooth-white highlights, preserve successful 26933 B OFF SDR-UHDR

## Guarded verification

- Replays the exact 26933 V1 R2 successful historical gates, including 26886/26887, 26903 and the original 26904 SPIR-V optimizer / CMake failures.
- Checks against the **actual 26933** full 2048-file SHA-locked compiled candidate, and uses signed/cross-hashed Actions artifact and executed builder/workflow/APK receipts.
- Runs source scope, B OFF invariant, shader contract, numerical clipping negative cases, reserved GLSL `coherent` injection, corruption/missing executable guards, forward/rollback patches, source/manifests and clean extraction.
- **In Actions only:** real pinned GLSL 16.5.0 ESSL300+310 and spirv-val/spirv-opt, native JNI/NDK both ABIs, Kotlin/Java compile, one full assembleDebug; no fallback to fake compiler or prior APK rebuild.
- Restores original exact RawLens native ABIs from **successful 26933 APK in the authenticated artifact**, not unauthenticated external RawLens GitHub API.
- Builds exactly one 26934 APK and only then publishes APK, successful compiled source TAR, actual builder/workflow hashes, receipts.

**Status:** PREPARED FOR ACTIONS, **not BUILD-PROVEN**; device image-quality unknown until installed photographs. Upload does not commit/push itself.

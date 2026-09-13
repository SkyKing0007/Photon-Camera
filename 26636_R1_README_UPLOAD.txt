PHOTON 26636 R1 — ISOLATED HEIC ULTRA HDR (MOTION + NIGHT, SUPER RES EXCLUDED)

RUNTIME AUTHORITY
- Successful 26635 R1 commit: e6790ebd2f2a8403191a276d659de4a708181efa
- Actions run: 34777964131
- Artifact: 10324098412 (photon-26635-r1-spatial-highlight-rolloff)
- Artifact ZIP SHA-256: fa1f51b03969edf1ce59934d33f46e4a688336d4c5270de18ba2237425a64b1b
- Exact compiled-candidate TAR SHA-256: fb5f2a3f48c737639e879aa2c7ee44c9c4a05d997aa9abc7424c3f69de7ad397
- Exact authority universe: 1713 app files.

VERIFICATION-MECHANICS AUTHORITY
- Exact successful 26635 R1 sequence is preserved: authority seed -> deterministic candidate -> semantic/regression ownership -> applicable shader gate -> authority-seeded live freeze -> Kotlin/Java -> both NDK ABIs -> full-index patches -> PRE-BUILD SAFETY -> full :app:assembleDebug -> one APK -> post-build invariance -> deterministic candidate export.
- 26636 modifies no GLSL, so the shader stage remains in sequence and proves the full shader universe invariant; real glslang is NOT APPLICABLE.

BACKUP
- User-created backup-26635-before-heic points to exact successful 26635 authority.

RUNTIME SCOPE
- Exactly 18 paths: 15 existing files modified + 3 new HEIC publisher files. See R1_26636_RUNTIME_CHANGED_PATHS.txt.
- 1713 base / 1716 candidate / 1698 protected / 801 protected native / 778 vendor / 7 DNG.
- Forward and rollback are deterministic full-index binary patches and are replayed at core.abbrev 7/12/40 with exact rollback.

HEIC CONTRACT
- HEIC is a fourth item in the existing top-left LiquidGlass output selector, using the same existing menu text style.
- HEIC is available only for Motion and Night, API 36+, with compatible hardware HEVC and Super Res OFF.
- Enabling Super Res while HEIC is selected returns the output selection to JPG; existing JPG/JPG+RAW/RAW selections are otherwise unchanged.
- Super Res / true-2x publication is explicitly excluded and its implementation remains protected.
- Existing JPEG/JPEG-R publication remains the reference branch and is not replaced.
- HEIC consumes the completed 8-bit Display-P3 SDR presentation via the existing Iris P3 conversion and the already-attached Iris gain map/metadata. It does not recompute gain-map math.
- Night HEIC consumes only the post-Jin attached/rebased gain map.
- Android 16-compatible hardware video/hevc MediaCodec is required. No x265/Kvazaar/software fallback and no silent SDR-only HEIC.
- ISO 21496-1 HEIF gain-map container support is pinned to libheif commit 4a3f74bc593ebfc29becc1ed5dd0a61cc66d40e1 plus the exact Google/libultrahdr v2.0.0 gain-map patch Git blob da5494f223f369781bbabcdaf6dbe192e0d74ca1.

VERSION
VERSION_NAME=0.9726636
VERSION_BUILD=26636

UPLOAD / COMMIT
Upload the contents of this ZIP to the root of experimental-clean-photon-rebuild in vscode.dev, preserving paths. Commit only the files supplied by this handoff and push that branch. Do not upload or commit an APK.

STATUS BEFORE ACTIONS
Prepared/upload-ready only after the packaged local-prebuild replay passes. Real Kotlin/Java/NDK/full Android assemble and post-build invariance are intentionally unclaimed until GitHub Actions succeeds.

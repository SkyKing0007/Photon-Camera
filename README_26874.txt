Photon 26874 — GUARDED VSCODE.DEV HANDOFF (not built until GitHub Actions proves)

Runtime authority: successful 26873 Actions run 40038942350
Runtime commit: bd9404291b96c45e2956d8c81c512462bca2558d
Runtime artifact: 12538711334, outer SHA256 f5a695cdba483f956eb63d6ad941d8442d39a0be990653a39c9473270f3f3ae6
Exact compiled-candidate TAR SHA256: 4cbd5e84c06c0e0b560c46d4bbbf360bf18c9d637496be022bb43ecf186c9d75
Verification authority: exact successful 26873 17-stage guarded script SHA256
121323a5eba3dca75ffb6f05089f73b180a6e692015895237cd780babb92aaa4
Branch: experimental-clean-photon-rebuild. NO backup. NO source commits/push by ChatGPT.

This is Experiment B's independent JPEG/R publication engine while keeping the Debug APK.
Effective B, Super Res OFF, lens-relative zoom <1.10x: B-only native optimized
libjpeg-turbo private static library, native 444 quality-98 baseline strip-parallel
encoding (decoded pixels equivalent to one-thread), concurrent gain-map encoding,
ICC attachment, in-memory Android JPEG/R packaging with exact Iris metadata,
atomic fsync/rename to publication path.
Effective B, Super Res ON: preserve existing direct RGB16F 50MP renderer,
full-pixel gain-map JPEG and true-2x 50MP SDR fallback; replace only JPEG/R
container assembly with the B-owned in-memory packager. No 12MP substitution.
A, B-selected high zoom with Super Res OFF routed exact A, Night, HEIC, DNG,
RAW color/tone/gain-map math, legacy JNI encoder all unchanged in active ownership.

Seven changed source files ONLY under handoff_payload_26874/app/.
Infrastructure difference from last success: generator + workflow + scoped B validation,
seven-file manifests + binary forward/rollback patch. A full explicit 17-stage
infrastructure diff and manifest hash are included. Workflow generates prior
successful 26871->26872->26873 mechanics before generating 26874.

Three-stage vscode.dev uploads, all on the active branch:
1. Upload ALL files listed in 26874_REPOSITORY_UPLOAD_ALLOWLIST.txt EXCEPT
   .github/workflows/build-26874-iris-rawr.yml and TRIGGER_26874.txt.
   Commit (message: "26874 Stage 1: Add isolated B JPEG/R native publisher and proofs").
   DO NOT PUSH.
2. Upload ONLY .github/workflows/build-26874-iris-rawr.yml.
   Commit (message: "26874 Stage 2: Add inherited guarded build workflow").
   DO NOT PUSH.
3. Upload ONLY TRIGGER_26874.txt.
   Commit (message: "26874 Stage 3: Trigger guarded B JPEG build").
   PUSH ONCE. Do not upload or commit any .apk or generated build_26874_iris_rawr.sh.

Local candidate proof: exact 1995-file prior universe, 1997-file new candidate,
7-file strict allowlist (5 existing modified, 2 new), protected 1990 files,
full-index forward/rollback git apply with core.abbrev 7/12/40, real prior
successful artifact rollback and active B/A routing regression. Pinned libjpeg
turbo source was built on Linux as an auxiliary host codec; its new strip
encoder passed decoded-pixel parity tests at 5 image dimensions.

IMPORTANT: These host checks are NOT Android compiler evidence. 26874 real Kotlin,
Java, pinned GLSL, NDK (both ABIs), full assembleDebug, final invariance, clean
handoff proof and device speed will only be authoritative if GitHub Actions
succeeds. No performance estimate is guaranteed.

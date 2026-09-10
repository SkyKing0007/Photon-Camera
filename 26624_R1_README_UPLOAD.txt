PHOTON CAMERA 26624 R1 — COMPONENT-OWNED SHORT RECOVERY

UPLOAD TARGET
Branch: experimental-clean-photon-rebuild
Expected current parent HEAD: 1a4f4bd99b785617ca6c18a232477953ab429b65
Expected parent: successful 26623 R1 adaptive upper tone + SHORT telemetry
Actions run: 34507995081
Artifact ID: 10164738775
Artifact ZIP SHA-256: 746c6c4058ec1f5d5b7ad3341bc6cd834222516bdd142430ea0d779f67fef718
Exact compiled candidate TAR SHA-256: c8ea95e0fea592753fc4cfb2a5a3e49a522e6e4b54b504db208807a890a55762
Target version/build: 0.9726624 / 26624
Backup: NONE (user requested no backup)

WHAT CHANGES
Runtime delta is exactly three files:
1. app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt
2. app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt
3. app/version.properties

26624 extends the already-active successful 26607 connected SHORT component path. Literal two-phase RAW clipping behaves exactly as before. Exposure-normalized effective/near-saturation NORMAL loss may now become component membership when that SAME probe has valid SHORT headroom; geometry still requires the existing sub-pixel same-CFA boundary proof and the existing CFA-safe neighboring-flow barrier. Once trust reaches an effective-loss cell, the existing physical/headroom guards can admit the actual aligned same-CFA SHORT sample into the same common Sabre accumulator. No spatial fill/inpainting/private SHORT RGB/late RGB blend is added.

WHAT IS FROZEN
Successful 26623 adaptive upper tone, complete Local Laplacian, viewfinder/displayGain solve, adaptive color, UHDR, true2x/native publication, DNG, capture exposure policy, CFA/Sabre common merge/Resolve/VGN, denoise and all non-SHORT runtime owners remain protected by authority manifests and semantic regression checks.

UPLOAD IN VSCODE.DEV
1. Confirm the branch is experimental-clean-photon-rebuild and the visible current commit is the successful 26623 commit above.
2. Extract this ZIP locally.
3. Upload/replace ALL extracted files into the repository ROOT, preserving paths.
4. IMPORTANT: do NOT manually copy handoff_payload_26624_r1/app/** into live app/**. The guarded Actions build reconstructs the exact candidate from the successful 26623 compiled artifact plus the canonical patch.
5. Source Control should contain only this sealed 26624 handoff package relative to the current successful 26623 commit. Commit once and push once.

Suggested commit message:
26624 R1 component-owned short recovery

Expected workflow:
Build 26624 R1 Component-Owned SHORT Recovery

STATUS BEFORE ACTIONS
Prepared/upload-ready only. Local packaged gates replay authority, candidate reconstruction, semantics/regressions, shader extraction/reserved scan and deterministic patches. Real pinned glslang, real Kotlin/Java compilers, both NDK ABIs, full :app:assembleDebug, exactly-one-APK and post-build invariance are authoritative only after the GitHub Actions run succeeds.

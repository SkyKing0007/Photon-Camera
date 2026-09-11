PHOTON CAMERA 26625 R1 — ROBUST SHORT FALLBACK GEOMETRY

UPLOAD TARGET
Branch: experimental-clean-photon-rebuild
Expected current parent HEAD: d0d48ab26006a868baa8525a0b81aad65939fac3
Expected parent: successful 26624 R1 component-owned SHORT recovery
Actions run: 34525392337
Artifact ID: 10171452870
Artifact ZIP SHA-256: d4f45ff32259ccb7d75f28e53189298ff325ecfa3beddf4e1440b7009693dac5
Exact compiled candidate TAR SHA-256: 99b7860aa385c4dc9256e1ea9c1ec0abe434c58c302d5ede24c4cbd28b8c0f30
Target version/build: 0.9726625 / 26625
Backup: NONE (user requested no backup)

WHAT CHANGES
Runtime delta is exactly three files:
1. app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt
2. app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt
3. app/version.properties

26625 addresses the exact 26624 direct-sun false-closed geometry case. The production SHORT local-affine field remains the primary geometry and its successful 26611 sub-pixel thresholds are unchanged. When a cell is outside that confidence envelope, 26625 may propose a deterministic frame-global affine built only from production-flow cells already inside <=0.95 RAW-pixel residual, with RANSAC/refit, >=30% inlier fraction, >=30% x/y spatial coverage and <=0.75 RAW-pixel model p90. This proposed geometry still cannot authorize SHORT by itself: the existing 5x5 same-CFA NORMAL/SHORT boundary radiometry must independently pass before component trust can seed. The exact geometry that passed boundary proof is then used for actual SHORT coverage/merge sampling only inside boundary-proven component trust.

WHAT IS FROZEN
Successful 26624 component-owned literal+effective-loss membership/rescue, component propagation/CFA-safe flow barrier, SHORT headroom and physical/source-clipping guards, common Sabre merge/Resolve/VGN, denoise, adaptive upper tone, complete Local Laplacian, viewfinder/displayGain, adaptive color, UHDR, true2x/native publication, DNG and capture exposure policy remain protected. No alignment threshold is globally loosened; no spatial fill/inpainting/private SHORT RGB/late RGB blend is added.

UPLOAD IN VSCODE.DEV
1. Confirm branch experimental-clean-photon-rebuild and current visible commit d0d48ab26006a868baa8525a0b81aad65939fac3.
2. Extract this ZIP locally.
3. Upload/replace ALL extracted files into the repository ROOT, preserving paths.
4. IMPORTANT: do NOT manually copy handoff_payload_26625_r1/app/** into live app/**. Actions reconstructs the exact candidate from successful 26624 compiled authority plus the canonical patch.
5. Commit once and push once.

Suggested commit message:
26625 R1 robust SHORT fallback geometry

Expected workflow:
Build 26625 R1 Robust SHORT Fallback Geometry

STATUS BEFORE ACTIONS
Prepared/upload-ready only. Local packaged gates replay exact 26624 authority, deterministic candidate reconstruction, semantic/regression checks, runtime-expanded shader reserved scans, infrastructure diff-audit and deterministic patches. Real pinned glslang, project Kotlin/Java, both NDK ABIs, full :app:assembleDebug, exactly-one-APK and post-build invariance are authoritative only after GitHub Actions succeeds.

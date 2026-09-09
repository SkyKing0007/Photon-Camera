26617 R1 — Capture-Adaptive Wronski Tonemap

BASE RUNTIME AUTHORITY
- successful 26616 R1.2
- commit 497206e90e0b286278b01dea54109769475a41f8
- Actions run 34387576106
- artifact ID 10118652261 / photon-26616-r1-wronski-exposure-fusion-ltm
- target branch experimental-clean-photon-rebuild

WHAT THIS HANDOFF DOES
- Runtime source is NOT committed directly in this ZIP.
- GitHub Actions downloads the exact successful 26616 artifact, reconstructs its final compiled candidate, applies the sealed deterministic full-index 26617 patch, verifies the exact 7-file runtime allowlist, and only then writes the authority-seeded candidate into the compiler worktree.
- Preserves the successful 26616 compact chandelier/ceiling X-reflection policy for compact physical highlights.
- Makes Wronski shadow/highlight synthetic exposure range capture-adaptive from signal statistics rather than a fixed +/-4 EV phone/scene tuning.
- Broad physical highlights can receive a stronger dark branch to prevent curtain/highlight flattening.
- Mips 4..2 reuse mip-5 exposure-selection authority while retaining branch-specific detail, preventing fine playpen/object edges from independently switching synthetic exposure and becoming traced/cartooned.
- boostLocalContrast remains false.
- Successful 26616 global exposure solver, physical HDR alpha/UHDR, true2x shared mip-2 solve, Sabre/SHORT/CFA/DNG/native/vendor ownership remain protected.
- No backup branch was created, per user request.

UPLOAD IN VSCODE.DEV
1. Confirm experimental-clean-photon-rebuild is currently at successful 26616 R1.2 commit 497206e90e0b286278b01dea54109769475a41f8.
2. Extract this ZIP locally if needed.
3. Upload/replace the ZIP contents at repository root, preserving .github/workflows/ and handoff_payload_26617/.
4. Do NOT copy handoff_payload_26617/app into repository live app/. It is sealed payload consumed by the guarded Actions build.
5. Source Control should show only this sealed 26617 handoff/infrastructure set, not live app/src changes.
6. Commit once and push once. Suggested message: 26617 R1 adaptive Wronski tonemap
7. The intended workflow is Build 26617 Adaptive Wronski Tonemap.

LOCAL STATUS AT PACKAGING
- Exact successful 26616 artifact/TAR authority replay: PASS.
- Deterministic candidate reconstruction: PASS.
- Adaptive-range / compact-highlight / structure-stable semantic regressions: PASS.
- Runtime allowlist: exactly 7 files.
- Full-index forward/rollback proof at core.abbrev 7/12/40: PASS.
- Protected/DNG/native/vendor invariance: PASS.
- Modified runtime-expanded reserved-identifier scan: PASS for 3 variants.
- REAL GLSL/Kotlin/Java/NDK/full assemble: NOT RUN locally; GitHub Actions is authoritative.

Do not call 26617 build-proven until its GitHub Actions run succeeds and the produced artifact/candidate is verified.

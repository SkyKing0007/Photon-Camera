PHOTON CAMERA 26626 R1 — BOUNDED SOURCE STRUCTURE + SHORT PROOF

UPLOAD TARGET
Branch: experimental-clean-photon-rebuild
Expected direct parent HEAD: 50764653ecd67e62b303ab0bf27325dd82ac4239
Target version/build: 0.9726626 / 26626
Backup: NONE (user explicitly requested no backup)

RUNTIME AUTHORITY
Successful 26625 R3 commit: 50764653ecd67e62b303ab0bf27325dd82ac4239
Actions run: 34552875046
Artifact ID: 10181524325
Artifact name: photon-26625-r1-robust-short-fallback-geometry
Artifact ZIP SHA-256: 8f339d2ed9c95f02b1e0d964b041e38147c3411307e1759a3624888d73fe14ac
Exact compiled candidate TAR SHA-256: d1ead1c9d881b784d8c57b1db9bd935f24562be3a0879c07b7df0d23365e7903

VERIFICATION-MECHANICS AUTHORITY
Successful 26624 R1 direct build sequence, commit d0d48ab26006a868baa8525a0b81aad65939fac3 / Actions run 34525392337.
26626 intentionally returns to the clean one-commit/direct-build mechanics that worked for 26624:
sealed package -> exact prior compiled artifact -> deterministic candidate -> semantic/regression/domain checks -> complete modified runtime-expanded GLSL reserved scan -> pinned real glslang -> authority-seeded live candidate -> real Kotlin/Java -> both NDK ABIs -> deterministic patches -> PRE-BUILD -> full :app:assembleDebug -> exactly one APK -> post-build invariance -> deterministic candidate export.
There is NO R2/R3 wrapper, NO git replace/graft, and NO --local-prebuild invocation from GitHub Actions.

INTENDED RUNTIME CHANGED-FILE ALLOWLIST — EXACTLY FIVE
1. app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl
2. app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt
3. app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt
4. app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java
5. app/version.properties

PRESENTATION CHANGE
- Successful 26625 remains the canonical baseline reconstruction.
- The existing 26623 global upper-tone owner remains unchanged.
- A source-domain Local-Laplacian reconstruction may preserve only bounded structure already present in the source.
- Maximum preservation strength is 0.30 * existing adaptive-enable * existing highlight pressure.
- Final source-guide gate begins at 0.65..0.72 and fades back out at 0.98..1.05 so lower body and genuine >1 HDR headroom remain under their existing 26625 owners.
- Fail-closed source-structure evidence uses balanced opposite-side structure at Local-Laplacian scales, capped by source structure; one-sided material steps, flat bright regions beside branches, and unsupported edges fall back to exact 26625.
- Existing 7 levels, 12 references, 0.35 EV detail radius, 0.94 large-edge slope and matched reduce/expand/reconstruct mechanics remain unchanged.
- Existing final RGB scalar application remains unchanged.
- Super Res ON and OFF share the same final corrected Local-Laplacian appearance map; no separate SR tone owner is added.

SHORT PROOF — READ-ONLY ONLY
- No existing SHORT threshold, geometry, radiometry, component propagation, flow barrier, source clip, physical weight, rescue weight, Sabre merge, Resolve or VGN equation changes.
- All 45 pre-existing embedded Sabre shader sources must remain byte-identical to successful 26625.
- Three new embedded shaders are diagnostic only: component/barrier coverage, normalized common-accumulator proxy, and pre/post SHORT accumulator delta.
- Telemetry distinguishes component membership from untrusted/barrier-frontier evidence and proves whether the unchanged final SHORT merge changes the common accumulator input.
- Telemetry must continue to state Resolve/output preservation is NOT directly measured; device image remains final visual proof.

PROTECTED OWNERS
Unchanged: global-log upper tone, Local-Laplacian reduce/accumulate/reconstruct, render.glsl RGB application, UHDR/gain-map policy, true2x/SR reconstruction and tree-edge protections, adaptive color, CFA reconstruction, denoise, AE/exposure policy, DNG, all inherited SHORT/CFA/Sabre shader equations, and all native/vendor code.

INFRASTRUCTURE SCOPE
New 26626 handoff/build/validator files are identity/scope adaptations around the successful 26624 direct sequence. The core compiler/NDK/patch/PRE-BUILD/assemble/postbuild order is intentionally unchanged. Infrastructure must be diff-audited against successful 26624 before Actions source writes.

UPLOAD IN VSCODE.DEV
1. Confirm branch experimental-clean-photon-rebuild and visible HEAD 50764653ecd67e62b303ab0bf27325dd82ac4239.
2. Extract this ZIP locally.
3. Upload/replace ALL extracted files into the repository ROOT, preserving paths.
4. Do NOT manually copy handoff_payload_26626_r1/app/** into live app/**. Actions reconstructs the exact candidate from successful 26625 compiled authority plus the canonical patch.
5. Source Control should show only this sealed 26626 handoff package; there should be no live app/** runtime edits.
6. Commit once and push once.

Suggested commit message:
26626 R1 bounded source structure and SHORT proof

Expected workflow:
Build 26626 R1 Bounded Source Structure + SHORT Proof

STATUS BEFORE ACTIONS
Prepared/upload-ready only after local clean-extract replay. Real pinned glslang, project Kotlin/Java compilers, both NDK ABIs, full :app:assembleDebug, exactly-one-APK and post-build invariance are authoritative only after the GitHub Actions run succeeds.

26616 R1.2 INFRASTRUCTURE COMPARATOR REPAIR

R1.1 reached real glslang 16.5.0 successfully and then failed only because verify_26616_infrastructure.py matched the 26616 handoff-scope git diff by the literal BASE_SUCCESS_COMMIT variable name while the exact successful 26615 R1.1 mechanism uses the equivalent HANDOFF_PARENT_COMMIT variable. R1.2 changes no runtime file, no 26616 patch, no Wronski math, no build script, no workflow, no allowlist, and no build ordering. It normalizes that infrastructure signature comparison to the git-diff command family and adds the exact failure as a permanent regression.

26616 R1.1 VIEWFINDER SHADER EXTRACTOR REPAIR

26616 R1 — Wronski Exposure Fusion Local Tone Mapping

BASE RUNTIME AUTHORITY
- successful 26615 R1.1
- commit 9ef80fb851bfa6d5e9ce3e0fceb1f907702edf54
- Actions run 34309735675
- artifact photon-26615-r1-iris-spatial-appearance
- target branch experimental-clean-photon-rebuild

WHAT THIS HANDOFF DOES
- Runtime source is NOT committed directly in this ZIP.
- GitHub Actions downloads the exact successful 26615 artifact, reconstructs its compiled candidate, applies the sealed deterministic full-index 26616 patch, verifies the exact 20-file runtime allowlist, and only then writes the authority-seeded candidate into the compiler worktree.
- Motion replaces 26615 coarse spatial presentation with one exact Wronski exposure-fusion LTM owner.
- Normal and true2x use one shared frozen Wronski solve.
- Night remains on its inherited path.
- Sabre/SHORT/CFA/DNG/physical HDR provenance remain protected.
- No backup branch was created, per user request.

UPLOAD IN VSCODE.DEV
1. Extract this ZIP locally if your browser does not expose its contents automatically.
2. Upload/replace the ZIP contents at the repository root on branch experimental-clean-photon-rebuild, preserving folders including .github/workflows/ and handoff_payload_26616/.
3. Do NOT copy handoff_payload_26616/app into the repository live app/ tree. It is a sealed payload consumed by the guarded build script.
4. Source Control should show only this sealed 26616 handoff/infrastructure set, not live app/src changes.
5. Commit the handoff and push once. Suggested commit message:
   26616 R1 Wronski exposure fusion LTM
6. The only intended workflow is: Build 26616 Wronski Exposure Fusion LTM.

LOCAL STATUS AT PACKAGING
- Exact 26615 artifact/TAR authority replay: PASS.
- Deterministic candidate reconstruction: PASS.
- One-LTM-owner / exact Wronski semantic gates: PASS.
- Runtime allowlist: exactly 20 files.
- Full-index forward/rollback proof at core.abbrev 7/12/40: PASS.
- Protected/DNG/native/vendor invariance: PASS.
- Runtime-expanded reserved-identifier scan: PASS for 12 variants.
- REAL GLSL/Kotlin/Java/NDK/full assemble: NOT RUN locally; GitHub Actions is required.

Do not call 26616 build-proven until its GitHub Actions run succeeds and the produced artifact/candidate is verified.


R1.1 repair note:
The failed R1 Actions run reached real glslang and failed only because verify_26616_shaders.py truncated the embedded viewfinder probe on a `);` sequence inside the GLSL string. R1.1 changes no runtime file, no 26616 patch, no Wronski math, no allowlist, and no build ordering. Replace the sealed handoff files with this R1.1 set and rerun the same 26616 workflow.

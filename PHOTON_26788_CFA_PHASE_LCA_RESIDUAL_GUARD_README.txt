PHOTON 26788 — VSCODE.DEV UPLOAD / COMMIT / PUSH

This handoff is PREPARED / UPLOAD-READY only. Real GLSL/Kotlin/Java/NDK/full assemble are NOT RUN locally.
GitHub Actions is the authoritative compiler/build proof.

No backup branch. Do not modify dev. Use branch: experimental-clean-photon-rebuild.
Do not upload or commit an APK.

TWO-STAGE UPLOAD — preserves the successful trigger pattern and prevents an incomplete-package build.

STAGE 1
Upload/replace every handoff file EXCEPT these two:
- .github/workflows/build-26788-jpeg-cfa-phase-residual.yml
- TRIGGER_26788.txt

This includes the handoff_payload_26788/ directory. Do NOT copy payload files into app/src yourself.
Commit and push Stage 1 to experimental-clean-photon-rebuild.
There should be no 26788 Actions run yet.

STAGE 2
Upload these two files together:
- .github/workflows/build-26788-jpeg-cfa-phase-residual.yml
- TRIGGER_26788.txt

Commit and push Stage 2 to experimental-clean-photon-rebuild.
The TRIGGER_26788.txt push starts the one intended 26788 workflow.

EXPECTED ACTIONS AUTHORITY IF SUCCESSFUL
- workflow: Build 26788 JPEG CFA Phase Residual
- artifact: photon-26788-jpeg-cfa-phase-residual
- APK: IrisCamera-0.9726788-26788-jpeg-cfa-phase-residual-debug.apk

The build reconstructs exact successful 26787 from Actions artifact 11529320634, applies the deterministic 3-file transform, verifies all manifests and semantic ownership, compiles exact runtime-expanded modified shaders with pinned glslang 16.5.0, runs real Kotlin/Java and both-ABI native compilers, proves forward/rollback patches at core.abbrev 7/12/40, emits PRE-BUILD SAFETY PROOF PASSED, runs full :app:assembleDebug, requires exactly one APK, then replays final invariance and clean extraction checks.
